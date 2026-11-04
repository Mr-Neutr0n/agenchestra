"""I-364 P1: çıktı kanalı envanteri hook.py taramasıyla uyumlu (`python -m pytest tests/test_cikti_kanallari.py -q`)."""
import os
import re
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import cikti_kanallari as CK  # noqa: E402


class Envanter(unittest.TestCase):
    def test_s1_belgedeki_hook_kanali_sayisi_taramaya_esit(self):
        with open(CK.BELGE_YOLU, encoding="utf-8") as f:
            belge = f.read()
        yazili = int(re.search(r"Hook kanalı sayısı: (\d+)", belge).group(1))
        self.assertEqual(yazili, len(CK.tara()))
        self.assertEqual(belge.count("### "), len(CK.tara()) + len(CK.MODEL_KANALLARI))

    def test_belge_guncel(self):
        self.assertTrue(CK.kontrol(), "belge eskimiş: python scripts/cikti_kanallari.py")

    def test_tarama_bilinen_kanallari_bulur(self):
        adlar = {ad for ad, _ in CK.tara()}
        self.assertEqual(adlar, {"additionalContext", "systemMessage", "decision block", "permissionDecision"})

    def test_ihlal_yeni_kanal_belgede_yoksa_yakalanir(self):  # belge sayısı taramadan farklıysa kontrol kırmızı
        sahte = CK.uret("systemMessage")
        self.assertNotEqual(sahte, CK.uret())

    def test_demo_yedi_kanal_numarali_sirayla(self):
        d = CK.demo()
        for i in range(1, 8):
            self.assertIn(f"\n{i}. ", d)
        self.assertNotIn("\n8. ", d)


if __name__ == "__main__":
    unittest.main()
