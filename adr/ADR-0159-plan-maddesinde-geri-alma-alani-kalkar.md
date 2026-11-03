# ADR-0159: Plan maddesinde Geri alma alanı kalkar; P-018 metni kapıyla hizalanır

**Durum:** Kabul edildi

**Tarih:** 2026-11-03

**Bağlam:**

- `**Geri alma:**` alanı P-018 (ADR-0126 dönemi) ile her plan maddesine zorunlu kondu ve çoğu maddede `git revert` türü sabit dolgu üretti.
- ADR-0136 alanı kapıdan (`is_sirasi.plan_eksikleri`) ve plan şablonlarından kaldırdı.
- P-018 metni, `readme-for-human.md`, `uretim_enjeksiyonu.json` bağlamı, ölü bir düzeltme ipucu ve testler alanı anmaya devam etti.
- Kural kapıyla çelişiyordu ve yazım anında modele eski alan listesi veriliyordu.
- Kullanıcı kararı (03.11.2026): alan komple kaldırılsın.

**Karar:**

- Plan maddesinde `**Geri alma:**` alanı hiçbir yerde istenmez: P-018 metni ve özeti, `KURALLAR.md`, `readme-for-human.md`, `ayarlar/uretim_enjeksiyonu.json`, `is_sirasi.py` ve testler buna göre sadeleşir.
- P-018'in diğer parçaları aynen kalır: `**Kabul:**`, `**Önce:**`, todo kanıt notu, çalışma özeti P/G karşılaştırması.
- Kapsam dışı: çalışma özetinin "Otomatik kararlar" alanı, Jira Teslim bloğu ve ADR'nin zorunlu geri alma bilgisi (P-015 Sonuçlar alanı).

**Seçenekler:**

- Yalnız pahalı maddelerde zorunlu tutmak: elendi; "pahalı" ölçütü öznel, kapı yazmaz, alan yine dolgu olur.
- Yalnız proje kopyasını düzeltmek: elendi; eklenti güncellemesinde eski metin geri gelir (P-022).
- Alanı kaldırmak: seçildi; geri alma bilgisi gerektiğinde `**Ne:**` ya da ADR Sonuçlar alanında yazılır.

**Sonuçlar:**

- Olumlu: plan maddeleri kısalır, kural metni ile kapı tutarlı olur, yazım anı bağlamı doğru alan listesini söyler.
- Olumsuz: riskli maddede geri alma yolunun yazılması artık kapıyla hatırlatılmaz.
- Geri alma yolu: bu işin commit'ini geri al ve P-018 metnine alanı yeniden ekle; kapı kodu değişmediği için ek iş yok.

**İlgili iş ya da kural kimliği:** I-377, P-018, ADR-0126, ADR-0136, P-022.
