# ADR-0156: Niyet defteri: atomik niyet kaydı, ham mesaj yok

**Durum:** Kabul edildi

**Tarih:** 2026-11-03

**Bağlam:**

- Kullanıcı mesajı bugün yalnız ilk cümle (en çok 120 karakter) olarak özetlenip niyet.jsonl, gunluk.jsonl ve konular.jsonl'a dağılıyor.
- Mesajdaki birden çok niyet, tür, başarı kriteri, canlı durum ve kanıt hiçbir yerde tutulmuyor.
- /orkestra:close niyetleri defterden değil transkriptten geriye dönük çıkarıyor; istek_id kullanılmıyor.
- Mesajın ilk 200-300 karakteri iki dosyada ikinci kopya olarak duruyor; transkript zaten saklıyor.

**Karar:**

- Her mesajdan çıkan atomik niyetler (tür, başarı kriteri, kısıt, durum, kanıt) istek_id'ye bağlı tek defterde (scripts/niyet_defteri.py, niyetler.jsonl) kaydedilir.
- Defter ham mesaj saklamaz; kaynak işaretçisi istek_id'dir. Niyet metni yine de maskeden geçer.
- Niyetleri ajan ilk turda `orkestra niyetler ekle` ile yazar; hook yalnız kimlik ve kısa yönerge üretir.
- Revize ve vazgeçme mesajı önceki niyete bağlanır; "karşılandı" ve "kısmen" kanıtsız yazılamaz.
- /orkestra:close defteri birincil, transkripti yedek kaynak olarak okur.
- Kapı gölge modda açılır (P-028); ihlal geçişi en az 60 anlamlı istekte niyet yazılma (kapsama) oranının Wilson alt sınırı en az %75 ölçülünce (uzunluk vekiliyle çok niyetli ayırma, elle etiketli 30 mesajda kesinlik %43 verdiği için bırakıldı) ayrı kararla yapılır.

**Seçenekler:**

- Seçilen: ayrı, ekleme-only niyet_defteri.py. Neden: konu_defteri.py ile aynı kanıtlı örüntü, geri alması kolay.
- Elendi: niyet.jsonl'a alan eklemek. Neden: hesap geneli dosyayı panel okuyor, şema bozulma riski yüksek.
- Elendi: her mesajdan ayrı LLM çağrısıyla niyet çıkarmak. Neden: maliyetli ve kayıyor; ajan zaten turun içinde.
- Elendi: ham mesajı maskeleyip saklamak. Neden: transkriptte zaten var, ikinci kopya sır ve boyut riski.

**Sonuçlar:**

- Olumlu: niyetler canlı izlenir, close kanıtlı ve tutarlı çalışır, sapma ölçülebilir.
- Olumsuz: ajan niyeti yazmayı unutabilir (gölge kapı ölçer); turda yaklaşık 80 token yönerge ekler.
- Geri alma: ORKESTRA_NIYET_DEFTERI=0 kapatır; modül ve komut silinirse eski close yolu çalışmaya devam eder.

**İlgili iş:** I-369, P-028, P-047, K-006

**Not:** günlüklerde mesajın tam metni yerine yalnız maskeli `ne` özeti (mesajın ilk cümlesi, en çok 120 karakter) kalır. Kapsama ölçüsü atomikliği ölçmez: çok niyetli mesaja tek niyet yazılması da yazıldı sayılır; gölge aşamada kabul edilen bilinen sınırdır.
