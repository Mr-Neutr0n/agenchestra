"""Açık soru kaydı (P-053): onay deposunda tur=soru yaşam döngüsü ve bağlam satırı."""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_onay import Temel, onay  # noqa: E402


class TestOnaySoru(Temel):
    def test_soru_ac_idempotent(self):
        a = onay.soru_ac(self.sd, "Kurayım mı?", ["Kur", "Önce liste"], oturum="o1")
        b = onay.soru_ac(self.sd, "  kurayım   mı? ", oturum="o1")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(a["tur"], "soru")
        self.assertEqual(len(onay.acik_sorular(self.sd)), 1)

    def test_baska_oturum_ayri_kayit(self):
        a = onay.soru_ac(self.sd, "Kurayım mı?", oturum="o1")
        b = onay.soru_ac(self.sd, "Kurayım mı?", oturum="o2")
        self.assertNotEqual(a["id"], b["id"])
        self.assertEqual(len(onay.acik_sorular(self.sd, "o1")), 1)

    def test_yanitla_ve_kapat(self):
        a = onay.soru_ac(self.sd, "Soru 1?", oturum="o1")
        b = onay.soru_ac(self.sd, "Soru 2?", oturum="o1")
        k = onay.soru_yanitla(self.sd, a["id"], "Kur")
        self.assertEqual(k["durum"], "uygulandi")
        onay.soru_kapat(self.sd, b["id"])
        self.assertEqual(onay.acik_sorular(self.sd), [])
        with self.assertRaises(ValueError):
            onay.soru_yanitla(self.sd, a["id"], "tekrar")

    def test_soru_olmayan_kayit_reddedilir(self):
        k = onay.iste(self.sd, "Karar", "m", tur="karar", oturum="o1")
        with self.assertRaises(ValueError):
            onay.soru_yanitla(self.sd, k["id"], "x")
        with self.assertRaises(ValueError):
            onay.soru_kapat(self.sd, k["id"])

    def test_yanitla_metinle(self):
        onay.soru_ac(self.sd, "Kurayım mı?", oturum="o1")
        self.assertIsNotNone(onay.soru_yanitla_metinle(self.sd, "o1", "kurayım mı?", "Kur"))
        self.assertIsNone(onay.soru_yanitla_metinle(self.sd, "o1", "kurayım mı?", "Kur"))

    def test_eskiyen_soru_kalkar(self):
        a = onay.soru_ac(self.sd, "Eski?", oturum="o1")
        k = onay._kayit_oku(self.sd, a["id"])
        k["olusturma"] = (datetime.datetime.now().astimezone() - datetime.timedelta(days=15)).isoformat(timespec="seconds")
        onay._kayit_yaz(self.sd, k)
        self.assertEqual(onay.acik_sorular(self.sd), [])
        self.assertEqual(onay._kayit_oku(self.sd, a["id"])["durum"], "eskidi")

    def test_baglam_satiri(self):
        self.assertEqual(onay.baglam_metni(self.sd, "o1", "UserPromptSubmit"), "")
        for i in range(5):
            onay.soru_ac(self.sd, f"Çok uzun bir soru metni numara {i} " + "x" * 200, oturum="o1")
        m = onay.baglam_metni(self.sd, "o1", "UserPromptSubmit")
        self.assertIn("Yanıtsız açık soru 5", m)
        self.assertLessEqual(len(onay.acik_soru_satiri(self.sd, "o1")), 300)
        self.assertEqual(onay.acik_soru_satiri(self.sd, "baska"), "")

    def test_soru_karar_sayacini_etkilemez(self):
        onay.soru_ac(self.sd, "Soru?", oturum="o1")
        m = onay.baglam_metni(self.sd, "o1", "SessionStart")
        self.assertNotIn("onaylanmış", m)

    def test_karar_ver_soruyu_reddeder(self):
        k = onay.soru_ac(self.sd, "Soru?", ["Evet"], oturum="o1")
        with self.assertRaises(ValueError):
            onay.karar_ver(self.sd, k["id"], "onay", secim="Evet")
        self.assertEqual(onay.acik_sorular(self.sd)[0]["durum"], "bekliyor")

    def test_sayac_soruyu_bekleyen_karar_saymaz(self):
        onay.soru_ac(self.sd, "Soru?", oturum="o1")
        s = onay.sayac(self.sd)
        self.assertEqual(s["bekliyor"], 0)
        self.assertEqual(s["uygulanacak"], 0)
        self.assertEqual(s["tur"]["soru"], 1)
        onay.iste(self.sd, "Karar", "m", tur="karar", oturum="o1")
        self.assertEqual(onay.sayac(self.sd)["bekliyor"], 1)


if __name__ == "__main__":
    unittest.main()
