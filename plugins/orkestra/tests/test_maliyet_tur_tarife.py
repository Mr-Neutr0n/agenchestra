"""ADR-0133: `orkestra maliyet tur` yazıcısı önbellek yazma tarifesini ajan türüne göre damgalar ve fiyatlar.

`py -3.13 -m pytest plugins/orkestra/tests/test_maliyet_tur_tarife.py -q -p no:cacheprovider`

- K1 alt ajan turu: tarife '5dk', maliyet 5dk yazma fiyatıyla.
- K2 ana ajan turu: tarife '1sa', maliyet 1sa yazma fiyatıyla.
"""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_maliyet_tur_is import AID, _Ortak  # noqa: E402

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import ork_lib as L  # noqa: E402


def beklenen(tarife):
    f = L.model_fiyati("claude-sonnet-5-5")
    return round((100 * f["giris"] + 50 * f["cikis"] + 30 * f["onbellek_okuma"] + 20 * f["onbellek_yazma_" + tarife]) / 1e6, 6)


class TestTurTarife(_Ortak):
    def test_k1_alt_ajan_5dk(self):
        self.ajan_onbellek("-", surec="bilinmiyor", ajan="?")
        r = self.tur(AID)
        self.assertEqual(r["tarife"], "5dk")
        self.assertEqual(r["maliyet_usd"], beklenen("5dk"))

    def test_k2_ana_ajan_1sa(self):
        r = self.tur()
        self.assertEqual(r["tarife"], "1sa")
        self.assertEqual(r["maliyet_usd"], beklenen("1sa"))


if __name__ == "__main__":
    unittest.main()
