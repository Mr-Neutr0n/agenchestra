"""I-419 Faz 05-08: routing_policy, platform_capabilities, escalation_policy saf fonksiyon testleri.

`py -3.13 -m pytest plugins/orkestra/tests/test_routing_v2.py -q`
"""
import json
import os
import sys
import unittest

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import escalation_policy as EP  # noqa: E402
import platform_capabilities as PC  # noqa: E402
import routing_policy as RP  # noqa: E402

with open(os.path.join(KOK, "ayarlar", "model_politikasi.json"), encoding="utf-8") as f:
    BLOK = json.load(f)["routing_v2"]


class KararTesti(unittest.TestCase):
    def test_standart_eslesme(self):
        k = RP.karar({"karmasiklik": "standard", "risk": 1, "dogrulanabilirlik": "full"}, BLOK)
        self.assertEqual((k["profil"], k["model"], k["effort"]), ("standard", "sonnet", "medium"))
        self.assertEqual(k["reason_codes"], ["varsayilan-eslesme"])

    def test_risk_profili_yukseltir(self):
        k = RP.karar({"karmasiklik": "mechanical", "risk": 3, "dogrulanabilirlik": "full"}, BLOK)
        self.assertEqual(k["profil"], "architecture")
        self.assertTrue(any(c.startswith("risk-tavani-yukseltti") for c in k["reason_codes"]))

    def test_bilinmeyen_girdi_fail_closed(self):
        k = RP.karar({}, BLOK)
        self.assertEqual(k["risk"], 3)
        self.assertIn("risk-bilinmiyor-en-yuksek", k["reason_codes"])
        self.assertEqual(k["denetci_model"], "opus")

    def test_denetci_her_zaman_zorunlu(self):
        for r in range(4):
            self.assertTrue(RP.karar({"karmasiklik": "scoped", "risk": r}, BLOK)["denetci_zorunlu"])

    def test_deterministik_ve_hash(self):
        a = RP.karar({"karmasiklik": "complex", "risk": 2}, BLOK)
        self.assertEqual(a, RP.karar({"karmasiklik": "complex", "risk": 2}, BLOK))
        self.assertEqual(len(a["policy_hash"]), 12)

    def test_risk_bool_gecersiz(self):
        self.assertEqual(RP.karar({"karmasiklik": "scoped", "risk": True}, BLOK)["risk"], 3)


class PlatformTesti(unittest.TestCase):
    K = {"model": "sonnet", "effort": "medium", "risk": 2}

    def test_ok(self):
        r = PC.kontrol(self.K, "claude_code", {"model": "sonnet", "effort": "medium"})
        self.assertEqual((r["durum"], r["engel"]), ("OK", False))

    def test_mismatch_yuksek_riskte_engel(self):
        r = PC.kontrol(self.K, "claude_code", {"model": "haiku", "effort": "medium"})
        self.assertEqual((r["durum"], r["engel"]), ("MISMATCH", True))

    def test_mismatch_dusuk_riskte_uyari(self):
        r = PC.kontrol({**self.K, "risk": 1}, "claude_code", {"model": "haiku", "effort": "low"})
        self.assertEqual((r["durum"], r["engel"]), ("MISMATCH", False))

    def test_cursor_unsupported(self):
        self.assertEqual(PC.kontrol(self.K, "cursor")["durum"], "UNSUPPORTED")

    def test_gozlem_yok_unverified(self):
        self.assertEqual(PC.kontrol(self.K, "claude_code")["durum"], "UNVERIFIED")

    def test_bilinmeyen_platform(self):
        self.assertTrue(PC.kontrol(self.K, "x")["engel"])


class EskalasyonTesti(unittest.TestCase):
    def test_ortam_yukseltmez(self):
        self.assertEqual(EP.sonraki("ortam", 5, "standard", BLOK)["eylem"], "ortam-duzelt")

    def test_kriter_belirsiz_karti_duzeltir(self):
        self.assertEqual(EP.sonraki("kriter-belirsiz", 3, "standard", BLOK)["eylem"], "kart-duzelt")

    def test_bir_ret_devam(self):
        self.assertEqual(EP.sonraki(None, 1, "standard", BLOK)["eylem"], "devam")

    def test_iki_ret_once_effort(self):
        r = EP.sonraki(None, 2, "standard", BLOK)
        self.assertEqual((r["eylem"], r["profil"], r["adim"]), ("yukselt", "complex", "effort"))

    def test_yetenek_yetersiz_model_degisimi(self):
        r = EP.sonraki("yetenek-yetersiz", 0, "complex", BLOK)
        self.assertEqual((r["profil"], r["adim"]), ("architecture", "model"))

    def test_en_ust_profilde_son(self):
        self.assertEqual(EP.sonraki("yetenek-yetersiz", 0, "frontier", BLOK)["eylem"], "son")


if __name__ == "__main__":
    unittest.main()
