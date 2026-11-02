"""Bash sözdizimi kapısı (ADR-0151): ajanın Bash aracına verdiği komut koşmadan `bash -n` ile ayrıştırılır; kabuğun kendisi
"unexpected EOF" / "syntax error" verecekse komut durdurulur ve betiği dosyaya yazma yolu söylenir. Model çağrılmaz.

İki denetim:
1. Uzunluk: araç komutu tek tırnak kaçışıyla komut satırına koyar; kaçışlı uzunluk ayardaki sınırı aşarsa komut kesilir ve
   kabuk "unexpected EOF" verir. `bash -n` bunu göremez (ham komut geçerlidir), bu yüzden ayrı ve ucuz bir sayımdır.
2. Ayrıştırma: gerçek bash (`bash -n`, komut koşmaz) ile; regex tırnak sayımı yapılmaz.

Geçer (ret yok): bash bulunamazsa, zaman aşımında, boş komutta, ayrıştırıcı başka bir sınıf hata verirse, tetik karakteri
yoksa. CRLF denetimden önce LF'ye çevrilir. Kip, kalıplar ve metinler kodda durmaz: `ayarlar/bash_sozdizimi.json` ve proje
durum dizinindeki `bash_sozdizimi.json` (anahtar bazında ezer). `ORKESTRA_BASH_SOZDIZIMI=0` kapıyı kapatır.
Kip: `golge` (kayıt + bağlam), `ihlal`/`reddet` (ret), `kapali`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARSAYILAN_YOL = os.path.join(_KOK, "ayarlar", "bash_sozdizimi.json")
PROJE_DOSYA = "bash_sozdizimi.json"
MODLAR = ("golge", "ihlal", "reddet", "kapali")
RET_MODLARI = ("ihlal", "reddet")
_BASH_ONBELLEK: dict = {}


def _json_oku(yol: str):
    try:
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def ayar_oku(sd=None) -> dict:
    ayar = _json_oku(VARSAYILAN_YOL) or {}
    if sd:
        proje = _json_oku(os.path.join(sd, PROJE_DOSYA))
        if proje:
            ayar.update(proje)
    return ayar


def mod(ayar: dict) -> str:
    if os.environ.get("ORKESTRA_BASH_SOZDIZIMI") == "0":
        return "kapali"
    m = ayar.get("mod", "kapali")
    return m if m in MODLAR else "kapali"


def _haric(yol: str, ayar: dict) -> bool:
    for k in ayar.get("haric_yol_kaliplari") or []:
        try:
            if re.search(k, yol):
                return True
        except re.error:
            continue
    return False


def bash_yolu(ayar: dict):
    """Ayardaki adaylar (ortam değişkenleri açılır), sonra PATH; hariç kalıba (WSL başlatıcısı gibi) uyan yol atlanır.
    Bulunamazsa None (kapı geçer)."""
    anahtar = json.dumps([ayar.get("bash_yollari"), ayar.get("haric_yol_kaliplari")], sort_keys=True)
    if anahtar in _BASH_ONBELLEK:
        return _BASH_ONBELLEK[anahtar]
    bulunan = None
    for aday in ayar.get("bash_yollari") or []:
        yol = os.path.expandvars(str(aday))
        if "%" not in yol and os.path.isfile(yol) and not _haric(yol, ayar):
            bulunan = yol
            break
    if not bulunan:
        yol = shutil.which("bash")
        if yol and not _haric(yol, ayar):
            bulunan = yol
    _BASH_ONBELLEK[anahtar] = bulunan
    return bulunan


def _normal(komut: str) -> str:
    return komut.replace("\r\n", "\n").replace("\r", "\n")


def uzunluk_bulgusu(komut: str, ayar: dict):
    """Kaçışlı uzunluk sınırı aşılıyorsa bulgu sözlüğü, değilse None."""
    try:
        sinir = int(ayar.get("uzunluk_en_cok") or 0)
        ek = int(ayar.get("uzunluk_tek_tirnak_eki") or 0)
    except (TypeError, ValueError):
        return None
    if sinir <= 0:
        return None
    kacisli = len(komut) + ek * komut.count("'")
    if kacisli > sinir:
        sablon = str(ayar.get("uzunluk_neden") or "{kacisli} > {sinir}")
        return {"sinif": "uzunluk", "neden": sablon.replace("{kacisli}", str(kacisli)).replace("{sinir}", str(sinir))}
    return None


def ayristir(komut: str, ayar: dict):
    """`bash -n` ile ayrıştırır; ret sınıfında hata varsa bulgu sözlüğü, aksi halde (geçerli, bash yok, zaman aşımı,
    başka sınıf hata) None."""
    if len(komut) > int(ayar.get("en_cok_karakter") or 200000):
        return None
    tetik = ayar.get("tetik_kalibi")
    if tetik:
        try:
            if not re.search(tetik, komut):
                return None
        except re.error:
            pass
    bash = bash_yolu(ayar)
    if not bash:
        return None
    secenek = [str(s) for s in (ayar.get("bash_secenekleri") or ["-n"])]
    if "-n" not in secenek:  # güvenlik: ayar ne derse desin komut asla koşmaz
        secenek.append("-n")
    ek = {}
    if os.name == "nt":
        ek["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        r = subprocess.run([bash, *secenek], input=komut.encode("utf-8"), capture_output=True,
                           timeout=float(ayar.get("zaman_asimi_sn") or 2), **ek)
    except Exception:  # zaman aşımı, başlatılamayan bash: geçer
        return None
    if r.returncode == 0:
        return None
    hata = r.stderr.decode("utf-8", errors="replace")
    for k in ayar.get("ret_kaliplari") or []:
        if k and k in hata:
            ilk = next((s.strip() for s in hata.splitlines() if k in s), hata.strip())
            ilk = re.sub(r"^.*?bash(?:\.exe)?:\s*", "", ilk)
            return {"sinif": "sozdizimi", "neden": f"bash -n: {ilk[:200]}"}
    return None


def denetle(komut, sd=None, ayar=None):
    """Komut koşunca kabuk hatası verecekse bulgu ({sinif, neden}), değilse None. Kip kapalıysa None."""
    ayar = ayar if ayar is not None else ayar_oku(sd)
    if mod(ayar) == "kapali" or not isinstance(komut, str) or not komut.strip():
        return None
    komut = _normal(komut)
    return uzunluk_bulgusu(komut, ayar) or ayristir(komut, ayar)


def yonerge_yolu(ayar: dict) -> str:
    y = str(ayar.get("yonerge") or "")
    return os.path.join(_KOK, y) if y and not os.path.isabs(y) else y


def _bicim(sablon, bulgu: dict, ayar: dict, **ek) -> str:
    metin = str(sablon or "")
    for k, v in {"neden": bulgu.get("neden", ""), "yonerge": yonerge_yolu(ayar), **ek}.items():
        metin = metin.replace("{" + k + "}", str(v))
    return metin


def ret_metni(bulgu: dict, ayar: dict) -> str:
    return _bicim(ayar.get("ret_metni"), bulgu or {}, ayar)


def golge_metni(bulgu: dict, ayar: dict) -> str:
    return _bicim(ayar.get("golge_metni"), bulgu or {}, ayar)


def uzun_betik_metni(komut, sd=None, ayar=None) -> str:
    """Satır eşiğini aşan ve `python -c`, `bash -c` ya da heredoc taşıyan komut için yönerge bağlamı; yoksa ''.
    Kip kapalıysa ''."""
    ayar = ayar if ayar is not None else ayar_oku(sd)
    if mod(ayar) == "kapali" or not isinstance(komut, str):
        return ""
    komut = _normal(komut)
    satir = komut.count("\n") + 1
    try:
        esik = int(ayar.get("satir_esigi") or 0)
    except (TypeError, ValueError):
        return ""
    if esik <= 0 or satir <= esik:
        return ""
    for k in ayar.get("uzun_betik_kaliplari") or []:
        try:
            if re.search(k, komut):
                return _bicim(ayar.get("uzun_betik_metni"), {}, ayar, satir=satir)
        except re.error:
            continue
    return ""
