"""P-053 / P3: karar sorusu cümleleri düz metinde yakalanır, bilgi ve retorik cümleler yakalanmaz."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import secim_ekrani_hatirlatma as S  # noqa: E402

POZITIF = [
    "Bu yapıyı kurmaya başlayayım mı, yoksa önce 1. adımdaki sınıf listesini görüp karar verelim mi?",
    "Kurayım mı, yoksa önce listeyi mi göreyim?",
    "Başlayalım mı?",
    "Önce testi yazalım mı?",
    "Bunu şimdi uygulayayım mı?",
    "Devam edeyim mi, yoksa burada dur mu?",
    "İlk dalgayı koşalım mı?",
    "Yoksa 2. seçenekle mi gidelim?",
    "Silelim mi, yoksa arşive mi taşıyalım?",
    "Planı onaylayalım mı?",
    "Bu kuralı ekleyelim mi?",
    "Şimdi push edeyim mi?",
    "Önce 3. maddeyi yapayım mı, yoksa 4. maddeye mi geçeyim?",
    "Hangisini istersiniz?",
    "İster misin?",
    "Yoksa önce 1. adımı mı bitirelim?",
    "Testleri çalıştırayım mı, yoksa önce kodu mu okuyayım?",
    "Sınıf listesini göreyim mi, yoksa doğrudan kurayım mı?",
    "Kapatayım mı, yoksa açık mı bırakalım?",
    "Taşıyalım mı?",
]
NEGATIF = [
    "Test geçti.",
    "Dosya 3 satır, yoksa değeri boş döner.",
    "Hata yoksa devam eder.",
    "Kural P-053 olarak yazıldı.",
    "Sonuç: 12 test geçti, 0 hata.",
    "Yoksa bloğu çalışmaz, çünkü anahtar eksik.",
    "Bu nedir? Bir kayıt türüdür.",
    "Sınıf listesi 1. adımda üretildi.",
    "Kurulum bitti; sıradaki adım todo'da.",
    "Panel 8765 portunda çalışıyor.",
    "`Başlayalım mı?` cümlesi kalıp testinde kullanılır.",
    "```\nKurayım mı?\n```",
    "Hook ilk denemede block eder.",
    "Veri yoksa tablo boş kalır.",
    "Commit 04d43951 ile kayda alındı.",
    "Sorunun kökü kalıp kaçağıydı.",
    "Karar verildi: ayrı depo kurulmaz.",
    "Önce 1. maddeyi bitirdim, sonra 2. maddeye geçtim.",
    "Dosya yoksa oluşturulur.",
    "Açık soru sayısı 3.",
    "Eşik 60 örnek.",
    "Bu bir bilgi cümlesidir.",
    "Plan onaylandı.",
    "Yanıt kısa tutuldu.",
    "Bağlantı kuruldu.",
    "İş kapandı.",
    "Test dosyası eklendi.",
    "Şema şu: tur, durum, anahtar.",
    "Kullanıcı bunu yapmazsa ne olur? Kayıt yoksa 3. satırda hata mı çıkar?",
    "Dosya yoksa mı hata verir?",
    "Kayıt yoksa ne olur?",
    "Anahtar yoksa hook mu düşer?",
    "Bu kalıp neden kaçtı?",
    "Mod yoksa varsayılan plan mı olur?",
    "Testler neden kırmızıydı?",
    "Kapı kapalıysa kayıt yazılır mı?",
    "Sayı yoksa 0 mı döner?",
    "Rapor yazıldı.",
    "Kayıt silinmedi.",
]


class TestKalip(unittest.TestCase):
    def test_pozitif(self):
        kacan = [c for c in POZITIF if not S.yanit_ihlali(c)]
        self.assertEqual(kacan, [], f"{len(POZITIF) - len(kacan)}/{len(POZITIF)}")

    def test_negatif(self):
        yanlis = [c for c in NEGATIF if S.yanit_ihlali(c)]
        self.assertLessEqual(len(yanlis), 1, yanlis)

    def test_kullanici_ornegi(self):
        self.assertTrue(S.yanit_ihlali(POZITIF[0]))

    def test_son_cumle_soru_isareti_yapisal(self):
        self.assertTrue(S.teklif_sonu("Kurulum bitti. Hangi yoldan gidelim?"))
        self.assertFalse(S.teklif_sonu("Kurulum bitti."))


if __name__ == "__main__":
    unittest.main()
