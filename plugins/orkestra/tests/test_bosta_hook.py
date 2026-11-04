"""I-376 (ADR-0158): bekleme anı bağlamı (scripts/bosta_baglam.py) ve CLI.
`PYTHONUTF8=1 py -3.13 -m pytest -q plugins/orkestra/tests/test_bosta_hook.py`
"""
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bosta as B  # noqa: E402
import bosta_baglam as BB  # noqa: E402
from test_bosta import madde, plan  # noqa: E402


def kart(is_id, ref, **alan):
    return {"id": f"G-{ref}", "is": is_id, "ref": ref, **alan}


class BaglamSatiri(unittest.TestCase):
    def test_aday_yoksa_sifir_karakter(self):
        self.assertEqual(BB.baglam_satiri({"adaylar": [], "elenen": {}}, "I-1"), "")

    def test_aday_varsa_en_cok_300_ve_numaralar_cekirdekle_ayni(self):
        p = plan(*[madde(n, yazma=f"d{n}.py") for n in range(1, 40)])
        s = B.baslatilabilir(p, {1: "denetimde"})
        satir = BB.baglam_satiri(s, "I-376")
        self.assertLessEqual(len(satir), 300)
        self.assertTrue(satir.startswith("orkestra (gölge) bosta"))
        self.assertIn(f"P{s['adaylar'][0]}", satir)

    def test_hesapla_bekleyen_denetimde_sayilir(self):
        p = plan(madde(1), madde(2, once="P1 — Çıktı: m"))
        self.assertEqual(BB.hesapla(p, None, {}, bekleyen=[1])["adaylar"], [])
        self.assertEqual(BB.hesapla(p, None, {}, bekleyen=[])["adaylar"], [1])


class HookSatiri(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.plan = os.path.join(self.t, "plan.md")
        with open(self.plan, "w", encoding="utf-8") as f:
            f.write(plan(madde(1), madde(2), madde(3, once="P1 — Çıktı: m")))

    def satir(self, bekleyen=(1,)):
        return BB.hook_satiri(self.t, self.t, "I-9", self.plan, None, bekleyen)

    def test_aday_varsa_satir_ve_olay(self):
        s = self.satir()
        self.assertIn("P2", s)
        self.assertNotIn("P3", s.split("Ayrıntı")[0])
        with open(os.path.join(self.t, "gunluk.jsonl"), encoding="utf-8") as f:
            olay = json.loads(f.readline())
        self.assertEqual((olay["tur"], olay["adaylar"]), ("bosta_aday", ["P2"]))

    def test_ortam_degiskeni_kapatir(self):
        os.environ["ORKESTRA_BOSTA"] = "0"
        try:
            self.assertEqual(self.satir(), "")
        finally:
            del os.environ["ORKESTRA_BOSTA"]

    def test_plan_yoksa_bos(self):
        self.assertEqual(BB.hook_satiri(self.t, self.t, "I-9", os.path.join(self.t, "yok.md"), None), "")

    def test_gecersiz_olayi(self):
        BB.gecersiz_yaz(self.t, "I-9", 2, "bağımlılık ret")
        with open(os.path.join(self.t, "gunluk.jsonl"), encoding="utf-8") as f:
            olay = json.loads(f.readline())
        self.assertEqual((olay["tur"], olay["madde"]), ("bosta_gecersiz", "P2"))

    def test_kart_durumu_ref_ve_is_ile_eslesir(self):
        os.makedirs(os.path.join(self.t, "gorevler"))
        for ad, k in (("G-1", kart("I-9", "P1", durum="teslim")), ("G-2", kart("I-8", "P2", durum="teslim"))):
            with open(os.path.join(self.t, "gorevler", ad + ".json"), "w", encoding="utf-8") as f:
                json.dump({**k, "id": ad}, f)
        self.assertEqual(BB.kart_durumlari(self.t, "I-9"), {1: "teslim"})


if __name__ == "__main__":
    unittest.main()
