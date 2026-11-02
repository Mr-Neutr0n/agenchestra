"""I-347 P4: rapor ayrıştırıcısı biçimden bağımsız; 'uygulandı' skill dosyası olmadan verilmez."""
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import onay  # noqa: E402

NUMARALI = "## 7. Skill adayları\n1. **commit-yaz** — 6 kez\n   ayrıntı\n2. **jira-story-yaz** — 5 kez\n"
ISARETLI = "## Skill adayları\n- **commit-yaz** — 6 kez\n* **jira-story-yaz** — 5 kez\n"
PARANTEZ = "## Skill önerileri\n1) **commit-yaz** — 6 kez\n2) **arsiv-tasi** — 5 kez\n"
KARISIK = "## Önerilen eylemler\n- hafızayı sadeleştir\n## Skill adayları\n- **a-b**\n```\n- kod içi\n```\n## Diğer\n- yok sayılır\n"


class AyrisTest(unittest.TestCase):
    def test_uc_bicim_de_skill_maddesi_verir(self):
        for metin in (NUMARALI, ISARETLI, PARANTEZ):
            m = [x for x in onay._rapor_maddeleri(metin) if x[0] == "skill"]
            self.assertEqual(len(m), 2, metin)
            self.assertEqual([x[1] for x in m], [1, 2])

    def test_skill_adi_isaretten_temizlenir(self):
        self.assertEqual(onay._skill_adi("- **commit-yaz** — 6 kez"), "commit-yaz")
        self.assertEqual(onay._skill_adi("2) **arsiv-tasi**"), "arsiv-tasi")

    def test_cit_ve_baska_bolum_maddesi_alinmaz(self):
        m = onay._rapor_maddeleri(KARISIK)
        self.assertEqual([(x[0]) for x in m], ["oneri", "skill"])

    def test_girintili_alt_madde_ust_madde_olmaz(self):
        metin = "## Skill adayları\n- **a-b** — 5 kez\n  - alt döküm 1\n  - alt döküm 2\n- **c-d**\n"
        m = onay._rapor_maddeleri(metin)
        self.assertEqual(len(m), 2)

    def test_devam_satiri_maddeye_katilir(self):
        m = [x for x in onay._rapor_maddeleri(NUMARALI) if x[1] == 1][0]
        self.assertIn("ayrıntı", m[2])


class UygulandiTest(unittest.TestCase):
    def kur(self, dosya_var):
        proje = tempfile.mkdtemp()
        sd = os.path.join(proje, ".claude", "orkestra")
        os.makedirs(os.path.join(sd, "onerilen_skill", "x-skill"))
        with open(os.path.join(sd, "onerilen_skill", "x-skill", "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: x-skill\ndescription: d\n---\ngövde\n")
        if dosya_var:
            os.makedirs(os.path.join(proje, ".claude", "skills", "x-skill"))
            with open(os.path.join(proje, ".claude", "skills", "x-skill", "SKILL.md"), "w", encoding="utf-8") as f:
                f.write("x")
        return sd

    def _onayli(self, sd):
        # skills klasöründe varsa _esitle_skill kayıt açmaz; kaydı doğrudan aç
        k = onay._yeni_kayit(sd, "skill", "Skill önerisi: x-skill", "m", None, "skill:x-skill", [], None)
        onay.karar_ver(sd, k["id"], "onay")
        return k["id"]

    def test_dosya_yoksa_uygulandi_reddedilir(self):
        sd = self.kur(False)
        i = self._onayli(sd)
        with self.assertRaises(ValueError):
            onay.uygulandi(sd, i, "yapıldı")

    def test_dosya_varsa_uygulandi_gecer(self):
        sd = self.kur(True)
        i = self._onayli(sd)
        self.assertEqual(onay.uygulandi(sd, i, "yapıldı")["durum"], "uygulandi")


if __name__ == "__main__":
    unittest.main()
