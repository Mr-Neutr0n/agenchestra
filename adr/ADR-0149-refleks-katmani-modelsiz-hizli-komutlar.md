# ADR-0149: Refleks katmanı: modelsiz hızlı komutlar

**Durum:** Kabul edildi

**Tarih:** 02.11.2026

**Bağlam:**

- Küçük, deterministik işler (ör. `/orkestra:update`) bugün skill olarak çalışır; skill yüklenir ve model turu harcanır.
- Eklentide modelsiz çalışan hızlı yol yoktu.
- `UserPromptSubmit` hook'u istemi engelleyip gerekçeyi kullanıcıya gösterebilir; engellenen istem modele ulaşmaz.
- P1 deneyi (`claude -p` 2.1.308, 3 koşu/kanal): `UserPromptSubmit` ve `UserPromptExpansion` engeli 0 tur, 0 USD; `!` ön eki engellenmeden modele gitti (`deney_refleks.md`).

**Karar:**

- Ayrı, hafif bir hook girdisi (`scripts/refleks_hook.py`) `hooks/hooks.json` içinde `UserPromptSubmit` altında ilk sıraya eklenir; `hook.py` içe aktarılmaz, günlük kilidine girilmez.
- Kanal: `UserPromptSubmit` `decision: block` + `reason`; ön ek `/ok <komut>`, tam eşleşme (ad ya da takma ad), parametre yok.
- Komutlar tek kayıt dosyasında (`ayarlar/refleks.json`) tanımlanır: ad, argüman listesi, `salt_okur: true`, zaman aşımı (en çok 8 sn), çıktı sınırı (en çok 4000 karakter).
- Yürütülebilir izin listesi yalnız `orkestra`; kabuksuz argüman listesi; kabuk metakarakteri ve yer tutucu reddedilir; çıktı maskelenir (`ork_lib.maskele`).
- Hata, sıfırdan farklı çıkış, zaman aşımı ya da eşleşmeme istemi model yoluna bırakır.
- Proje ezmesi (`.claude/orkestra/refleks.json`) yalnız kapatabilir, kayıt ekleyemez.
- Her koşu `refleks.jsonl` dosyasına (komut, ms) yazılır.

**Seçenekler:**

- Her iş için ayrı skill: elendi, model turu ve yükleme maliyeti kalır.
- Yalnız terminalde `orkestra <komut>`: elendi, sohbetten çıkmayı gerektirir.
- `!orkestra <komut>` (yerleşik kabuk ön eki): elendi, `claude -p` kipinde engellenmeden modele gitti; etkileşimli davranış doğrulanmadı.
- Model destekli niyet sınıflama: elendi, amaç modelsiz yoldur.
- Komut metni (kabuk satırı) kaydı: elendi, kayıt dosyası değişirse rastgele komut çalışır.
- `hook.py` dağıtıcısına çıkış eklemek: elendi, ağır içe aktarma ve günlük kilidi sıcak yola girer (kilit zaman aşımı hataları görülüyor).

**Sonuçlar:**

- Olumlu: refleks komutlarında 0 tur, 0 USD, bağlam yüklenmez (P8).
- Olumsuz: süre CLI açılışına bağlı; p95 `panel` 1297 ms, `isler` 2109 ms (hedef 1 sn, KISMEN). `update --kuru` kirli yayın klonunda 1 çıkış verir ve model yoluna düşer. Etkileşimli ekran görünümü doğrulanmadı.
- Geri alma: `ayarlar/refleks.json` içinde `mod: kapali` ya da `ORKESTRA_REFLEKS=0`; hooks.json girdisi silinirse davranış eski haline döner.

**İlgili iş ya da kural kimliği:** I-345, P-015, P-022, K-006, ADR-0108
