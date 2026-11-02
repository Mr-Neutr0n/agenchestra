"""I-347 P2: girdi.json skill_adaylari alanı ve kaydet sonrası taslak üretimi."""
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import perspektif as P  # noqa: E402

with open(os.path.join(KOK, "tests", "veri", "skill_kume_ornek.jsonl"), encoding="utf-8") as _f:
    ORNEK = [json.loads(s) for s in _f if s.strip()]


class GirdiTest(unittest.TestCase):
    def test_adaylar_alani_esikten_gelir(self):
        a = P._skill_adaylari(ORNEK, [])
        self.assertEqual(a["esik"], 5)
        self.assertGreaterEqual(len(a["adaylar"]), 1)
        self.assertTrue(all(c["adet"] >= 5 for c in a["adaylar"]))

    def test_mevcut_skill_isaretli_gelir(self):
        a = P._skill_adaylari(ORNEK, ["jira-story-yaz"])
        self.assertTrue(any(c["mevcut_skill"] == ["jira-story-yaz"] for c in a["adaylar"]))

    def _kur(self):
        proje = tempfile.mkdtemp()
        sd = os.path.join(proje, ".claude", "orkestra")
        os.makedirs(os.path.join(sd, "perspektif"))
        a = P._skill_adaylari(ORNEK, [])
        with open(os.path.join(sd, "perspektif", "girdi.json"), "w", encoding="utf-8") as f:
            json.dump({"skill_adaylari": a}, f)
        return sd, a

    def test_taslak_yalniz_raporun_sectigi_kume_icin(self):
        sd, a = self._kur()
        secilen = a["adaylar"][0]
        rapor = os.path.join(sd, "perspektif", "perspektif_x.md")
        with open(rapor, "w", encoding="utf-8") as f:
            f.write("## 7. Skill adayları\n- **ozel-ad** — %d kez (küme %s)\n" % (secilen["adet"], secilen["id"]))
        self.assertEqual(P._skill_taslaklari(sd, rapor), ["ozel-ad"])
        self.assertTrue(os.path.isfile(os.path.join(sd, "onerilen_skill", "ozel-ad", "SKILL.md")))
        self.assertEqual(P._skill_taslaklari(sd, rapor), [])  # ikinci kez üzerine yazmaz

    def test_rapor_kume_anmiyorsa_taslak_yok(self):
        sd, _ = self._kur()
        rapor = os.path.join(sd, "perspektif", "perspektif_y.md")
        with open(rapor, "w", encoding="utf-8") as f:
            f.write("## 7. Skill adayları\n- **serbest-ad** — 6 kez\n")
        self.assertEqual(P._skill_taslaklari(sd, rapor), [])
        self.assertFalse(os.path.exists(os.path.join(sd, "onerilen_skill")))

    def test_girdi_alani_bozuksa_kayit_bozulmaz(self):
        sd = tempfile.mkdtemp()
        self.assertEqual(P._skill_taslaklari(sd), [])


if __name__ == "__main__":
    unittest.main()
