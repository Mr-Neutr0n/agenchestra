#!/usr/bin/env python3
"""Nedene göre yükseltme (Faz 07, I-419): körlemesine daha pahalı modele geçilmez.

Eylemler: kart-duzelt (kriter belirsiz), ortam-duzelt (ortam sorunu), yukselt (yetenek yetersiz ya da aynı profilde
tekrar ret), devam. Yükseltme `yukseltme_sirasi` ile yapılır: önce effort, model değişimi ancak sonra.
"""
from __future__ import annotations

import routing_policy as RP

AYNI_PROFILDE_EN_COK_RET = 2


def sonraki(neden: str | None, ret_sayisi: int, profil: str, blok: dict, sira: list | None = None) -> dict:
    sira = sira or ["effort", "model"]
    if neden == "kriter-belirsiz":
        return {"eylem": "kart-duzelt", "profil": profil}
    if neden == "ortam":
        return {"eylem": "ortam-duzelt", "profil": profil}
    yukselt = neden == "yetenek-yetersiz" or ret_sayisi >= AYNI_PROFILDE_EN_COK_RET
    if not yukselt:
        return {"eylem": "devam", "profil": profil}
    profiller = blok["route_profiles"]
    dizi = RP._siradaki(profiller)
    i = dizi.index(profil)
    if i + 1 >= len(dizi):
        return {"eylem": "son", "profil": profil}
    hedef = dizi[i + 1]
    ayni_model = profiller[hedef]["model"] == profiller[profil]["model"]
    adim = "effort" if ayni_model else "model"
    if sira and sira[0] == "effort" and not ayni_model:
        # Önce aynı modelde daha yüksek effort aranır; yoksa model değişir.
        aday = next((d for d in dizi[i + 1:] if profiller[d]["model"] == profiller[profil]["model"]), None)
        if aday:
            hedef, adim = aday, "effort"
    return {"eylem": "yukselt", "profil": hedef, "adim": adim}
