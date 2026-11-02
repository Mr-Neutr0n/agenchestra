"""Yapamam kanıt kapısı (ADR-0153, P-045): yanıtta "yapamam / erişimim yok" türü gerçek bir yapamama iddiası, denenen komut
ya da engel kanıtı (Denendi, Engel, hata çıktısı, kural kimliği) olmadan yazılmışsa ölçüm kaydı düşer. Yalnız ölçer:
engellemez, kullanıcıya gürültü yapmaz, model çağrılmaz.

Ölçüm (olcum_yapamam_20261102.md): yanlış çıkan yapamam iddiasının tamamı kanıt türü taşımayanlardandı; doğru sınırlar
kanıtla yazılmıştı. Kalıplar, kip ve eşikler kodda durmaz: `ayarlar/yapamam_kaniti.json` (eklenti varsayılanı) ve proje durum
dizinindeki aynı adlı dosya (anahtar bazında ezer). Kip: `golge`, `kapali`. `ORKESTRA_YAPAMAM_KANITI=0` kapatır.
"""
from __future__ import annotations

import json
import os
import re

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARSAYILAN_YOL = os.path.join(_KOK, "ayarlar", "yapamam_kaniti.json")
PROJE_DOSYA = "yapamam_kaniti.json"
KAPI = "yapamam_kaniti"
MODLAR = ("golge", "kapali")
_CUMLE_SONU = ".!?\n"


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


def mod(ayar: dict) -> str:
    if os.environ.get("ORKESTRA_YAPAMAM_KANITI") == "0":
        return "kapali"
    m = ayar.get("mod", "kapali")
    return m if m in MODLAR else "kapali"


def normallestir(metin) -> str:
    """Türkçe büyük/küçük harf farkını giderir (İ→i, I→ı); uzunluk korunur."""
    return (metin or "").replace("İ", "i").replace("I", "ı").lower()


def _ilk(kaliplar, norm: str):
    for k in kaliplar or []:
        try:
            m = re.search(k, norm)
        except re.error:
            continue
        if m:
            return m
    return None


def _alintida(norm: str, bas: int) -> bool:
    """İddia, açılmış ama kapanmamış tırnak ya da ters tırnak içinde mi (alıntı, kural anlatımı)."""
    parca = norm[:bas]
    return any(parca.count(c) % 2 == 1 for c in ('"', "`", "«"))


def degerlendir(metin, sd=None) -> dict:
    """Kanıtsız gerçek yapamama iddiası varsa {"kalip", "alinti"}; yoksa boş sözlük. Kip `kapali` ise boş."""
    ayar = ayar_oku(sd)
    if mod(ayar) == "kapali" or not isinstance(metin, str) or not metin.strip():
        return {}
    norm = normallestir(metin)
    if _ilk(ayar.get("kanit_kaliplari"), norm):
        return {}
    for k in ayar.get("iddia_kaliplari") or []:
        try:
            ml = list(re.finditer(k, norm))
        except re.error:
            continue
        for m in ml:
            if _alintida(norm, m.start()):
                continue
            bas = max(norm.rfind(c, 0, m.start()) for c in _CUMLE_SONU) + 1
            sonlar = [i for i in (norm.find(c, m.end()) for c in _CUMLE_SONU) if i != -1]
            return {"kalip": k, "alinti": metin[bas:(min(sonlar) + 1 if sonlar else len(metin))].strip()}
    return {}
