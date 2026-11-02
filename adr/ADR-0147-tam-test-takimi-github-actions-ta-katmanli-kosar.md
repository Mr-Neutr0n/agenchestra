# ADR-0147: Tam test takımı GitHub Actions'ta koşar, CI katmanlıdır

**Durum:** Kabul edildi

**Tarih:** 2026-11-02

**Bağlam:**

- Tam test takımı yerel makinede ~4,5 dk sürüyor ve makine genelinde kira kuyruğu yaratıyor (`plugins/orkestra/GELISTIRME.md` Test takımı, `scripts/kaynak_kira.py`).
- GitHub Actions bugün 428 test dosyasından yalnız 7'sini koşuyor (`.github/workflows/orkestra-test.yml:24`).
- Oturumları tam takımdan alıkoyan kuyruk kapısı `golge` modunda (`ayarlar/kuyruk.json`); `GELISTIRME.md` hedefli test, `.claude/rules/orkestra.md` tam komut diyor.
- Kullanıcı kararı (02.11.2026): tam takım her push ve PR'da koşmasın, yük GitHub'a taşınsın, yerelden çıksın.

**Karar:**

- CI iki katmanlıdır: hızlı katman (mevcut taşınabilirlik işi) her `push` ve `pull_request`'te; tam takım katmanı yalnız `main`'e push, gece `schedule` ve elle `workflow_dispatch` ile.
- Tam takım katmanı `test_paralel.py` ile ubuntu-latest ve windows-latest, Python 3.13'te koşar, `timeout-minutes: 30`; macOS ve Python 3.9 yalnız hızlı katmanda kalır.
- Oturumlar commit öncesi yalnız hedefli test koşar; kural tek metinde (`GELISTIRME.md` Test takımı) yazılır, `test_yonlendirme` hook'u çıplak tam koşuyu CI komutuna yönlendirir.
- Yerel entegrasyon şeridinin (ADR-0142) tam koşusu bu ADR ile kaldırılmaz; kuyruk kapısının `ihlal` geçişi ve şeridin devri P4 ölçümüne bağlı ayrı kararlardır (P-028).
- Kırmızı tam koşu başarısız test adlarını job özetine yazar.

**Seçenekler:**

- Her push ve PR'da tam takım, 3 işletim sistemi: elendi, kullanıcı istemedi ve iş sayısı 6'dan fazla.
- Yalnız gece koşusu: elendi, kırık `main` 24 saate kadar gizli kalır.
- Self-hosted runner (bu makine): elendi, yükü yine bu makineye geri getirir.
- Kuyruk kapısını hemen `ihlal` yapmak: elendi, ölçümsüz geçiş P-028'e aykırı.
- Yerel şerit olduğu gibi kalsın: elendi, yük yerelde kalır.

**Sonuçlar:**

- Olumlu: yerel CPU yükü ve kira kuyruğu azalır; tam koşu tek ve herkese açık yerde.
- Olumsuz: `main` kırık commit alabilir ve CI sonradan haber verir; CI'daki bilinen kırık testler (I-304) ilk koşuyu kırmızı yapar.
- Geri alma: `orkestra-tam-takim.yml` silinir, kural metni eski haline getirilir; `ORKESTRA_KUYRUK_KAPISI=0` kapıyı kapatır.

**İlgili iş ya da kural kimliği:** I-341, ADR-0142, I-304, P-028, P-041
