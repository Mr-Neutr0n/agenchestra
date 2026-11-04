"""Bekleme anı aday listesi: kart durumu okuma, hook bağlamı ve günlük olayları (ADR-0158, I-376).

Çekirdek karar `bosta.baslatilabilir`dedir. Bu modül durumu işin kartlarından toplar, ≤300 karakterlik bağlam satırını kurar
ve `bosta_aday` / `bosta_gecersiz` olaylarını gunluk.jsonl'a yazar. Mod `ayarlar/bosta.json` (golge: yalnız bağlam ve kayıt;
kapatma ORKESTRA_BOSTA=0). Hiçbir hata aracı bozmaz.
"""
from __future__ import annotations

import os
import re

import bosta as B
import is_onay
import kapi_mod
import ork_lib as L

KAPI = "bosta"
SINIR = 300
_REF = re.compile(r"^P(\d+)$")


def acik_mi() -> bool:
    return os.environ.get("ORKESTRA_BOSTA", "1") != "0"


def kart_durumlari(sd: str, is_id: str | None) -> dict[int, str]:
    """{P numarası: durum} — işin kartlarından (`ref: P<n>`); aynı P için en son okunan kart geçerlidir."""
    sonuc: dict[int, str] = {}
    for k in L.kartlar(sd, derin=False):
        m = _REF.match(str(k.get("ref", "")))
        if not m or (is_id and k.get("is") != is_id):
            continue
        sonuc[int(m.group(1))] = L.kart_durumu_hesapla(k)
    return sonuc


def hesapla(plan_metni: str, kayit: dict | None, durumlar: dict[int, str], bekleyen=(), plan_denetimde=False) -> dict:
    d = dict(durumlar)
    for n in bekleyen:
        d[n] = "denetimde"
    return B.baslatilabilir(plan_metni, d, onayli=not is_onay.bekliyor_mu(kayit), plan_denetimde=plan_denetimde)


def baglam_satiri(sonuc: dict, is_id: str) -> str:
    """Aday yoksa boş (0 karakter); varsa en çok 300 karakter."""
    ad = sonuc.get("adaylar") or []
    if not ad:
        return ""
    liste = ", ".join(f"P{n}" for n in ad)
    s = (f"orkestra (gölge) bosta: beklerken başlatılabilir bağımsız madde: {liste}. Başlatmadan önce plandaki Kabul'a "
         f"bak. Ayrıntı: orkestra is bosta {is_id}")
    return s[:SINIR]


def olay_yaz(sd: str, tur: str, is_id: str, **alan) -> None:
    try:
        L.jsonl_ekle(os.path.join(sd, "gunluk.jsonl"), {"zaman": L.simdi(), "tur": tur, "is": is_id, **alan})
    except Exception:
        pass


def gecersiz_yaz(sd: str, is_id: str, p: int, neden: str) -> None:
    """Başlatılmış bağımsız işin sonradan geçersizleştiğini kaydeder (ret ölçümünün verisi)."""
    olay_yaz(sd, "bosta_gecersiz", is_id, madde=f"P{p}", neden=L.maskele(neden)[:200])


def hook_satiri(sd: str, cwd: str, is_id: str | None, plan_yolu: str | None, kayit: dict | None, bekleyen=()) -> str:
    """Denetçi başlarken çağrılır. Mod golge: satır döner ve `bosta_aday` yazılır. Hata ya da kapalıysa ''."""
    try:
        if not acik_mi() or not is_id or not plan_yolu or not os.path.isfile(plan_yolu):
            return ""
        with open(plan_yolu, encoding="utf-8") as f:
            metin = f.read()
        s = hesapla(metin, kayit, kart_durumlari(sd, is_id), bekleyen)
        satir = baglam_satiri(s, is_id)
        if satir:
            olay_yaz(sd, "bosta_aday", is_id, adaylar=[f"P{n}" for n in s["adaylar"]], mod=kapi_mod.mod(KAPI, cwd))
        return satir
    except Exception:
        return ""
