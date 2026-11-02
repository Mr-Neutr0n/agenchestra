# ADR-0151: Açık sorular Gelen kutusunda kalır ve karar soruları düğmeyle sunulur

**Durum:** Kabul edildi

**Tarih:** 2026-11-02

**Bağlam:**

Ajan kullanıcıya soru sorduğunda soru yalnız o turun metninde ya da seçim ekranında yaşıyordu. Kullanıcı başka şey yazarsa ya da ekranı kapatırsa soru hiçbir depoda kalmıyor, sonraki tur ondan habersiz başlıyordu (kullanıcı: "sorular soruluyor ama sonrasında unutuluyor").

Ayrıca "Kurayım mı, yoksa önce listeyi görelim mi?" biçimli düz metin sorular P-029 kalıplarından kaçıyordu: `yoksa` kalıbı nokta ve virgülde kesiliyordu ("1." gibi sayı noktası dahil).

**Karar:**

- Sorular mevcut onay deposunda `tur=soru` kaydı olarak tutulur (scripts/onay.py); ikinci kayıt sistemi kurulmaz. Yaşam döngüsü: `bekliyor` → yanıtlanınca `uygulandi`, kapatılınca `iptal`, 14 gün yanıtsız kalırsa `eskidi`.
- Kayıt kaynağında açılır: PreToolUse'ta AskUserQuestion ve dolu `ask` alanlı wrap_up, Stop'ta düz metin karar sorusu (scripts/acik_soru.py, hook.py bağlantıları). Alt ajan ve auto modu soru açmaz (P-029, ADR-0086).
- Kapanış: PostToolUse'ta yanıtlanan AskUserQuestion, UserPromptSubmit'te düğme etiketiyle gelen mesaj, panelden "Yanıtlandı" / "Gerek yok" ya da `orkestra onay soru-kapat`.
- Panel Gelen kutusunda ayrı "Açık sorular" grubu (seçenek düğmeleri, Yanıtlandı, Gerek yok); Gelen kutusu rozetine katılır. Soru "bekleyen karar" sayılmaz: `sayac()["bekliyor"]`, Onaylar sekmesi ve /orkestra:onay yönergesi onu içermez, `karar_ver` soruyu reddeder.
- Açık soru olan oturumun SessionStart ve UserPromptSubmit bağlamına en çok 300 karakterlik tek satır eklenir; açık soru yokken 0 karakter.
- Kalıp kaçağı kaynağında kapatılır: `yoksa` kalıbı sayı noktasını geçer, `…ayım mı, yoksa` ve `…elim mi?` kalıpları eklenir. Son cümle `?` denetimi (yapisal_mod) golge kalır (P-028).
- Kural P-053 olarak yazılır.

**Seçenekler:**

- Ayrı sorular.jsonl defteri: elendi; ikinci kayıt sistemi, panelde ikinci okuma yolu ve sayaç gerektirir.
- Soruları mevcut insan kararı kartına karıştırmak: elendi; karar onayı ile soru yanıtı karışır, sayı görünmez olur.
- Yalnız istem güçlendirmek: elendi; tur başı yönerge zaten var ve örnek cümle onunla da üretildi.
- Yapısal denetimi doğrudan block yapmak: elendi; yanlış pozitif ölçülmeden retorik soruları engeller (P-028).

**Sonuçlar:**

- Olumlu: yanıtlanmayan soru kaybolmaz; kullanıcı tek yerden görür, ajan bağlamında hatırlatma alır.
- Olumsuz: düz metin sorunun yanıtını hook anlayamaz; kayıt açık kalır ve ajan `soru-kapat` ile ya da kullanıcı panelden kapatır, yoksa 14 gün sonra eskir.
- Geri alma: ORKESTRA_ACIK_SORU=0 yakalamayı kapatır; panel grubu kayıt yoksa görünmez. Kayıtlar onaylar/ altında düz JSON'dur.

**İlgili iş:** I-358, P-053, P-029, ORK-ADR-0086
