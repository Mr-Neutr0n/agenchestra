# ADR-0168: MCP sunucuları kullanım sınıfına göre kapsamlanır

**Durum:** Kabul edildi

**Tarih:** 2026-11-05

**Bağlam:**

- `orkestra mcp kur` seçimsiz çağrılınca kayıttaki tüm sunucuları `claude mcp add --scope user` ile kaydediyordu; kullanıcı düzeyindeki sunucular her projede, her oturumda başlar.
- Claude Code stdio sunucusunu ilk araç çağrısına kadar ertelemez; ertelenen yalnız araç tanımlarıdır (code.claude.com/docs/en/mcp.md, 05.11.2026).
- 05.11.2026 08:32'de iki oturum aynı saniyede 3221226505 (0xC0000409) koduyla düştü; aynı dakikalarda `webthreatdefsvc` ve `dwm` de çöktü. O ölçümde commit 44 / 47,7 GB, boş RAM 0,1 GB; oturum başına 9 sarmalayıcı (37 sarmalayıcı, 5 oturum).
- Yetim süreç yok: 54 sarmalayıcının hiçbirinin ebeveyni ölü değildi; yük sunucu sayısındandır.

**Karar:**

- Her MCP kaydı `sinif` taşır: `hafif`, `agir` ya da `tarayici`. Eklenti kaydında sınıf zorunludur; proje ezmesi sınıfsız olabilir ve proje düzeyinde sayılır.
- `orkestra mcp kur` kapsamı sınıftan türetir: `hafif` → `user`, diğerleri → `project`. Seçimsiz çağrı yalnız `hafif` olanları kurar; `--hepsi` hepsini sınıfına göre kapsamlar.
- `orkestra mcp goc` kullanıcı kaydındaki hafif olmayan sunucular için kaldırma ve proje kurulum komutlarını yazar; `~/.claude.json`'a dokunmaz.
- `orkestra mcp olc` canlı sarmalayıcıları oturum başına sayar; eklenti kaydı dışındaki kullanıcı sunucularını ayrı bildirir.
- SessionStart açılışta boş RAM ve commit kullanımını ölçer (`bellek_olcum`), eşik altında tek satır uyarı verir (gölge: `kapi_golge / bellek_kapisi`, engel yok, P-028).
- Uygulama günlüğündeki çıkış kodları hata defterine `cokus` kaynağıyla girer (`orkestra hata cokus`, SessionStart'ta otomatik).

**Seçenekler:**

- Seçilen: sınıfa göre kapsam. Neden: belgelenmiş kapsam modeline uyar, ürün davranışına dayanmaz.
- Elenen: stdio sunucularını ilk çağrıya kadar erteleme. Neden elendi: belgede böyle bir ayar yok.
- Elenen: alt ajan tanımında `mcpServers`. Neden elendi: eklenti alt ajanlarında yok sayılır (sub-agents.md).
- Elenen: oturum başına `--strict-mcp-config --mcp-config`. Neden elendi: bayrak oturumu başlatan komuta verilir; masaüstü uygulamasının bayrak kabul ettiği doğrulanmadı.
- Elenen: proje düzeyi `disabledMcpServers`. Neden elendi: kayıt kullanıcı düzeyinde kalır, her yeni projede elle tekrar gerekir.

**Sonuçlar:**

- Tarayıcı ya da ağır sunucu gereken proje bunu `orkestra mcp kur --mcp <ad>` ile proje dizininde açıkça ister.
- Eklenti kaydı dışındaki kullanıcı sunucuları (ör. özel bir veritabanı sunucusu) sınıflanmaz ve `mcp olc` çıktısında `kayit_disi_kullanici_sunuculari` altında görünür.
- Mevcut kullanıcı kaydının göçü kullanıcıya aittir; ajan `~/.claude.json` yazmaz.
- Bellek kapısı gölgededir; engelleyici moda geçiş en az 7 günlük `bellek_olcum` verisi ve yanlış pozitif ölçümünden sonra ayrı karardır.
- Geri alma: `ayarlar/mcp_kimlik.json` sınıflarını `hafif` yapmak, `ORKESTRA_BELLEK_KAPISI=0`.

**İlgili:** ADR-0096, ADR-0097 (MCP kimlik kaydı), P-028 (gölge kapı), P-040 (ADR deposu), I-397.
