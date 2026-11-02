<!-- Bu dosya scripts/dokuman_uret.py ile üretilir; elle düzenleme. -->

# Ajanlar

Kaynak: `agents/<ad>.md`. Çağrı: Agent aracı, `subagent_type: orkestra:<ad>`.

| Ajan | Görev | Model | Araçlar |
|---|---|---|---|
| `arastirmaci` | Orkestra salt okuma araştırmacısı — kod, veritabanı ve belge taraması, web araştırması, kanıt toplama. | sonnet | Read, Glob, Grep, Bash, PowerShell, WebFetch, WebSearch |
| `arsivci` | Orkestra arşivcisi — oturum çıktılarını projenin arşiv klasörüne taşır; sır taraması, anonimleştirme, db.py hariç tutma, README dizin satırı. | haiku | Read, Glob, Grep, Bash, PowerShell, Skill |
| `denetci` | Orkestra DENETÇİSİ — bir işçinin çıktısını görev kartının kabul kriterlerine göre bağımsız ve şüpheci biçimde denetler, onay ya da ret kararı yazar. | sonnet | Read, Glob, Grep, Bash, Edit |
| `hafiza-bakimcisi` | Orkestra hafıza bakımcısı — kullanıcının ONAYLADIĞI perspektif önerilerini otomatik hafızaya uygular; kopyaları birleştirir, eskimiş kayıtları düzeltir, MEMORY.md dizinini okuma sınırı içinde yeniden yazar. | sonnet | Read, Write, Edit, Glob, Grep |
| `isci-t1` | Orkestra T1 işçisi — kalıplı, mekanik, kısa işler; biçimleme, sınıflama, özet, günlük satırı, hazır betiği çalıştırıp çıktısını raporlama. | haiku | Read, Write, Edit, Glob, Grep, Bash, Skill |
| `isci-t2` | Orkestra T2 işçisi — muhakemeli mekanik işler; kod/DB taraması, madde kimliği senkronu, betik iskeleti, md/CSV/xlsx dökümü, çok dosyalı düzenleme. | sonnet | Read, Write, Edit, Glob, Grep, Bash, PowerShell, WebFetch, WebSearch, Skill |
| `isci-t3` | Orkestra T3 işçisi — muhakeme ağırlıklı işler; sentez, iddia doğrulama kararı, story/rapor içeriği, rakip karşılaştırması. | opus | Read, Write, Edit, Glob, Grep, Bash, PowerShell, WebFetch, WebSearch, Skill |
| `isci-t4` | Orkestra T4 işçisi — yalnız açıkça çok zor ya da alt basamakta iki kez reddedilmiş işler. | opus | Read, Write, Edit, Glob, Grep, Bash, PowerShell, WebFetch, WebSearch, Skill |
| `perspektif-ajani` | Orkestra PERSPEKTİF ajanı — arka planda hafıza bakımı ve skill avı yapar; hafızayı ve skill'leri YALNIZ OKUR, öneri raporu yazar. | sonnet | Read, Glob, Grep, Write, Bash |
| `skill-avcisi` | Orkestra skill avcısı — olay günlüğünden, ortak defterden ve token defterinden tekrar eden işleri bulur, skill taslağı (SKILL.md) önerir. | sonnet | Read, Glob, Grep, Write, Bash |
| `test-yazari` | Orkestra TEST YAZARI — sinif=kod kartlarında, uygulama kodundan ÖNCE kabul kriterlerinden test yazar ve testlerin kırmızı olduğunu teyit eder. | sonnet | Read, Write, Edit, Glob, Grep, Bash |
| `triyaj` | Ana ajanın UCUZ ön sınıflayıcısı. | haiku | Read, Grep, Glob |
