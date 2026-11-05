---
name: yaklasim
description: "Sohbet sorusunu yanıtlamadan önce aday yolları (skill, MCP aracı, kod ya da canlı kayıt, resmi belge) sayıp en ucuz yeterli olanı seçtirir. Hook bağlamında 'YOL:' notu göründüğünde, kullanıcı 'nasıl bir yaklaşım', 'best in class yanıt', 'hangi yoldan çözelim', 'farklı çözüm yolları' dediğinde kullan. Yeni skill aramak için find-skills, yapı standardı için standart kullanılır; bu skill yalnız yanıt öncesi yol taraması içindir."
---

## Amaç

Yanıtın doğrudan kod yazarak, hafızadan ya da mevcut plana çıpalanarak başlamasını önler (P-048, P-056). Ayrıntı kural metni olarak bağlamda durmaz, çağrılınca yüklenir.

## Adımlar

1. Soruyu kendi cümlenle tek satıra yeniden yaz; belirsizse tek soruyla teyit et.
   - Üç iç soru (P-056): bu soru hangi kararı etkiliyor; en az bir uygulanabilir rakip yaklaşım ne (mevcut skill, hook, kural dahil); mevcut plana ya da belgeye çıpalandım mı.
   - Rakip yalnız sonucu değiştiriyorsa yanıtta tek cümleyle anılır; yoksa yazılmaz (P-001).
2. Aday yolları say, her biri tek satır:
   - skill: `SearchSkills` ya da skill listesi,
   - MCP aracı: `ToolSearch` ile ilgili araç,
   - kod ya da canlı kayıt: dosya, ayar, günlük,
   - resmi belge (ürün ya da araç davranışı için).
3. En ucuz yeterli yolu seç (önce deterministik kod ya da dosya, sonra araç, en son LLM yargısı); seçilmeyeni tek cümleyle nedeniyle an.
4. Seçilen yolla bak; kurallar yinelenmez, bağlanır:
   - doğrulama: P-021,
   - çelişkileri bulup sentez: P-031,
   - çözüm kalitesi (kök neden, rakip yollar, ölçüm): P-030.
5. Bakılamayan iddiaya 'doğrulanmadı' yaz.

## Sınır

- Yanıt kısalığı P-001'dedir: tarama sonucu uzun listeyle değil, seçilen yolun sonucuyla yanıtlanır.
- İş açma, onay ve push kuralları değişmez.
- Hook notu gölge moddadır (ADR-0103, ADR-0164); zorlama kapısı yoktur.
