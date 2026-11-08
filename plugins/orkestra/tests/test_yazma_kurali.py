"""I-421: yazma niyetinde üretimden önce iskelet kuralı; bağlı worktree'de yazma kökü; niyet yoksa boş."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import yazma_kurali as Y  # noqa: E402


def _git(cwd, *a):
    subprocess.run(["git", "-c", "safe.directory=*", *a], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t"})


class YazmaKurali(unittest.TestCase):
    def test_yazma_niyetinde_iskelet_kurali(self):
        for m in ("raporu yaz", "bir analiz belgesi hazırla", "plan.md hazırla", "Özet çıkar"):
            with self.subTest(m=m):
                self.assertIn("iskelet", Y.ana_ajan_metni(m))

    def test_niyet_yoksa_bos(self):
        for m in ("testleri çalıştır", "bu hata neden oluyor", "tamam", ""):
            with self.subTest(m=m):
                self.assertEqual(Y.ana_ajan_metni(m), "")

    def test_env_ile_kapatilir(self):
        with mock.patch.dict(os.environ, {"ORKESTRA_YAZMA_KURALI": "0"}):
            self.assertEqual(Y.ana_ajan_metni("raporu yaz"), "")

    def test_bozuk_girdi_bos(self):
        self.assertEqual(Y.ana_ajan_metni(None), "")

    def test_bagli_worktree_kokunu_soyler_ana_agacta_soylemez(self):
        t = tempfile.mkdtemp(prefix="ork_wt_")
        try:
            ana = os.path.join(t, "ana")
            os.makedirs(ana)
            _git(ana, "init", "-q", "-b", "main")
            with open(os.path.join(ana, "a.txt"), "w") as f:
                f.write("x")
            _git(ana, "add", ".")
            _git(ana, "commit", "-q", "-m", "i")
            wt = os.path.join(t, "wt")
            _git(ana, "worktree", "add", "-q", wt, "-b", "dal")
            self.assertIn("bağlı worktree", Y.ana_ajan_metni("raporu yaz", wt))
            self.assertNotIn("bağlı worktree", Y.ana_ajan_metni("raporu yaz", ana))
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
