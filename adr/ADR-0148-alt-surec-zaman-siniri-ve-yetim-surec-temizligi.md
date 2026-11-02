# ADR-0148: Alt süreçler süre sınırlı olur, yetim süreçler bakımda temizlenir

**Durum:** Kabul edildi

**Tarih:** 01.11.2026

**Bağlam:**

- 01.11.2026 16:40 ölçümü: boş RAM 496 MB / 11.947 MB, 105 adet 1 saatten eski ebeveynsiz git.exe, 23 sa önce başlamış yetim oturum_bakim.py, 20,5 sa önce başlamış yetim mcp_kimlik.py.
- `ork_lib.git` süresiz bekler ve stdin'i miras alır (scripts/ork_lib.py:1216); takılan git hook'u ve bakım kilidini tutar.
- Yetim süreci toplayan hiçbir bakım adımı yoktur; ADR-0123 arka plan görevi için "süreç öldürülmez" der, yetim kalıntı o kapsamda değildir.

**Karar:**

- `ork_lib.git` 60 sn zaman aşımı ve stdin=DEVNULL taşır; aşımda returncode 124 döner.
- `scripts/surec_temizle.py` oturum bakımında koşar: ebeveyni ölü + eşikten eski + izin listesindeki süreci ağacıyla öldürür (git ≥1 sa; mcp_kimlik.py, oturum_bakim.py, test_paralel.py ≥2 sa).
- Her silme `surec_temizle.jsonl`'a yazılır; mod ayarı `ayarlar/surec_temizle.json` (uygula | golge), kapatma ORKESTRA_SUREC_TEMIZLE=0.
- panel.py, MCP sunucuları ve canlı ebeveynli süreçler dokunulmaz.

**Seçenekler:**

- Elenen: yalnız tur sonunda yetimleri raporlamak. Neden elendi: sızıntı sürer, kullanıcıya iş çıkar (K-006).
- Elenen: Windows Job Object ile çocukları ebeveynle öldürmek. Neden elendi: hook'lar kısa ömürlü ayrık süreç başlatır, Job Object ayrık bakım ve panel yaşam döngüsünü bozar; ayrıca Claude Desktop'un kendi süreçleri kapsam dışıdır.
- Elenen: conhost.exe yetimlerini öldürmek. Neden elendi: işletim sistemi yönetir, canlı konsolu kapatabilir.

**Sonuçlar:**

- Olumlu: takılı git hook'u en çok 60 sn tutar; yetimler her saat bakımda temizlenir.
- Olumsuz: yanlış pozitif riski (izin listesi, yaş ve ebeveyn kapısıyla sınırlı); PID yeniden kullanımı doğum zamanıyla ayıklanır.
- Geri alma: ORKESTRA_SUREC_TEMIZLE=0 ya da ayar modu golge; `git` zaman aşımı sabiti GIT_ZAMAN_ASIMI.

**İlgili iş:** I-327; ADR-0123 (arka plan görevi yaşı), K-006.
