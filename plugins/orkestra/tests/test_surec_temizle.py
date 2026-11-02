"""Yetim süreç temizliği (ADR-0148): yalnız ebeveyni ölü + eşikten eski + izinli süreç aday olur; bakım temizliği kilitten bağımsız başlar."""
import os
import sys
import tempfile
import unittest
import unittest.mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import oturum_bakim  # noqa: E402
import surec_temizle as T  # noqa: E402

AYAR = {"git_esik_sn": 3600, "python_esik_sn": 7200, "python_betikler": ["mcp_kimlik.py", "oturum_bakim.py"]}
SIMDI = 1_000_000.0


def s(pid, ppid, ad, yas, cmd=""):
    return {"pid": pid, "ppid": ppid, "ad": ad, "t": SIMDI - yas, "cmd": cmd}


class AdayTest(unittest.TestCase):
    def aday(self, liste):
        return {a["pid"] for a in T.adaylar(liste, SIMDI, AYAR, kendi=0)}

    def test_yetim_eski_git_aday(self):
        self.assertEqual(self.aday([s(10, 999, "git.exe", 4000)]), {10})

    def test_canli_ebeveynli_git_degil(self):
        self.assertEqual(self.aday([s(1, 0, "claude.exe", 9000), s(10, 1, "git.exe", 4000)]), set())

    def test_esik_alti_git_degil(self):
        self.assertEqual(self.aday([s(10, 999, "git.exe", 600)]), set())

    def test_pid_yeniden_kullanimi_yetim_sayilir(self):
        # ebeveyn kaydı çocuktan SONRA doğmuş: PID başka sürece geçmiş
        self.assertEqual(self.aday([s(10, 1, "git.exe", 4000), s(1, 0, "x.exe", 100)]), {10})

    def test_izinli_betik_aday_panel_degil(self):
        liste = [s(20, 999, "python.exe", 9000, r"python C:\x\scripts\mcp_kimlik.py playwright"),
                 s(21, 999, "pythonw.exe", 9000, r'"pythonw.exe" "C:\x\scripts\panel.py" _kos 8765')]
        self.assertEqual(self.aday(liste), {20})

    def test_python_esik_alti_degil(self):
        self.assertEqual(self.aday([s(20, 999, "python.exe", 600, "python mcp_kimlik.py")]), set())

    def test_baska_surec_adi_degil(self):
        self.assertEqual(self.aday([s(30, 999, "node.exe", 99999)]), set())

    def test_kendi_pid_degil(self):
        self.assertEqual({a["pid"] for a in T.adaylar([s(10, 999, "git.exe", 4000)], SIMDI, AYAR, kendi=10)}, set())


class TemizleTest(unittest.TestCase):
    def test_golge_oldurmez_uygula_oldurur(self):
        liste = [s(10, 999, "git.exe", 9000)]
        with unittest.mock.patch.object(T, "listele", return_value=liste), \
                unittest.mock.patch.object(T, "ayar_oku", return_value={**T._VARSAYILAN}), \
                unittest.mock.patch.object(T, "oldur", return_value=True) as o, \
                unittest.mock.patch("time.time", return_value=SIMDI):
            self.assertEqual(T.temizle(None, "golge")["oldurulen"], 0)
            o.assert_not_called()
            self.assertEqual(T.temizle(None, "uygula")["oldurulen"], 1)

    def test_kapatma_ortam_degiskeni(self):
        with unittest.mock.patch.dict(os.environ, {"ORKESTRA_SUREC_TEMIZLE": "0"}):
            self.assertIsNone(T.temizle(None, "uygula"))


class BakimBagimsizTest(unittest.TestCase):
    def test_temizle_bakim_kilidi_tutulurken_de_baslar(self):
        with tempfile.TemporaryDirectory() as sd, \
                unittest.mock.patch.object(oturum_bakim.subprocess, "Popen") as p, \
                unittest.mock.patch.object(oturum_bakim.L, "kilit"):
            oturum_bakim.L.kilit.return_value.__enter__ = lambda *_: None
            oturum_bakim.L.kilit.return_value.__exit__ = lambda *_: False
            self.assertTrue(oturum_bakim._temizle_baslat(sd))
            self.assertIn("surec_temizle.py", " ".join(p.call_args[0][0]))
            self.assertFalse(oturum_bakim._temizle_baslat(sd))  # aralık dolmadan ikinci kez başlamaz


if __name__ == "__main__":
    unittest.main()
