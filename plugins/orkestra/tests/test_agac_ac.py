"""`orkestra agac ac` (I-380, ADR-0161): iş çalışma ağacı deponun .claude/worktrees altında, ad dalıyla açılır."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
from komutlar import agac  # noqa: E402


def git(yol, *a):
    return subprocess.run(["git", "-C", yol, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()


class AgacAcTest(unittest.TestCase):
    def setUp(self):
        self.k = os.path.realpath(tempfile.mkdtemp())
        self.depo = os.path.join(self.k, "depo")
        os.makedirs(self.depo)
        git(self.depo, "init", "-q", "-b", "main")
        with open(os.path.join(self.depo, "a.txt"), "w", encoding="utf-8") as f:
            f.write("a")
        git(self.depo, "add", ".")
        git(self.depo, "commit", "-q", "-m", "a")
        self._koku = os.environ.pop("ORKESTRA_AGAC_KOKU", None)

    def tearDown(self):
        os.environ.pop("ORKESTRA_AGAC_KOKU", None)
        if self._koku is not None:
            os.environ["ORKESTRA_AGAC_KOKU"] = self._koku
        shutil.rmtree(self.k, ignore_errors=True)

    def test_depo_icinde_ad_dalıyla_acilir(self):
        yol, dal = agac.agac_ac(self.depo, "deneme")
        self.assertEqual(os.path.realpath(yol), os.path.realpath(os.path.join(self.depo, ".claude", "worktrees", "deneme")))
        self.assertEqual(dal, "deneme")
        self.assertIn("deneme", git(self.depo, "worktree", "list"))
        self.assertEqual(git(yol, "rev-parse", "--abbrev-ref", "HEAD"), "deneme")

    def test_klasor_git_tarafindan_yok_sayilir(self):
        agac.agac_ac(self.depo, "deneme")
        self.assertEqual(git(self.depo, "status", "--porcelain"), "")

    def test_ana_depo_baska_agactan_da_ayni_kok(self):
        yol, _ = agac.agac_ac(self.depo, "bir")
        self.assertEqual(os.path.realpath(agac._ana_depo(yol)), os.path.realpath(self.depo))

    def test_gecersiz_ad_ve_tekrar_reddedilir(self):
        with self.assertRaises(ValueError):
            agac.agac_ac(self.depo, "../kacis")
        agac.agac_ac(self.depo, "iki")
        with self.assertRaises(ValueError):
            agac.agac_ac(self.depo, "iki")

    def test_ortam_degiskeni_koku_degistirir(self):
        os.environ["ORKESTRA_AGAC_KOKU"] = os.path.join(self.k, "dis")
        yol, _ = agac.agac_ac(self.depo, "uc")
        self.assertEqual(os.path.realpath(yol), os.path.realpath(os.path.join(self.k, "dis", "depo", "uc")))


if __name__ == "__main__":
    unittest.main()
