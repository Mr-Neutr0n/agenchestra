"""Skill taslağı üretici (I-347 P3): eşik aşan iş kümesinden LLM'siz SKILL.md + GEREKCE.md iskeleti.

Taslak `<durum dizini>/onerilen_skill/<ad>/` altına yazılır; devreye alma kullanıcının onayıyla olur (onay.py `_esitle_skill`
bu klasörü izler). Var olan taslak ya da devreye alınmış skill üzerine yazılmaz. Ham istek metni taslağa girmez (yalnız küme kökleri, sayı, tarih). LLM yalnız taslağı zenginleştirmek isterse üstüne yazar (taslak iskelet bırakır).
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_SIR = re.compile(
    r"(?i)(\b(?:sk|pk|ghp|gho|xox[bp]|AKIA)[-_][A-Za-z0-9_-]{8,}"       # anahtar önekleri
    r"|\b[A-Za-z0-9+/_-]{32,}={0,2}"                                        # uzun belirteç
    r"|(?:password|parola|şifre|secret|token|apikey|api_key|key)\s*[:=]\s*\S+"
    r"|(?:postgres(?:ql)?|mongodb(?:\+srv)?|mysql|redis|amqp)://\S+)")
_KISI = re.compile(r"([\w.+-]+@[\w-]+\.[\w.]+|(?<!\w)@\w{2,})")
_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def sirsiz(metin: str, sinir: int = 110) -> str:
    """Sır benzeri değer, e-posta ve @anma [gizli] olur; satır sonları tek boşluk; metin kısaltılır."""
    s = _KISI.sub("[gizli]", _SIR.sub("[gizli]", str(metin or "")))
    return re.sub(r"\s+", " ", s).strip()[:sinir]


def _tam_sozcuk(kok: str, ornekler: list[str]) -> str:
    """Kökle başlayan en kısa tam sözcük (örneklerden); yoksa kökün kendisi. 'commi' → 'commit'."""
    adaylar = [w for o in ornekler for w in re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", o.lower()) if w.startswith(kok)]
    return min(adaylar, key=len) if adaylar else kok


def slug(kokler: list[str], ornekler: list[str] | None = None) -> str:
    """Küme köklerinden skill adı: ascii, küçük harf, tire; en çok 3 kök (örnek verilirse tam sözcüğe genişler)."""
    parca = []
    for k in [_tam_sozcuk(k, ornekler or []) for k in kokler[:3]]:
        a = unicodedata.normalize("NFKD", k.translate(_TR)).encode("ascii", "ignore").decode().lower()
        a = re.sub(r"[^a-z0-9]+", "", a)
        if a:
            parca.append(a)
    return "-".join(parca) or "tekrar-eden-is"


def tetik_cumleleri(c: dict) -> list[str]:
    """Ham istek metni taslağa girmez (çalışan adı, parola, adres sızabilir; sırsız() bunları deterministik yakalayamaz).

    Tetik, kümenin kök sözcüklerinden ve sayılarından kurulur; ham örnekler yalnız günlükte kalır.
    """
    return [f"Kullanıcı şu sözcüklerle tekrar tekrar istiyor: {', '.join(c.get('kokler', [])[:6])}"] if c.get("kokler") else []


def skill_md(ad: str, c: dict) -> str:
    tet = tetik_cumleleri(c)
    desc = (f"Tekrar eden iş ({c['adet']} kez; anahtar sözcükler: {', '.join(c.get('kokler', [])[:5])}). "
            "Kullanıcı bu işi istediğinde kullan.")
    satirlar = ["---", f"name: {ad}", f"description: {desc}", "---", "",
                f"# {ad}", "",
                "> TASLAK: betikle üretildi (I-347). Adımları gerçek yapılan işe göre doldur, sonra devreye al.", "",
                "## Ne zaman kullanılır", ""]
    satirlar += [f"- {t}" for t in tet] or ["- (örnek yok)"]
    satirlar += ["", "## Adımlar", "", "1. (Bu işin tekrar eden adımlarını yaz.)", "",
                 "## Sınırlar", "", "- Sır değeri çıktıya yazılmaz.", ""]
    return "\n".join(satirlar)


def gerekce_md(ad: str, c: dict, esik: int) -> str:
    satirlar = [f"# {ad} — neden önerildi", "",
                f"**Küme:** {c.get('id')}", "",
                f"**Sayı:** {c['adet']} istek (eşik {esik})", "",
                f"**Tarihler:** {', '.join(c.get('tarihler', [])[:10])}", "",
                f"**Kök sözcükler:** {', '.join(c.get('kokler', []))}", ""]
    if c.get("mevcut_skill"):
        satirlar += [f"**Benzer mevcut skill:** {', '.join(c['mevcut_skill'])} (yeni skill açmadan önce bunu genişletmeyi değerlendir)", ""]
    satirlar += ["## Örnek istekler", "", "Ham istek metni sır ve kişi adı riskiyle taslağa yazılmaz; günlükte kümeye göre bakılır:",
                 f"`python scripts/skill_kume.py --json` (küme {c.get('id')})", ""]
    return "\n".join(satirlar)


def uret(sd: str, adaylar: list[dict], esik: int, adlar: dict | None = None) -> list[str]:
    """Her aday için taslak yazar; var olan taslak/skill'e dokunmaz. Yazılan skill adlarını döner.

    adlar: {küme id: skill adı} (raporun seçtiği ad); verilmezse ad köklerden türer.
    """
    proje = os.path.dirname(os.path.dirname(os.path.abspath(sd)))
    yazilan = []
    for c in adaylar:
        if c.get("mevcut_skill"):
            continue  # zaten karşılığı olan iş için yeni skill önerilmez
        ad = (adlar or {}).get(c.get("id")) or slug(c.get("kokler", []), c.get("ornekler"))
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ad):
            continue
        hedef = os.path.join(sd, "onerilen_skill", ad)
        if os.path.exists(hedef) or os.path.exists(os.path.join(proje, ".claude", "skills", ad)):
            continue
        os.makedirs(hedef)
        for dosya, icerik in (("SKILL.md", skill_md(ad, c)), ("GEREKCE.md", gerekce_md(ad, c, esik))):
            with open(os.path.join(hedef, dosya), "w", encoding="utf-8", newline="\n") as f:
                f.write(icerik)
        yazilan.append(ad)
    return yazilan


def main(argv=None) -> int:
    import ork_lib as L
    import sayac
    import skill_kume as K
    sd = L.durum_dizini(os.getcwd())
    if not sd:
        print("skill_taslak: durum dizini yok", file=sys.stderr)
        return 1
    s = K.hesapla(sd)
    y = uret(sd, s["adaylar"], sayac.ESIK)
    print(f"{len(s['adaylar'])} aday, {len(y)} taslak yazıldı" + (": " + ", ".join(y) if y else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
