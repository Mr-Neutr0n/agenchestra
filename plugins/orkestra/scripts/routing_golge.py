#!/usr/bin/env python3
"""Yönlendirme v2 gölge kaydı (I-419): kart açılırken v2 kararı hesaplanır, v1 atamasıyla karşılaştırılır, gunluk.jsonl'a
`kapi_golge` (kapı routing_v2) olarak yazılır. Kartı asla reddetmez ve değiştirmez; yalnız `routing_v2.durum == golge` iken çalışır.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_politika as MP  # noqa: E402
import ork_lib as L  # noqa: E402
import routing_policy as RP  # noqa: E402

KAPI = "routing_v2"
BASAMAK_PROFIL = {"T0": "mechanical", "T1": "scoped", "T2": "standard", "T3": "architecture", "T4": "frontier"}
RISK = {"dusuk": 1, "orta": 2, "yuksek": 3}
ALT_TUR_DOSYASI = os.path.join(L.PLUGIN_ROOT, "ayarlar", "gorev_alt_turleri.json")


def alt_tur(kimlik: str | None) -> dict | None:
    if not kimlik:
        return None
    try:
        with open(ALT_TUR_DOSYASI, encoding="utf-8") as f:
            return next((t for t in json.load(f)["alt_turler"] if t["id"] == kimlik), None)
    except (OSError, ValueError, KeyError):
        return None


def karsilastir(kart: dict, sd: str | None = None) -> dict | None:
    """Gölge kapalıysa None; açıksa {v1, v2, ayni, alt_tur} (saf, yazmaz)."""
    st = MP.v2_durum(sd)
    if st["durum"] != "golge":
        return None
    cfg = MP.yukle(sd)
    t = alt_tur(kart.get("alt_tur"))
    risk = RISK.get(str(kart.get("risk") or "").lower())
    if t and isinstance(t.get("risk_floor"), int):
        risk = max(risk or 0, t["risk_floor"])
    karmasiklik = BASAMAK_PROFIL.get(str(kart.get("basamak") or "").upper())
    v2 = RP.karar({"karmasiklik": karmasiklik, "risk": risk}, cfg["routing_v2"])
    b = (cfg.get("basamak") or {}).get(str(kart.get("basamak") or "").upper()) or {}
    v1 = {"model": b.get("model"), "effort": b.get("effort")}
    ayni = (v1["model"], v1["effort"]) == (v2["model"], v2["effort"])
    return {"v1": v1, "v2": {k: v2[k] for k in ("profil", "model", "effort", "risk")}, "ayni": ayni, "alt_tur": (t or {}).get("id")}


def kaydet(sd: str, kart: dict) -> None:
    """Kart açılışında çağrılır; hata kartı bozmaz."""
    try:
        s = karsilastir(kart, sd)
        if s is None:
            return
        L.jsonl_ekle(os.path.join(sd, "gunluk.jsonl"), {
            "zaman": L.simdi(), "tur": "kapi_golge", "kapi": KAPI, "is": kart.get("is") or "-",
            "neden": f"v1 {s['v1']['model']}/{s['v1']['effort']} v2 {s['v2']['model']}/{s['v2']['effort']} ({s['v2']['profil']}, risk {s['v2']['risk']}) ayni={s['ayni']}"[:300]})
    except Exception:  # noqa: BLE001 — gölge kayıt kartı asla düşürmez
        return
