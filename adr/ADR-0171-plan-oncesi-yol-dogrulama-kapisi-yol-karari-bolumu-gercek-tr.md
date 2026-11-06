# ADR-0171: Plan öncesi yol doğrulama kapısı: Yol kararı bölümü, gerçek trafik kanıtı

**Durum:** Kabul edildi

**Tarih:** 2026-11-06

**Bağlam:**

I-370'te (PE-453) plan düzeltmeyi V2 `resolve()` yoluna kurdu; dağıtıcı (`agent/runtime.py` `dispatch_query`, `agent/nodes/route.py`) mevcut durumda hiç anılmadı. 06.11.2026 ölçümünde "Bu hafta Pazartesi satışı." 6 koşunun 4'ünde V1'e düştü. Kök neden: kanıt standardı tanımsızdı (belge "V2 sürdürülüyor" kabul edildi), mevcut durum §1 giriş noktası istemiyordu, P-052 tetikleyicisi ajan yargısındaydı ve mekanik kapısı yoktu. Ölçüm engeli neden değildi (I-370 planı VPN bağlıyken yazıldı).

**Karar:**

Yeni sıralı işlerde (is.json `yol: true`) mevcut durum `## Yol kararı` bölümünü taşır: Giriş noktası ve dallanmalar (dosya:satır), Gerçek trafik (ölçüm ya da ölçülemedi + kapatan plan maddesi), Karar (sürdür | başka yol | yeni yol + rakip gerekçe). Dallanma adayları `orkestra yol dallanma` ile betikten türetilir. Plan denetçisi altıncı satır `Yol kanıtı` yanıtlar. Denetim `is_sirasi.yol_karari_eksikleri` ile gölge modda (P-028) yapılır; P-052 metni bunu tanımlar. Ihlale geçiş: kapı sonrası 10 yeni işte bölümün dolu ve kanıtlı oranı ölçülür, yanlış pozitifler elle sınıflanır, ayrı kararla.

**Seçenekler:**

- Yalnız P-052 metnini sıkılaştırmak: elendi, tetik ajan yargısında kalır (I-370 kusuru).
- P-030 denetçisine yalnız beşinci soru: elendi, sonradan yakalar, belge üretilirken zorlama yok.
- `gorunum_olcumu_*` kapısını genişletmek: elendi, o kapı plan Kabul alanını yoklar, mevcut durumu değil.
- Şablon bölümü + betik + gölge kapı + kural (seçildi): kusur belgenin üretildiği yerde önlenir (L2), aday listesi türetilir (L1), kapı güvenlik ağıdır (L6).

**Sonuçlar:**

- Olumlu: yol kararı giriş noktası ve ölçüme dayanır; eski işler etkilenmez (bayraksız).
- Olumsuz: mevcut durum belgesi uzar; ad-kalıbı taraması dağıtıcıyı kaçırabilir (aday listesi, ajan doğrular).
- Geri alma: `ORKESTRA_YOL_KAPISI=0` ya da `ayarlar/yol_karari.json` kaldırılır; şablon bölümü silinir.

**İlgili iş:** I-411; P-052, P-028, P-030, ORK-ADR-0136
