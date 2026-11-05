# ADR-0167: Panel penceresi son_30_gun ve istemci önbellek politikası

**Durum:** Kabul edildi

**Tarih:** 2026-11-05

**Bağlam:**

Panelde "Bu ay" penceresi takvim ayının başından bugüne kadardı; ayın ilk günlerinde neredeyse boş görünüyordu. Ayrıca panel yavaştı: yanıtlar `no-store`, sıkıştırmasız ve HTTP/1.0 idi; boşta kalan panelde soğuk `isler.json` 6 ile 60 sn sürdü (canlı panel, 05.11.2026).

**Karar:**

- Pencere anahtarı `bu_ay` yerine `son_30_gun` olur: bugün ve önceki 29 takvim günü. Tek tanım `ork_lib.pencere_icinde`; `analitik.hedef_panosu` aynı aralığı kullanır. Önceki dönem, hemen önceki 30 gündür. Takvim ayına bağlı maliyet kartları ("Bu ay", ay sonu tahmini) değişmez.
- GET 200 yanıtları zayıf ETag taşır (değişmediyse 304), `Cache-Control: no-cache` ile her seferinde doğrulanır, gzip ile gider. Sunucu HTTP/1.1 keep-alive konuşur; yazma istekleri ve SSE bağlantıyı kapatır.
- Tarayıcının temel istekleri (`alan=*`) süresiz ısıtılır (eskiden son istekten 10 dk sonra bırakılıyordu). `calisma_alanlari` (4 sn) ve niyet görünümü (4 sn) kısa ömürlü bellek kullanır.

**Seçenekler:**

- Yalnız etiketi değiştirmek: elendi, anahtar ve hesap takvim ayında kalır, ikinci kopya (`analitik.py`) tutarsız kalırdı.
- Uzun `max-age` ile statik dosya: elendi, sürüm geçişinde eski js kalır; `no-cache` + ETag aynı kazancı (304) bayatlık riskiyle yaşatmaz.
- Ayrı önbellek sunucusu (Redis vb.): elendi, tek kullanıcılı yerel panel için bağımlılık ve işletme yükü, kazanç aynı süreç içi önbellekle alınıyor.
- `niyet.gorunum` içinde genel bellek: elendi, testler ve başka çağıranlar bayat sonuç görür; bellek yalnız panelde.

**Sonuçlar:**

- Olumlu: gzip ile `isler.json` yaklaşık %79 küçüldü (test örneği); ikinci yüklemede 304; boşta kalıp dönen kullanıcı soğuk üretimi beklemez.
- Olumsuz: soğuk üretimin kendisi hâlâ 4 ile 8 sn (`_tum_topla`, `niyet.gorunum`, `maliyet_kayitlari`); yalnızca süreç ilk açıldığında görülür. Kalıcı çözüm üretici maliyetini düşürmektir (ayrı iş).
- Geri alma: `ORKESTRA_PANEL_ISITMA=0` ısıtmayı kapatır; `panel.py` commit'leri geri alınabilir, anahtar adı `PENCERELER` içinde.

**İlgili iş:** I-393
