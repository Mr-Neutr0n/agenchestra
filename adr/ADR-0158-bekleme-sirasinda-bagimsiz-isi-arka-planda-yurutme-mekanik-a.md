# ADR-0158: Bekleme sırasında bağımsız işi arka planda yürütme: mekanik aday listesi

**Durum:** Kabul edildi

**Tarih:** 2026-11-03

**Bağlam:**

Denetçi ya da başka bir süreç beklenirken ajan boş duruyordu; bekleme anında hangi işin güvenle başlatılabileceğini belirleyen kod yoktu. `paralellik.dalgalar` planı metinden hesaplar ve statiktir; kart durumunu (onaylandi, denetimde, reddedildi) bilmez. Kullanıcı 03.11.2026: beklerken boş durulmasın, yalnız kesinleşmiş, bağımsız ve yazma alanı kesişmeyen işler arka planda yürüsün.

**Karar:**

- Aday belirleme ayrı, durum duyarlı bir çekirdek olur: `scripts/bosta.py::baslatilabilir`. `is dalga` ve `paralellik.dalgalar` değişmez (plan kapısı aynı fonksiyonu kullanır).
- Aday koşulları (hepsi): iş onaylı ve plan denetimde değil; madde `bekliyor`; `Kabul` dolu (ADR-0159: `Geri alma` alanı plandan kalktı); `Önce` bağımlılıklarının (Çıktı ve Çakışma) tamamı `onaylandi`; yazma alanı `calisiyor`, `denetimde`, `reddedildi` maddelerle ve önceden seçilen adaylarla ayrık.
- Komut `orkestra is bosta <iş> [--bekleyen P<n>] [--gecersiz P<n> --neden …]`; denetçi (`orkestra:denetci`) başlarken PreToolUse hook'u aday varsa en çok 300 karakter bağlam ekler, aday yokken 0 karakter (`scripts/bosta_baglam.py`).
- Başlatma kararı ajandadır; hook Agent başlatamaz. Mekanik olan yalnız aday listesidir.
- Kapı P-028 gereği `golge` modda açılır (`ayarlar/bosta.json`); engellemez. Kural P-055.
- Ret maliyeti: aday kendi yazma alanında çalışır, geri dönüş o maddenin değişikliğinin geri alınmasıdır; plan denetimdeyse aday verilmez.
- Sınır: koşullar `Önce` ve `Yazma alanı` beyanlarının doğruluğuna dayanır; yanlış beyan mantıksal bağımlılığı yakalamaz. Ret etkisi tests/test_bosta_ret.py ile geçmiş planlarda ölçülür, canlıda `bosta_gecersiz` günlüğü izlenir.

**Seçenekler:**

- `dalgalar`a durum parametresi eklemek: elendi; plan kapısı ve dalga raporu aynı fonksiyonu kullanır, regresyon riski.
- `is dalga --bosta` bayrağı: elendi; durum duyarlı ve statik çıktı karışır.
- P-035 metnine madde eklemek: elendi; P-035 ihlal modunda, metin değişikliği kapı sözleşmesini bozar. Yeni kural P-055.
- Oturum başı kalıcı hatırlatma: elendi; boşluk anında değil önceden okunur ve unutulur. Tam zamanında bağlam seçildi.
- Hook'un işçiyi kendiliğinden başlatması: elendi; Claude Code hook'u Agent başlatamaz.
- Rastgele üretilmiş plan şekilleriyle tek başına test: elendi; gerçek planlarda görülmeyen şekiller üretir. Üretilmiş küme gerçek planlarla birlikte kullanılır.

**Sonuçlar:**

- Olumlu: bekleme anı aday listesi mekanik ve test edilmiş; 50 geçmiş planda 421 aday ve 0 geçersizleşen aday, 300 üretilmiş planda 0 ihlal.
- Olumsuz: kalite plan beyanlarına bağlı; ret riski plan metninden okunur, alan olarak zorunlu değildir. Hook yalnız denetçi başlangıcında tetiklenir, diğer bekleme anları ajanın `orkestra is bosta` çağrısına kalır.
- Geri alma: `ayarlar/bosta.json` `mod` ile ya da `ORKESTRA_BOSTA=0` ile kapanır; kod eklenti worktree commit'lerinin geri alınmasıyla kalkar. İhlal moduna geçiş ölçümden sonra ayrı ADR ile.

**İlgili iş:** I-376; kural P-055; ORK-ADR-0080 (paralellik), ORK-ADR-0035 (gölge kapılar)
