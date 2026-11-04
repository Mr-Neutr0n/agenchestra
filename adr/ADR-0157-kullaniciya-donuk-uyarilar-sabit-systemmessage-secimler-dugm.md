# ADR-0157: Kullanıcıya dönük uyarılar sabit systemMessage, seçimler düğme

**Durum:** Kabul edildi

**Tarih:** 2026-11-03

**Bağlam:**

"Oturum uzadı" devir uyarısı `additionalContext` ile modele serbest metin olarak gidiyordu; model cümleyi kendi sözleriyle yazıyor, düğme sunmuyordu. `soguk_onbellek.devir_uyarisi` ikinci bir sabit uyarı üretiyordu; aynı turda iki devir uyarısı çıkabiliyordu.

**Karar:**

- Devir uyarısı tek sabit biçimle (`devir_esigi.devir_metni`: ölçü, öneri, seçenek) `systemMessage` ile kullanıcıya gider.
- Modele yalnız `devir_esigi.YONERGE` gider: cümleyi yeniden yazma, karar gerekirse `wrap_up` ile "Devir belgesi üret" ve "Burada sürdür" düğmelerini sun.
- Aynı turda en çok bir devir uyarısı çıkar.
- Çıktı kanalı envanteri `scripts/cikti_kanallari.py` ile hook.py taramasından üretilir (4 hook, 3 model kanalı).

**Seçenekler:**

- Yalnız istemi sıkılaştırmak: elendi, model biçimi yine değiştirir.
- Düğmeyi hook'tan çizmek: elendi, hook düğme çizemez.
- İki tetikleyiciyi birleştirmek: elendi, eşikleri farklı (5 M okuma, 200k bağlam); metin ortak, tur başına bir uyarı.

**Sonuçlar:**

- Olumlu: aynı girdi aynı metin; uyarı biçimi modele bağlı değil; kanal sayısı betikle sayılır.
- Olumsuz: düğmenin çıkması modelde zorlanamaz, yalnız yönergeyle istenir; oran ölçümü takip işidir.
- Geri alma: `i364-cikti-kanallari` dalını geri al; `ORKESTRA_DEVIR_ESIGI=0` uyarıyı kapatır.

**İlgili iş:** I-364, K-005, P-001, ORK-ADR-0153 (atıf)
