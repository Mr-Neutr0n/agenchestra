"""is_anlati._gaplar hem yeni (## 5.) hem eski (## 6.) Gap analizi düzenini okur.

Kabul kriterleri:
  K1  `## 5. Gap analizi` altındaki `- **G<n>:**` satırları okunur.
  K2  `## 6. Gap analizi` altındaki satırlar okunur (eski düzen).
  K3  Gap bölümü yoksa liste boştur.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import is_anlati  # noqa: E402


class GapBolumTest(unittest.TestCase):
    def test_k1_yeni_duzen(self):
        md = "# B\n\n## 5. Gap analizi\n\n- **G1:** hedef → mevcut → fark\n"
        self.assertEqual([g for g, _ in is_anlati._gaplar(md)], ["G1"])

    def test_k2_eski_duzen(self):
        md = "# B\n\n## 6. Gap analizi\n\n- **G1:** a\n- **G2:** b\n"
        self.assertEqual([g for g, _ in is_anlati._gaplar(md)], ["G1", "G2"])

    def test_k3_bolum_yok(self):
        self.assertEqual(is_anlati._gaplar("# B\n\n## 1. Hedef\n"), [])


if __name__ == "__main__":
    unittest.main()
