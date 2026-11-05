"""Kapanış mesajı süreç anlatımı kapısı (ADR-0163, I-387, P-014, P-045).

Kullanıcıya giden son mesajda ajanın kendi iç sürecini anlatan cümleler ("onayı kendim verdim", "gerekçem şu",
"hook beni engelledi") günlüğe `kural_ihlal / kapanis_surec` olarak düşer. Mekanizma `onleme_yanit.py` ile aynıdır
(ayar okuma, normalleştirme, kalıp eşleme yardımcıları oradan gelir); yalnız ölçer: engellemez, model çağrılmaz.

Kalıplar, kip ve eşikler `ayarlar/kapanis_surec.json` (eklenti varsayılanı) ve proje durum dizinindeki
`kapanis_surec.json` (anahtar bazında ezer). Kip: `golge`, `kapali`. `ORKESTRA_KAPANIS_SUREC=0` kapatır.
Ölçüm: `python scripts/kapanis_surec.py rapor [durum_dizini]`.
"""
from __future__ import annotations

import json
import os
import sys

import onleme_yanit as OY

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARSAYILAN_YOL = os.path.join(_KOK, "ayarlar", "kapanis_surec.json")
PROJE_DOSYA = "kapanis_surec.json"
KURAL = "kapanis_surec"
MODLAR = ("golge", "kapali")


def ayar_oku(sd=None) -> dict:
    ayar = OY._json_oku(VARSAYILAN_YOL) or {}
    if sd:
        proje = OY._json_oku(os.path.join(sd, PROJE_DOSYA))
        if proje:
            ayar.update(proje)
    return ayar


def mod(ayar: dict) -> str:
    if os.environ.get("ORKESTRA_KAPANIS_SUREC") == "0":
        return "kapali"
    m = ayar.get("mod", "kapali")
    return m if m in MODLAR else "kapali"


def degerlendir(metin, sd=None) -> dict:
    """Metinde süreç anlatımı kalıbı varsa {"kalip", "alinti"} (ihlal cümlesi); aksi halde boş sözlük."""
    ayar = ayar_oku(sd)
    if mod(ayar) == "kapali" or not isinstance(metin, str) or not metin.strip():
        return {}
    norm = OY.normallestir(metin)
    bulgu = OY._ilk_eslesme(ayar.get("kaliplar"), norm)
    if not bulgu:
        return {}
    kalip, m = bulgu
    bas = max(norm.rfind(c, 0, m.start()) for c in OY._CUMLE_SONU) + 1
    sonlar = [i for i in (norm.find(c, m.end()) for c in OY._CUMLE_SONU) if i != -1]
    return {"kalip": kalip, "alinti": metin[bas:(min(sonlar) + 1 if sonlar else len(metin))].strip()}


def rapor(sd) -> dict:
    """Günlükteki `kural_ihlal / kapanis_surec` kayıtlarını sayar; geçiş eşiği ayardan."""
    yol = os.path.join(sd, "gunluk.jsonl")
    ihlal = 0
    if os.path.exists(yol):
        with open(yol, encoding="utf-8") as f:
            for s in f:
                try:
                    k = json.loads(s)
                except ValueError:
                    continue
                if k.get("tur") == "kural_ihlal" and k.get("kural") == KURAL:
                    ihlal += 1
    return {"ihlal": ihlal, "mod": mod(ayar_oku(sd)), "gecis_esigi": ayar_oku(sd).get("gecis_esigi")}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rapor":
        import ork_lib as L
        hedef = sys.argv[2] if len(sys.argv) > 2 else L.durum_dizini()
        print(json.dumps(rapor(hedef), ensure_ascii=False))
    else:
        print(__doc__)
