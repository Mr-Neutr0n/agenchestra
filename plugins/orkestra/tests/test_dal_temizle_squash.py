"""Squash ile birleşen dal kapanış temizliğinde aday olur, benzersiz içerikli dal olmaz (I-380, ADR-0161)."""
import os
import shutil
import sys
import tempfile
import time
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
sys.path.insert(0, os.path.join(KOK, "tests"))
import dal_temizle  # noqa: E402
from test_dal_temizle import commit, git  # noqa: E402


class SquashTemizleTest(unittest.TestCase):
    def setUp(self):
        self._ortam = os.environ.pop("CLAUDE_PROJECT_DIR", None)
        os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        self.k = tempfile.mkdtemp()
        self.depo = os.path.join(self.k, "depo")
        os.makedirs(self.depo)
        git(self.depo, "init", "-q", "-b", "main")
        commit(self.depo, "a")
        self.oturum = os.path.join(self.k, "oturum")
        git(self.depo, "worktree", "add", "-q", "-b", "oturum", self.oturum)
        self.sq = os.path.join(self.k, "sq")
        git(self.depo, "worktree", "add", "-q", "-b", "sq", self.sq)
        commit(self.sq, "s1")
        commit(self.sq, "s2")
        self.bz = os.path.join(self.k, "bz")
        git(self.depo, "worktree", "add", "-q", "-b", "bz", self.bz)
        commit(self.bz, "benzersiz")
        git(self.depo, "merge", "-q", "--squash", "sq")          # squash: sq main'in atası olmaz
        git(self.depo, "commit", "-q", "-m", "squash sq")
        commit(self.depo, "sonradan")                            # main sonradan ilerlemiş
        self.gelecek = time.time() + 48 * 3600

    def tearDown(self):
        if self._ortam is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = self._ortam
        shutil.rmtree(self.k, ignore_errors=True)

    def test_birlesmis_mi_iki_yonlu(self):
        self.assertNotEqual(dal_temizle._git(self.depo, "merge-base", "--is-ancestor", "sq", "main").returncode, 0)  # squash: ata değil
        self.assertTrue(dal_temizle.birlesmis_mi(self.depo, "sq"))
        self.assertFalse(dal_temizle.birlesmis_mi(self.depo, "bz"))

    def test_squash_aday_benzersiz_atlanir(self):
        s = dal_temizle.agaclar_temizle(self.oturum, "oturum", "golge", self.gelecek)
        adaylar = [os.path.basename(a["yol"]) for a in s["aday"]]
        self.assertEqual(adaylar, ["sq"], s)
        nedenler = {os.path.basename(x["yol"]): x["neden"] for x in s["atlanan"]}
        self.assertEqual(nedenler.get("bz"), "birlesmemis", s)


if __name__ == "__main__":
    unittest.main()
