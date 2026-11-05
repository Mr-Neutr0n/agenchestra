"""Panel penceresi son_30_gun: bugün dahil 30 takvim günü (I-393, ADR-0167); ayın başından bağımsız."""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import ork_lib as L  # noqa: E402


class Son30(unittest.TestCase):
    def test_sinir_gunleri(self):
        b = datetime.date(2026, 11, 2)   # ayın 2'si: eski 'bu_ay' tanımı yalnız 2 gün gösterirdi
        self.assertTrue(L.pencere_icinde("son_30_gun", b, b))
        self.assertTrue(L.pencere_icinde("son_30_gun", b - datetime.timedelta(days=29), b))
        self.assertFalse(L.pencere_icinde("son_30_gun", b - datetime.timedelta(days=30), b))
        self.assertFalse(L.pencere_icinde("son_30_gun", b + datetime.timedelta(days=1), b))

    def test_gun_sayisi_ve_onceki_aralik(self):
        b = datetime.date(2026, 11, 5)
        self.assertEqual(L.pencere_gun_sayisi("son_30_gun", b), 30)
        bas, bit = L.onceki_aralik("son_30_gun", b)
        self.assertEqual((bit - bas).days + 1, 30)
        self.assertEqual(bit, b - datetime.timedelta(days=30))

    def test_eski_anahtar_yok(self):
        self.assertNotIn("bu_ay", L.PENCERELER)
        self.assertIn("son_30_gun", L.PENCERELER)


if __name__ == "__main__":
    unittest.main()
