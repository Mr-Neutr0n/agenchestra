"""Çöken oturum kaydı (I-397 P5, ADR-0155): Claude masaüstü uygulamasının `main.log` dosyasındaki
`Session <kimlik> query error: Error: Claude Code process exited with code <N>` satırları hata defterine
(`hata.jsonl`, kaynak `cokus`) girer; `orkestra hata en-cok --kaynak cokus` sayar.

Çöküş uygulama sürecinde olur, oturum içi hook çalışmaz; bu yüzden kaynak uygulamanın kendi günlüğüdür.
Yol: Windows `%LOCALAPPDATA%\\Claude\\logs\\main.log`, `ORKESTRA_UYGULAMA_GUNLUGU` ile değiştirilir. Yalnız son baytlar okunur,
aynı (oturum, zaman) ikinci kez yazılmaz. Dosya yok ya da okunamıyorsa sessiz geçer; model çağrılmaz, sır içermez.
"""
from __future__ import annotations

import os
import re
from datetime import datetime

import ork_lib as L

DOSYA = "hata.jsonl"
KAYNAK = "cokus"
SON_BAYT = 600_000
_SATIR = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[error\] Session (local_[0-9a-f]{8})\S* query error: "
                    r"Error: Claude Code process exited with code (\d+)\s*$", re.MULTILINE)


def gunluk_yolu() -> str | None:
    yol = os.environ.get("ORKESTRA_UYGULAMA_GUNLUGU")
    if yol:
        return yol
    yerel = os.environ.get("LOCALAPPDATA")
    return os.path.join(yerel, "Claude", "logs", "main.log") if yerel else None


def _zaman(metin: str) -> str:
    return datetime.strptime(metin, "%Y-%m-%d %H:%M:%S").astimezone().isoformat(timespec="seconds")


def ayristir(metin: str) -> list:
    """Log metninden çıkış olayları: [{zaman, oturum (local_ + 8 hane), kod}]."""
    return [{"zaman": _zaman(m.group(1)), "oturum": m.group(2), "kod": int(m.group(3))} for m in _SATIR.finditer(metin)]


def imza(kod: int) -> str:
    return f"cokus: Claude Code işlemi beklenmedik çıkış (kod {kod} = 0x{kod:08X})"


def _oku(yol: str, son_bayt: int) -> str:
    with open(yol, "rb") as f:
        f.seek(0, os.SEEK_END)
        boy = f.tell()
        f.seek(max(0, boy - son_bayt))
        return f.read().decode("utf-8", errors="replace")


def tara(sd: str, yol: str | None = None, son_bayt: int = SON_BAYT) -> int:
    """Yeni çıkış olaylarını hata.jsonl'e yazar; yazılan satır sayısını döner. Hatada ve dosya yoksa 0."""
    try:
        yol = yol or gunluk_yolu()
        if not yol or not os.path.isfile(yol):
            return 0
        olaylar = ayristir(_oku(yol, son_bayt))
        defter = os.path.join(sd, DOSYA)
        var = {(r.get("oturum"), r.get("zaman")) for r in L.jsonl_oku(defter)
               if isinstance(r, dict) and r.get("kaynak") == KAYNAK}
        yazilan = 0
        for o in olaylar:
            if (o["oturum"], o["zaman"]) in var:
                continue
            L.jsonl_ekle(defter, {"v": 1, "kaynak": KAYNAK, "imza": imza(o["kod"]), "zaman": o["zaman"],
                                  "oturum": o["oturum"], "kod": o["kod"],
                                  "ileti": f"{o['oturum']} oturumu {o['kod']} koduyla düştü"})
            yazilan += 1
        return yazilan
    except Exception:
        return 0
