# ADR-0165: Eklenti deposunda PR açılmaz; dal yerelde main'e birleştirilir ve main push edilir

**Durum:** Kabul edildi

**Tarih:** 2026-11-05

**Bağlam:**

Eklenti deposu (Desktop\Claude-Orchestration, uzak mertdurukan/agenchestra) kullanıcıya aittir. GELISTIRME.md "Yayın akışı" ve "Yan işler" bölümleri `main`'e "yalnız `--ff-only` ya da PR ile" girilmesini söylüyordu. I-386'da ajan PR açtı (PR 15); kullanıcı PR istemediğini, depo kendisine ait olduğu için doğrudan commit, birleştirme ve push yapılabileceğini söyledi. PR bu depoda başka bir kişinin gözden geçirme kapısı değildir, yalnız ek adım ve bekleme getirir.

**Karar:**

- Yeni kural P-057 (ZORUNLU, eklenti katmanı): iş kendi dalında commitlenir; hedefli testler geçince dal `origin/main` üzerine alınır, yerelde `main`'e fast-forward birleştirilir ve `main` push edilir. PR açılmaz; açılmış PR birleşen commit anılarak kapatılır.
- GELISTIRME.md'deki "ya da PR ile" ifadeleri kaldırılır.
- Push kuralları değişmez: zorla, silme ve ayna push reddedilir; push yalnız açık istek ya da /auto ile yapılır.
- Eklenti dışındaki depolar kapsam dışıdır.

**Seçenekler:**

- Davranışı yalnız hafızada tutmak: elendi; hafıza yalnız bu kullanıcının oturumlarında yüklenir, kural katalog ve KURALLAR.md ile her projeye ve her oturuma taşınır.
- PreToolUse hook'u ile `gh pr create` engellemek: şimdilik elendi; tekrar eden ihlal kanıtı yok, yeni kapı P-028 gereği önce gölge olurdu; tekrar ederse ayrı iş.
- PR'ı korumak, yalnız otomatik birleştirmek: elendi; gereksiz ek adım ve bekleme.

**Sonuçlar:**

- Olumlu: yayın akışı kısalır, kullanıcı isteğiyle tutarlı olur.
- Olumsuz: gözden geçirme ara adımı yoktur; güvence hedefli testler ve ayrı denetçi onayıdır.
- Geri alma: `orkestra kural kapat P-057` ve GELISTIRME.md ifadelerini eski haline getirmek.

**İlgili:** ADR-0050 (tek main), ADR-0086 (/auto push yetkisi), ADR-0161 (iş worktree'leri), P-006.
