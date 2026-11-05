# ADR-0166: Panel zaman penceresi tek kaynak ve etkin mod göstergesi

**Durum:** Kabul edildi

**Tarih:** 2026-11-05

**Bağlam:**

- Kullanıcı panelde 3 gün, hafta, ay filtrelerinin sayfalarda doğru çalışmadığını bildirdi.
- 05.11.2026 ölçümü: İşler sayfasında beş pencerede de 39 satır kalıyor, pencere yalnız tutarı değiştiriyor.
- Pencere seçimi iki anahtarda tutuluyor: v2 için orkestra.v2.pencere, klasik sayfalar için orkestra.pencere.<alan>.
- Çalışma modu yalnız Ayarlar sayfasında görünüyor; işin kendi modu panelde yok.

**Karar:**

- Pencere seçimi tek anahtarda tutulur: orkestra.v2.pencere; klasik G.pencere bileşeni onu okur ve yazar.
- İşler listesi seçili pencerede etkinliği olan işlere daralır; Gelen kutusu öğeleri süzülmez.
- Gün grafiği dizi konumuyla değil takvim tarihiyle süzülür.
- /isler.json her işe is_onay.mod ile hesaplanan mod alanını verir; üst çubuk varsayılan modu, satır ve ayrıntı işin modunu gösterir.

**Seçenekler:**

- Sunucuda pencere süzmesi elendi: aynı ölçütün ikinci tanımını doğurur.
- İki anahtarı olayla eşitlemek elendi: iki kaynak sürer ve tutarsızlık geri gelir.
- Yalnız Ayarlar sayfasını geliştirmek elendi: kullanıcı modu her sayfada görmek istiyor.

**Sonuçlar:**

- Olumlu: seçim her sayfada aynı, İşler listesi pencereyi izler, mod her yerde görünür.
- Olumsuz: pencere dışında kalan açık iş listeden gizlenir; gizlenen sayısı satırla belirtilir ve Tümü hepsini gösterir.
- Geri alma: istemci süzmesi tek işlevde, kaldırılınca liste eski hâline döner; eski anahtar silinmez.

**İlgili iş:** I-389
