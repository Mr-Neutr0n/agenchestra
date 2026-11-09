# ADR-0174: Arşivli oturum sürecini bakımda `--resume` kimliğiyle kapat, gölge modda başlar

**Durum:** Kabul edildi

**Tarih:** 2026-11-09

**Bağlam:**

- Uygulama arşivlenen oturumu `isRunning:false` gösterir, agent `claude.exe` süreci kalabilir (kullanıcı bildirimi, 09.11.2026).
- Eklentide arşiv olayını yakalayan hook yoktur; bakım koşucusu `oturum_bakim.py` en çok saatte bir koşar.
- Uygulama oturum meta dosyaları (`claude-code-sessions/**/local_*.json`) `isArchived` ve `cliSessionId` taşır.
- Oturum sürecinin kendi oturumunu belirleyen alan `--resume=<cliSessionId>`dır; `--add-dir` başka oturumun not klasörünü taşıyabilir.
- Aynı gün `--add-dir` içindeki `local_` ile yapılan elle eşleme çalışan PE-453 oturumunun sürecini yanlış kapattı; kök neden bu eşleme anahtarıdır.

**Karar:**

- Bakım koşucusuna `arsiv_surec` adımı eklenir: meta dosyalarından arşivli oturumların `cliSessionId` değerleri okunur, yalnız `--resume=<bu kimlik>` taşıyan ve `--type=` taşımayan `claude.exe` süreçleri eşlenir.
- `--add-dir` içindeki `local_` hiçbir koşulda eşleme anahtarı değildir.
- Kapı `arsiv_surec_kapat` ayarıyla gölge modda açılır: eşleşenler `kapi_golge` olarak kaydedilir, süreç kapatılmaz. İhlal geçişi ≥7 gün gölge, yanlış eşleşme 0 ve bakım turu başına ≥1 koşu ölçümünden sonra ayrı kararla yapılır.
- Kapatma ihlal modunda `taskkill /T` ile pencere açmadan (`CREATE_NO_WINDOW`) yapılır. `ORKESTRA_ARSIV_SUREC_KAPAT=0` kapatır.

**Seçenekler:**

- Seçilen: `--resume` = meta `cliSessionId`. Neden: sürecin kendi oturumunu belirler.
- Elenen: `--add-dir` içindeki `local_<kimlik>`. Neden elendi: canlı süreç başka oturumun not klasörünü taşıyabilir, yanlış kapatma yaşandı.
- Elenen: süreç adı ya da yaşa göre kapatma. Neden elendi: çalışan oturumu da kapatır.
- Elenen: arşiv olayında anlık kapatma. Neden elendi: olay için hook yok.
- Elenen: uygulama API'si (`list_sessions`). Neden elendi: hook ve bakım içinden çağrılamaz.

**Sonuçlar:**

- Olumlu: arşivli oturumların süreçleri en geç bir bakım turu (en çok saat) sonra kapanır; bellek geri kazanılır.
- Olumsuz: Yanlış eşleşme çalışan oturumu keser; gölge ölçümü ve `isArchived` doğrulaması bunu sınırlar.
- Sınır: Windows dışında süreç listesi alınamazsa adım hiçbir şey yapmaz.
- Geri alma: `ORKESTRA_ARSIV_SUREC_KAPAT=0` ya da ayar dosyasında `mod: golge`.

**İlgili iş:** I-423; ADR-0092 (bakım koşucusu), P-028, P-040
