"""Tekrar eden iş kümeleme (I-347 P1): kullanıcı istekleri LLM'siz iş türüne kümelenir.

Neden: sayaç anahtarı serbest metindi, aynı iş farklı yazılınca ayrı sayılıyordu; perspektif de skill adayını son 40 ham
istekten tahmin ediyordu. Burada bildirim ve sistem metni süzülür, kalan istekler gövde kökü (ilk KOK_UZUNLUK harf) kümesi
üzerinden Jaccard benzerliğiyle gruplanır. Eşik tek kaynaktır: `sayac.ESIK` (kümedeki istek sayısı bu eşikte aday olur).
Benzerlik eşiği BENZERLIK, tests/veri/skill_kume_ornek.jsonl etiketli örneğinin ilk yarısıyla seçildi, ikinci yarıda sınanır.

Komut satırı: `python skill_kume.py [--gun 14] [--json]` (durum dizinini çalışma klasöründen bulur).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

KOK_UZUNLUK = 5  # Türkçe ek çeşitliliğini sönümler: "commitle", "commit", "commiti" aynı kök
BENZERLIK = 0.5  # etiketli örnekte seçildi (tests/test_skill_kume.py)
EN_AZ_SOZCUK = 3  # "onaylıyorum", "yap" gibi kısa istekler iş türü taşımaz
GURULTU_ONEKI = ("<system-reminder", "<task-notification", "<command-", "<local-command", "<ci-monitor",
                 "[system notification", "<pasted_content", "caveat:")
DURAK = frozenset("""ve ile bir bu şu da de mi mı mu mü ki için gibi ama veya ya ne var yok çok daha en
the and for with that this you are not from""".split())
_SOZCUK = re.compile(r"[a-zçğıöşü0-9_]{3,}", re.IGNORECASE)
_URL_YOL = re.compile(r"(https?://\S+|[a-z]:[\\/]\S+|\S+[\\/]\S+\.\w{1,5})", re.IGNORECASE)
_SAYI = re.compile(r"\b\d[\d.:,/-]*\b")


def temizle(metin) -> str | None:
    """Gürültü (bildirim, sistem hatırlatması) ise None; değilse adres ve sayıları atılmış küçük harfli metin."""
    s = str(metin or "").strip()
    if not s or s.lower().startswith(GURULTU_ONEKI):
        return None
    s = _SAYI.sub(" ", _URL_YOL.sub(" ", s)).lower().replace("i̇", "i")
    return s


def kokler(metin: str) -> frozenset:
    return frozenset(w[:KOK_UZUNLUK] for w in _SOZCUK.findall(metin) if w not in DURAK)


def benzerlik(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def kumele(istekler: list[dict], esik: float = BENZERLIK) -> list[dict]:
    """istekler: [{"zaman": ..., "metin": ...}] → kümeler (en büyük önce).

    Küme: {"id", "adet", "temsil", "kokler", "tarihler", "ornekler"}. Lider tabanlı: istek, liderine en benzer kümeye
    (benzerlik >= esik) girer, yoksa yeni küme açar; sonuç girdi sırasından bağımsız tutarlılık için tarihe göre sıralı işlenir.
    """
    kumeler: list[dict] = []
    for r in sorted(istekler, key=lambda x: str(x.get("zaman", ""))):
        t = temizle(r.get("metin"))
        k = kokler(t) if t is not None else frozenset()
        if len(k) < EN_AZ_SOZCUK:
            continue
        en, en_b = None, 0.0
        for c in kumeler:
            b = benzerlik(k, c["_lider"])
            if b > en_b:
                en, en_b = c, b
        if en is not None and en_b >= esik:
            en["adet"] += 1
            en["tarihler"].append(str(r.get("zaman", ""))[:10])
            if len(en["ornekler"]) < 5:
                en["ornekler"].append(str(r.get("metin", ""))[:160])
            en["_ortak"] &= k
        else:
            kumeler.append({"_lider": k, "_ortak": set(k), "adet": 1, "tarihler": [str(r.get("zaman", ""))[:10]],
                            "temsil": str(r.get("metin", ""))[:160], "ornekler": [str(r.get("metin", ""))[:160]]})
    sonuc = []
    for c in sorted(kumeler, key=lambda c: -c["adet"]):
        ortak = sorted(c["_ortak"] or c["_lider"])
        sonuc.append({"id": "k-" + hashlib.sha256("|".join(ortak).encode("utf-8")).hexdigest()[:8], "adet": c["adet"],
                      "temsil": c["temsil"], "kokler": ortak, "tarihler": sorted(set(c["tarihler"])),
                      "ornekler": c["ornekler"]})
    return sonuc


def adaylar(kumeler: list[dict], esik: int, mevcut_skiller: list[str] | None = None) -> list[dict]:
    """Eşik (sayac.ESIK) ve üstü kümeler; temsil/örnekler zaten var olan bir skill adıyla örtüşenler `mevcut` işaretlenir."""
    ad_kokleri = {s: kokler(s.replace("-", " ").replace(":", " ")) for s in (mevcut_skiller or [])}
    out = []
    for c in kumeler:
        if c["adet"] < esik:
            continue
        k = frozenset(c["kokler"])
        eslesen = [s for s, ak in ad_kokleri.items() if ak and len(ak & k) / len(ak) >= 0.6]
        out.append({**c, "mevcut_skill": eslesen})
    return out


def gunluk_istekleri(sd: str, gun: int = 14) -> list[dict]:
    import ork_lib as L
    esik = (datetime.datetime.now().astimezone() - datetime.timedelta(days=gun)).isoformat()
    return [r for r in L.jsonl_oku(os.path.join(sd, "gunluk.jsonl"))
            if r.get("tur") == "istek" and str(r.get("zaman", "")) >= esik]


def hesapla(sd: str, gun: int = 14, skiller: list[str] | None = None) -> dict:
    import sayac
    kumeler = kumele(gunluk_istekleri(sd, gun))
    return {"gun": gun, "esik": sayac.ESIK, "kume_sayisi": len(kumeler),
            "adaylar": adaylar(kumeler, sayac.ESIK, skiller)[:20]}


def main(argv=None) -> int:
    import argparse
    import ork_lib as L
    ap = argparse.ArgumentParser(description="İstekleri iş türüne kümeler")
    ap.add_argument("--gun", type=int, default=14)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    sd = L.durum_dizini(os.getcwd())
    if not sd:
        print("skill_kume: durum dizini yok", file=sys.stderr)
        return 1
    s = hesapla(sd, a.gun)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        print(f"{s['kume_sayisi']} küme, eşik {s['esik']}, aday {len(s['adaylar'])}")
        for c in s["adaylar"]:
            print(f"- {c['id']} ×{c['adet']}: {c['temsil'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
