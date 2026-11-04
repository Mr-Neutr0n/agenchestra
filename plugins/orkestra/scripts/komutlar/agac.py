"""orkestra komutları: agac (iş çalışma ağacı; I-380, ADR-0161). Model çağırmaz.

`orkestra agac ac AD [--taban main] [--depo YOL]`   deponun `.claude/worktrees/AD` altında AD dalıyla çalışma ağacı açar
"""
from __future__ import annotations

import os
import re

from komutlar._ortak import hata

AD_DESENI = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")


def _ana_depo(yol: str) -> str | None:
    """`yol`un git deposunun ANA çalışma ağacı kökü (başka çalışma ağacından çağrılsa da aynı kök)."""
    import ork_lib as L
    r = L.git(["rev-parse", "--path-format=absolute", "--git-common-dir"], yol)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    ortak = r.stdout.strip().replace("\\", "/").rstrip("/")
    return ortak[:-5] if ortak.endswith("/.git") else None


def agac_ac(depo: str, ad: str, taban: str = "main") -> tuple[str, str]:
    """İş çalışma ağacını açar; (yol, dal) döner. Hata durumunda ValueError."""
    import ork_lib as L
    if not AD_DESENI.match(ad):
        raise ValueError(f"ad geçersiz ({ad}): küçük harf, rakam, '.', '_' ya da '-' ile başlayıp en çok 63 karakter")
    yol, varsayilan = L.agac_yolu(depo, ad, onek="")
    if os.path.exists(yol):
        raise ValueError(f"çalışma ağacı klasörü zaten var: {yol}")
    if L.git(["rev-parse", "--verify", "--quiet", f"refs/heads/{ad}"], depo).returncode == 0:
        raise ValueError(f"{ad} dalı zaten var; başka ad seç")
    r = L.git(["rev-parse", "--verify", taban + "^{commit}"], depo)
    if r.returncode != 0:
        raise ValueError(f"taban okunamadı ({taban}): {(r.stderr or r.stdout).strip()}")
    if varsayilan:
        L._gizli_klasoru_dislat(depo)
    r = L.git(["worktree", "add", "-b", ad, yol, r.stdout.strip()], depo)
    if r.returncode != 0:
        raise ValueError(f"git worktree add başarısız: {(r.stderr or r.stdout).strip()}")
    return yol, ad


def cmd_ac(a):
    depo = _ana_depo(a.depo or os.getcwd())
    if not depo:
        hata("git deposu bulunamadı; --depo ile ver")
    try:
        yol, dal = agac_ac(depo, a.ad, a.taban)
    except ValueError as e:
        hata(str(e))
    print(f"{yol} (dal {dal})")


def kaydet(alt):
    p = alt.add_parser("agac", help="iş çalışma ağacı: deponun .claude/worktrees altında aç").add_subparsers(dest="alt", required=True)
    c = p.add_parser("ac", help="çalışma ağacı aç (yol ve dal adı tek komuttan türer)")
    c.add_argument("ad")
    c.add_argument("--taban", default="main")
    c.add_argument("--depo", default=None)
    c.set_defaults(f=cmd_ac)
