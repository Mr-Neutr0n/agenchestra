"""Niyet defteri gölge kapısı ve ölçümü (ADR-0156, P-028): kapi_golge, tek yazım, kısa onay, rapor, kapatma."""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import niyet_defteri as ND  # noqa: E402
import niyet_defteri_kapi as K  # noqa: E402
import ork_lib as L  # noqa: E402


class Kapi(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp(prefix="ork_niyetk_")
        self.gl = os.path.join(self.sd, "gunluk.jsonl")

    def tearDown(self):
        shutil.rmtree(self.sd, ignore_errors=True)

    def istek(self, iid, ne, uzunluk, oturum="o1"):
        L.jsonl_ekle(self.gl, {"zaman": L.simdi(), "oturum": oturum, "tur": "istek", "istek_id": iid, "ne": ne, "uzunluk": uzunluk})

    def golge(self):
        return [k for k in L.jsonl_oku(self.gl) if k.get("tur") == "kapi_golge"]

    def test_niyetsiz_istek_golgeye_yazilir_ve_engellemez(self):
        self.istek("o1-0001", "Niyet defteri kurulsun lütfen", 300)
        self.assertTrue(K.stop_kontrol(self.sd, "o1"))
        g = self.golge()
        self.assertEqual((len(g), g[0]["kapi"]), (1, "niyet_defteri"))

    def test_ayni_istek_icin_tek_yazim(self):
        self.istek("o1-0001", "Niyet defteri kurulsun lütfen", 300)
        K.stop_kontrol(self.sd, "o1")
        self.assertFalse(K.stop_kontrol(self.sd, "o1"))
        self.assertEqual(len(self.golge()), 1)

    def test_niyet_yazildiysa_yazilmaz(self):
        self.istek("o1-0001", "Niyet defteri kurulsun lütfen", 300)
        ND.ekle(self.sd, "o1", "o1-0001", "istek", "Defter kurulsun")
        self.assertFalse(K.stop_kontrol(self.sd, "o1"))
        self.assertEqual(self.golge(), [])

    def test_kisa_onay_niyet_beklemez(self):
        self.istek("o1-0001", "evet yap", 8)
        self.istek("o1-0002", "Tamam, yap", 10)
        self.assertFalse(K.stop_kontrol(self.sd, "o1"))

    def test_kapali_env(self):
        self.istek("o1-0001", "Niyet defteri kurulsun lütfen", 300)
        os.environ["ORKESTRA_NIYET_DEFTERI"] = "0"
        try:
            self.assertFalse(K.stop_kontrol(self.sd, "o1"))
        finally:
            del os.environ["ORKESTRA_NIYET_DEFTERI"]
        self.assertEqual(self.golge(), [])

    def test_rapor_oran_ve_wilson(self):
        for i in range(1, 11):
            self.istek(f"o1-{i:04d}", "Anlamlı bir kullanıcı isteği", 400)
        for i in range(1, 9):  # 8 mesaja iki niyet, 2 mesaja niyet yok
            iid = f"o1-{i:04d}"
            ND.ekle(self.sd, "o1", iid, "istek", "Bir")
            ND.ekle(self.sd, "o1", iid, "kisit", "İki")
        self.istek("o1-0099", "evet yap", 8)  # kısa onay: payda dışı
        r = K.rapor(self.sd)
        self.assertEqual((r["n"], r["yazilan"], r["oran"], r["ortalama_niyet"]), (10, 8, 0.8, 2.0))
        self.assertLess(r["wilson_alt"], 0.8)
        self.assertFalse(r["gecis_hazir"])  # n < 60


if __name__ == "__main__":
    unittest.main()
