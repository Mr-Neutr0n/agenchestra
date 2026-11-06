"""I-410 (ADR-0158): kart açılma kapısı (gölge). Eşiği aşan iş kartsız yürütülürse kapi_golge/kart_acilma
yazılır; yazma işlemi engellenmez. `py -3.13 -m pytest plugins/orkestra/tests/test_kart_golge.py`
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import hook  # noqa: E402


class KartGolgeKapisiTest(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp(prefix="ork_kart_golge_")
        self._esik_patch = mock.patch.object(hook, "_kart_golge_esik", return_value=3)
        self._esik_patch.start()
        self._bagli_patch = mock.patch.object(hook, "_bagli_is", return_value="I-410")
        self._bagli_patch.start()

    def tearDown(self):
        self._esik_patch.stop()
        self._bagli_patch.stop()
        shutil.rmtree(self.sd, ignore_errors=True)
        os.environ.pop("ORKESTRA_KART_GOLGE", None)

    def _kayitlar(self):
        yol = os.path.join(self.sd, "gunluk.jsonl")
        if not os.path.exists(yol):
            return []
        with open(yol, encoding="utf-8") as f:
            return [json.loads(x) for x in f if x.strip()]

    def _kart_yok(self):
        return mock.patch.object(hook, "_kart_acik_mi", return_value=False)

    def _kart_var(self):
        return mock.patch.object(hook, "_kart_acik_mi", return_value=True)

    def _yaz(self, n, proje=None):
        proje = proje or self.sd
        with self._kart_yok():
            for i in range(n):
                hook._kart_golge_kapisi(self.sd, "o1", None, proje, os.path.join(proje, f"dosya{i}.py"))

    def test_esik_altinda_yazmaz(self):
        self._yaz(3)  # esik 3: 3 dosya esigi asmaz (> 3 degil)
        self.assertEqual(self._kayitlar(), [])

    def test_esik_asilinca_bir_kez_yazar(self):
        self._yaz(5)
        k = [x for x in self._kayitlar() if x.get("kapi") == "kart_acilma"]
        self.assertEqual(len(k), 1)
        self.assertEqual(k[0]["tur"], "kapi_golge")
        self.assertEqual(k[0]["is"], "I-410")
        self.assertEqual(k[0]["dosya_sayisi"], 4)

    def test_acik_kart_varsa_yazmaz(self):
        with self._kart_var():
            for i in range(5):
                hook._kart_golge_kapisi(self.sd, "o1", None, self.sd, os.path.join(self.sd, f"dosya{i}.py"))
        self.assertEqual(self._kayitlar(), [])

    def test_acik_kart_sayaci_sifirlar(self):
        self._yaz(5)
        self.assertTrue(self._kayitlar())
        open(os.path.join(self.sd, "gunluk.jsonl"), "w", encoding="utf-8").close()
        with self._kart_var():
            hook._kart_golge_kapisi(self.sd, "o1", None, self.sd, os.path.join(self.sd, "sonradan.py"))
        self._yaz(5)
        k = [x for x in self._kayitlar() if x.get("kapi") == "kart_acilma"]
        self.assertEqual(len(k), 1)  # kart görülünce sayaç sıfırlanır, yeniden eşik aşılınca tek kayıt

    def test_alt_ajan_muaf(self):
        with self._kart_yok():
            for i in range(5):
                hook._kart_golge_kapisi(self.sd, "o1", "alt-1", self.sd, os.path.join(self.sd, f"dosya{i}.py"))
        self.assertEqual(self._kayitlar(), [])

    def test_env_kapatir(self):
        os.environ["ORKESTRA_KART_GOLGE"] = "0"
        self._yaz(5)
        self.assertEqual(self._kayitlar(), [])

    def test_bagli_is_yoksa_yazmaz(self):
        with mock.patch.object(hook, "_bagli_is", return_value=None):
            self._yaz(5)
        self.assertEqual(self._kayitlar(), [])


if __name__ == "__main__":
    unittest.main()
