"""I-423 / ADR-0174: arşivli oturum süreç eşlemesi. Anahtar yalnız `--resume=<cliSessionId>`; `--add-dir` yanılgısı eşleşmez."""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import arsiv_surec as A  # noqa: E402

ARS = "cf820118-32c9-4dd7-80e1-106541106719"      # arşivli oturumun cliSessionId
CANLI = "c1b94c9b-6559-443d-9108-ea742700ef1d"    # çalışan oturumun cliSessionId


def _s(pid, komut, ad="claude.exe"):
    return {"pid": pid, "ad": ad, "komut": komut}


class Esleme(unittest.TestCase):
    def test_arsivli_resume_eslesir(self):
        r = A.eslestir([_s(1, f"claude.exe --output-format stream-json --resume={ARS} --model x")], {ARS})
        self.assertEqual([x["pid"] for x in r], [1])

    def test_arsivsiz_resume_eslesmez(self):
        self.assertEqual(A.eslestir([_s(2, f"claude.exe --resume={CANLI}")], {ARS}), [])

    def test_add_dir_yanilgisi_eslesmez(self):
        """Canlı süreç arşivli oturumun not klasörünü taşır: kimlik yalnız --add-dir'de, --resume canlı."""
        k = f"claude.exe --resume={CANLI} --add-dir=C:/x/side-session-notes/local_408cc622-cca4-470e-a36b-0455dcee6863"
        self.assertEqual(A.eslestir([_s(3, k)], {ARS, "408cc622-cca4-470e-a36b-0455dcee6863"}), [])

    def test_uygulama_surecleri_eslesmez(self):
        for t in ("renderer", "gpu-process", "utility", "crashpad-handler"):
            with self.subTest(t=t):
                self.assertEqual(A.eslestir([_s(4, f"claude.exe --type={t} --resume={ARS}")], {ARS}), [])

    def test_kimliksiz_ve_baska_ad_eslesmez(self):
        self.assertEqual(A.eslestir([_s(5, "claude.exe --output-format x")], {ARS}), [])
        self.assertEqual(A.eslestir([_s(6, f"node.exe --resume={ARS}", ad="node.exe")], {ARS}), [])

    def test_bozuk_girdi(self):
        self.assertEqual(A.eslestir(None, {ARS}), [])
        self.assertEqual(A.eslestir([{"pid": "x"}, {}], {ARS}), [])


class Meta(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp(prefix="ork_meta_")
        self.d = os.path.join(self.t, "a", "b")
        os.makedirs(self.d)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def _yaz(self, ad, kim, arsiv):
        with open(os.path.join(self.d, f"local_{ad}.json"), "w", encoding="utf-8") as f:
            json.dump({"sessionId": "local_" + ad, "cliSessionId": kim, "isArchived": arsiv}, f)

    def test_yalniz_arsivli_kimlikler(self):
        self._yaz("1", ARS, True)
        self._yaz("2", CANLI, False)
        self.assertEqual(A.arsivli_kimlikler([self.t]), {ARS})

    def test_ayni_kimlik_arsivsizde_de_varsa_cikarilir(self):
        self._yaz("1", ARS, True)
        self._yaz("2", ARS, False)
        self.assertEqual(A.arsivli_kimlikler([self.t]), set())

    def test_bozuk_meta_atlanir(self):
        with open(os.path.join(self.d, "local_x.json"), "w") as f:
            f.write("{bozuk")
        self._yaz("1", ARS, True)
        self.assertEqual(A.arsivli_kimlikler([self.t]), {ARS})


if __name__ == "__main__":
    unittest.main()
