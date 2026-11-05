"""İddia-kaynak kapısı (gölge) birim testleri: sayı-çıktı eşleşmesi ve kaynak etiketi denetimi."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import iddia_kaynak as IK  # noqa: E402


def turler(bulgular):
    return sorted({b["tur"] for b in bulgular})


class SayiTesti(unittest.TestCase):
    def setUp(self):
        self.ayar = IK.ayar_oku()

    def test_ciktida_olmayan_sayi_uyari(self):
        # PE-455 tipi vaka: sayı komutla hesaplanmadan yazıldı
        b = IK.analiz("Toplam 135 koşu var (Ölçüm çıktısı).", "kaç koşu var?", ["wc: 42 satır"], self.ayar)
        self.assertIn("sayi_kaynaksiz", turler(b))

    def test_ciktida_gecen_sayi_sessiz(self):
        b = IK.analiz("Toplam 135 koşu var (Ölçüm çıktısı).", "kaç koşu var?", ["koşu sayısı: 135"], self.ayar)
        self.assertEqual(b, [])

    def test_istemdeki_sayi_sessiz(self):
        b = IK.analiz("Dediğin 250 adet doğru (Kullanıcı sözü).", "250 adet var diyorum", [], self.ayar)
        self.assertEqual(b, [])

    def test_binlik_ayirac_normallesir(self):
        b = IK.analiz("Toplam 1.250 satır (Ölçüm çıktısı).", "say", ["1250"], self.ayar)
        self.assertEqual(b, [])

    def test_kod_blogu_ve_satir_kodu_atlanir(self):
        yanit = "Komut:\n```\nseq 1 9999\n```\nÇıktı `12345` gibi."
        self.assertEqual(IK.sayilar(yanit, self.ayar), [])

    def test_tarih_kimlik_madde_numarasi_sayilmaz(self):
        yanit = "1. Adım P-021 ve ADR-0156, 05.11.2026 tarihinde I-399 için (Doküman)."
        self.assertEqual(IK.sayilar(yanit, self.ayar), [])

    def test_tek_haneli_sayi_sayilmaz(self):
        self.assertEqual(IK.sayilar("3 madde var", self.ayar), [])


class EtiketTesti(unittest.TestCase):
    def setUp(self):
        self.ayar = IK.ayar_oku()

    def test_etiketsiz_iddia_uyari(self):
        b = IK.analiz("Dün yanlış güne gidiyor.", "değerlendir", ["x"], self.ayar)
        self.assertIn("etiketsiz_iddia", turler(b))

    def test_etiketli_iddia_sessiz(self):
        b = IK.analiz("Dün yanlış güne gidiyor (Kod: sorgu.py:12).", "değerlendir", ["x"], self.ayar)
        self.assertEqual(b, [])

    def test_dogrulanmadi_cumlesi_sessiz(self):
        b = IK.analiz("Yedek yolda eksik var, doğrulanmadı: dosya okunamadı.", "değerlendir", ["x"], self.ayar)
        self.assertEqual(b, [])

    def test_bir_cumledeki_isaret_digerini_aklamaz(self):
        yanit = "Birinci cümle doğrulanmadı. Dün yanlış güne gidiyor."
        self.assertIn("etiketsiz_iddia", turler(IK.analiz(yanit, "s", ["x"], self.ayar)))

    def test_iddia_olmayan_cumle_sessiz(self):
        self.assertEqual(IK.analiz("Tamam, yapıyorum.", "s", [], self.ayar), [])

    def test_etiket_listesi_sekiz_tur(self):
        for ad in ("Veritabanı", "Kod", "Doküman", "Eski sohbet", "Ölçüm çıktısı", "Jira", "Kullanıcı sözü", "Hafıza"):
            b = IK.analiz("Tablo yok (%s)." % ad, "s", ["x"], self.ayar)
            self.assertEqual(b, [], ad)


class KipVeHataTesti(unittest.TestCase):
    def test_kip_kapali_ortam(self):
        os.environ["ORKESTRA_KANIT_KAPISI"] = "0"
        try:
            self.assertEqual(IK.mod(IK.ayar_oku()), "kapali")
        finally:
            del os.environ["ORKESTRA_KANIT_KAPISI"]

    def test_varsayilan_kip_golge(self):
        self.assertEqual(IK.mod(IK.ayar_oku()), "golge")

    def test_bozuk_dokum_sessiz(self):
        self.assertEqual(IK.degerlendir("/yok/dokum.jsonl", "135 koşu var"), [])

    def test_dokumden_uc_uca(self):
        satirlar = [
            {"type": "user", "timestamp": "t", "message": {"content": "kaç koşu?"}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "wc -l x"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "42 x"}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Toplam 135 koşu (Ölçüm çıktısı)."}]}},
        ]
        with tempfile.TemporaryDirectory() as d:
            yol = os.path.join(d, "t.jsonl")
            with open(yol, "w", encoding="utf-8") as f:
                f.write("\n".join(json.dumps(s) for s in satirlar))
            self.assertIn("sayi_kaynaksiz", turler(IK.degerlendir(yol, "Toplam 135 koşu (Ölçüm çıktısı).")))
            self.assertEqual(IK.degerlendir(yol, "Toplam 42 koşu (Ölçüm çıktısı)."), [])


if __name__ == "__main__":
    unittest.main()
