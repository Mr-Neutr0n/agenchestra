"""ADR-0151 P4: hata imzası sınıflama tablosu (ayarlar/hata_onleme_siniflari.json) ve hata_kayit'in kök alanına işlemesi.
`PYTHONUTF8=1 python -m pytest -q plugins/orkestra/tests/test_hata_onleme_siniflari.py`
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import hata_kayit as HK  # noqa: E402

TABLO = os.path.join(KOK, "ayarlar", "hata_onleme_siniflari.json")
BASAMAKLAR = {f"L{i}" for i in range(7)}

# (kaynak türü, tür, ileti): en sık 10 imzanın iletileri, kaynak koddaki metinden (sayı ve yol imzada normalleşir).
ORNEKLER = [
    ("kod", "TimeoutError", "kilit alınamadı: C:\\x\\.claude\\orkestra\\kartlar\\G-12.json.lock"),
    ("davranis", "hook-red", "iş onay bekliyor (P-016): önce mevcut durum → plan → todo hazırlanır, bağlantılarıyla kullanıcıya gösterilir"),
    ("davranis", "is-klasoru-yanlis", "iş klasörü oturum kökü dışında: C:/a/b (oturum kökü: C:/a/c). Belge bağlantıları oturum köküne göre çözülür"),
    ("davranis", "hook-red", "auto modunda kullanıcıya soru sorulmaz (ADR-0086): kararı en iyi uygulamayla kendin ver"),
    ("davranis", "hook-red", "bu oturum bir işe bağlı değil; bağsız oturumda dosya yazılmaz (plan.md/todo.md dahil). Önce bağlan"),
    ("davranis", "hook-red", "K-003: kutu/soru aracı turu bitirir; işin belgeleri değişti ve bağlantıları yanıtta yok."),
    ("davranis", "hook-red", "plan doğrulaması güncel değil (plan sonradan değişti): `orkestra plan dogrula <iş> --yaz`."),
    ("davranis", "hook-red", "iş onay bekliyor (P-016): commit, ekleme/itme, bağımlılık kurma ve onay komutu kullanıcı onayından önce çalıştırılmaz."),
    ("davranis", "hook-red", "kart/defter yazan `orkestra` komutunu tek başına çalıştır (zincir, boru, yönlendirme olmadan)."),
    ("davranis", "hook-red", "iş onay bekliyor (P-016): kabuk komutunun yazdığı yol çözülemedi (değişkenli yol); proje dışına yazacaksan yolu açık yaz."),
]


def satirlar(sd):
    with open(os.path.join(sd, HK.DOSYA), encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


class TestTablo(unittest.TestCase):
    def setUp(self):
        HK._SINIF_ONBELLEK.clear()

    def test_tablo_alanlari(self):
        with open(TABLO, encoding="utf-8") as f:
            d = json.load(f)
        self.assertEqual(len(d["siniflar"]), 10)
        for s in d["siniflar"]:
            self.assertIn(s["onlenebilir"], BASAMAKLAR)
            self.assertTrue(s["sahip"])
            self.assertTrue(s["desen"])

    def test_on_imza_eslesir_ve_her_satir_kullanilir(self):
        kullanilan = set()
        for _, tur, ileti in ORNEKLER:
            with self.subTest(ileti=ileti[:40]):
                s = HK.onleme_sinifi(HK.imza(tur, ileti))
                self.assertIsNotNone(s, HK.imza(tur, ileti))
                kullanilan.add(s["desen"])
        self.assertEqual(len(kullanilan), 10)  # her örnek kendi satırına düşer, iki örnek aynı satırı paylaşmaz

    def test_bilinmeyen_imza_none(self):
        self.assertIsNone(HK.onleme_sinifi(HK.imza("OSError", "başka bir hata")))


class TestKayit(unittest.TestCase):
    def setUp(self):
        HK._SINIF_ONBELLEK.clear()

    def test_bilinen_imza_kok_onlenebilir_ve_sahip(self):
        for sinif, tur, ileti in ORNEKLER:
            with self.subTest(ileti=ileti[:40]), tempfile.TemporaryDirectory() as sd:
                if sinif == "kod":
                    HK.kaydet(sd, "ozet", tur, ileti)
                else:
                    HK.davranis(sd, tur, ileti)
                (s,) = satirlar(sd)
                self.assertIn(s["kok"]["onlenebilir"], BASAMAKLAR)
                self.assertTrue(s["kok"]["sahip"])

    def test_bilinmeyen_imza_eski_davranis(self):
        with tempfile.TemporaryDirectory() as sd:
            HK.kaydet(sd, "hook", "OSError", "x")
            HK.davranis(sd, "hook-red", "orkestra: ortak defter elle düzenlenmez")
            HK.davranis(sd, "is-klasoru-yanlis", "klasörde başka işin kaydı var: C:\\x\\y")
            kod, red, klasor = satirlar(sd)
            self.assertNotIn("kok", kod)
            self.assertEqual(red["kok"], {"kaynak": "betik", "onlenebilir": None, "cozum": HK.TURLER["hook-red"][2]})
            self.assertIs(klasor["kok"]["onlenebilir"], True)
            self.assertNotIn("sahip", klasor["kok"])

    def test_tablo_okunamazsa_eski_davranis(self):
        with tempfile.TemporaryDirectory() as sd:
            bozuk = os.path.join(sd, "bozuk.json")
            with open(bozuk, "w", encoding="utf-8") as f:
                f.write("{bozuk")
            with mock.patch.object(HK, "SINIF_TABLOSU", bozuk):
                HK._SINIF_ONBELLEK.clear()
                HK.kaydet(sd, "ozet", *ORNEKLER[0][1:])
                k = HK.kok_neden(ORNEKLER[1][1], ORNEKLER[1][2])
            with mock.patch.object(HK, "SINIF_TABLOSU", os.path.join(sd, "yok.json")):
                HK._SINIF_ONBELLEK.clear()
                k2 = HK.kok_neden(ORNEKLER[1][1], ORNEKLER[1][2])
            (s,) = satirlar(sd)
            self.assertNotIn("kok", s)
            self.assertNotIn("sahip", k)
            self.assertNotIn("sahip", k2)
            self.assertIsNone(k["onlenebilir"])


if __name__ == "__main__":
    unittest.main()
