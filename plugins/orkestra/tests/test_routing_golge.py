"""I-419: routing_v2 gölge kaydı; kapalıyken sessiz, gölgede yalnız gunluk.jsonl'a yazar, 56 alt tür verisi tutarlı.

`py -3.13 -m pytest plugins/orkestra/tests/test_routing_golge.py -q`
"""
import copy
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import routing_golge as RG  # noqa: E402

with open(os.path.join(KOK, "ayarlar", "model_politikasi.json"), encoding="utf-8") as f:
    BLOK = json.load(f)["routing_v2"]


def sd_golge(durum="golge"):
    sd = tempfile.mkdtemp()
    b = copy.deepcopy(BLOK)
    b["durum"] = durum
    with open(os.path.join(sd, "model_politikasi.json"), "w", encoding="utf-8") as f:
        json.dump({"routing_v2": b}, f)
    return sd


class GolgeTesti(unittest.TestCase):
    def test_kapaliyken_none_ve_yazmaz(self):
        sd = sd_golge("kapali")
        self.assertIsNone(RG.karsilastir({"basamak": "T2", "risk": "orta"}, sd))
        RG.kaydet(sd, {"basamak": "T2", "risk": "orta", "is": "I-1"})
        self.assertFalse(os.path.exists(os.path.join(sd, "gunluk.jsonl")))

    def test_golgede_karsilastirir(self):
        s = RG.karsilastir({"basamak": "T2", "risk": "orta"}, sd_golge())
        self.assertEqual(s["v1"], {"model": "sonnet", "effort": "medium"})
        self.assertEqual(s["v2"]["model"], "sonnet")
        self.assertTrue(s["ayni"])

    def test_yuksek_risk_v2_farkli(self):
        s = RG.karsilastir({"basamak": "T1", "risk": "yuksek"}, sd_golge())
        self.assertFalse(s["ayni"])
        self.assertEqual(s["v2"]["profil"], "architecture")

    def test_gunluge_yazar(self):
        sd = sd_golge()
        RG.kaydet(sd, {"basamak": "T1", "risk": "yuksek", "is": "I-1"})
        with open(os.path.join(sd, "gunluk.jsonl"), encoding="utf-8") as f:
            k = json.loads(f.readline())
        self.assertEqual((k["tur"], k["kapi"]), ("kapi_golge", "routing_v2"))

    def test_bozuk_kart_dusurmez(self):
        RG.kaydet(sd_golge(), {"basamak": None, "risk": None})
        RG.kaydet(sd_golge(), {})

    def test_alt_tur_risk_tabani(self):
        t = next(t for t in json.load(open(RG.ALT_TUR_DOSYASI, encoding="utf-8"))["alt_turler"] if t["risk_floor"] >= 2)
        s = RG.karsilastir({"basamak": "T1", "risk": "dusuk", "alt_tur": t["id"]}, sd_golge())
        self.assertGreaterEqual(s["v2"]["risk"], t["risk_floor"])


class AltTurVerisiTesti(unittest.TestCase):
    def test_56_benzersiz_ve_hipotez(self):
        d = json.load(open(RG.ALT_TUR_DOSYASI, encoding="utf-8"))
        ids = [t["id"] for t in d["alt_turler"]]
        self.assertEqual((len(ids), len(set(ids))), (56, 56))
        self.assertEqual(d["durum"], "HYPOTHESIS_NOT_BENCHMARKED")

    def test_modeller_yasak_degil(self):
        import model_politika as MP
        for t in json.load(open(RG.ALT_TUR_DOSYASI, encoding="utf-8"))["alt_turler"]:
            self.assertFalse(MP.yasak_mi(t["proposed_model"]), t["id"])


if __name__ == "__main__":
    unittest.main()
