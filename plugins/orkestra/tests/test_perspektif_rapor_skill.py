"""I-347 P5: skill hattı ölçümü — halka sayıları ve tıkanan halka."""
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import perspektif_rapor as R  # noqa: E402


class TikananTest(unittest.TestCase):
    def h(self, **k):
        d = dict.fromkeys(R.HALKALAR, 1)
        d.update(k)
        return d

    def test_ilk_sifir_halka(self):
        self.assertEqual(R.tikanan(self.h(rapor_maddesi=0, kume_anan=0, taslak=0)), "rapor_maddesi")

    def test_tum_halkalar_doluysa_yok(self):
        self.assertIsNone(R.tikanan(self.h()))

    def test_istek_yoksa_istek_tikanir(self):
        self.assertEqual(R.tikanan(dict.fromkeys(R.HALKALAR, 0)), "istek")


class OlcTest(unittest.TestCase):
    def test_bos_durum_dizininde_hata_vermez(self):
        proje = tempfile.mkdtemp()
        sd = os.path.join(proje, ".claude", "orkestra")
        os.makedirs(sd)
        o = R.olc(sd)
        self.assertEqual(o["halkalar"]["istek"], 0)
        self.assertEqual(o["tikanan"], "istek")
        json.dumps(o)

    def test_taslak_ve_istek_sayilir(self):
        proje = tempfile.mkdtemp()
        sd = os.path.join(proje, ".claude", "orkestra")
        os.makedirs(os.path.join(sd, "onerilen_skill", "x"))
        with open(os.path.join(sd, "onerilen_skill", "x", "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("x")
        self.assertEqual(R.olc(sd)["halkalar"]["taslak"], 1)


if __name__ == "__main__":
    unittest.main()
