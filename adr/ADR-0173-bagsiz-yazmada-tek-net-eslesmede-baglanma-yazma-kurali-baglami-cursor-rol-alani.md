# ADR-0173: Bağsız yazmada tek net eşleşmede bağlanma, yazma kuralı bağlamı, Cursor rol alanı

**Durum:** Kabul edildi

**Tarih:** 2026-11-09

**Bağlam:**

- Kapı retleri üretimden sonra geldiği için 28-31 KB'lık belge ret başına baştan üretiliyor (kullanıcı raporu, aynı yazım üç kez).
- Son 14 günde 3168 turda 823 ret; bağsız ret 65 (`orkestra hata ozet`, 08.11.2026).
- Worktree dışı yol reddi Claude Code'da doğar ve hook'tan önce çalışır; hook yolu çeviremez (ADR-0162 spike).
- ADR-0162 her mesajda otomatik iş açmayı iş kirliliği nedeniyle eledi.
- Cursor `subagentStart` olayında `subagent_type` ve `subagent_id` gönderir, araç çağrılarında alt ajanı belirten alan yoktur (cursor.com/docs/hooks).

**Karar:**

- `_is_kapisi` tek net eşleşmede (en yüksek puan ≥ 0,6 ve ikinciden ≥ 0,2 yüksek) oturumu o açık işe bağlar; iş açmaz. Kapı `bagsiz_otomatik_bagla` ayarıyla gölge modda açılır (P-028); `ihlal` geçişi ölçümden sonra ayrı kararla yapılır.
- UserPromptSubmit, yazma niyeti taşıyan mesajda iskelet + bölüm kuralını ve bağlı worktree'de yazma kökünü üretimden önce bağlama koyar (`yazma_kurali.py`; `ORKESTRA_YAZMA_KURALI=0` kapatır).
- Cursor adaptörü `subagent_type` ve `subagent_id` alanlarını `agent_type` ve `agent_id` olarak eşler; Claude'un kendi alanları ezilmez.

**Seçenekler:**

- Seçilen: tek net eşleşmede bağlanma. Neden: iş açmaz, yalnız var olana bağlar; belirsizde ret sürer.
- Elenen: Write yolunu `updatedInput` ile çevirmek. Neden elendi: Claude Code hook'tan önce reddediyor (ADR-0162).
- Elenen: her bağsız yazmada yeni iş. Neden elendi: iş kirliliği (ADR-0162).
- Elenen: SessionStart'ta oturumu işe önceden bağlamak. Neden elendi: yazmayan oturumlar da iş bağlar.
- Elenen: yalnız ret mesajı ya da P-012/P-016 hatırlatmasını sıkılaştırmak. Neden elendi: ret üretimden sonra gelir, hatırlatma yazım boyutunu bilmez.
- Elenen: Cursor araç olaylarında rolü oturum kaydından okumak. Neden elendi: eşzamanlı oturumda yanlış oturumu seçer; Cursor araç olayında alt ajan alanı da göndermez.

**Sonuçlar:**

- Olumlu: tek net eşleşmeli bağsız yazımda ret ve yeniden üretim oluşmaz (ihlal moduna geçince); büyük belgede ret en çok bir bölüme mal olur.
- Olumsuz: yanlış tek eşleşme oturumu yanlış işe bağlayabilir; gölge kayıtlarında yanlış bağlanma 0 ve ≥20 olay görülmeden ihlal moduna geçilmez.
- Sınır: Cursor araç çağrılarında rol hâlâ bilinmez; yalnız SubagentStart/SubagentStop rolü tanır.
- Sınır: ADR-0162'nin worktree kökü bildirimi `i375-on-adimlar` dalında kalmıştır; `yazma_kurali.py` aynı bilgiyi yalnız yazma niyetinde verir.
- Geri alma: `ORKESTRA_BAGSIZ_OTOMATIK_BAGLA=0`, `ORKESTRA_YAZMA_KURALI=0`; Cursor eşlemesi için commit geri alınır.

**İlgili iş:** I-421; ADR-0162, P-028, P-040
