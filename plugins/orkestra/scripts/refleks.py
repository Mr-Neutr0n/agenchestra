"""Refleks katmanı (ADR-0149): '/ok <komut>' istemini model turu açmadan, kayıtlı salt-okur komutla yanıtlar.

Kayıt `ayarlar/refleks.json`dır; komut kabuksuz, argüman listesiyle koşar. Hata, zaman aşımı ya da eşleşmeme `None` döner;
çağıran (refleks_hook.py) bu durumda istemi model yoluna bırakır. Bu modül `hook.py`yi içe aktarmaz; `ork_lib` yalnız çıktı
maskelemek için, eşleşmeden sonra tembel yüklenir.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AYAR = os.path.join(KOK, "ayarlar", "refleks.json")
CLI = os.path.join(KOK, "scripts", "orkestra.py")
IZINLI_YURUTULEBILIR = ("orkestra",)
ZAMAN_ASIMI_TAVAN = 8
CIKTI_TAVAN = 4000
_AD = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")
_ARG = re.compile(r"^(--)?[A-Za-z0-9_][A-Za-z0-9_.:=/-]*$")


def dogrula(kayit) -> list[str]:
    """Kayıt şema denetimi; boş liste = geçerli. S4: salt_okur olmayan, izinsiz yürütülebilir, kabuk metakarakterli kayıt reddedilir."""
    if not isinstance(kayit, dict):
        return ["kayıt sözlük değil"]
    hata = []
    ad = kayit.get("ad")
    if not isinstance(ad, str) or not _AD.match(ad):
        hata.append("ad geçersiz")
    takma = kayit.get("takma", [])
    if not isinstance(takma, list) or any(not isinstance(t, str) or not _AD.match(t) for t in takma):
        hata.append("takma geçersiz")
    if kayit.get("salt_okur") is not True:
        hata.append("salt_okur true değil")
    arg = kayit.get("arguman")
    if not isinstance(arg, list) or not arg or any(not isinstance(a, str) for a in arg):
        hata.append("arguman liste değil")
    else:
        if arg[0] not in IZINLI_YURUTULEBILIR:
            hata.append("yürütülebilir izin listesinde değil")
        for a in arg[1:]:
            if not _ARG.match(a):
                hata.append("argüman kabuk metakarakteri ya da yer tutucu içeriyor: " + a[:20])
    za = kayit.get("zaman_asimi", ZAMAN_ASIMI_TAVAN)
    if not isinstance(za, (int, float)) or isinstance(za, bool) or not 0 < za <= ZAMAN_ASIMI_TAVAN:
        hata.append("zaman_asimi 0-%d dışında" % ZAMAN_ASIMI_TAVAN)
    cs = kayit.get("cikti_siniri", CIKTI_TAVAN)
    if not isinstance(cs, int) or isinstance(cs, bool) or not 0 < cs <= CIKTI_TAVAN:
        hata.append("cikti_siniri 0-%d dışında" % CIKTI_TAVAN)
    return hata


def _oku(yol: str):
    try:
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def yukle(sd: str | None = None, ayar: str | None = None) -> tuple[str, str, list[dict]]:
    """(mod, on_ek, geçerli kayıtlar). Proje ezmesi (sd/refleks.json) yalnız kapatabilir. Bozuk dosya = kapalı."""
    d = _oku(ayar or AYAR)
    if d is None:
        return "kapali", "/ok", []
    mod = d.get("mod") if d.get("mod") in ("acik", "kapali") else "kapali"
    on_ek = d.get("on_ek") if isinstance(d.get("on_ek"), str) and re.fullmatch(r"/[a-z]{1,10}", d.get("on_ek")) else "/ok"
    kayitlar = [k for k in (d.get("komutlar") or []) if not dogrula(k)]
    if sd:
        e = _oku(os.path.join(sd, "refleks.json")) or {}
        if e.get("mod") == "kapali":
            mod = "kapali"
        kapat = e.get("kapat")
        if isinstance(kapat, list):
            kayitlar = [k for k in kayitlar if k["ad"] not in kapat]
    return mod, on_ek, kayitlar


def esles(istem: str, on_ek: str, kayitlar: list[dict]) -> dict | None:
    """Tam eşleşme: '<on_ek> <ad|takma>' (büyük/küçük harf ve baştaki/sondaki boşluk önemsiz). Başka her şey None."""
    parcalar = (istem or "").strip().lower().split()
    if len(parcalar) != 2 or parcalar[0] != on_ek:
        return None
    for k in kayitlar:
        if parcalar[1] == k["ad"] or parcalar[1] in k.get("takma", []):
            return k
    return None


def calistir(kayit: dict, cwd: str | None = None) -> str | None:
    """Komutu kabuksuz koşar; hata, sıfırdan farklı çıkış ya da zaman aşımında None. Çıktı maskelenir ve kırpılır."""
    if dogrula(kayit):
        return None
    argv = [sys.executable, CLI] + kayit["arguman"][1:]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run(argv, cwd=cwd or None, env=env, capture_output=True, stdin=subprocess.DEVNULL, shell=False,
                           timeout=min(kayit.get("zaman_asimi", ZAMAN_ASIMI_TAVAN), ZAMAN_ASIMI_TAVAN))
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    metin = (p.stdout or b"").decode("utf-8", "replace").strip()
    if not metin:
        return None
    try:
        sys.path.insert(0, os.path.join(KOK, "scripts"))
        import ork_lib
        metin = ork_lib.maskele(metin)
    except Exception:  # noqa: BLE001 — maskelenemeyen çıktı gösterilmez
        return None
    sinir = min(kayit.get("cikti_siniri", CIKTI_TAVAN), CIKTI_TAVAN)
    return metin if len(metin) <= sinir else metin[:sinir] + "\n… (kırpıldı)"


def _iz_yaz(sd: str | None, ad: str, ms: int) -> None:
    klasor = sd if sd and os.path.isdir(sd) else os.path.join(os.path.expanduser("~"), ".orkestra")
    try:
        os.makedirs(klasor, exist_ok=True)
        with open(os.path.join(klasor, "refleks.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"komut": ad, "ms": ms, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def denetle(istem: str, cwd: str | None = None) -> dict | None:
    """Hook girdisi: eşleşirse {"decision": "block", "reason": çıktı}, aksi halde None (istem model yoluna düşer)."""
    if os.environ.get("ORKESTRA_REFLEKS") == "0":
        return None
    sd = os.path.join(cwd, ".claude", "orkestra") if cwd else None
    mod, on_ek, kayitlar = yukle(sd)
    if mod != "acik":
        return None
    kayit = esles(istem, on_ek, kayitlar)
    if kayit is None:
        return None
    t0 = time.perf_counter()
    cikti = calistir(kayit, cwd)
    if cikti is None:
        return None
    _iz_yaz(sd, kayit["ad"], int((time.perf_counter() - t0) * 1000))
    return {"decision": "block", "reason": cikti}
