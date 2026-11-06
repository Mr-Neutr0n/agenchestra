"""ADR-0171: yol kararı için dallanma adayları (L1: betikle türet, ajan elle yazmaz).

Python kaynağında dağıtıcı, sınıflayıcı, yönlendirici ve çözümleyici adlı fonksiyonları dosya:satır ve çağrı sayısıyla
listeler. Çıktı ADAY listesidir: ajan giriş noktasından her dallanmayı kodu okuyarak doğrular."""
from __future__ import annotations

import ast
import os
import re

ADAY = re.compile(r"dispatch|route|router|classif|siniflay|resolve|select|handler|planner|choose", re.I)
GUCLU = re.compile(r"dispatch|route|router|classif|siniflay", re.I)  # giriş dağıtımı: önce bunlar
ATLA = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox", "tests", "test"}
AZAMI_DOSYA = 3000


def _py_dosyalar(kok: str):
    n = 0
    for d, alt, adlar in os.walk(kok):
        alt[:] = [a for a in alt if a not in ATLA and not a.startswith(".")]
        for ad in adlar:
            if ad.endswith(".py") and not ad.startswith("test_"):
                n += 1
                if n > AZAMI_DOSYA:
                    return
                yield os.path.join(d, ad)


def tara(kok: str) -> list[dict]:
    """[{ad, dosya, satir, cagri}] — çağrı sayısı, adın kök altında çağrı olarak geçtiği yer sayısı."""
    tanim: list[tuple[str, str, int]] = []
    cagri: dict[str, int] = {}
    for yol in _py_dosyalar(kok):
        try:
            with open(yol, encoding="utf-8", errors="replace") as f:
                agac = ast.parse(f.read())
        except (OSError, SyntaxError, ValueError):
            continue
        goreli = os.path.relpath(yol, kok).replace(os.sep, "/")
        for dugum in ast.walk(agac):
            if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef)) and ADAY.search(dugum.name):
                tanim.append((dugum.name, goreli, dugum.lineno))
            elif isinstance(dugum, ast.Call):
                f = dugum.func
                ad = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
                if ad:
                    cagri[ad] = cagri.get(ad, 0) + 1
    out = [{"ad": a, "dosya": d, "satir": s, "cagri": cagri.get(a, 0)} for a, d, s in tanim]
    out.sort(key=lambda r: (not GUCLU.search(r["ad"]), -r["cagri"], r["dosya"], r["satir"]))
    return out


def metin(kok: str, sinir: int = 60) -> str:
    r = tara(kok)
    if not r:
        return "Aday yok; giriş noktasını elle bul (dosya:satır) ve Yol kararı bölümüne yaz."
    satirlar = [f"- {x['dosya']}:{x['satir']} `{x['ad']}` ({x['cagri']} çağrı)" for x in r[:sinir]]
    if len(r) > sinir:
        satirlar.append(f"- … {len(r) - sinir} aday daha (--sinir ile artır)")
    return "\n".join(["Dallanma adayları (ADAY listesi; giriş noktasından her dallanmayı kodu okuyarak doğrula):"] + satirlar)
