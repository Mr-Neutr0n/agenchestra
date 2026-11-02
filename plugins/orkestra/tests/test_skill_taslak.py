"""I-347 P3: taslak üretici — sır/e-posta süzme, üzerine yazmama, mevcut skill atlama."""
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import skill_taslak as T  # noqa: E402

KUME = {"id": "k-1", "adet": 6, "temsil": "değişiklikleri commitle", "kokler": ["commi", "değiş"],
        "tarihler": ["2026-10-01"], "ornekler": ["commitle ve ali@firma.com'a yaz", "token=abcd1234efgh5678 ile commitle",
                                                 "postgresql://u:p@host/db commitle"]}


def kur():
    proje = tempfile.mkdtemp()
    sd = os.path.join(proje, ".claude", "orkestra")
    os.makedirs(sd)
    return proje, sd


class TaslakTest(unittest.TestCase):
    def test_sir_ve_eposta_taslaga_girmez(self):
        _, sd = kur()
        T.uret(sd, [KUME], 5)
        ad = T.slug(KUME["kokler"], KUME["ornekler"])
        for d in ("SKILL.md", "GEREKCE.md"):
            m = open(os.path.join(sd, "onerilen_skill", ad, d), encoding="utf-8").read()
            for yasak in ("ali@firma.com", "abcd1234efgh5678", "postgresql://"):
                self.assertNotIn(yasak, m)

    def test_ham_istek_metni_taslaga_girmez(self):
        _, sd = kur()
        k = dict(KUME, ornekler=["Ayşe Yılmaz için commitle, Bearer eyJabc.def sunucu 10.0.0.5 pwd=abc", "Mehmet şifresi hunter2"])
        ad = T.uret(sd, [k], 5)[0]
        for d in ("SKILL.md", "GEREKCE.md"):
            m = open(os.path.join(sd, "onerilen_skill", ad, d), encoding="utf-8").read()
            for yasak in ("Ayşe", "Yılmaz", "Bearer", "10.0.0.5", "pwd=abc", "Mehmet", "hunter2"):
                self.assertNotIn(yasak, m)

    def test_frontmatter_ad_ve_aciklama(self):
        _, sd = kur()
        ad = T.uret(sd, [KUME], 5)[0]
        m = open(os.path.join(sd, "onerilen_skill", ad, "SKILL.md"), encoding="utf-8").read()
        self.assertTrue(m.startswith(f"---\nname: {ad}\ndescription: "))
        self.assertEqual(ad, "commitle-degis")

    def test_uzerine_yazmaz(self):
        _, sd = kur()
        T.uret(sd, [KUME], 5)
        self.assertEqual(T.uret(sd, [KUME], 5), [])

    def test_devredeki_skill_atlanir(self):
        proje, sd = kur()
        os.makedirs(os.path.join(proje, ".claude", "skills", "commitle-degis"))
        self.assertEqual(T.uret(sd, [KUME], 5), [])

    def test_mevcut_skill_karsiligi_olan_kume_atlanir(self):
        _, sd = kur()
        self.assertEqual(T.uret(sd, [dict(KUME, mevcut_skill=["commit-yaz"])], 5), [])


if __name__ == "__main__":
    unittest.main()
