"""orkestra komutları: `yol` — plan öncesi yol kararı yardımcıları (ADR-0171)."""
from __future__ import annotations

import os

import yol_dallanma as YD
from komutlar._ortak import hata


def cmd_yol_dallanma(a):
    kok = os.path.abspath(a.kok)
    if not os.path.isdir(kok):
        return hata(f"dizin yok: {kok}")
    print(YD.metin(kok, a.sinir))


def kaydet(alt):
    p = alt.add_parser("yol", help="plan öncesi yol kararı yardımcıları (ADR-0171)")
    p.add_argument("--yardım", action="help", help="bu yardımı gösterir")
    s = p.add_subparsers(dest="yol_komut", required=True)
    d = s.add_parser("dallanma", help="dağıtıcı/sınıflayıcı/rota adaylarını dosya:satır listeler")
    d.add_argument("kok", help="taranacak kod kökü")
    d.add_argument("--sinir", type=int, default=60)
    d.set_defaults(f=cmd_yol_dallanma)
