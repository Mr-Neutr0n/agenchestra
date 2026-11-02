"""Skill öneri hattı ölçümü (I-347 P5): her halkanın sayısı, hat hangi halkada tıkanıyor görünsün.

Halkalar: istek → küme → aday → rapor maddesi → taslak → onay kaydı → devreye alınan skill.
Salt okur; durum dizinine yazmaz. Komut: `orkestra perspektif rapor [--json] [--gun 14]`.
"""
from __future__ import annotations

import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HALKALAR = ("istek", "kume", "aday", "rapor_maddesi", "kume_anan", "taslak", "onay_kaydi", "uygulandi")


def olc(sd: str, gun: int = 14) -> dict:
    import onay
    import sayac
    import skill_kume as K
    kumeler = K.kumele(K.gunluk_istekleri(sd, gun))
    istek = len(K.gunluk_istekleri(sd, gun))
    adaylar = K.adaylar(kumeler, sayac.ESIK)
    rapor = onay.en_yeni_rapor(sd)
    maddeler = []
    if rapor:
        with open(rapor, encoding="utf-8", errors="replace") as f:
            maddeler = [m for m in onay._rapor_maddeleri(f.read()) if m[0] == "skill"]
    kume_anan = sum(1 for m in maddeler if "k-" in m[2] and any(c["id"] in m[2] for c in adaylar))
    kok = os.path.join(sd, "onerilen_skill")
    taslak = sum(1 for d in (os.listdir(kok) if os.path.isdir(kok) else [])
                 if os.path.isfile(os.path.join(kok, d, "SKILL.md")))
    try:
        kayitlar = [k for k in onay._hepsi(sd) if k.get("tur") == "skill"
                    or str(k.get("baslik", "")).startswith("Skill adayı:")]
    except Exception:
        kayitlar = []
    durum = collections.Counter(k.get("durum") for k in kayitlar)
    try:
        with open(os.path.join(sd, "sayac.json"), encoding="utf-8") as f:
            sj = json.load(f)
    except (OSError, ValueError):
        sj = {}
    h = {"istek": istek, "kume": len(kumeler), "aday": len(adaylar), "rapor_maddesi": len(maddeler),
         "kume_anan": kume_anan, "taslak": taslak, "onay_kaydi": len(kayitlar), "uygulandi": durum.get("uygulandi", 0)}
    return {"gun": gun, "esik": sayac.ESIK, "halkalar": h, "onay_durumlari": dict(durum),
            "sayac": {"anahtar": len(sj), "esige_ulasan": sum(1 for v in sj.values()
                                                              if isinstance(v, dict) and v.get("sayi", 0) >= sayac.ESIK)},
            "rapor": os.path.basename(rapor) if rapor else None, "tikanan": tikanan(h)}


def tikanan(h: dict) -> str | None:
    """Sayısı sıfır olan ilk halka: hat orada kopuktur (önceki halka doluyken)."""
    onceki = None
    for ad in HALKALAR:
        if h[ad] == 0 and (onceki is None or h[onceki] > 0):
            return ad
        onceki = ad
    return None


def main(argv=None) -> int:
    import argparse
    import ork_lib as L
    ap = argparse.ArgumentParser(description="Skill öneri hattı halka sayıları")
    ap.add_argument("--gun", type=int, default=14)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    sd = L.durum_dizini(os.getcwd())
    if not sd:
        print("perspektif_rapor: durum dizini yok", file=sys.stderr)
        return 1
    o = olc(sd, a.gun)
    if a.json:
        print(json.dumps(o, ensure_ascii=False, indent=1))
    else:
        print(f"Skill hattı (son {o['gun']} gün, eşik {o['esik']}, rapor {o['rapor'] or 'yok'})")
        for ad in HALKALAR:
            print(f"- {ad}: {o['halkalar'][ad]}")
        print(f"- onay durumları: {o['onay_durumlari'] or '-'}")
        print(f"- tıkanan halka: {o['tikanan'] or 'yok'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
