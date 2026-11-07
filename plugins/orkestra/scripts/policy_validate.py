#!/usr/bin/env python3
"""Orkestra yönlendirme politikası v2 doğrulayıcı (Faz 04, I-419).

`ayarlar/model_politikasi.json` içindeki `routing_v2` bloğunu denetler. Saf fonksiyon: dosya okumaz, yan etkisi yoktur.
Geçersiz blok fail-closed: `gecerli` False döner ve çağıran v1 basamak tablosuna düşer.
"""
from __future__ import annotations

GECERLI_EFFORT = ("low", "medium", "high", "xhigh", "max")
GECERLI_DURUM = ("kapali", "golge", "acik")
RISK_ARALIK = (0, 3)
PROFIL_ALANLARI = ("model", "effort", "risk_ceiling", "verify_required")


def dogrula(cfg: dict, yasak_mi=None) -> dict:
    """{'gecerli': bool, 'hatalar': [kod: ayrıntı], 'surum': int|None}. Blok yoksa gecerli False, hata 'blok-yok'."""
    hatalar: list[str] = []
    if not isinstance(cfg, dict):
        return {"gecerli": False, "hatalar": ["cfg-sozluk-degil"], "surum": None}
    blok = cfg.get("routing_v2")
    if not isinstance(blok, dict):
        return {"gecerli": False, "hatalar": ["blok-yok"], "surum": None}

    durum = blok.get("durum")
    if durum not in GECERLI_DURUM:
        hatalar.append(f"durum-gecersiz: {durum!r}")

    profiller = blok.get("route_profiles")
    if not isinstance(profiller, dict) or not profiller:
        hatalar.append("route_profiles-bos")
        profiller = {}
    for ad, p in profiller.items():
        if not isinstance(p, dict):
            hatalar.append(f"profil-sozluk-degil: {ad}")
            continue
        for alan in PROFIL_ALANLARI:
            if alan not in p:
                hatalar.append(f"profil-alan-eksik: {ad}.{alan}")
        if p.get("effort") not in GECERLI_EFFORT:
            hatalar.append(f"effort-gecersiz: {ad}={p.get('effort')!r}")
        r = p.get("risk_ceiling")
        if not isinstance(r, int) or isinstance(r, bool) or not (RISK_ARALIK[0] <= r <= RISK_ARALIK[1]):
            hatalar.append(f"risk_ceiling-gecersiz: {ad}={r!r}")
        m = p.get("model")
        if not isinstance(m, str) or not m.strip():
            hatalar.append(f"model-bos: {ad}")
        elif yasak_mi is not None and yasak_mi(m):
            hatalar.append(f"model-yasak: {ad}={m}")
        if p.get("verify_required") is not True:
            hatalar.append(f"dogrulama-zorunlu-degil: {ad}")

    vars_ = blok.get("routing_defaults")
    if not isinstance(vars_, dict):
        hatalar.append("routing_defaults-yok")
    else:
        if vars_.get("unknown_complexity") not in profiller:
            hatalar.append(f"unknown_complexity-profil-degil: {vars_.get('unknown_complexity')!r}")
        if vars_.get("unknown_risk") != RISK_ARALIK[1]:
            hatalar.append("unknown_risk-en-yuksek-degil")  # belirsiz risk fail-closed: en yüksek risk

    # Risk tavanı yükselirken model gücü düşmemeli: aynı model ailesinde effort sırası korunur.
    sira = {e: i for i, e in enumerate(GECERLI_EFFORT)}
    for ad, p in profiller.items():
        if isinstance(p, dict) and p.get("effort") in sira and isinstance(p.get("risk_ceiling"), int) and p["risk_ceiling"] >= 3:
            if str(p.get("model")).lower() == "haiku":
                hatalar.append(f"risk3-haiku: {ad}")

    return {"gecerli": not hatalar, "hatalar": hatalar, "surum": cfg.get("surum")}
