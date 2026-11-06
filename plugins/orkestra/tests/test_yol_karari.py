"""ADR-0171 / P-052 gölge kapısı: mevcut durum `## Yol kararı` taşır; I-370 ihlal vakası."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import is_sirasi as S  # noqa: E402

# I-370 (PE-453): Jira örneği V2 yolunu izledi, dağıtıcı (dispatch_query/route) hiç anılmadı.
I370 = """## 1. İstek ya da veri hangi yoldan geçiyor

**Sonuç:** "Dün" iki yoldan çözülür.

### 1.1 V2 satış yolu

1. Çalışma zamanı sunucu saatini alır (agent/runtime.py:414).
2. Çözümleyici YESTERDAY hesaplar (domain/calendar/timeframe.py:185).
"""

YOL = """
## Yol kararı

**Sonuç:** İki yol var; V1 trafiğin 4/6'sını alıyor, karar başka yol.

### Giriş noktası ve dallanmalar

- `dispatch_query` sınıflayıcıya göre V1 ya da V2 seçer (agent/runtime.py:62).
- Sınıflayıcı boş kümede V1'e düşer (agent/nodes/route.py:318).

### Gerçek trafik

- 6 koşuda 4 V1, 2 V2 (06.11.2026 10:00).

### Karar

- başka yol: V1 de düzeltilir. Rakip: V2 sürdür, trafiğin çoğunu görmez.
"""


class YolKarari(unittest.TestCase):
    def test_ihlal_vakasi_kapisiz_gecer_kapiyla_reddedilir(self):
        # Kapı olmadan (eski düzen) I-370 metni mevcut durum olarak kabul edilirdi; kapıyla eksik döner.
        eksik = S.yol_karari_metin_eksikleri(I370)
        self.assertEqual(len(eksik), 1)
        self.assertIn("Yol kararı", eksik[0])

    def test_dolu_bolum_temiz(self):
        self.assertEqual(S.yol_karari_metin_eksikleri(I370 + YOL), [])

    def test_dosya_satirsiz_giris_noktasi_reddedilir(self):
        m = YOL.replace("(agent/runtime.py:62)", "").replace("(agent/nodes/route.py:318)", "")
        e = S.yol_karari_metin_eksikleri(I370 + m)
        self.assertTrue(any("Giriş noktası" in x for x in e))

    def test_trafik_kanitsiz_reddedilir_olculemedi_plan_maddesiyle_gecer(self):
        bos = YOL.replace("- 6 koşuda 4 V1, 2 V2 (06.11.2026 10:00).", "- V2 sürdürülüyor.")
        self.assertTrue(any("Gerçek trafik" in x for x in S.yol_karari_metin_eksikleri(bos)))
        engel = YOL.replace("- 6 koşuda 4 V1, 2 V2 (06.11.2026 10:00).", "- ölçülemedi — VPN kapalı; P6 ölçümü kapatır.")
        self.assertEqual(S.yol_karari_metin_eksikleri(engel), [])
        planmadan = YOL.replace("- 6 koşuda 4 V1, 2 V2 (06.11.2026 10:00).", "- ölçülemedi — VPN kapalı.")
        self.assertTrue(any("Gerçek trafik" in x for x in S.yol_karari_metin_eksikleri(planmadan)))

    def test_kararsiz_reddedilir(self):
        m = YOL.replace("- başka yol: V1 de düzeltilir. Rakip: V2 sürdür, trafiğin çoğunu görmez.", "- bence iyi.")
        self.assertTrue(any("Karar" in x for x in S.yol_karari_metin_eksikleri(m)))

    def test_sablon_yorumu_bolum_sayilmaz(self):
        sablon = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sablonlar", "mevcut_durum.md"), encoding="utf-8").read()
        self.assertEqual(len(S.yol_karari_metin_eksikleri(sablon)), 1)  # yalnız yorum: bölüm boş

    def test_denetci_altinci_satir_planda_aranir(self):
        plan = "## Best in class denetimi\n\n- **Kök neden:** ✔ x\n"
        with mock.patch.object(S, "mevcut_durum_yolu", return_value="x"), mock.patch.object(S, "_oku", return_value=I370 + YOL), \
             mock.patch.object(S, "_plan_oku", return_value=plan):
            self.assertTrue(any("Yol kanıtı" in x for x in S.yol_karari_eksikleri("k")))
            with mock.patch.object(S, "_plan_oku", return_value=plan + "- **Yol kanıtı:** ✔ x\n"):
                self.assertEqual(S.yol_karari_eksikleri("k"), [])

    def test_golge_modda_engellemez(self):
        with mock.patch.object(S, "yol_karari_eksikleri", return_value=["x"]), \
             mock.patch.object(S, "yol_kapsaminda_mi", return_value=True), \
             mock.patch("kapi_mod.kaydet", return_value=False), mock.patch("kapi_mod.mod", return_value="golge"):
            self.assertEqual(S.yol_karari_uyari("k"), [])

    def test_bayraksiz_is_kapsam_disi(self):
        with mock.patch.object(S, "sirali_mi", return_value=True), mock.patch("builtins.open", side_effect=OSError):
            self.assertFalse(S.yol_kapsaminda_mi("k"))

    def test_kapatma_env(self):
        with mock.patch.dict(os.environ, {"ORKESTRA_YOL_KAPISI": "0"}):
            self.assertFalse(S.yol_kapisi_acik())


if __name__ == "__main__":
    unittest.main()
