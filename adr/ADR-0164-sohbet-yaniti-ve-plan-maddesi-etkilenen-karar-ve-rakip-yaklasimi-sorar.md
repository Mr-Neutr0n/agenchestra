# ADR-0164: Sohbet yanıtı ve plan maddesi etkilenen kararı ve rakip yaklaşımı yanıttan önce sorar (P-056)

**Durum:** Kabul edildi

**Tarih:** 2026-11-05

**Bağlam:**

Kullanıcı (05.11.2026, I-383 sohbeti) ajanın sohbet sorularına ilk yanıtta sorunun arkasındaki kararı ve rakip yaklaşımları çıkarmadığını, mevcut plana çıpalanıp dar yanıt verdiğini söyledi. P-030 (Alternatifler + ayrı denetçi) yalnız belge ve plan işlerinde var. Sohbet yanıtı öncesi tek tetik P-048 YOL notudur (ayarlar/soru_sinif.json yol_sozlesmesi); aday yol sayar, "hangi kararı etkiliyor" diye sormaz. Plan şablonu Alternatifler ister, maddenin etkilediği kararı istemez.

**Karar:**

- Yeni kural P-056 (ZORUNLU, eklenti katmanı): sohbet yanıtı ve her plan maddesi etkilenen kararı ve en az bir uygulanabilir rakip yaklaşımı (mevcut skill, hook, kural dahil) çıkarır; mevcut plana çıpalanmaz.
- Sohbet: P-048 YOL notunun metni üç iç soruyu söyler (karar, rakip, çıpa); not 300 karakter sınırında kalır, yanıt P-001 kısalığında kalır. Ek bağlam ve ek not yoktur.
- Plan: şablonlara ayrı `**Etkilenen karar:**` alanı, Üretim anı ve uretim_enjeksiyonu plan metnine aynı çift, denetçi sorusuna (best_in_class.md, agents/denetci.md) aynı çift eklenir.
- `scripts/is_sirasi.karar_eksikleri` alan eksiğini gölgede yoklar (`kapi_golge/etkilenen_karar`); engellemez, ihlal modu yoktur (P-028).

**Seçenekler:**

- YOL notu sabit, üç soru yalnız skills/yaklasim'da: elendi; skill çağrılmadıkça yüklenmez, P-048 geçmişi tetiksiz kuralın işlemediğini gösterdi.
- Ayrı KARAR notu: elendi; her mesaja ek bağlam, iki not birbirini tekrarlar.
- P-048'i yerinde genişletmek: elendi; P-048 sohbet kapsamlı, plan tarafı P-030'a ait, sınırlar bulanır.
- `- Karar:` satırı Alternatifler içinde: elendi; `_alternatif_satirlari` her `- ` satırını sayar, Seçilen yerine geçebilir (is_sirasi.py).
- Stop hook'u ile yanıtta rakip aramak: elendi; anlamsal içerik kodla sınanamaz.

**Sonuçlar:**

- Olumlu: ek model çağrısı ve ek bağlam yok; mevcut gölge ölçüm ve kapatma anahtarları geçerli.
- Olumsuz: yanıt kalitesi etkisi gölge günlükte (en az 30 oturum) ölçülmeden iddia edilmez; eski planlar alansız çıkar (geriye dönük 214 planda 1161/1163 madde alansız, 05.11.2026), yoklama yalnız gölgedir.
- Geri alma: `yol_sozlesmesi` metnini eski haline almak, kuralı `orkestra kural kapat P-056` ile kapatmak; yoklama için ORKESTRA_BIC_KAPISI=0.

**İlgili:** ADR-0103 (YOL notu), ADR-0068 (Üretim anı), ADR-0111 (üretim anı enjeksiyonu), P-030, P-048, P-028.
