# Orkestra dokümanı

Orkestra, Claude Code içinde çalışan bir ajan orkestrasyon eklentisidir: plugin, subagent, skill, hook, workflow ve otomatik hafıza.

## Nereden başlamalı

- **Yeni kullanıcı:** [readme-for-human.md](../readme-for-human.md) kurulum, ilk iş ve sorun gidermeyi anlatır.
- **Kavramlar ve mimari:** bu sayfa.
- **Tam envanter (kaynaktan üretilir):** aşağıdaki başvuru sayfaları.
- **Ajanlara verilen kurallar:** [KURALLAR.md](../KURALLAR.md).
- **Eklentiyi geliştirenler:** [GELISTIRME.md](../GELISTIRME.md).

## Başvuru sayfaları

Bu sayfalar `scripts/dokuman_uret.py` ile kaynak dosyalardan üretilir; elle düzenlenmez.

- [Skill'ler](basvuru/skiller.md): her `/orkestra:<ad>` komutu ve ne zaman kullanılacağı.
- [Ajanlar](basvuru/ajanlar.md): işçiler, denetçi, triyaj, araştırmacı ve diğerleri.
- [CLI](basvuru/cli.md): `orkestra` komutlarının tam yardım metni.
- [Ayarlar ve kapılar](basvuru/ayarlar.md): `ayarlar/*.json` ve kapı modları.
- [Hook'lar](basvuru/hooklar.md): hangi olayda hangi komut çalışır.
- [Kurallar](basvuru/kurallar.md): her projeye yüklenen eklenti kuralları.
- [Standartlar ve şablonlar](basvuru/standartlar.md): PR, commit, review, belge şablonları.
- [Ortam değişkenleri](basvuru/ortam.md): `ORKESTRA_*` anahtarları ve kapıları kapatma.
- [ADR dizini](basvuru/adr.md): mimari karar kayıtları.

Başvuruyu yenilemek için:

```bash
python scripts/dokuman_uret.py
```

Güncellik denetimi için `python scripts/dokuman_uret.py --kontrol` çalıştırılır; eskimişse çıkış kodu 1 olur.

## Kavramlar

### Maliyet merdiveni

- Her iş izin verilen en ucuz basamakta başlar: betik, Haiku, Sonnet, Opus orta, Opus yüksek.
- İşçi ajanlar `isci-t1`, `isci-t2`, `isci-t3` ve `isci-t4` bu basamaklara karşılık gelir.
- İki ret sonrası iş bir üst basamağa çıkar.

### Roller

- **Ana ajan** planlar, dağıtır ve toplar; işçi işini yapmaz, onay yazmaz.
- **İşçi** görev kartını uygular.
- **Denetçi** (`denetci`) işçi çıktısını kabul kriterlerine göre ayrı bir ajan olarak denetler; kimse kendi işini onaylamaz.
- **Triyaj** (`triyaj`) büyük isteği iş sınıflarına ve basamaklara ayırır.
- **Test yazarı** (`test-yazari`) kod kartlarında kod yazılmadan önce kırmızı testi yazar.

### Görev kartı ve defterler

- Görev kartı bir işin tek sorusunu, kabul kriterlerini ve yazma alanını taşır (`orkestra kart`).
- Ortak defter her ajanın ne yaptığını kaydeder (`orkestra defter`).
- Token defteri ajan, süreç ve model kırılımıyla maliyeti kaydeder (`orkestra maliyet`).

### Kapılar

- Kapı, kuralı kodla zorlayan denetimdir; bir hook ya da CLI komutu çalıştırır.
- Her kapının `ayarlar/<ad>.json` dosyasında bir modu vardır: `golge` yalnız uyarır ve günlüğe yazar, `ihlal` reddeder.
- Yeni kapılar önce `golge` modunda açılır; ihlal modu ölçümden sonra ayrı kararla verilir.
- Ortam değişkeni `ORKESTRA_<KAPI>_KAPISI=0` ilgili kapıyı kapatır.

## Mimari

### Katmanlar

- **Kural katmanı:** `kurallar/eklenti_kurallari.json` her projeye yüklenir; proje kuralları üstüne eklenir ve çakışmada proje kazanır.
- **Hook katmanı:** `hooks/hooks.json` Claude Code olaylarını `scripts/hook.py`'ye bağlar. Olaylar: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, SubagentStart, SubagentStop, Stop, Notification, PreCompact, SessionEnd, ConfigChange.
- **CLI katmanı:** `scripts/orkestra.py` komut modüllerini kaydeder; ajanlar ve kullanıcı `orkestra <komut>` ile çağırır.
- **Ajan ve skill katmanı:** `agents/` ve `skills/` altındaki dosyalar rolleri ve tekrar eden işleri tanımlar.
- **Panel:** `orkestra panel` ile açılan yerel arayüz işleri, onayları ve maliyeti gösterir.

### Hook akışı

- **UserPromptSubmit** kullanıcı mesajını sınıflar, işe bağlar ve onayı yakalar.
- **PreToolUse** her araç çağrısından önce izin politikasını, yazma alanını ve onay kapısını uygular.
- **PostToolUse** sonucu deftere ve günlüğe işler.
- **Stop** tur sonunda bağlantı satırlarını ve çıktı sözleşmesini denetler.

### Veri nerede durur

- Proje durumu `.claude/orkestra/` altındadır.
- İşler proje içindeki iş klasörlerinde `is.json` ile tutulur.
- Kimlik ve anahtarlar kullanıcı düzeyindeki kimlik klasöründedir ve `orkestra kimlik` ile okunur.
- Sistem haritası `.claude/orkestra/sistem_haritasi/` altında betikle üretilir (`orkestra harita`).

## İş yaşam döngüsü

Çok adımlı bir iş şu sırayla yürür:

1. `orkestra is ac` yeni iş açar, `orkestra is devam` var olana bağlanır.
2. Önce mevcut durum belgesi, sonra plan, sonra todo yazılır; sıra `orkestra is sira` ile görülür.
3. `orkestra plan dogrula` plan iddialarını kanıtla doğrular; plan yazarından ayrı denetçi best in class denetimini yapar.
4. Kullanıcı onaylar; `/orkestra:auto` modunda kullanıcının mesajı onay yerine geçer.
5. Maddeler dalgalara bölünür (`orkestra is dalga`); bağımsız maddeler paralel koşar.
6. Her çıktı ayrı denetçiden geçer; todo maddeleri kanıt notuyla kapanır.
7. `orkestra is kapat` çalışma özetiyle işi kapatır; kapanışta ADR ve plan kapsama denetimi yapılır.

## Önemli sınırlar

- Push yalnız kullanıcının açık isteğiyle yapılır; zorla push her modda reddedilir.
- Sır değeri hiçbir çıktıya girmez; sır yalnız yeriyle anılır.
- Genel davranış önce eklenti kaynağına yazılır; projede yalnız yapılandırma kalır.
- Karar gerekçeleri [ADR dizininde](basvuru/adr.md) durur.
