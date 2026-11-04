"""orkestra komutları: `is bosta` — bekleme anında başlatılabilecek bağımsız plan maddeleri (ADR-0158, I-376).

Plan ve kart durumları okunur, `bosta.baslatilabilir` aday listesi üretir. Başlatma ana ajandadır; komut yalnız listeler.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import bosta_baglam as BB  # noqa: E402
from komutlar._ortak import hata, sd_gerekli  # noqa: E402
from komutlar.dalga import plan_yolu_coz  # noqa: E402

_REF = re.compile(r"^P(\d+)$")


def cmd_is_bosta(a):
    sd = sd_gerekli()
    yol, kayit = plan_yolu_coz(sd, a.hedef)
    with open(yol, encoding="utf-8") as f:
        metin = f.read()
    is_id = (kayit or {}).get("id")
    if a.gecersiz:
        m = _REF.match(a.gecersiz.strip().upper())
        if not m or not is_id:
            hata("--gecersiz P<n> ister ve iş kimliği çözülebilmeli")
        BB.gecersiz_yaz(sd, is_id, int(m.group(1)), a.neden or "")
        print(f"bosta_gecersiz yazıldı: {a.gecersiz.upper()}")
        return
    bekleyen = []
    for n in (x.strip() for x in (a.bekleyen or "").split(",") if x.strip()):
        m = _REF.match(n.upper())
        if not m:
            hata(f"--bekleyen biçimi P<n>[,P<n>]: {n}")
        bekleyen.append(int(m.group(1)))
    s = BB.hesapla(metin, kayit, BB.kart_durumlari(sd, is_id), bekleyen, a.plan_denetimde)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return
    if not s["adaylar"]:
        print("aday yok")
    else:
        print("aday: " + ", ".join(f"P{n}" for n in s["adaylar"]))
    for n, neden in sorted(s["elenen"].items()):
        print(f"  P{n} elendi: {neden}", file=sys.stderr)


def kaydet(alt):
    """`is` alt komutlarına `bosta`yı ekler (isler.kaydet'ten SONRA çağrılmalı; MODULLER sırası)."""
    is_parser = alt.choices.get("is")
    if is_parser is None:
        raise RuntimeError("bosta: `is` komutu kayıtlı değil (isler modülü önce kaydedilmeli)")
    is_alt = next(x for x in is_parser._actions if isinstance(x, argparse._SubParsersAction))
    d = is_alt.add_parser("bosta", help="bekleme anında başlatılabilecek bağımsız plan maddelerini listeler (ADR-0158)")
    d.add_argument("--yardım", action="help", help="bu yardımı gösterir")
    d.add_argument("hedef", help="iş kimliği (I-nnn), iş klasörü ya da plan.md yolu")
    d.add_argument("--bekleyen", metavar="P1,P2", help="şu an beklenen maddeler (kartı olmasa da denetimde sayılır)")
    d.add_argument("--plan-denetimde", dest="plan_denetimde", action="store_true", help="plan denetimde: aday verilmez")
    d.add_argument("--gecersiz", metavar="P<n>", help="başlatılmış bağımsız maddenin sonradan geçersizleştiğini günlüğe yazar (bosta_gecersiz)")
    d.add_argument("--neden", help="--gecersiz ile birlikte: geçersizleşme nedeni")
    d.add_argument("--json", action="store_true", help="çıktıyı JSON verir")
    d.set_defaults(f=cmd_is_bosta)
