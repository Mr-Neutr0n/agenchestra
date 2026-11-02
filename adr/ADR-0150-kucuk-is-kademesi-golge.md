# ADR-0150: Küçük iş kademesi (gölge)

**Durum:** Kabul edildi

**Tarih:** 02.11.2026

**Bağlam:** Küçük işlerde (≤4 araç) üç belge, ADR satırı ve ayrı denetçi aynı yükü getiriyor; ana ajan turları 47,4 saat, alt ajanlar 20,4 saat (zaman.jsonl, maliyet_tur.jsonl, 30.10-02.11.2026).

**Karar:** `is.json` `kademe: kucuk` alanı eklenir; küçük kademede yalnız sözleşme ve tek todo zorunlu olur. Kademe önce gölge modda (P-028) çalışır: kapı ne yapacağını günlüğe yazar, engellemez.

**Seçenekler:**

- Kademe alanı (seçildi): iş boyutu açıkça beyan edilir, ölçülebilir.
- Kapıları doğrudan kapatmak (elendi): güvence kaybı ölçülmeden olur.
- Matcher daraltma (elendi): başka sorunu (hook gecikmesi) çözer, belge yükünü değil.

**Sonuçlar:** Olumlu: küçük işte belge ve denetçi süresi azalır. Olumsuz: riskli iş küçük diye beyan edilebilir; gölge günlük yanlış pozitifi ölçer. Geri alma: `ayarlar/kucuk_kademe.json` mod alanı (gölge; kademe yalnız günlük yazar, kapatmak için `--kucuk` bayrağı kullanılmaz).

**İlgili iş:** I-353, P-028, P-015
