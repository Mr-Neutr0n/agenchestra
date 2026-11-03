"""`orkestra niyetler` komutu gerçek giriş noktasından (scripts/orkestra.py kaydı) çalışır (ADR-0156)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ORKESTRA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "orkestra.py")


class Komut(unittest.TestCase):
    def setUp(self):
        self.kok = tempfile.mkdtemp(prefix="ork_niyetler_")
        os.makedirs(os.path.join(self.kok, ".claude", "orkestra"))
        self.env = {**os.environ, "PYTHONUTF8": "1", "CLAUDE_CODE_SESSION_ID": "oturum1", "CLAUDE_PROJECT_DIR": self.kok}
        self.env.pop("ORKESTRA_NIYET_DEFTERI", None)

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)

    def calistir(self, *arg):
        return subprocess.run([sys.executable, ORKESTRA, "niyetler", *arg], cwd=self.kok, env=self.env,
                              capture_output=True, text=True, encoding="utf-8")

    def test_ekle_durum_liste_ve_rapor(self):
        r = self.calistir("ekle", "istek", "Niyet defteri kurulsun", "--istek", "oturum1-0001", "--kriter", "close defterden okur")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "oturum1-0001/1"), r.stderr)
        r = self.calistir("durum", "oturum1-0001/1", "karsilandi")
        self.assertNotEqual(r.returncode, 0)  # kanıtsız karşılandı reddedilir
        r = self.calistir("durum", "oturum1-0001/1", "karsilandi", "--kanit", "tests yeşil")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.calistir("liste", "--json")
        liste = json.loads(r.stdout)
        self.assertEqual((liste[0]["id"], liste[0]["durum"], liste[0]["kanit"]), ("oturum1-0001/1", "karsilandi", "tests yeşil"))
        r = self.calistir("liste")
        self.assertIn("toplam 1: açık 0, karşılandı 1", r.stdout)
        r = self.calistir("rapor", "--json")
        self.assertEqual((r.returncode, json.loads(r.stdout)["n"]), (0, 0))

    def test_gecersiz_tur_ve_ilgisiz_revize_reddedilir(self):
        self.assertNotEqual(self.calistir("ekle", "bilinmeyen", "x", "--istek", "oturum1-0001").returncode, 0)
        r = self.calistir("ekle", "revize", "Yeni", "--istek", "oturum1-0002", "--ilgili", "oturum1-0009/1")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
