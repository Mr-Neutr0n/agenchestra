"""Arşivli oturumun agent süreç ağacını bakımda kapatır (ADR-0174, I-423). Model çağırmaz.

Eşleme anahtarı yalnız sürecin kendi oturumunu belirleyen `--resume=<cliSessionId>` alanıdır; uygulama oturum meta
dosyalarındaki (`claude-code-sessions/**/local_*.json`) `cliSessionId` ile eşleşir ve o oturum `isArchived:true` olmalıdır.
`--add-dir` içindeki `local_` başka oturumun not klasörü olabilir (canlı süreç taşır) ve anahtar DEĞİLDİR.
Uygulamanın kendi süreçleri `--type=` taşır; hedeflenmez. Aynı `cliSessionId`yi arşivsiz bir meta da taşıyorsa süreç hedeflenmez.
Gölge modda (varsayılan, ayarlar/arsiv_surec_kapat.json) yalnız `kapi_golge` kaydı yazılır. ORKESTRA_ARSIV_SUREC_KAPAT=0 kapatır.
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg  # noqa: E402
import ork_lib as L  # noqa: E402

KAPI = "arsiv_surec_kapat"
_RESUME = re.compile(r"--resume[= ]\"?([0-9a-fA-F-]{36})")


def _meta_kokleri() -> list:
    """Uygulama oturum meta dizinleri (Windows: %LOCALAPPDATA%/Claude-Data/*/claude-code-sessions)."""
    yerel = os.environ.get("LOCALAPPDATA")
    if not yerel:
        return []
    return glob.glob(os.path.join(yerel, "Claude-Data", "*", "claude-code-sessions"))


def arsivli_kimlikler(kokler: list | None = None) -> set:
    """Yalnız arşivli oturumlara ait `cliSessionId` kümesi; aynı kimliği arşivsiz bir meta da taşıyorsa çıkarılır."""
    arsivli: set = set()
    canli: set = set()
    for kok in (_meta_kokleri() if kokler is None else kokler):
        for yol in glob.glob(os.path.join(kok, "*", "*", "local_*.json")):
            try:
                with open(yol, encoding="utf-8") as f:
                    d = json.load(f)
            except (OSError, ValueError):
                continue
            kim = d.get("cliSessionId") if isinstance(d, dict) else None
            if not isinstance(kim, str) or not kim:
                continue
            (arsivli if d.get("isArchived") is True else canli).add(kim)
    return arsivli - canli


def eslestir(surecler, arsivli: set) -> list:
    """Süreç sözlüklerinden ({pid, ad, komut}) hedef olanları döndürür; şüphede eşleşmez."""
    sonuc = []
    for s in surecler or []:
        try:
            if str(s.get("ad", "")).lower() != "claude.exe":
                continue
            komut = str(s.get("komut") or "")
            if "--type=" in komut:
                continue
            m = _RESUME.search(komut)
            if m and m.group(1).lower() in {a.lower() for a in arsivli}:
                sonuc.append({"pid": int(s["pid"]), "resume": m.group(1).lower()})
        except (TypeError, ValueError, KeyError):
            continue
    return sonuc


def surec_listesi() -> list:
    """Windows: claude.exe süreçleri (pid, ad, komut, ebeveyn). Diğer sistemlerde ya da hatada boş."""
    if os.name != "nt":
        return []
    komut = ("Get-CimInstance Win32_Process -Filter \"Name='claude.exe'\" | "
             "Select-Object @{n='pid';e={$_.ProcessId}},@{n='ad';e={$_.Name}},@{n='komut';e={$_.CommandLine}} | ConvertTo-Json -Compress")
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", komut], capture_output=True, text=True,
                           encoding="utf-8", timeout=20, **cfg.PENCERESIZ)
        v = json.loads(p.stdout or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    return [v] if isinstance(v, dict) else (v if isinstance(v, list) else [])


def _kendi_ata_zinciri() -> set:
    """Bu sürecin ve atalarının pid'leri: bakımı başlatan oturum asla kapatılmaz."""
    zincir = {os.getpid()}
    if os.name != "nt":
        return zincir
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                            "$i=%d; while($i){$i; $p=(Get-CimInstance Win32_Process -Filter \"ProcessId=$i\").ParentProcessId; if($p -eq $i){break}; $i=$p}" % os.getpid()],
                           capture_output=True, text=True, timeout=20, **cfg.PENCERESIZ)
        zincir |= {int(x) for x in p.stdout.split() if x.isdigit()}
    except (OSError, subprocess.TimeoutExpired):
        pass
    return zincir


def kapat(pid: int) -> bool:
    """Süreç ağacını pencere açmadan sonlandırır."""
    if os.name != "nt":
        return False
    try:
        r = subprocess.run(["taskkill", "/PID", str(int(pid)), "/T", "/F"], capture_output=True, timeout=30, **cfg.PENCERESIZ)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def calistir(sd: str, cwd: str, surecler=None, arsivli: set | None = None, kapatici=None) -> dict:
    """Bakım adımı: eşleşenleri gölge modda kaydeder, ihlal modunda kapatır. Dönen sözlük bakım önbelleğine yazılır."""
    if os.environ.get("ORKESTRA_ARSIV_SUREC_KAPAT") == "0" or not sd:
        return {}
    try:
        import kapi_mod
        mod = kapi_mod.mod(KAPI, cwd or None)
        hedefler = eslestir(surec_listesi() if surecler is None else surecler, arsivli_kimlikler() if arsivli is None else arsivli)
        hedefler = [h for h in hedefler if h["pid"] not in _kendi_ata_zinciri()] if hedefler else []
        kapatildi = 0
        for h in hedefler:
            if mod == "ihlal":
                kapatildi += 1 if (kapatici or kapat)(h["pid"]) else 0
            L.jsonl_ekle(os.path.join(sd, "gunluk.jsonl"), {"zaman": L.simdi(), "tur": "kapi_golge" if mod != "ihlal" else "arsiv_surec_kapatildi",
                                                            "kapi": KAPI, "pid": h["pid"], "resume": h["resume"], "arsivli": True})
        return {"mod": mod, "eslesen": len(hedefler), "kapatilan": kapatildi} if hedefler else {}
    except Exception:  # noqa: BLE001  (bakım adımı hook'u ve diğer adımları düşürmez)
        return {}
