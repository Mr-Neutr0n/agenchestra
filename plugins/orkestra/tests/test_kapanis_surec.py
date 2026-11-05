"""ADR-0163 (I-387, P-014/P-045): kapanış mesajında süreç anlatımı kapısı (scripts/kapanis_surec.py, hook.py Stop bağı)
ve ajanın `orkestra is onayla` komutunun koşulsuz reddi (scripts/is_onay.py). Gölge: yalnız ölçer.
`python -m pytest -q plugins/orkestra/tests/test_kapanis_surec.py`
Derlem yapaydır (mekanizma testi); gerçek yanıtlarla doğruluk ölçümü gölge dönemin işidir (ayarda gecis_esigi).
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import kapanis_surec as K  # noqa: E402
import is_onay  # noqa: E402

IHLAL = [
    "Kapanışta `orkestra is onayla`'yı kendim çalıştırdım. Gerekçem, 'tam izin' mesajının auto modunda onay yerine geçmesiydi. Bu çalışma özetine de yazıldı.",
    "Onayı kendim verdim ve işe devam ettim.",
    "Gerekçem şu: plan tamamdı.",
    "Hook beni engelledi, ben de başka yoldan yazdım.",
    "Önce hook reddetti, sonra komutu yeniden denedim.",
    "Kapı bana izin vermedi; onayı ben çalıştırdım.",
    "Bu karar P-016 gereği alındı.",
    "ADR-0086 uyarınca onayı kendim ilerlettim.",
    "`orkestra is kapat` komutunu çalıştırdım ve gerekçesini özete yazdım.",
    "Bu adım çalışma özetine de yazıldı.",
    "Plandan sapma olarak onayı kendi kararımla verdim.",
    "Sonra orkestra is devam komutunu kullandım, ardından todo'yu güncelledim.",
    "Kural K-006 nedeniyle önce kök nedene baktım.",
]
TEMIZ = [
    "Testler geçti: 25 başarılı, 0 hatalı.",
    "Stop kapısı eklendi; gölge kipte kural_ihlal yazıyor.",
    "Kullanıcı P-014'ü konuşuyor: kural yalnız metindi, şimdi kapı var.",
    "ADR-0163 eklenti deposunda yazıldı.",
    "Açık kalan: ihlal kipine geçiş, ölçümden sonra ayrı karar.",
    "Ana sayı: 13 ihlal, 13 temiz örnek, yanlış pozitif 0.",
    "Hook ayarı ayarlar/kapanis_surec.json dosyasında; proje ezmesi destekli.",
    "`orkestra is onayla` komutu artık PreToolUse'ta reddediliyor.",
    "Şablon güncellendi, kapanış yalnız üç alandan üretilir.",
    "K-006 kök neden kuralı değişmedi.",
    "Kullanıcı gerekçe istedi; gerekçe: kapı yanlış pozitif vermiyor.",
    "Rapor hazır, bağlantı aşağıda.",
    "Plan onaylandı, uygulamaya geçiyorum.",
]


class _Ortak(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ork_kapanis_")
        self.sd = os.path.join(self.tmp, ".claude", "orkestra")
        os.makedirs(self.sd)
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        os.environ.pop("ORKESTRA_KAPANIS_SUREC", None)

    def tearDown(self):
        self._env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def gunluk(self):
        yol = os.path.join(self.sd, "gunluk.jsonl")
        if not os.path.exists(yol):
            return []
        with open(yol, encoding="utf-8") as f:
            return [json.loads(s) for s in f if s.strip()]


class Derlem(_Ortak):
    def test_ayar_golge(self):
        self.assertEqual(K.mod(K.ayar_oku(self.sd)), "golge")

    def test_derlem_boyutu(self):
        self.assertGreaterEqual(len(IHLAL), 10)
        self.assertGreaterEqual(len(TEMIZ), 10)

    def test_ihlaller_yakalanir(self):
        kacan = [m for m in IHLAL if not K.degerlendir(m, self.sd)]
        self.assertEqual(kacan, [])

    def test_temizler_gecer(self):
        fazla = [m for m in TEMIZ if K.degerlendir(m, self.sd)]
        self.assertEqual(fazla, [])

    def test_alinti_ihlal_cumlesi(self):
        b = K.degerlendir("Testler geçti. Onayı kendim verdim. Rapor hazır.", self.sd)
        self.assertEqual(b["alinti"], "Onayı kendim verdim.")


class Kapatma(_Ortak):
    def test_env_kapatir(self):
        os.environ["ORKESTRA_KAPANIS_SUREC"] = "0"
        self.assertEqual(K.degerlendir(IHLAL[0], self.sd), {})

    def test_proje_ayari_ezer(self):
        with open(os.path.join(self.sd, K.PROJE_DOSYA), "w", encoding="utf-8") as f:
            json.dump({"mod": "kapali"}, f)
        self.assertEqual(K.degerlendir(IHLAL[0], self.sd), {})

    def test_bozuk_girdi_guvenli(self):
        self.assertEqual(K.degerlendir(None, self.sd), {})
        self.assertEqual(K.degerlendir("  ", self.sd), {})


class HookBaglantisi(_Ortak):
    def _kayit(self, metin):
        import hook
        hook._kapanis_surec_yanit(self.sd, "o1", {"last_assistant_message": metin})
        return [k for k in self.gunluk() if k.get("kural") == K.KURAL]

    def test_ihlal_kayit_dusurur(self):
        k = self._kayit(IHLAL[0])
        self.assertEqual(len(k), 1)
        self.assertEqual(k[0]["tur"], "kural_ihlal")
        self.assertEqual(k[0]["mod"], "golge")

    def test_temiz_kayit_dusurmez(self):
        self.assertEqual(self._kayit(TEMIZ[0]), [])

    def test_rapor_sayar(self):
        self._kayit(IHLAL[0])
        self._kayit(IHLAL[1])
        self.assertEqual(K.rapor(self.sd)["ihlal"], 2)


class OnaylaReddi(unittest.TestCase):
    def test_komut_onay_durumundan_bagimsiz_reddedilir(self):
        for komut in ("orkestra is onayla I-1", "cd x && orkestra is onayla I-1", "orkestra.py is onayla I-1"):
            self.assertTrue(is_onay.onayla_engeli(komut), komut)

    def test_baska_komut_gecer(self):
        for komut in ("orkestra is devam I-1", "git status"):
            self.assertEqual(is_onay.onayla_engeli(komut), "", komut)

    def test_env_kapatir(self):
        with mock.patch.dict(os.environ, {"ORKESTRA_ONAY_KAPISI": "0"}):
            self.assertEqual(is_onay.onayla_engeli("orkestra is onayla I-1"), "")


if __name__ == "__main__":
    unittest.main()
