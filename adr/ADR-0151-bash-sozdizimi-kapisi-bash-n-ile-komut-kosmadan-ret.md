# ADR-0151: Bash sözdizimi kapısı: bash -n ile komut koşmadan ret

**Durum:** Kabul edildi

**Tarih:** 2026-11-02

**Bağlam:**

- Ajanın satır içi Bash komutu hata verince komut koşuyor, sonra PostToolUseFailure `arac-hatasi` olarak kaydediyor; `kok.onlenebilir` alanı boş kalıyordu.
- hata.jsonl'da (22.10-02.11.2026) `unexpected EOF` 4 kayıt; oturum kayıtlarında Bash komutlarından 89'u "unexpected EOF" ile bitmiş.
- Ölçüm: bu 89'un yalnız 3'ü gerçek tırnak dengesizliği; çoğu araç sınırı (tek tırnak kaçışından sonra ≈7840 karakteri aşan komut kesiliyor).
- hata.jsonl'daki ilk 10 imza 1086 satırın 588'ini oluşturuyor ve hiçbiri önleme basamağına bağlı değildi.

**Karar:**

- `scripts/bash_sozdizimi.py`: `bash -n` ayrıştırması + kaçışlı uzunluk kuralı (karakter + 4 × tek tırnak > 7840) + uzun betik yönerge bağlamı. hook.py Bash dalında (PowerShell dışı) çağrılır; ret metni Write ile dosyaya yazma yolunu ve `standartlar/bash_komut_yazimi.md` dosyasını gösterir.
- Kapı `golge` modunda açıldı (P-028): `kapi_golge / bash_sozdizimi` yazılır, komut engellenmez. `ihlal` geçişi 14 gün sonra ölçümle ayrı kararla yapılır. Kapatma: `ORKESTRA_BASH_SOZDIZIMI=0`.
- `ayarlar/hata_onleme_siniflari.json`: ilk 10 imza için basamak ve sahip; `hata_kayit.py` yeni kayıtta `kok.onlenebilir` ve `kok.sahip` yazar. Tablo okunamazsa eski davranış.
- Yapamam/yanlış karar kaybı bu ADR'nin kapsamı dışında, ayrı işe devredildi.

**Seçenekler:**

- Elenen: kalıp/regex ile tırnak sayma. Heredoc ve kaçışta yanlış pozitif üretir.
- Elenen: komutu updatedInput ile otomatik dosyaya çevirmek. Niyeti, çalışma dizinini ve stdin'i sessizce değiştirir.
- Elenen: genis_tarama modülünü genelleştirmek. Kalıp ve ayrıştırma doğruluğu ayrı ölçülmeli.
- Elenen: hata_kayit `TURLER` tablosunu genişletmek. `tur` anahtarlıdır, imza deseni anahtarlı değildir; kod değişikliği gerekir.
- Elenen: doğrudan `ihlal` modu. Uzunluk eşiğinin marjı dar (en büyük başarılı 7818, en küçük başarısız 7863, eşik 7840); yanlış ret gerçek komutu bloklar.

**Sonuçlar:**

- Olumlu: hatalı ya da kesilecek komut koşmadan işaretlenir ve yönerge hazırdır; hata imzaları sahip ve basamakla kaydedilir.
- Tekrar oynatma (28.652 başarılı komut): uzunluk kuralı sahte ret 0. 320 komutluk ayrıştırma örneğinde sahte ret 0 (3/n üst sınırı ≤%0,94). 89 EOF komutundan 85'i işaretlenir; 4'ü (`\\\`` kalıbı geçerli bash, aracın kaçışı kırıyor) yakalanamaz ve bu ADR'de kabul edilir.
- Olumsuz: uzunluk eşiği araç davranışına bağlı; marj 45 karakter. Her komutta bash süreci ≈0,25 sn ek maliyet.
- Doğrulama: 14 gün sonra (birleştirme tarihinden): hata.jsonl `unexpected EOF` ≤1, tekrar eden ret oranı ≤%25; sağlanırsa ihlal moduna ayrı ADR ile geçilir.
- Geri alma: `ORKESTRA_BASH_SOZDIZIMI=0` ya da birleştirme commit'i `git revert`.

**İlgili iş:** I-359; P-045, K-006, P-028
