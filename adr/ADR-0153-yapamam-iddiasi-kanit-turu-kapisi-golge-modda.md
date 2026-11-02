# ADR-0153: Yapamam iddiası kanıt türü kapısı gölge modda

**Durum:** Kabul edildi

**Tarih:** 2026-11-02

**Bağlam:**

Kullanıcı sorusu: "bir birimlik iş 5-6 birime çıkıyor." Brief'te "yapamam" iddiası ve sonradan yanlış çıkan karar suçlanıyordu.

Ölçüm (02.11.2026 20:49, son 7 gün, 168 oturum, 5020 asistan metin turu): 37 aday, 32 tekil olay; iki etiketleyici (kappa 0,752, alt eşik 0,60) ve hakem.

Bulgu: yaklaşık 21 olay doğru araç ya da ortam sınırıdır; kesin yanlış 1, olası yanlış 4. Yanlış ya da olası yanlışların tamamı DOGRULANMADAN_IDDIA sınıfındadır (denenmeden yazılmış).

Kök neden: yapamam cümlesi yanıt metninde serbest doğar; P-023 yalnız kimlik/anahtar sözcüklerini, P-021 yalnız bilgi sorusunu yoklar. Karar kaybı (geri alınan karar) bu örneklemde ölçülmedi.

**Karar:**

- Hata anı bağlamına tek satır eklendi (L4): yapamam yazmadan önce "Denendi: … Engel: …" (standartlar/kok_neden.md, Araç hatası anı).
- Stop zincirine gölge kapı eklendi: kanıt türü olmayan yapamam cümlesi gunluk.jsonl'a `kapi_golge / yapamam_kaniti` yazar (scripts/yapamam_kaniti.py, ayarlar/yapamam_kaniti.json, mod golge).
- İhlal moduna geçiş ayrı karardır: canlı pencerede 30 tetik ve elle sınıflamayla 0 yanlış pozitif (P-028).

**Seçenekler:**

- Seçilen: hata anı satırı (L4) artı gölge ölçüm. Neden: iddia hata sonrası doğar; mevcut enjeksiyon orada çalışır, yeni sabit yük yok.
- Elenen: kanitsiz_iddia tetik kalıplarına yapamam eklemek. Neden elendi: kalibrasyon kesinliği %29; yeniden kalibrasyon gerekir.
- Elenen: her kullanıcı mesajına sabit hatırlatma. Neden elendi: 32 olayın yaklaşık 21'i doğru sınırdı; gürültü ve token maliyeti.
- Elenen: kapıyı baştan ihlal modunda açmak. Neden elendi: gerçek adaylarda 17/37 parça işaretlendi, DOGRULANMADAN olaylardan yalnız 2/5 yakalandı; kesinlik düşük.

**Sonuçlar:**

- Olumlu: yanlış yapamam kaynağı olan kanıtsız cümleler günlükte görünür; kanıt satırı hata anında ajana hatırlatılır.
- Olumsuz: kapı "yanlış"ı değil "kanıt türü yazılmamış"ı ölçer; kesinlik düşüktür, bu yüzden engellemez. Karar kaybı ölçülmedi ve "5-6 birim" etkisi bu örneklemle doğrulanamadı.
- Geri alma: ayarlar/yapamam_kaniti.json mod "kapali" ya da ORKESTRA_YAPAMAM_KANITI=0.

**İlgili iş:** I-361 (McD); kural P-045, P-028, P-023, P-021; ORK-ADR-0085.
