# ADR-0169: Kaynak etiketli iddia doğrulama kapısı (gölge)

**Durum:** Kabul edildi (gölge modda)

**Tarih:** 2026-11-05

**Bağlam:** 05.11.2026'da bir oturumda ajan, araçlar elindeyken sayıyı komutla hesaplamadan ve iddiayı kodla doğrulamadan yazdı (bakamama değil bakmama). P-021 kapısı yalnız kanıt aracı çağrısının varlığına bakar (scripts/kanitsiz_iddia.py), araç çıktısındaki sayıyı ve cümle başına kaynak etiketini denetlemez; tur ayrıştırıcı tool_result içeriğini atıyordu (scripts/kanit_olcum.py).

**Karar:** Stop aşamasında deterministik, model çağrısız gölge kapı `iddia_kaynak` eklenir (scripts/iddia_kaynak.py, ayarlar/iddia_kaynak.json, hook.py `_iddia_kaynak_yanit`). Yanıttaki sayı aynı turun araç çıktısında ya da isteminde yoksa `sayi_kaynaksiz`, olgu iddiası kaynak türü etiketi (Veritabanı, Kod, Doküman, Eski sohbet/oturum, Ölçüm çıktısı, Jira/Web, Kullanıcı sözü, Hafıza) ya da "doğrulanmadı" taşımıyorsa `etiketsiz_iddia` bulgusu `gunluk.jsonl`'a `kapi_golge / iddia_kaynak` yazılır. Tur ayrıştırıcı araç çıktılarını `ciktilar` alanında taşır. Kural metni P-058'dır. Kapı engellemez ve uyarı vermez (P-028).

**Seçenekler:** (1) Seçilen: deterministik sayı ve etiket denetimi. (2) Elenen: Stop'ta model hakemi; maliyet, gecikme, belirsizlik. (3) Elenen: P-021 tetik kalıplarını genişletmek; kesinlik %29. (4) Elenen: yalnız istem hatırlatması; olay hatırlatma varken yaşandı.

**Sonuçlar:** 100 gerçek yanıtta ölçüm (olcum_iddia_kaynak.md): etiket bulgularında yanlış pozitif ≈ %29 (eşik ≤%10), bu yüzden uyarı ya da ihlal geçişi yapılmaz; kapı gölgede kalır, tasarım/görüş/tablo cümleleri ayıklanıp yeniden ölçülür. Sayı denetimi daha dar ve ayrı geçişe aday. ORKESTRA_KANIT_KAPISI=0 kapatır.

**İlgili iş:** I-399
