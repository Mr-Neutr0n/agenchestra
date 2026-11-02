"""Proje kökü bulma: iç içe `.claude/agent-memory` klasörleri kök sayılmaz (I-348).

Kök mantığı yalnız ork_lib.proje_dizini'nde yaşar; plan_dogrulama ve is_sirasi onu çağırır.
"""
from __future__ import annotations

import glob
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import ork_lib as L  # noqa: E402
import plan_dogrulama as PD  # noqa: E402
import is_sirasi as S  # noqa: E402

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")


class IcIceKokTest(unittest.TestCase):
    def setUp(self):
        self.kok = os.path.realpath(tempfile.mkdtemp())
        os.makedirs(os.path.join(self.kok, ".claude", "orkestra"))
        # RNV benzeri iç içe klasörler: yalnız alt ajan hafızası taşıyan `.claude`
        self.rnv = os.path.join(self.kok, "RNV")
        self.is_klasoru = os.path.join(self.rnv, "063-is")
        os.makedirs(os.path.join(self.rnv, ".claude", "agent-memory"))
        os.makedirs(os.path.join(self.is_klasoru, ".claude", "agent-memory"))
        with open(os.path.join(self.kok, "kanit.py"), "w", encoding="utf-8") as f:
            f.write("x = 1\n")
        self.plan = os.path.join(self.is_klasoru, "plan.md")
        with open(self.plan, "w", encoding="utf-8") as f:
            f.write("# plan\n")
        self._ortam = os.environ.pop("CLAUDE_PROJECT_DIR", None)

    def tearDown(self):
        if self._ortam is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = self._ortam
        shutil.rmtree(self.kok, ignore_errors=True)

    def test_proje_dizini_agent_memory_koku_calmaz(self):
        self.assertEqual(L.proje_dizini(self.is_klasoru, ortami_yoksay=True), self.kok)

    def test_proje_dizini_ortam_acik_yolu_ezmez(self):
        os.environ["CLAUDE_PROJECT_DIR"] = tempfile.gettempdir()
        try:
            self.assertEqual(L.proje_dizini(self.is_klasoru, ortami_yoksay=True), self.kok)
        finally:
            del os.environ["CLAUDE_PROJECT_DIR"]

    def test_proje_dizini_orkestrasiz_proje_en_yakin_claude_yedek_olur(self):
        bos = os.path.realpath(tempfile.mkdtemp())
        try:
            os.makedirs(os.path.join(bos, ".claude"))
            alt = os.path.join(bos, "a", "b")
            os.makedirs(alt)
            self.assertEqual(L.proje_dizini(alt, ortami_yoksay=True), bos)
        finally:
            shutil.rmtree(bos, ignore_errors=True)

    def test_plan_dogrulama_proje_koku_ic_ice_vaka(self):
        self.assertEqual(PD.proje_koku(self.plan), self.kok)
        kokler = PD.kokler_plan("", self.is_klasoru, PD.proje_koku(self.plan))
        self.assertIsNotNone(PD._coz("kanit.py", kokler))

    def test_is_sirasi_kok_adaylari_ic_ice_vaka(self):
        self.assertEqual(S._kok_adaylari(self.is_klasoru)[0], self.kok)

    def test_claude_yukari_cikis_dongusu_yalniz_ork_libte(self):
        sayac = {}
        for yol in glob.glob(os.path.join(SCRIPTS, "*.py")):
            with open(yol, encoding="utf-8") as f:
                n = f.read().count('os.path.isdir(os.path.join(d, ".claude"')
            if n:
                sayac[os.path.basename(yol)] = n
        self.assertEqual(sayac, {}, f"yukarı çıkış `.claude` döngüsü ork_lib.proje_dizini dışında kopyalanmış: {sayac}")


if __name__ == "__main__":
    unittest.main()
