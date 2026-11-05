# ADR-0170: Arşiv düğmesi: iş kalmayınca wrap_up kutusu tek Arşivle düğmesi

**Durum:** Kabul edildi

**Tarih:** 2026-11-05

**Bağlam:**

Oturumda yapılacak iş ve konuşulacak konu kalmadığında kullanıcı sohbeti arşivlemek ister. Bugün kapanış kutusu (`mcp__ccd_turn__wrap_up`) bu düğmeyi kendiliğinden taşımıyor. Ayrıca ajan `wrap_up` çağırmadan turu bitirirse `update_plan` şeridi "0/6 yapıldı · devam ediyor" diye takılı kalıyor. Kullanıcı 05.11.2026'da iki şey istedi: iş kalmayınca Arşivle düğmesi çıksın ve basınca sohbet arşivlensin; sohbete girince takılı şerit yerine yalnız Arşivle görünsün.

**Karar:**

- İş kalmadığında (açık kart yok, onay bekleyen iş yok, bağlı işte açık todo yok, `ask` yok) ana ajanın `wrap_up` çağrısına `actions=[{"action":"archive"}]` hook tarafından eklenir; `ask` da eklenir ("Sohbet arşivlensin mi?"), çünkü uygulama kutuyu yalnız `ask` ve `actions` birlikte olunca çizer (canlı deneme 05.11.2026: ask'siz çağrıda kutu çizilmedi). Uygulamanın kendi `archive` eylemi kullanılır; sohbeti uygulama arşivler.
- Ekleme PreToolUse `updatedInput` ile yapılır (`scripts/arsiv_dugmesi.py`, `hook._arsiv_dugmesi_kapisi`). İzin kipi güncel girdiyi onaya düşürecekse çağrı, eksiksiz yönergeyle reddedilir.
- Çalışma yapan tur (plan listesi ya da dosya değişikliği) iş kalmamışken `wrap_up`'sız biterse Stop tur başına bir kez block eder (`hook._arsiv_dugmesi_yanit`). `wrap_up` plan listesini kapattığı için şerit takılı kalmaz.
- Kapı ilk günden `ihlal` modundadır (kullanıcı kararı, P-028 istisnası). `ORKESTRA_ARSIV_DUGMESI=0` kapatır.

**Seçenekler:**

- Yalnız kural metni (ajan kendisi eklesin): elendi. Ajan unutur; kullanıcı "kesinlikle" istedi, bu yüzden mekanik zorlama gerekir.
- Yalnız Stop block: elendi. Sonradan yakalar (P-045 L6); düğme girdiyi üretildiği yerde düzelten PreToolUse ile kendiliğinden gelir (L3).
- Uygulama dışı arşivleme betiği (`archive_session` aracı): elendi. Kullanıcının bastığı düğme uygulamanın kendi eylemidir; ayrı yol iki mekanizma yaratır.
- Seçilen: PreToolUse girdi düzeltmesi (L3) artı Stop güvenlik ağı.

**Sonuçlar:**

- Olumlu: iş bitince tek tıkla arşiv; takılı şerit kalmaz; model çağrısı yok.
- Olumsuz: izin kipi `updatedInput`'u onaya düşürürse ilk çağrı reddedilir ve ajan bir tur harcar. Açık iş tespiti kart, onay ve todo kayıtlarına dayanır; konuşulacak konu kalıp kalmadığını hook bilemez, o ajanın `ask`'ıyla belirtilir.
- Geri alma: `ORKESTRA_ARSIV_DUGMESI=0` ya da `ayarlar/arsiv_dugmesi.json` `mod: kapali`; kod geri alma commit'iyle kaldırılır.

**İlgili iş:** I-391; kural P-059
