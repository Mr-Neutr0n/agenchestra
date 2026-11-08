# ADR-0172: Cursor kurulumu: komut yazımı, tek uçuş, kopya eşleme, dinamik sonda ve host'tan bağımsız oturum kimliği

**Durum:** Kabul edildi

**Tarih:** 2026-11-08

**Bağlam:**

I-018 (Cursor uyumu) analizinde Orkestra'nın Cursor'a kurulduğunda hata vermeden kırıldığı ve hiçbir denetimin bunu söylemediği görüldü. Hepsi Cursor CLI 2026.10.16 üzerinde, Claude ortamından arındırılmış (CLAUDE*, ORKESTRA*, ANTHROPIC*, Git Bash değişkenleri ve eklenti bin yolu çıkarılmış) gerçek ajan koşularıyla ölçüldü.

1. Cursor Shell'inde `orkestra` komutu yok. Claude Code eklenti `bin` klasörünü yalnız kendi Bash'inin PATH'ine ekler. Cursor CLI'nin Shell'i PowerShell'dir; `Get-Command orkestra` boş döndü. Hook ve skill'lerin ajana verdiği her `orkestra kart/niyet/is …` komutu bu yüzden başarısız olurdu.
2. Oturum kimliği yalnız `CLAUDE_CODE_SESSION_ID` / `CLAUDE_SESSION_ID` değişkenlerinden okunuyordu. Cursor Shell'inde bunlar yok; `CURSOR_CONVERSATION_ID` var ve hook yükündeki `session_id` ile aynı (Shell değeri ile hook yükü aynı koşuda karşılaştırıldı; ayrıca 468 hook kaydında `session_id == conversation_id`). Niyet defteri, iş talebi, hata kaydı ve ortak defter Cursor'da oturumsuz yazılıyor ya da "oturum kimliği bulunamadı" ile duruyordu.
3. Yerel Cursor kopyası (`~/.cursor/plugins/local/orkestra`) elle kopyalanıyordu ve bayatlamıştı (13/42 skill, `.mcp.json` yok, adaptörün eski sürümü). Kopyayı eşleyen bir mekanizma yoktu.
4. Cursor, aynı hook olayını yüklü her Orkestra kopyası için ayrı süreçle çalıştırır: yerel kopya, Claude eklenti önbelleğinin Cursor'a üçüncü taraf içe aktarımı ve proje hook'u. Ölçüm: sessionStart, postToolUse ve sessionEnd ikişer, preToolUse üç kez geldi. Her kopya defteri ve kapıları ayrı yazar. Birden çok kopya aynı çağrı için `updated_input` döndürürse Cursor hiçbirini uygulamadı (üç sahte hook ile ölçüldü, komut değişmeden çalıştı); bu yüzden komut yazımı tek başına yetmezdi.
5. Cursor, Git Bash'ten başlatıldığında hook komutlarını bash'te çalıştırır; PowerShell sözdizimli komutlar hata verir ve Shell aracı tamamen engellenir. Hook komutlarındaki baştaki tırnaklı yol (`"C:/.../python.exe" ...`) PowerShell'de söz dizimi hatasıdır; eklentinin kendi `python -c "..."` biçimi her iki kabukta çalışır.

Kök neden: Cursor desteği hook olaylarının çevirisi olarak tasarlandı (`cursor_hook.py`); Shell tarafı sözleşmesi (komutun erişilebilirliği, oturum kimliği, kopya güncelliği, çok kopyalı yükleme) ölçülmeden Claude'daki gibi varsayıldı. `doktor` Cursor için yalnız BOM'u denetliyordu. Bu işin ilk ölçüm girişimi de Claude oturumunun PATH'ini devraldığı için "komut var" gösterdi: ölçüm, ölçülen host'un ortamını taklit etmedi.

**Karar:**

