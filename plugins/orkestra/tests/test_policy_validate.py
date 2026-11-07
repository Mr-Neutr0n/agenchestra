"""I-419 Faz 04: routing_v2 bloğu doğrulayıcısı ve v2_durum fail-closed davranışı.

`py -3.13 -m pytest plugins/orkestra/tests/test_policy_validate.py -q`
"""
import copy
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import model_politika as MP  # noqa: E402
import policy_validate as PV  # noqa: E402

AYAR = os.path.join(KOK, "ayarlar", "model_politikasi.json")


def cfg():
    with open(AYAR, encoding="utf-8") as f:
        return json.load(f)


class DogrulamaTesti(unittest.TestCase):
    def test_gercek_dosya_gecerli_ve_kapali(self):
        c = cfg()
        self.assertTrue(PV.dogrula(c, MP.yasak_mi)["gecerli"])
        self.assertEqual(c["routing_v2"]["durum"], "kapali")

    def test_v1_alanlari_degismedi(self):
        c = cfg()
        self.assertEqual(c["basamak"]["T4"], {"model": "opus", "effort": "xhigh"})
        self.assertEqual(c["surum"], 1)

    def test_blok_yoksa_gecersiz(self):
        c = cfg()
        del c["routing_v2"]
        self.assertEqual(PV.dogrula(c)["hatalar"], ["blok-yok"])

    def test_gecersiz_effort_reddedilir(self):
        c = cfg()
        c["routing_v2"]["route_profiles"]["standard"]["effort"] = "ultra"
        self.assertIn("effort-gecersiz: standard='ultra'", PV.dogrula(c)["hatalar"])

    def test_yasak_model_reddedilir(self):
        c = cfg()
        c["routing_v2"]["route_profiles"]["complex"]["model"] = "claude-fable-5-1"
        r = PV.dogrula(c, MP.yasak_mi)
        self.assertFalse(r["gecerli"])
        self.assertIn("model-yasak: complex=claude-fable-5-1", r["hatalar"])

    def test_risk_araligi_ve_tur(self):
        c = cfg()
        c["routing_v2"]["route_profiles"]["mechanical"]["risk_ceiling"] = 9
        c["routing_v2"]["route_profiles"]["scoped"]["risk_ceiling"] = True
        h = PV.dogrula(c)["hatalar"]
        self.assertIn("risk_ceiling-gecersiz: mechanical=9", h)
        self.assertIn("risk_ceiling-gecersiz: scoped=True", h)

    def test_belirsiz_risk_en_yuksek_olmali(self):
        c = cfg()
        c["routing_v2"]["routing_defaults"]["unknown_risk"] = 1
        self.assertIn("unknown_risk-en-yuksek-degil", PV.dogrula(c)["hatalar"])

    def test_risk3_haiku_reddedilir(self):
        c = cfg()
        p = c["routing_v2"]["route_profiles"]["architecture"]
        p["model"] = "haiku"
        self.assertIn("risk3-haiku: architecture", PV.dogrula(c)["hatalar"])

    def test_dogrulama_zorunlu(self):
        c = cfg()
        c["routing_v2"]["route_profiles"]["frontier"]["verify_required"] = False
        self.assertIn("dogrulama-zorunlu-degil: frontier", PV.dogrula(c)["hatalar"])

    def test_sozluk_olmayan_girdi(self):
        self.assertFalse(PV.dogrula(None)["gecerli"])


class V2DurumTesti(unittest.TestCase):
    def test_varsayilan_kapali(self):
        self.assertEqual(MP.v2_durum()["durum"], "kapali")

    def test_proje_ezmesi_acar_ama_gecersizse_kapanir(self):
        with tempfile.TemporaryDirectory() as sd:
            c = copy.deepcopy(cfg()["routing_v2"])
            c["durum"] = "golge"
            with open(os.path.join(sd, "model_politikasi.json"), "w", encoding="utf-8") as f:
                json.dump({"routing_v2": c}, f)
            self.assertEqual(MP.v2_durum(sd)["durum"], "golge")
            c["route_profiles"]["standard"]["effort"] = "ultra"
            with open(os.path.join(sd, "model_politikasi.json"), "w", encoding="utf-8") as f:
                json.dump({"routing_v2": c}, f)
            r = MP.v2_durum(sd)
            self.assertEqual(r["durum"], "kapali")
            self.assertFalse(r["gecerli"])

    def test_ortam_degiskeni_kapatir(self):
        with tempfile.TemporaryDirectory() as sd:
            c = copy.deepcopy(cfg()["routing_v2"])
            c["durum"] = "acik"
            with open(os.path.join(sd, "model_politikasi.json"), "w", encoding="utf-8") as f:
                json.dump({"routing_v2": c}, f)
            os.environ["ORKESTRA_ROUTING_V2"] = "0"
            try:
                self.assertEqual(MP.v2_durum(sd)["durum"], "kapali")
            finally:
                del os.environ["ORKESTRA_ROUTING_V2"]


if __name__ == "__main__":
    unittest.main()
