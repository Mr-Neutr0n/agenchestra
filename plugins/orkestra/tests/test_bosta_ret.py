"""I-376 (ADR-0158) S2: ret simülasyonu. Beklenen madde X reddedilirse geçersizleşen küme (X'e Önce zinciriyle bağlı ya da
yazma alanı X ile kesişen maddeler) başlatılan aday kümesiyle ayrık olmalı. Bağımsız oracle: dolaylı bağımlılık kapanışı.
Veri: tohumlu üretilmiş plan kümesi (her zaman) + geçmiş gerçek planlar (ORKESTRA_GECMIS_PLAN_KOKU; yoksa gerçek plan testi atlanır).
`PYTHONUTF8=1 py -3.13 -m pytest -q plugins/orkestra/tests/test_bosta_ret.py`
"""
import glob
import os
import random
import re
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bosta as B  # noqa: E402
import paralellik as PR  # noqa: E402
from test_bosta import madde, plan  # noqa: E402


def etkilenen(md, x):
    """Oracle: x reddedilirse geçersizleşenler = x'e (dolaylı dahil) Önce ile bağlı olanlar + yazma alanı x ile kesişenler."""
    kume = {x}
    degisti = True
    while degisti:
        degisti = False
        for n, m in md.items():
            if n not in kume and any(d in kume for d, _t, _g in m["once"]):
                kume.add(n)
                degisti = True
    kes = {n for n, m in md.items() if n != x and PR.alan_kesisir(m["yazma"], md[x]["yazma"])} if x in md else set()
    return (kume | kes) - {x}


def ihlaller(metin, aday_fn=None):
    """(x, aday) çiftleri: x denetimde iken aday seçilen ama x reddedilince geçersizleşecek madde."""
    aday_fn = aday_fn or (lambda m, d: B.baslatilabilir(m, d)["adaylar"])
    md = PR.maddeler(metin)
    sonuc = []
    for x in md:
        d = {n: "bekliyor" for n in md}
        d[x] = "denetimde"
        etk = etkilenen(md, x)
        sonuc += [(x, a) for a in aday_fn(metin, d) if a in etk]
    return sonuc


def alan_tamamla(metin):
    """Geçmiş planlarda Kabul yoksa eklenir (aday kümesi boş kalıp testi anlamsızlaştırmasın)."""
    def dol(m):
        blok = m.group(0)
        for alan in ("Kabul",):
            if f"**{alan}:**" not in blok:
                blok = blok.rstrip("\n") + f"\n**{alan}:** x\n"
        return blok
    return re.sub(r"(?ms)^#{2,4}\s+P\d+\b.*?(?=^#{2,4}\s+P\d+\b|^##\s|\Z)", dol, metin)


def uret(tohum):
    r = random.Random(tohum)
    n = r.randint(3, 9)
    alanlar = ["a.py", "b.py", "scripts/*.py", "scripts/c.py", "docs/d.md", "tests/*"]
    parcalar = []
    for i in range(1, n + 1):
        once = "yok"
        if i > 1 and r.random() < 0.5:
            j = r.randint(1, i - 1)
            once = f"P{j} — " + r.choice(["Çıktı: modül", "Çakışma: alan"])
            if "Çakışma" in once:
                parcalar.append(None)
        parcalar_i = madde(i, once=once, yazma=r.choice(alanlar))
        parcalar.append(parcalar_i)
    return plan(*[p for p in parcalar if p])


class RetSimulasyonu(unittest.TestCase):
    def test_uretilmis_planlarda_gecersizleşen_aday_yok(self):
        toplam_aday = 0
        for tohum in range(300):
            metin = uret(tohum)
            self.assertEqual(ihlaller(metin), [], f"tohum={tohum}")
            md = PR.maddeler(metin)
            toplam_aday += sum(len(B.baslatilabilir(metin, {x: "denetimde"})["adaylar"]) for x in md)
        self.assertGreater(toplam_aday, 100, "test anlamsız: yeterli aday üretilmedi")

    def test_gecmis_gercek_planlar(self):
        koku = os.environ.get("ORKESTRA_GECMIS_PLAN_KOKU") or ""
        dosyalar = sorted(glob.glob(os.path.join(koku, "*", "plan.md"))) if koku else []
        planlar = []
        for d in dosyalar:
            try:
                metin = alan_tamamla(open(d, encoding="utf-8").read())
            except OSError:
                continue
            if PR.maddeler(metin) and all(m["yazma"] for m in PR.maddeler(metin).values()):
                planlar.append((d, metin))
        if not planlar:
            self.skipTest("geçmiş plan kökü yok")
        sayi_aday = 0
        for d, metin in planlar:
            self.assertEqual(ihlaller(metin), [], d)
            sayi_aday += sum(len(B.baslatilabilir(metin, {x: "denetimde"})["adaylar"]) for x in PR.maddeler(metin))
        print(f"\ngeçmiş plan: {len(planlar)}, aday toplamı: {sayi_aday}")
        if len(dosyalar) >= 30:
            self.assertGreaterEqual(len(planlar), 30)
        self.assertGreater(sayi_aday, 0)

    def test_gevsetilmis_kosul_testi_kirmizi_yapar(self):
        def gevsek(metin, d):  # Önce bağımlılığı denetlemeyen sürüm: çekirdek bunu yapmıyor, oracle yakalamalı
            md = PR.maddeler(metin)
            return [n for n in md if d.get(n, "bekliyor") == "bekliyor"]
        kirmizi = sum(len(ihlaller(uret(t), gevsek)) for t in range(50))
        self.assertGreater(kirmizi, 0)

    def test_gevsek_alan_kosulu_da_yakalanir(self):
        p = plan(madde(1, yazma="a.py"), madde(2, yazma="a.py"))
        self.assertEqual(ihlaller(p), [])
        self.assertEqual(ihlaller(p, lambda m, d: [2] if d[1] == "denetimde" else []), [(1, 2)])

    def test_cikti_ve_cakisma_bagimliligi_ayri_ayri(self):
        for tur in ("Çıktı: modül", "Çakışma: a.py"):
            p = plan(madde(1, yazma="a.py"), madde(2, once=f"P1 — {tur}", yazma="a.py" if "Çakışma" in tur else "b.py"))
            s = B.baslatilabilir(p, {1: "denetimde"})
            self.assertEqual(s["adaylar"], [], tur)
            self.assertIn("P1", s["elenen"][2])
            self.assertEqual(B.baslatilabilir(p, {1: "onaylandi"})["adaylar"], [2], tur)

    def test_dolayli_bagimlilik(self):
        p = plan(madde(1), madde(2, once="P1 — Çıktı: m", yazma="b.py"), madde(3, once="P2 — Çıktı: m", yazma="c.py"))
        self.assertEqual(B.baslatilabilir(p, {1: "denetimde"})["adaylar"], [])


if __name__ == "__main__":
    unittest.main()
