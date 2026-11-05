"""İddia-kaynak kapısı (gölge): yanıttaki sayı aynı turun araç çıktısında ya da kullanıcı isteminde geçmiyorsa
(`sayi_kaynaksiz`) ve değerlendirme/var-yok iddiası bir kaynak türü etiketi ya da "doğrulanmadı" taşımıyorsa
(`etiketsiz_iddia`) bulgu üretir. Model çağrılmaz; yalnız ölçer (gölge): engellemez, kullanıcıya uyarı vermez.

Kalıplar, etiket listesi ve eşikler kodda durmaz: `ayarlar/iddia_kaynak.json` (eklenti varsayılanı) ve proje durum
dizinindeki aynı adlı dosya (anahtar bazında ezer). `ORKESTRA_KANIT_KAPISI=0` kapıyı kapatır. Hatada sessiz geçer.
"""
from __future__ import annotations

import json
import os
import re

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARSAYILAN_YOL = os.path.join(_KOK, "ayarlar", "iddia_kaynak.json")
PROJE_DOSYA = "iddia_kaynak.json"
KAPI = "iddia_kaynak"
MODLAR = ("golge", "kapali")


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
    if os.environ.get("ORKESTRA_KANIT_KAPISI") == "0":
        return "kapali"
    m = ayar.get("mod", "kapali")
    return m if m in MODLAR else "kapali"


def normallestir(metin) -> str:
    """Türkçe büyük/küçük harf farkını giderir (İ→i, I→ı)."""
    return (metin or "").replace("İ", "i").replace("I", "ı").lower()


def _sil(kaliplar, metin: str) -> str:
    for k in kaliplar or []:
        try:
            metin = re.sub(k, " ", metin, flags=re.S)
        except re.error:
            continue
    return metin


_BINLIK = re.compile(r"\d{1,3}(?:[.,]\d{3})+(?!\d)")


def _basamak(sayi: str) -> str:
    """Binlik ayracı kaldırır (1.250 → 1250); ondalık virgül noktaya çevrilir (54,7 → 54.7)."""
    if _BINLIK.fullmatch(sayi):
        return re.sub(r"[.,]", "", sayi)
    return sayi.replace(",", ".")


def sayilar(yanit: str, ayar: dict) -> list:
    """Yanıttaki iddia sayıları (kod, tarih, kimlik, madde numarası ayıklanır; binlik ayraç kaldırılır; tekrarsız)."""
    govde = _sil(ayar.get("ayiklama_kaliplari"), yanit or "")
    min_hane = int(ayar.get("min_hane", 2) or 2)
    gorulen = []
    for m in re.finditer(r"\d[\d.,]*\d|\d", govde):
        s = _basamak(m.group(0))
        if len(re.sub(r"\D", "", s)) >= min_hane and s not in gorulen:
            gorulen.append(s)
    return gorulen


def _kaynakta(sayi: str, kaynak: str) -> bool:
    return re.search(r"(?<!\d)%s(?!\d)" % re.escape(sayi), kaynak) is not None


def _cumleler(yanit: str):
    govde = re.sub(r"```.*?```", " ", yanit or "", flags=re.S)
    for parca in re.split(r"(?<=[.!?])\s+|\n+", govde):
        p = " ".join(parca.split()).strip("-*• ")
        if p:
            yield p


def _ara(kalip, metin: str) -> bool:
    try:
        return bool(kalip) and re.search(kalip, metin) is not None
    except re.error:
        return False


def _etiket_kalibi(ayar: dict) -> str:
    ad = "|".join(re.escape(normallestir(e)) for e in ayar.get("etiketler") or [])
    return r"([\(\[]\s*(%s)\b|kaynak:\s*(%s)\b)" % (ad, ad) if ad else ""


def analiz(yanit: str, istem: str, ciktilar, ayar: dict) -> list:
    """Bulgu listesi: [{'tur': 'sayi_kaynaksiz'|'etiketsiz_iddia', 'alinti': ...}]. Kip kapalıysa boş."""
    if mod(ayar) == "kapali" or not isinstance(yanit, str) or not yanit.strip():
        return []
    bulgular = []
    kaynak = _basamak_metni("\n".join([istem or ""] + [c for c in (ciktilar or []) if isinstance(c, str)]))
    for s in sayilar(yanit, ayar):
        if not _kaynakta(s, kaynak):
            bulgular.append({"tur": "sayi_kaynaksiz", "alinti": s})
    etiket = _etiket_kalibi(ayar)
    for c in _cumleler(yanit):
        n = normallestir(c)
        if _ara(ayar.get("iddia_kalibi"), n) and not _ara(ayar.get("muaf_kalibi"), n) and not _ara(etiket, n):
            sinir = int(ayar.get("alinti_max_karakter", 120) or 120)
            bulgular.append({"tur": "etiketsiz_iddia", "alinti": c[:sinir]})
    return bulgular[: int(ayar.get("max_bulgu", 10) or 10)]


def _basamak_metni(metin: str) -> str:
    """Kaynak metindeki binlik/ondalık ayraçlı sayıları ayraçsız biçime getirir (1.250 → 1250)."""
    metin = _BINLIK.sub(lambda m: re.sub(r"[.,]", "", m.group(0)), metin)
    return re.sub(r"(?<=\d),(?=\d)", ".", metin)


def degerlendir(transcript_path, yanit=None, sd=None) -> list:
    """Son turun yanıtını (ya da verilen metni) aynı turun istemi ve araç çıktılarıyla karşılaştırır. Hatada boş liste."""
    try:
        import kanit_olcum as K
        ayar = ayar_oku(sd)
        if mod(ayar) == "kapali":
            return []
        tur = K.son_tur(transcript_path, ayar.get("kuyruk_bayt", 2_000_000))
        if not tur:
            return []
        return analiz(yanit if yanit else tur["yanit"], tur["istem"], tur.get("ciktilar") or [], ayar)
    except Exception:
        return []
