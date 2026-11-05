# ADR-0163: Kapanış mesajında süreç anlatımı kapısı

**Durum:** Kabul edildi

**Tarih:** 2026-11-05

**Bağlam:**

- Kapanış mesajında ajan kendi iç sürecini anlattı ("onayı kendim çalıştırdım, gerekçem ...").
- P-014 bunu yasaklar ama yalnız metindir; Stop hook'unda zorlayan kapı yoktu.
- Mesajın kaynağı sablonlar/calisma_ozeti.md'deki 'Plandan sapmalar' ve 'Otomatik kararlar' bölümleridir.

**Karar:**

- L1: kapanış mesajı yalnız 'Ne yapıldı', 'Ana sayı', 'Açık kalanlar' alanlarından üretilir; şablon, auto skill'i ve P-014 metni bunu söyler.
- L5: scripts/kapanis_surec.py Stop'ta süreç anlatımı kalıplarını (ayarlar/kapanis_surec.json, proje ezmesi destekli) ölçer; kip golge, gunluk.jsonl'a kural_ihlal / kapanis_surec. Mekanizma onleme_yanit.py ile aynıdır.
- L0: ajanın `orkestra is onayla` komutu onay durumundan bağımsız PreToolUse'ta reddedilir (is_onay.onayla_engeli).
- İhlal kipine geçiş P-028 gereği ayrı karardır: 30 Stop örneği ve 0 yanlış pozitif (`python scripts/kapanis_surec.py rapor`).

**Seçenekler:**

- onleme_yanit.py'ye kalıp eklemek: iki kural tek ayarda karışır, elendi.
- Hook onayı erkene almak: onayın neden geç geldiği kanıtlanamadı, elendi.
- Yalnız kural metni: P-014 zaten var, yetmedi, elendi.

**Sonuçlar:**

- Süreç anlatımı ölçülür; yanlış pozitif oranı gölge dönemde belirlenir.
- Ajan onayı hiçbir durumda kendisi veremez; `echo orkestra is onayla` gibi komutlar da reddedilir (kasıtlı, ihtiyatlı).

**İlgili iş:** I-387
