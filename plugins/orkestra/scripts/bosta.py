"""Bekleme anı aday listesi (ADR-0158, I-376): denetçi ya da başka süreç beklenirken başlatılabilecek bağımsız plan maddeleri.

Durum duyarlıdır; `paralellik.dalgalar` statik kalır. Karar ajandadır, bu modül yalnız aday listesi üretir.

Aday koşulları (hepsi):
- iş onaylı ve plan denetimde değil;
- madde `bekliyor` (durumu yok ya da bilinmiyorsa bekliyor sayılır);
- `Kabul` alanı dolu (ADR-0159: `Geri alma` alanı plandan kalktı);
- `Önce` bağımlılıklarının (Çıktı ve Çakışma) tamamı `onaylandi`;
- yazma alanı `calisiyor`, `denetimde`, `reddedildi` maddelerin ve önceden seçilen adayların alanıyla ayrık.

Sınır: koşullar `Önce` ve `Yazma alanı` beyanlarının doğruluğuna dayanır; yanlış beyan mantıksal bağımlılığı yakalamaz.
"""
from __future__ import annotations

import paralellik as PR

BEKLIYOR = "bekliyor"
ONAYLI = "onaylandi"
ALAN_ENGELLEYEN = ("calisiyor", "denetimde", "reddedildi")


def _dolu(blok: str, alan: str) -> bool:
    return bool(PR._alan_degeri(blok, alan).strip())


def baslatilabilir(plan_metni: str, durumlar: dict[int, str] | None = None, onayli: bool = True,
                   plan_denetimde: bool = False) -> dict:
    """{'adaylar': [P numaraları], 'elenen': {n: neden}}; `durumlar` {P numarası: durum} (eksik madde bekliyor)."""
    durumlar = durumlar or {}
    md = PR.maddeler(plan_metni)
    bloklar = PR._p_bloklari(plan_metni)
    elenen: dict[int, str] = {}
    adaylar: list[int] = []
    if not onayli or plan_denetimde:
        neden = "iş onaylı değil" if not onayli else "plan denetimde"
        return {"adaylar": [], "elenen": {n: neden for n in md if durumlar.get(n, BEKLIYOR) == BEKLIYOR}}
    engel_alanlari = [m["yazma"] for n, m in md.items() if durumlar.get(n, BEKLIYOR) in ALAN_ENGELLEYEN]
    for n, m in sorted(md.items()):
        durum = durumlar.get(n, BEKLIYOR)
        if durum != BEKLIYOR:
            continue
        blok = bloklar.get(n, "")
        if not _dolu(blok, "Kabul"):
            elenen[n] = "Kabul alanı boş"
        else:
            bekleyen = [d for d, _tur, _g in m["once"] if durumlar.get(d, BEKLIYOR) != ONAYLI]
            if bekleyen:
                elenen[n] = "Önce bağımlılığı onaylanmadı: " + ", ".join(f"P{d}" for d in bekleyen)
            elif any(PR.alan_kesisir(m["yazma"], a) for a in engel_alanlari):
                elenen[n] = "yazma alanı çalışan, denetimdeki ya da reddedilen maddeyle kesişiyor"
            else:
                adaylar.append(n)
                engel_alanlari.append(m["yazma"])  # aday birbirini engeller: aynı alana iki iş verilmez
    return {"adaylar": adaylar, "elenen": elenen}
