"""Açılışta bellek uyarısı (I-397, ADR-0155, P-028): oturum açılırken boş RAM ve commit kullanımı ölçülür.

Eşiklerin altında tek satır uyarı bağlama eklenir ve `kapi_golge / bellek_kapisi` günlüğe yazılır; her açılışta ayrıca
`bellek_olcum` düşer (eşik bu verinin yüzdeliğinden türetilir: `esik_oner`). Gölge modda hiçbir şeyi engellemez.
Ayar: `ayarlar/bellek_kapisi.json` (eklenti varsayılanı) ve proje durum dizinindeki `bellek_kapisi.json` (anahtar bazında ezer).
`ORKESTRA_BELLEK_KAPISI=0` kapatır. Model çağrılmaz; hatada sessiz geçer, oturumu engellemez.
"""
from __future__ import annotations

import json
import os

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARSAYILAN_YOL = os.path.join(_KOK, "ayarlar", "bellek_kapisi.json")
PROJE_DOSYA = "bellek_kapisi.json"
KAPI = "bellek_kapisi"


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


def acik(ayar: dict) -> bool:
    return os.environ.get("ORKESTRA_BELLEK_KAPISI") != "0" and ayar.get("mod", "kapali") != "kapali"


def olc() -> dict | None:
    """{'bos_ram_gb', 'commit_yuzde'}; platform desteklenmiyorsa ya da okunamazsa None."""
    try:
        if os.name == "nt":
            import ctypes

            class _Durum(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            d = _Durum()
            d.dwLength = ctypes.sizeof(_Durum)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(d)) or not d.ullTotalPageFile:
                return None
            return {"bos_ram_gb": round(d.ullAvailPhys / 2 ** 30, 2),
                    "commit_yuzde": round((d.ullTotalPageFile - d.ullAvailPageFile) * 100 / d.ullTotalPageFile, 1)}
        with open("/proc/meminfo", encoding="utf-8") as f:
            m = {s.split(":")[0]: int(s.split()[1]) for s in f if ":" in s}
        toplam, bos = m.get("CommitLimit"), m.get("Committed_AS")
        if not toplam or bos is None or "MemAvailable" not in m:
            return None
        return {"bos_ram_gb": round(m["MemAvailable"] / 2 ** 20, 2), "commit_yuzde": round(bos * 100 / toplam, 1)}
    except Exception:
        return None


def _tr(x: float, basamak: int = 1) -> str:
    return f"{x:.{basamak}f}".replace(".", ",")


def degerlendir(olcum, ayar: dict) -> str | None:
    """Eşik aşımında tek satır uyarı; ölçüm yoksa ya da eşikler aşılmadıysa None."""
    if not olcum:
        return None
    nedenler = []
    if olcum["bos_ram_gb"] < float(ayar.get("bos_ram_gb_esik", 1.0)):
        nedenler.append(f"boş RAM {_tr(olcum['bos_ram_gb'])} GB (eşik {_tr(float(ayar.get('bos_ram_gb_esik', 1.0)))})")
    if olcum["commit_yuzde"] > float(ayar.get("commit_yuzde_esik", 90)):
        nedenler.append(f"commit %{_tr(olcum['commit_yuzde'], 0)} (eşik %{_tr(float(ayar.get('commit_yuzde_esik', 90)), 0)})")
    if not nedenler:
        return None
    return ("Bellek dar: " + "; ".join(nedenler) + ". Kullanılmayan oturumları kapat; MCP yükü için `orkestra mcp olc`.")


def esik_oner(degerler: list, yuzdelik: float):
    """Gölge ölçümlerinin (boş RAM GB) alt yüzdeliği; veri yoksa None. Eşik bu değerden elle güncellenir."""
    if not degerler:
        return None
    x = sorted(degerler)
    return float(x[int(yuzdelik / 100 * (len(x) - 1))])


def oturum_basi(sd, oid, olcum=None, ayar=None) -> str:
    """Açılış ölçümünü günlüğe yazar; eşik aşılmışsa uyarı satırını döner (gölge: ayrıca kapi_golge), yoksa ''."""
    try:
        ayar = ayar if ayar is not None else ayar_oku(sd)
        if not acik(ayar):
            return ""
        olcum = olcum if olcum is not None else olc()
        if not olcum:
            return ""
        import ork_lib as L
        yol = os.path.join(sd, "gunluk.jsonl")
        L.jsonl_ekle(yol, {"zaman": L.simdi(), "oturum": oid, "tur": "bellek_olcum", **olcum})
        uyari = degerlendir(olcum, ayar)
        if uyari:
            L.jsonl_ekle(yol, {"zaman": L.simdi(), "oturum": oid, "tur": "kapi_golge", "kapi": KAPI, "neden": uyari[:300]})
        return uyari or ""
    except Exception:
        return ""
