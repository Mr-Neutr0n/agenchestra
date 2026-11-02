"""ADR-0151: hook Bash dalındaki sözdizimi kapısı (hook._bash_sozdizimi_kapisi). Geçici projede koşar.
`PYTHONUTF8=1 python -m pytest -q plugins/orkestra/tests/test_hook_bash_sozdizimi.py`
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import hook  # noqa: E402
import bash_sozdizimi as BS  # noqa: E402

OTURUM = "bashsoz1234-oturum"
DENGESIZ = 'echo "kapanmayan tirnak'
UZUN = "python - <<'EOF'\n" + "\n".join(f"x{i} = {i}" for i in range(25)) + "\nEOF"


@unittest.skipUnless(BS.bash_yolu(BS.ayar_oku()), "bash bulunamadı")
class TestHookBashSozdizimi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ork_hbs_")
        self.sd = os.path.join(self.tmp, ".claude", "orkestra")
        os.makedirs(os.path.join(self.sd, "oturumlar"))
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        for k in ("ORKESTRA_BASH_SOZDIZIMI", "ORKESTRA_GENIS_TARAMA", "ORKESTRA_RUYA", "ORKESTRA_PERSPEKTIF"):
            os.environ.pop(k, None)
        os.environ["CLAUDE_PROJECT_DIR"] = self.tmp
        os.environ["ORKESTRA_SIRA_KAPISI"] = "0"
        os.environ["ORKESTRA_ONAY_KAPISI"] = "0"
        hook._BEKLEYEN_UYARI = ""
        self.ayar({"mod": "ihlal", "zaman_asimi_sn": 15})

    def tearDown(self):
        self._env.stop()
        hook._BEKLEYEN_UYARI = ""
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ayar(self, d):
        with open(os.path.join(self.sd, BS.PROJE_DOSYA), "w", encoding="utf-8") as f:
            json.dump(d, f)

    def pre(self, komut, arac="Bash"):
        g = {"tool_name": arac, "cwd": self.tmp, "session_id": OTURUM, "tool_input": {"command": komut}}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                hook.pre_tool_use(g)
            except SystemExit:
                pass
        ham = buf.getvalue().strip()
        return (json.loads(ham.splitlines()[-1]) if ham else {}).get("hookSpecificOutput", {})

    def kayitlar(self):
        yol = os.path.join(self.sd, "gunluk.jsonl")
        if not os.path.isfile(yol):
            return []
        with open(yol, encoding="utf-8") as f:
            return [g for g in (json.loads(s) for s in f if s.strip()) if g.get("kural") == "bash_sozdizimi"]

    def test_dengesiz_tirnak_reddedilir_ve_gunluge_yazilir(self):
        ho = self.pre(DENGESIZ)
        self.assertEqual(ho.get("permissionDecision"), "deny")
        self.assertIn("Write", ho.get("permissionDecisionReason", ""))
        self.assertIn("bash_komut_yazimi.md", ho.get("permissionDecisionReason", ""))
        k = self.kayitlar()
        self.assertEqual([(g["tur"], g["kapi"]) for g in k], [("kapi_ret", "bash_sozdizimi")])
        self.assertEqual(k[0]["sinif"], "sozdizimi")

    def test_powershell_aracinda_ret_yok(self):
        ho = self.pre(DENGESIZ, arac="PowerShell")
        self.assertNotEqual(ho.get("permissionDecision"), "deny")
        self.assertEqual(self.kayitlar(), [])

    def test_ortam_degiskeni_kapatir(self):
        os.environ["ORKESTRA_BASH_SOZDIZIMI"] = "0"
        self.assertNotEqual(self.pre(DENGESIZ).get("permissionDecision"), "deny")
        self.assertEqual(self.kayitlar(), [])

    def test_golge_modda_ret_yok_kapi_golge_yazilir(self):
        self.ayar({"mod": "golge", "zaman_asimi_sn": 15})
        ho = self.pre(DENGESIZ)
        self.assertNotEqual(ho.get("permissionDecision"), "deny")
        self.assertEqual([g["tur"] for g in self.kayitlar()], ["kapi_golge"])
        self.assertIn("bash_komut_yazimi.md", ho.get("additionalContext", ""))

    def test_varsayilan_mod_golge(self):
        os.remove(os.path.join(self.sd, BS.PROJE_DOSYA))
        self.assertEqual(BS.mod(BS.ayar_oku(self.sd)), "golge")

    def test_uzun_betik_yonerge_baglami(self):
        ho = self.pre(UZUN)
        self.assertNotEqual(ho.get("permissionDecision"), "deny")
        self.assertIn("Write", ho.get("additionalContext", ""))
        self.assertIn("bash_komut_yazimi.md", ho.get("additionalContext", ""))
        self.assertEqual(self.kayitlar(), [])

    def test_kisa_gecerli_komut_baglamsiz_gecer(self):
        ho = self.pre('echo "tamam"')
        self.assertNotEqual(ho.get("permissionDecision"), "deny")
        self.assertNotIn("bash_komut_yazimi.md", ho.get("additionalContext", ""))
        self.assertEqual(self.kayitlar(), [])

    def test_uzunluk_siniri_reddedilir(self):
        ho = self.pre("echo '" + "a" * 8000 + "'")
        self.assertEqual(ho.get("permissionDecision"), "deny")
        self.assertEqual([g["sinif"] for g in self.kayitlar()], ["uzunluk"])

    def test_modul_hata_atarsa_gecer(self):
        with mock.patch.object(BS, "denetle", side_effect=RuntimeError("x")):
            self.assertNotEqual(self.pre(DENGESIZ).get("permissionDecision"), "deny")


if __name__ == "__main__":
    unittest.main()
