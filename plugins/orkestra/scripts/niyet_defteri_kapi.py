"""Niyet defteri gölge kapısı ve ölçümü (ADR-0156, P-028).

stop_kontrol: tur biterken oturumun son anlamlı kullanıcı isteği için defterde niyet yoksa gunluk.jsonl'a `kapi_golge`
yazar; iş engellenmez. rapor: anlamlı isteklerde niyet yazılma (kapsama) oranı ve Wilson alt sınırı (ihlal geçiş ölçüsü).
"""
from __future__ import annotations

import json
import os
import re

import niyet_defteri as ND
import ork_lib as L

VARSAYILAN = {"n_min": 60, "wilson_alt_min": 0.75, "kisa_mesaj_uzunluk": 15}
_ONAY = re.compile(r"^\W*(evet|hayır|tamam|olur|yap|onay\w*|başla|devam|ok|okay|peki|tamamdır)\W*(yap\W*)?$", re.I)


def ayar(sd: str | None = None) -> dict:
    """Eklenti ayarı + proje ezmesi; bozuk ya da eksikse varsayılan."""
    sonuc = dict(VARSAYILAN)
    kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yollar = [os.path.join(kok, "ayarlar", ND.KAPI + ".json")]
    if sd:
        yollar.append(os.path.join(sd, ND.KAPI + ".json"))
    for y in yollar:
        try:
            with open(y, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(d, dict):
            for k in VARSAYILAN:
                if isinstance(d.get(k), (int, float)):
                    sonuc[k] = d[k]
    return sonuc


def _anlamli(k: dict, cfg: dict) -> bool:
    """Niyet beklenen istek: kısa onay ve çok kısa mesajlar (evet, yap, tamam) niyet taşımaz."""
    ne = str(k.get("ne") or "")
    return int(k.get("uzunluk") or len(ne)) >= cfg["kisa_mesaj_uzunluk"] and not _ONAY.match(ne)


def _istekler(sd: str, oturum: str | None = None) -> list[dict]:
    return [k for k in L.jsonl_oku(os.path.join(sd, "gunluk.jsonl"))
            if k.get("tur") == "istek" and k.get("istek_id") and (oturum is None or k.get("oturum") == oturum)]


def _niyet_sayisi(sd: str) -> dict[str, int]:
    s: dict[str, int] = {}
    for k in ND.oku(sd):
        if k.get("tur") == "niyet":
            s[k["istek_id"]] = s.get(k["istek_id"], 0) + 1
    return s


def stop_kontrol(sd: str, oturum: str) -> bool:
    """Son anlamlı istek için niyet yoksa gunluk.jsonl'a bir kez `kapi_golge` yazar. Hata çağırana taşmaz."""
    try:
        if not ND.acik() or not oturum or not sd:
            return False
        cfg = ayar(sd)
        anlamli = [k for k in _istekler(sd, oturum) if _anlamli(k, cfg)]
        if not anlamli:
            return False
        son = anlamli[-1]["istek_id"]
        if _niyet_sayisi(sd).get(son):
            return False
        gl = os.path.join(sd, "gunluk.jsonl")
        neden = f"istek {son} için ajan niyet yazmadı"
        if any(k.get("tur") == "kapi_golge" and k.get("kapi") == ND.KAPI and k.get("neden") == neden
               for k in L.jsonl_oku(gl)[-300:]):
            return False
        L.jsonl_ekle(gl, {"zaman": L.simdi(), "oturum": oturum, "tur": "kapi_golge", "kapi": ND.KAPI, "is": "-", "neden": neden})
        return True
    except Exception:
        return False


def rapor(sd: str) -> dict:
    """Anlamlı isteklerde kapsama (istek başına en az 1 niyet) oranı ve Wilson alt sınırı.

    Payda etiketleyici gerektirmez: "çok niyetli" mesajı uzunluk vekiliyle ayırmak 30 gerçek mesajlık elle etiketli
    örnekte kesinlik %43, duyarlılık %43 verdi (I-369); bu yüzden kapı ölçüsü kapsamadır, atomiklik ayrıca bilgi olarak verilir."""
    from kanit_olcum import wilson
    cfg = ayar(sd)
    sayi = _niyet_sayisi(sd)
    anlamli = [k for k in _istekler(sd) if _anlamli(k, cfg)]
    n = len(anlamli)
    yazilan = sum(1 for k in anlamli if sayi.get(k["istek_id"], 0) >= 1)
    ort = round(sum(sayi.get(k["istek_id"], 0) for k in anlamli if sayi.get(k["istek_id"], 0)) / yazilan, 2) if yazilan else None
    alt = round(wilson(yazilan, n)[0], 3) if n else None
    return {"n": n, "yazilan": yazilan, "oran": round(yazilan / n, 3) if n else None, "wilson_alt": alt,
            "n_min": cfg["n_min"], "wilson_alt_min": cfg["wilson_alt_min"],
            "ortalama_niyet": ort, "etiketleyici": "yok: payda = kısa onay olmayan her istek (kapsama)",
            "gecis_hazir": bool(n >= cfg["n_min"] and alt is not None and alt >= cfg["wilson_alt_min"])}


def yonerge(sd: str, istek_id: str | None, metin: str) -> str:
    """Kullanıcı mesajında ajana tek satırlık niyet yazma yönergesi (en çok 300 karakter); kısa onayda ve kapalıyken boş.

    Metin yalnız sınıflama içindir, hiçbir yere yazılmaz."""
    try:
        if not ND.acik() or not istek_id or not _anlamli({"ne": metin, "uzunluk": len(metin or "")}, ayar(sd)):
            return ""
        return ("NİYET DEFTERİ (ADR-0156): mesajdaki her ayrı niyeti işe başlamadan "
                "`orkestra niyetler ekle istek|kisit|revize|vazgec|soru \"tek cümle\"` ile yaz "
                "(ham mesaj ve sır yazma); bitince `orkestra niyetler durum ID karsilandi --kanit …`.")
    except Exception:
        return ""
