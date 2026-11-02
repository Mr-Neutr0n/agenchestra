"""Yetim süreç temizliği (ADR-0148): ebeveyni ölmüş ve eşikten eski git / eklenti betiği süreçlerini ağacıyla öldürür.

Kanıt (01.11.2026): 105 takılı git.exe (ort. 7,4 sa), 23 sa önce başlamış oturum_bakim.py, 20 sa önce başlamış
mcp_kimlik.py yetimi; hepsi ebeveynsiz, CPU'suz. Yalnız standart kütüphane. Ebeveyn ölü sayılır: PID yok ya da ebeveyn
kaydı çocuktan SONRA doğmuş (PID yeniden kullanımı). Panel ve MCP sunucuları ebeveynliyken dokunulmaz.
Komut: `python surec_temizle.py [--uygula|--golge] [--sd DURUM_KLASORU]` (varsayılan: ayar modu).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg  # noqa: E402

AYAR_YOLU = os.path.join(_KOK, "ayarlar", "surec_temizle.json")
_VARSAYILAN = {"mod": "uygula", "git_esik_sn": 3600, "python_esik_sn": 7200,
               "python_betikler": ["mcp_kimlik.py", "oturum_bakim.py", "test_paralel.py"]}
_PS = ("Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{pid=[int]$_.ProcessId;ppid=[int]$_.ParentProcessId;"
       "ad=$_.Name;t=([DateTimeOffset]$_.CreationDate).ToUnixTimeSeconds();cmd=$_.CommandLine} } | ConvertTo-Json -Compress")


def etkin() -> bool:
    return (os.environ.get("ORKESTRA_SUREC_TEMIZLE") or "").strip() != "0"


def ayar_oku() -> dict:
    ayar = dict(_VARSAYILAN)
    try:
        with open(AYAR_YOLU, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            ayar.update(d)
    except Exception:  # noqa: BLE001
        pass
    return ayar


def listele() -> list[dict]:
    """[{pid, ppid, ad, t (başlangıç epoch), cmd}]; alınamazsa []."""
    try:
        if os.name == "nt":
            r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=60, **cfg.PENCERESIZ)
            v = json.loads(r.stdout or "[]")
            return [x for x in (v if isinstance(v, list) else [v]) if isinstance(x, dict)]
        r = subprocess.run(["ps", "-eo", "pid=,ppid=,etimes=,comm=,args="], capture_output=True, text=True, timeout=30, **cfg.PENCERESIZ,
                           stdin=subprocess.DEVNULL)
        simdi, cikti = time.time(), []
        for satir in r.stdout.splitlines():
            a = satir.split(None, 4)
            if len(a) >= 4:
                cikti.append({"pid": int(a[0]), "ppid": int(a[1]), "ad": a[3], "t": simdi - int(a[2]),
                              "cmd": a[4] if len(a) > 4 else ""})
        return cikti
    except Exception:  # noqa: BLE001
        return []


def _betik(cmd: str) -> str:
    """Komut satırındaki *.py betik adı (küçük harf); yoksa ''."""
    for parca in (cmd or "").replace("\\", "/").replace('"', " ").split():
        if parca.lower().endswith(".py"):
            return parca.rsplit("/", 1)[-1].lower()
    return ""


def adaylar(sureclar: list[dict], simdi: float, ayar: dict, kendi: int | None = None) -> list[dict]:
    """Yetim + eşikten eski + izin listesinde olan süreçler. Saf işlev (test edilebilir)."""
    kendi = os.getpid() if kendi is None else kendi
    kimlik = {s["pid"]: s for s in sureclar}
    izinli = {b.lower() for b in ayar.get("python_betikler", [])}
    sonuc = []
    for s in sureclar:
        ad = (s.get("ad") or "").lower().removesuffix(".exe")
        if s["pid"] == kendi or ad not in ("git", "python", "pythonw", "python3"):
            continue
        yas = simdi - float(s.get("t") or simdi)
        ata = kimlik.get(s["ppid"])
        if ata is not None and float(ata.get("t") or 0) <= float(s.get("t") or 0):
            continue  # ebeveyn canlı
        if ad == "git":
            if yas >= ayar["git_esik_sn"]:
                sonuc.append({**s, "yas": int(yas), "neden": "yetim git"})
        elif yas >= ayar["python_esik_sn"] and _betik(s.get("cmd", "")) in izinli:
            sonuc.append({**s, "yas": int(yas), "neden": "yetim eklenti betiği"})
    return sonuc


def oldur(pid: int) -> bool:
    """Süreci ağacıyla öldürür; başarıyı döner."""
    try:
        if os.name == "nt":
            r = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, stdin=subprocess.DEVNULL,
                               timeout=30, **cfg.PENCERESIZ)
            return r.returncode == 0
        os.kill(pid, 9)
        return True
    except Exception:  # noqa: BLE001
        return False


def temizle(sd: str | None = None, mod: str | None = None) -> dict | None:
    """Adayları bulur; modda 'uygula' ise öldürür. Özet sözlüğü döner (bakım önbelleğine yazılır)."""
    if not etkin():
        return None
    ayar = ayar_oku()
    mod = mod or ayar["mod"]
    ad = adaylar(listele(), time.time(), ayar)
    oldurulen = [a for a in ad if mod == "uygula" and oldur(a["pid"])]
    if sd and ad:
        try:
            import ork_lib as L
            for a in ad:
                L.jsonl_ekle(os.path.join(sd, "surec_temizle.jsonl"),
                             {"zaman": L.simdi(), "mod": mod, "pid": a["pid"], "ad": a["ad"], "yas_sn": a["yas"],
                              "neden": a["neden"], "oldu": a in oldurulen, "cmd": (a.get("cmd") or "")[:160]})
        except Exception:  # noqa: BLE001
            pass
    return {"mod": mod, "aday": len(ad), "oldurulen": len(oldurulen)} if ad else None


if __name__ == "__main__":
    m = "uygula" if "--uygula" in sys.argv else "golge" if "--golge" in sys.argv else None
    sd = sys.argv[sys.argv.index("--sd") + 1] if "--sd" in sys.argv and sys.argv.index("--sd") + 1 < len(sys.argv) else None
    print(json.dumps(temizle(sd, m) or {"aday": 0}, ensure_ascii=False))
