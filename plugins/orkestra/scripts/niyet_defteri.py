"""Niyet defteri (ADR-0156, I-369): her kullanıcı mesajından çıkan atomik niyetler kalıcı ve kanıtlı kaydedilir.

Defter proje başına `.claude/orkestra/niyetler.jsonl`, ekleme-only ve kilitlidir (ork_lib.jsonl_ekle). Ham mesaj
saklanmaz: kaynak işaretçisi `istek_id`'dir (ork_lib.istek_id_yeni); metin transkriptte kalır. Niyet metni maskeden geçer.
Olaylar:
  niyet   ajan yazar: tür (istek, kisit, revize, vazgec, soru), ne, kriter (ekranda görülecek sonuç), kisit, ilgili
  durum   acik, karsilandi, kismen, vazgecildi; karsilandi ve kismen kanıtsız yazılamaz
Tür revize/vazgec önceki niyete `ilgili` ile bağlanır ve onu vazgecildi yapar. Kapatma: ORKESTRA_NIYET_DEFTERI=0.
Kapı: scripts/niyet_defteri_kapi.py (mod: golge, P-028). Ayar: ayarlar/niyet_defteri.json.
"""
from __future__ import annotations

import os
import re

import ork_lib as L

DOSYA = "niyetler.jsonl"
KAPI = "niyet_defteri"
TURLER = ("istek", "kisit", "revize", "vazgec", "soru")
DURUMLAR = ("acik", "karsilandi", "kismen", "vazgecildi")
KANIT_ISTEYEN = ("karsilandi", "kismen")
NE_AZAMI = 160
ALAN_AZAMI = 200


def acik() -> bool:
    return os.environ.get("ORKESTRA_NIYET_DEFTERI") != "0"


def yol(sd: str) -> str:
    return os.path.join(sd, DOSYA)


def _temiz(m: str | None, n: int) -> str:
    t = " ".join(re.sub(r"</?[A-Za-z_\-]+[^>]*>", " ", L.maskele(m or "")).split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def oku(sd: str) -> list[dict]:
    return L.jsonl_oku(yol(sd))


def _oturum(sd: str, oturum: str) -> list[dict]:
    return [k for k in oku(sd) if k.get("oturum") == oturum]


def guncel(sd: str, oturum: str) -> list[dict]:
    """Oturumun niyetleri, her biri en son durum ve kanıtıyla (durum olayı yoksa acik)."""
    niyetler: dict[str, dict] = {}
    for k in _oturum(sd, oturum):
        if k.get("tur") == "niyet":
            niyetler[k["id"]] = {**k, "durum": "acik", "kanit": None}
        elif k.get("tur") == "durum" and k.get("id") in niyetler:
            niyetler[k["id"]]["durum"] = k.get("durum")
            niyetler[k["id"]]["kanit"] = k.get("kanit")
    return list(niyetler.values())


def _yaz(sd: str, oturum: str, tur: str, **alan) -> None:
    kayit = {"zaman": L.simdi(), "oturum": oturum, "tur": tur}
    kayit.update({k: v for k, v in alan.items() if v not in (None, "")})
    L.jsonl_ekle(yol(sd), kayit)


def durum_yaz(sd: str, oturum: str, niyet_id: str, durum: str, kanit: str | None = None) -> None:
    """Niyetin durumunu yazar. karsilandi ve kismen kanıt ister; bilinmeyen niyet reddedilir."""
    if durum not in DURUMLAR:
        raise ValueError(f"durum geçersiz: {durum} (olabilecekler: {', '.join(DURUMLAR)})")
    if niyet_id not in {k["id"] for k in guncel(sd, oturum)}:
        raise ValueError(f"niyet bulunamadı: {niyet_id}")
    kanit_t = _temiz(kanit, ALAN_AZAMI)
    if durum in KANIT_ISTEYEN and not kanit_t:
        raise ValueError(f"{durum} kanıt ister (dosya:satır, komut çıktısı ya da sayı)")
    _yaz(sd, oturum, "durum", id=niyet_id, durum=durum, kanit=kanit_t or None)


def ekle(sd: str, oturum: str, istek_id: str, tur: str, ne: str, kriter: str | None = None,
         kisit: str | None = None, ilgili: str | None = None) -> str:
    """Bir mesajdan çıkan niyeti ekler, kimliğini (`<istek_id>/<n>`) döndürür. revize/vazgec `ilgili` ister ve onu kapatır."""
    if tur not in TURLER:
        raise ValueError(f"tür geçersiz: {tur} (olabilecekler: {', '.join(TURLER)})")
    ne_t = _temiz(ne, NE_AZAMI)
    if not ne_t:
        raise ValueError("ne boş olamaz")
    if tur in ("revize", "vazgec") and ilgili not in {k["id"] for k in guncel(sd, oturum)}:
        raise ValueError(f"{tur} mevcut bir niyete bağlanmalı (ilgili={ilgili})")
    sira = 1 + sum(1 for k in guncel(sd, oturum) if k.get("istek_id") == istek_id)
    kimlik = f"{istek_id}/{sira}"
    _yaz(sd, oturum, "niyet", id=kimlik, istek_id=istek_id, niyet_tur=tur, ne=ne_t,
         kriter=_temiz(kriter, ALAN_AZAMI) or None, kisit=_temiz(kisit, ALAN_AZAMI) or None, ilgili=ilgili)
    if tur in ("revize", "vazgec"):
        _yaz(sd, oturum, "durum", id=ilgili, durum="vazgecildi",
             kanit=f"{'yerine' if tur == 'revize' else 'vazgeçildi'}: {kimlik}")
    return kimlik


def sayim(sd: str, oturum: str) -> dict:
    s = {"toplam": 0, "acik": 0, "karsilandi": 0, "kismen": 0, "vazgecildi": 0}
    for k in guncel(sd, oturum):
        s["toplam"] += 1
        s[k["durum"]] += 1
    return s
