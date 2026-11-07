#!/usr/bin/env python3
"""Orkestra yönlendirme kararı v2 (Faz 05-06-08, I-419): özellik -> profil, model, effort, risk, denetçi, gerekçe kodları.

Saf fonksiyon: dosya okumaz, yan etkisi yoktur. Politika `model_politikasi.json` `routing_v2` bloğudur. Bilinmeyen girdi
fail-closed: karmaşıklık 'standard', risk 3 (en yüksek). Kapalı bayrakta çağıran v1 basamak tablosuna düşer.
"""
from __future__ import annotations

import hashlib
import json

PROFIL_SIRA = ("mechanical", "scoped", "standard", "complex", "architecture", "frontier")


def politika_ozeti(blok: dict) -> dict:
    ham = json.dumps({"p": blok.get("route_profiles"), "d": blok.get("routing_defaults")}, sort_keys=True, ensure_ascii=False)
    return {"policy_hash": hashlib.sha256(ham.encode("utf-8")).hexdigest()[:12]}


def _siradaki(profiller: dict) -> list:
    return [p for p in PROFIL_SIRA if p in profiller] + [p for p in profiller if p not in PROFIL_SIRA]


def karar(ozellik: dict, blok: dict) -> dict:
    """ozellik: {karmasiklik, risk, dogrulanabilirlik}. Dönüş: karar sözlüğü; 'reason_codes' her seçimi açıklar."""
    profiller = blok["route_profiles"]
    vars_ = blok.get("routing_defaults") or {}
    kodlar: list[str] = []
    sira = _siradaki(profiller)

    k = (ozellik or {}).get("karmasiklik")
    if k not in profiller:
        k = vars_.get("unknown_complexity", "standard")
        kodlar.append("karmasiklik-bilinmiyor")
    r = (ozellik or {}).get("risk")
    if not isinstance(r, int) or isinstance(r, bool) or not 0 <= r <= 3:
        r = 3
        kodlar.append("risk-bilinmiyor-en-yuksek")
    if (ozellik or {}).get("dogrulanabilirlik") not in ("full", "partial", "none"):
        kodlar.append("dogrulanabilirlik-bilinmiyor-partial")

    profil = k
    while profiller[profil]["risk_ceiling"] < r:
        i = sira.index(profil)
        if i + 1 >= len(sira):
            kodlar.append("risk-tavani-asildi-en-ust-profil")
            break
        profil = sira[i + 1]
        kodlar.append(f"risk-tavani-yukseltti:{profil}")

    p = profiller[profil]
    denetci_model = "opus" if r >= 3 else "sonnet"
    return {
        "profil": profil, "model": p["model"], "effort": p["effort"], "risk": r,
        "denetci_zorunlu": True, "denetci_model": denetci_model,
        "reason_codes": kodlar or ["varsayilan-eslesme"],
        **politika_ozeti(blok),
    }
