"""I-376 (ADR-0158): bekleme anı aday listesi (scripts/bosta.py). Durum duyarlı; `is dalga` statik kalır.
`PYTHONUTF8=1 py -3.13 -m pytest -q plugins/orkestra/tests/test_bosta.py`
"""
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import bosta as B  # noqa: E402


def madde(n, once="yok", yazma=None, kabul="ölçülebilir ölçüt"):
    s = f"### P{n} Başlık {n}\n**Ne:** iş\n"
    if kabul is not None:
        s += f"**Kabul:** {kabul}\n"
    s += f"**Önce:** {once}\n**Yazma alanı:** {yazma or f'dosya{n}.py'}\n"
    return s


def plan(*maddeler):
    return "# Plan\n\n## 4. Plan maddeleri\n\n" + "\n".join(maddeler) + "\n## Dalgalar\n"


def adaylar(metin, durumlar, **kw):
    return B.baslatilabilir(metin, durumlar, **kw)["adaylar"]


class AdayKosullari(unittest.TestCase):
    def test_hepsi_saglanirsa_aday(self):
        p = plan(madde(1), madde(2))
        self.assertEqual(adaylar(p, {1: "denetimde", 2: "bekliyor"}), [2])

    def test_cikti_bagimliligi_onaysiz_aday_degil(self):
        p = plan(madde(1), madde(2, once="P1 — Çıktı: modül"))
        self.assertEqual(adaylar(p, {1: "denetimde", 2: "bekliyor"}), [])

    def test_cakisma_bagimliligi_onaysiz_aday_degil(self):
        p = plan(madde(1, yazma="a.py"), madde(2, once="P1 — Çakışma: a.py", yazma="a.py"))
        self.assertEqual(adaylar(p, {1: "denetimde", 2: "bekliyor"}), [])

    def test_bagimlilik_onaylaninca_aday(self):
        p = plan(madde(1), madde(2, once="P1 — Çıktı: modül"))
        self.assertEqual(adaylar(p, {1: "onaylandi", 2: "bekliyor"}), [2])

    def test_reddedilen_bagimlilik_aday_degil(self):
        p = plan(madde(1), madde(2, once="P1 — Çıktı: modül"))
        self.assertEqual(adaylar(p, {1: "reddedildi", 2: "bekliyor"}), [])

    def test_yazma_alani_denetimdeki_ile_kesisir(self):
        p = plan(madde(1, yazma="scripts/*.py"), madde(2, yazma="scripts/a.py"))
        self.assertEqual(adaylar(p, {1: "denetimde", 2: "bekliyor"}), [])

    def test_yazma_alani_calisan_ile_kesisir(self):
        p = plan(madde(1, yazma="a.py"), madde(2, yazma="a.py"))
        self.assertEqual(adaylar(p, {1: "calisiyor", 2: "bekliyor"}), [])

    def test_yazma_alani_reddedilen_ile_kesisir(self):
        p = plan(madde(1, yazma="a.py"), madde(2, yazma="a.py"))
        self.assertEqual(adaylar(p, {1: "reddedildi", 2: "bekliyor"}), [])

    def test_onayli_madde_alani_engellemez(self):
        p = plan(madde(1, yazma="a.py"), madde(2, yazma="a.py"))
        self.assertEqual(adaylar(p, {1: "onaylandi", 2: "bekliyor"}), [2])

    def test_zaten_calisan_madde_aday_degil(self):
        p = plan(madde(1))
        self.assertEqual(adaylar(p, {1: "calisiyor"}), [])

    def test_kabul_bos_aday_degil(self):
        p = plan(madde(1), madde(2, kabul=None))
        self.assertEqual(adaylar(p, {1: "denetimde", 2: "bekliyor"}), [])

    def test_plan_denetimde_aday_yok(self):
        p = plan(madde(1), madde(2))
        self.assertEqual(adaylar(p, {1: "bekliyor", 2: "bekliyor"}, plan_denetimde=True), [])

    def test_is_onaysiz_aday_yok(self):
        p = plan(madde(1), madde(2))
        self.assertEqual(adaylar(p, {1: "denetimde", 2: "bekliyor"}, onayli=False), [])

    def test_durumsuz_madde_bekliyor_sayilir(self):
        p = plan(madde(1), madde(2))
        self.assertEqual(adaylar(p, {1: "denetimde"}), [2])

    def test_elenen_nedeni_yazilir(self):
        p = plan(madde(1), madde(2, once="P1 — Çıktı: modül"))
        s = B.baslatilabilir(p, {1: "denetimde", 2: "bekliyor"})
        self.assertIn("P1", s["elenen"][2])

    def test_iki_bagimsiz_madde_ikisi_de_aday_ve_birbirine_cakismaz(self):
        p = plan(madde(1), madde(2, yazma="x.py"), madde(3, yazma="x.py"))
        self.assertEqual(adaylar(p, {1: "denetimde"}), [2])  # P3 seçilen P2 ile kesişir


if __name__ == "__main__":
    unittest.main()