1. `ork_lib.oturum_kimligi()` oturum kimliğinin tek çözümleyicisi olur. Sıra: `ORKESTRA_OTURUM`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_SESSION_ID`, `CURSOR_CONVERSATION_ID`. `ork_lib.defter_ekle`, `hata_kayit` ve `niyet` bunu kullanır. Claude'da ilk iki değişken öncelikli olduğundan davranış değişmez.
2. Kabuk türünden bağımsız komut yazımı: `cursor_hook.py` preToolUse'ta Shell komutunda tırnak dışı, komut konumundaki çıplak `orkestra` sözcüğünü `python "<eklenti>/scripts/orkestra.py"` ile değiştirir (`updated_input`). Tırnak içi metne, argümanlara ve `xorkestra` gibi sözcüklere dokunmaz. Bu biçim PowerShell, cmd ve bash'te aynı çalışır; PATH'e ve kullanıcı ortamına dokunulmaz. Hook zaten `--ajan-id` ekleyerek komutu yeniden yazıyorsa onun çıktısı üzerine uygulanır. Reddedilen komuta dokunulmaz, `permission` alanına karışılmaz. `ORKESTRA_CURSOR_KOMUT_YAZ=0` kapatır.
3. Tek uçuş: aynı olay yükünü alan Orkestra kopyaları arasında ilk gelen süreç sahiptir ve `hook.py`'yi bir kez çalıştırır; sonraki kopyalar sahibin çıktısını aynen yazar. Anahtar olay adı ile ham yükün özeti; kilit ve sonuç dosyaları geçici klasörde tutulur. Kilit 15 saniyeden eskiyse aynı yükün yeni bir olayı sayılır. Sahip hata verirse bekleyenler kendi başına çalışır. Okuma-yalnız çağrılar (hook.py'nin zaten atladığı) kilitlenmez. `ORKESTRA_CURSOR_TEKIL=0` kapatır. Bu korumayı taşımayan eski kopyalar etkilenmez; `doktor` onları bayat kopya olarak bildirir.
4. `doktor` yeni `cursor_kurulum` kontrolünü (opsiyonel sınıf) ekler: (a) kullanıcı ve makine PATH'iyle (Windows'ta kayıt defterinden) `orkestra` komutu yoksa ve Cursor'un çalıştıracağı adaptör komutu yeniden yazmıyorsa uyarı; (b) yerel Cursor kopyası kaynaktan eksik ya da farklı dosya taşıyorsa uyarı; (c) Claude eklentisi de kuruluysa çift yükleme izi. Cursor izi yoksa atlanır.
5. Kopya eşleme: `cursor_kur.py` yerel Cursor kopyasını eklenti kaynağıyla eşler. Yalnız eksik ve farklı dosyalar yazılır, hedefteki fazlalığa dokunulmaz, `tests/evals/docs/__pycache__` kopyalanmaz, bağlantı (junction/symlink) hedefe dokunulmaz. Önce tam yedek `<makine dizini>/cursor_yedek/<zaman>/orkestra` altına alınır (en yeni 5 yedek kalır). `doktor --duzelt --evet` B sınıfı onarım olarak uygular; `doktor --geri-al` yedeği geri koyar.
6. Dinamik sonda: `orkestra doktor --cursor-sonda` gerçek bir Cursor CLI ajan koşusu yapar (temiz ortam, geçici proje, kullanıcının gerçek Cursor kurulumu). Kanıt hook ve dosya tarafındadır: adaptör komutu açık yola yazdı mı, komut Shell'de çıktı verdi mi, Shell'in `CURSOR_CONVERSATION_ID` değeri hook yükündeki `session_id` ile aynı mı. Model kullanır ve ~1 dk sürer, bu yüzden yalnız açık istekle koşar; hook ve doktor kontrolleri bunu çağırmaz.

**Seçenekler:**

- Kullanıcı PATH'ine `orkestra` bin klasörünü eklemek: reddedildi. Kullanıcı ortamını değiştirir, kabuk türüne (PowerShell/Git Bash/cmd) ve IDE'nin PATH'i ne zaman okuduğuna bağlıdır; ölçülemeyen IDE davranışı kalır. Komut yazımı kabuktan bağımsız ve ölçüldü.
- `sessionStart` çıktısındaki `env` ile PATH eklemek: reddedildi. Belge bu değişkenlerin yalnız sonraki hook süreçlerine aktığını söylüyor, Shell'e değil.
- `permission` ile `ask`: Cursor `ask` kararını uygulamıyor (019 ölçümü); komut yazımı `permission` alanına dokunmaz.
- Birden çok kopyanın çakışan `updated_input`'una güvenmek: reddedildi, uygulanmadığı ölçüldü; tek uçuş (Karar 3) ile çıktı kopyalar arasında aynı olur.
- Yalnız belgelemek: reddedildi; sessiz kırığı göstermez.
- Sondayı doktorun her koşusuna eklemek: reddedildi. Model çağrısı yapar ve süre alır.

**Sonuçlar:**

- Cursor CLI'de (PowerShell Shell) `orkestra` komutu PATH'te olmadan çalışır ve oturum kimliği gerektiren komutlar `CURSOR_CONVERSATION_ID` ile yazılır; dinamik sonda üç ölçümde de geçti (08.11.2026, kopya eşlendikten sonra): komut yeniden yazıldı, komut çıktı verdi, oturum kimliği eşit.
- Tek uçuş ve yeniden yazım için üç kopya (yerel, Claude önbelleği ve proje hook'u) aynı kodu taşımalıdır. Claude eklenti önbelleği Cursor'a içe aktarılırken yerel kopyanın kökünü kullandığından ölçümde üç kopyanın çıktısı aynıydı. Önbellek kopyası ayrı bir kök kullanan bir kurulumda eski sürüm kalırsa `doktor` çift yükleme ve bayat kopya uyarısı verir.
- Cursor IDE'nin Shell türü ölçülmedi. Yazılan komut kabuktan bağımsızdır (`python "<yol>"`), ama IDE içinde koşulmuş bir ölçüm yoktur; bu açık kalır.
- Git Bash'ten başlatılan Cursor CLI'de hook komutları bash'te çalıştığından kullanıcıya özgü bir hata görülebilir; sonda bu izleri ortamdan çıkarır ve gerçek kullanımı (PowerShell/IDE) ölçer.
- Claude yolu değişmez: oturum çözümleyicide Claude değişkenleri önceliklidir, Cursor değişiklikleri `cursor_hook.py` ve Cursor'a özgü `doktor` kontrolüyle sınırlıdır.
- Kopya eşleme kullanıcı klasörüne yazar; yedek ve `--geri-al` ile geri alınabilir.

**İlgili:** I-018, `Claude_Orkestrasyon/019-20261016-cursor-uyumu/cursor_eksiklik_analizi_20261108.md` (G5, G18, G22), ADR-0120 (ajan üretici deseni), P-022, P-028.
