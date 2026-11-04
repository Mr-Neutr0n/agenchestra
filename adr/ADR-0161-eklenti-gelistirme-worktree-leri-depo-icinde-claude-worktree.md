# ADR-0161: Eklenti geliştirme worktree'leri depo içinde .claude/worktrees altında açılır

**Durum:** Kabul edildi

**Tarih:** 2026-11-04

**Bağlam:**

GELISTIRME.md:22 worktree'yi `../co-wt/<iş>` ile ana kopyanın yanına, yani masaüstüne açtırıyordu.

main_kopya_kapisi ret metni yol vermiyordu; ajanlar masaüstünde `co-*` kardeş klasörleri açtı (04.11.2026: 10 worktree).

Kart worktree'leri zaten `<depo>/.claude/worktrees/` altındadır (ork_lib.py `agac_yolu`).

Kapanış temizliği yalnız `--is-ancestor` ile ölçtüğü için squash birleşen dallar hiç aday olmuyordu.

**Karar:**

İş worktree'leri `<depo>/.claude/worktrees/<ad>` altında `orkestra agac ac <ad>` ile açılır; yolu tek yardımcı (`agac_yolu`) üretir.

Ret metni ve GELISTIRME.md aynı komutu gösterir.

Kapanış temizliği squash ile birleşmiş dalları içerik denkliğiyle (`git merge-tree --write-tree`) da tanır.

**Seçenekler:**

- Elenen: masaüstünde kardeş klasör (mevcut). Neden: masaüstü kirlenir, araçlar tek kökte bulamaz, kart düzeniyle çelişir.
- Elenen: `~\.orkestra\agaclar\<depo>\` dış kök varsayılan. Neden: `ORKESTRA_AGAC_KOKU` ile seçilebilir; varsayılanı çekmek ikinci yer yaratır.
- Elenen: GitHub PR durumuyla temizlik. Neden: ağ ve kimlik ister; yerel `merge-tree` aynı sonucu çevrimdışı verir (spike: squash dal "ağaç eşit", benzersiz dal "ağaç farklı").

**Sonuçlar:**

Olumlu: tek yol, masaüstü temiz, temizlik kendiliğinden işler.

Olumsuz: `.claude/worktrees` altındaki iç içe klasör IDE taramasını yavaşlatabilir; `.git/info/exclude` bir kez yazılır.

Geri alma: GELISTIRME.md ve ret metni eski haline döner, `agac ac` komutu kaldırılır; açılmış worktree'ler olduğu gibi çalışır.

**İlgili iş:** I-380; ilgili kural K-006, P-022, P-028, P-040.
