#!/usr/bin/env python3
"""Platform yetenek kapısı (Faz 06, I-419): istenen model/effort ile gerçekten çalışan karşılaştırılır.

Durumlar: OK, MISMATCH (gözlenen farklı), UNSUPPORTED (platform bu ayarı uygulamıyor), UNVERIFIED (gözlem yok).
Risk >= 2'de OK dışı her durum engeldir (fail-closed); düşük riskte uyarıdır.
"""
from __future__ import annotations

# Kaynak: paket FAZ_01 bulguları; canlı doğrulanmadı (plan §6). Değerler ayarla ezilebilir.
YETENEK = {
    "claude_code": {"model_secimi": True, "effort_secimi": True},
    "cursor": {"model_secimi": False, "effort_secimi": False},
}


def kontrol(karar: dict, platform: str, gozlenen: dict | None = None, yetenek: dict | None = None) -> dict:
    y = (yetenek or YETENEK).get(platform)
    if y is None:
        durum, neden = "UNSUPPORTED", "platform-bilinmiyor"
    elif not y.get("model_secimi") or not y.get("effort_secimi"):
        durum, neden = "UNSUPPORTED", "platform-model-effort-secmiyor"
    elif not gozlenen:
        durum, neden = "UNVERIFIED", "gozlem-yok"
    elif gozlenen.get("model") == karar["model"] and gozlenen.get("effort") == karar["effort"]:
        durum, neden = "OK", "istenen-esit-gozlenen"
    else:
        durum, neden = "MISMATCH", "istenen-gozlenenden-farkli"
    engel = durum != "OK" and karar.get("risk", 3) >= 2
    return {"durum": durum, "neden": neden, "engel": engel, "platform": platform}
