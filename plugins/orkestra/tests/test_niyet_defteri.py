"""Niyet defteri çekirdeği (ADR-0156, I-369): atomik niyet, ham mesaj yok, kanıtlı durum, ilgili bağı, maskeleme."""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import niyet_defteri as ND  # noqa: E402


class NiyetDefteri(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp(prefix="ork_niyet_")

    def tearDown(self):
        shutil.rmtree(self.sd, ignore_errors=True)

    def test_iki_niyetli_mesaj_iki_satir_ve_metin_alani_yok(self):
        a = ND.ekle(self.sd, "o1", "o1-0001", "istek", "Niyet defteri kurulsun", kriter="close defterden okur")
        b = ND.ekle(self.sd, "o1", "o1-0001", "kisit", "Ham mesaj saklanmasın")
        self.assertEqual((a, b), ("o1-0001/1", "o1-0001/2"))
        satirlar = ND.oku(self.sd)
        self.assertEqual(len(satirlar), 2)
        for k in satirlar:
            self.assertNotIn("metin", k)
            self.assertEqual(k["istek_id"], "o1-0001")

    def test_sir_maskelenir(self):
        ND.ekle(self.sd, "o1", "o1-0001", "istek", "Rapor a.b@ornek.com adresine gitsin")
        self.assertNotIn("a.b@ornek.com", open(ND.yol(self.sd), encoding="utf-8").read())

    def test_gecersiz_tur_ve_bos_ne_reddedilir(self):
        with self.assertRaises(ValueError):
            ND.ekle(self.sd, "o1", "o1-0001", "bilinmeyen", "x")
        with self.assertRaises(ValueError):
            ND.ekle(self.sd, "o1", "o1-0001", "istek", "   ")

    def test_kanitsiz_karsilandi_reddedilir(self):
        n = ND.ekle(self.sd, "o1", "o1-0001", "istek", "Modül yazılsın")
        with self.assertRaises(ValueError):
            ND.durum_yaz(self.sd, "o1", n, "karsilandi")
        with self.assertRaises(ValueError):
            ND.durum_yaz(self.sd, "o1", n, "karsilandi", kanit="  ")
        ND.durum_yaz(self.sd, "o1", n, "karsilandi", kanit="tests/test_niyet_defteri.py yeşil")
        g = ND.guncel(self.sd, "o1")[0]
        self.assertEqual((g["durum"], g["kanit"]), ("karsilandi", "tests/test_niyet_defteri.py yeşil"))

    def test_bilinmeyen_niyete_durum_yazilamaz(self):
        with self.assertRaises(ValueError):
            ND.durum_yaz(self.sd, "o1", "o1-0009/1", "vazgecildi")

    def test_vazgec_ilgili_niyetin_durumunu_degistirir(self):
        a = ND.ekle(self.sd, "o1", "o1-0001", "istek", "Tabloya yazılsın")
        ND.ekle(self.sd, "o1", "o1-0002", "vazgec", "Tablo işini bırak", ilgili=a)
        d = {k["id"]: k["durum"] for k in ND.guncel(self.sd, "o1")}
        self.assertEqual(d[a], "vazgecildi")

    def test_revize_eskiyi_kapatir_yeniyi_acik_birakir(self):
        a = ND.ekle(self.sd, "o1", "o1-0001", "istek", "Ham mesaj maskelensin")
        b = ND.ekle(self.sd, "o1", "o1-0002", "revize", "Mesaj yerine niyet çıkarılsın", ilgili=a)
        d = {k["id"]: k for k in ND.guncel(self.sd, "o1")}
        self.assertEqual(d[a]["durum"], "vazgecildi")
        self.assertIn(b, d[a]["kanit"])
        self.assertEqual(d[b]["durum"], "acik")

    def test_revize_ve_vazgec_ilgili_ister(self):
        with self.assertRaises(ValueError):
            ND.ekle(self.sd, "o1", "o1-0002", "revize", "x")
        with self.assertRaises(ValueError):
            ND.ekle(self.sd, "o1", "o1-0002", "vazgec", "x", ilgili="o1-0009/1")

    def test_sayim_ve_oturum_ayrimi(self):
        a = ND.ekle(self.sd, "o1", "o1-0001", "istek", "Bir")
        ND.ekle(self.sd, "o1", "o1-0001", "istek", "İki")
        ND.ekle(self.sd, "o2", "o2-0001", "istek", "Başka oturum")
        ND.durum_yaz(self.sd, "o1", a, "karsilandi", kanit="komut çıktısı")
        self.assertEqual(ND.sayim(self.sd, "o1"), {"toplam": 2, "acik": 1, "karsilandi": 1, "kismen": 0, "vazgecildi": 0})

    def test_kapali_env(self):
        os.environ["ORKESTRA_NIYET_DEFTERI"] = "0"
        try:
            self.assertFalse(ND.acik())
        finally:
            del os.environ["ORKESTRA_NIYET_DEFTERI"]


if __name__ == "__main__":
    unittest.main()
