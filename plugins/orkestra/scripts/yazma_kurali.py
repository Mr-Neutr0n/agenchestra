"""I-421: büyük belge yazma niyetinde üretimden ÖNCE yazma kuralı bağlamı.
Kapı retleri (bağsız oturum, worktree dışı yol) üretilmiş metnin yeniden üretilmesine yol açar; kural üretimden önce
bilinirse ret oluşmaz ya da bir bölüme mal olur. Yalnız yazma niyeti taşıyan mesajda eklenir (bağlam şişmesin).
ORKESTRA_YAZMA_KURALI=0 kapatır."""
import os
import re

import ork_lib as L

_NIYET = re.compile(
    r"\b(rapor|belge|doküman|dokuman|analiz|özet|ozet|döküm|dokum|kılavuz|kilavuz|plan|yaz|hazırla|hazirla|"
    r"markdown|\.md|inceleme|karşılaştırma|karsilastirma)", re.I)

ISKELET = ("Yazma kuralı: ~8 KB'ı aşacak belgeyi tek Write ile üretme; önce başlık iskeletini yaz, sonra bölüm bölüm "
           "Edit ile doldur (kapı reddi en çok bir bölüme mal olur).")


def _bagli_agac_koku(cwd):
    try:
        kok = L.git_koku(cwd)
        if not kok:
            return None
        gd = L.git(["rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"], kok).stdout.split("\n")
        if len(gd) < 2 or os.path.normcase(gd[0].strip()) == os.path.normcase(gd[1].strip()):
            return None
        return kok
    except Exception:
        return None


def ana_ajan_metni(metin: str, cwd=None) -> str:
    """Yazma niyeti varsa iskelet kuralı (+ bağlı worktree oturumunda yazma kökü); yoksa ''. Hatada ''."""
    if os.environ.get("ORKESTRA_YAZMA_KURALI") == "0":
        return ""
    try:
        if not isinstance(metin, str) or not _NIYET.search(metin):
            return ""
        s = ISKELET
        kok = _bagli_agac_koku(cwd) if cwd else None
        if kok:
            s += f" Bu oturum bağlı worktree'de; dosyalar yalnız {kok.replace(os.sep, '/')} altına yazılır, dışı reddedilir."
        return s
    except Exception:
        return ""
