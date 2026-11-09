"""I-423 / ADR-0174: bakım adımı. Gölge modda süreç kapatılmaz yalnız kayıt düşer; ihlalde kapatılır; env kapatır."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import arsiv_surec as A  # noqa: E402
import kapi_mod  # noqa: E402

ARS = "cf820118-32c9-4dd7-80e1-106541106719"
SUREC = [{"pid": 999991, "ad": "claude.exe", "komut": f"claude.exe --resume={ARS}"},
         {"pid": 999992, "ad": "claude.exe", "komut": "claude.exe --type=renderer"}]


class Bakim(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp(prefix="ork_sd_")

    def tearDown(self):
        shutil.rmtree(self.sd, ignore_errors=True)

    def _gunluk(self):
        try:
            with open(os.path.join(self.sd, "gunluk.jsonl"), encoding="utf-8") as f:
                return [json.loads(x) for x in f if x.strip()]
        except OSError:
            return []

    def test_golge_kapatmaz_kaydeder(self):
        k = mock.Mock(return_value=True)
        with mock.patch.object(kapi_mod, "mod", return_value="golge"):
            r = A.calistir(self.sd, "", surecler=SUREC, arsivli={ARS}, kapatici=k)
        k.assert_not_called()
        self.assertEqual(r["eslesen"], 1)
        g = self._gunluk()
        self.assertEqual([(x["tur"], x["pid"], x["resume"]) for x in g], [("kapi_golge", 999991, ARS)])

    def test_ihlal_kapatir(self):
        k = mock.Mock(return_value=True)
        with mock.patch.object(kapi_mod, "mod", return_value="ihlal"):
            r = A.calistir(self.sd, "", surecler=SUREC, arsivli={ARS}, kapatici=k)
        k.assert_called_once_with(999991)
        self.assertEqual(r["kapatilan"], 1)

    def test_env_kapatir(self):
        k = mock.Mock(return_value=True)
        with mock.patch.dict(os.environ, {"ORKESTRA_ARSIV_SUREC_KAPAT": "0"}), mock.patch.object(kapi_mod, "mod", return_value="ihlal"):
            self.assertEqual(A.calistir(self.sd, "", surecler=SUREC, arsivli={ARS}, kapatici=k), {})
        k.assert_not_called()

    def test_eslesme_yoksa_bos_ve_kayitsiz(self):
        with mock.patch.object(kapi_mod, "mod", return_value="ihlal"):
            self.assertEqual(A.calistir(self.sd, "", surecler=SUREC, arsivli=set(), kapatici=mock.Mock()), {})
        self.assertEqual(self._gunluk(), [])

    def test_ayar_dosyasi_golge(self):
        self.assertEqual(kapi_mod.mod(A.KAPI), "golge")

    def test_bakim_adimi_kayitli(self):
        import oturum_bakim
        self.assertIn("arsiv_surec", [a for a, _ in oturum_bakim._adimlar(self.sd, "")])


if __name__ == "__main__":
    unittest.main()
