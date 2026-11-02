"""git çağrıları süre sınırlıdır (ADR-0148): aşımda returncode 124 döner; scripts altında timeout'suz git çağrısı kalmaz."""
import ast
import glob
import os
import subprocess
import sys
import unittest
import unittest.mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import ork_lib as L  # noqa: E402


class GitZamanAsimiTest(unittest.TestCase):
    def test_asimda_124_doner(self):
        with unittest.mock.patch.object(L.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 1)):
            r = L.git(["status"], ".", timeout=1)
        self.assertEqual(r.returncode, 124)
        self.assertIn("zaman aşımı", r.stderr)

    def test_stdin_kapali_ve_sure_verilir(self):
        with unittest.mock.patch.object(L.subprocess, "run") as run:
            L.git(["status"], ".")
        kw = run.call_args.kwargs
        self.assertEqual(kw["stdin"], subprocess.DEVNULL)
        self.assertEqual(kw["timeout"], L.GIT_ZAMAN_ASIMI)

    def test_timeoutsuz_git_cagrisi_yok(self):
        kotu = []
        for f in glob.glob(os.path.join(KOK, "scripts", "**", "*.py"), recursive=True):
            try:
                agac = ast.parse(open(f, encoding="utf-8", errors="replace").read())
            except SyntaxError:
                continue
            for n in ast.walk(agac):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                        and getattr(n.func.value, "id", "") == "subprocess" and n.args
                        and isinstance(n.args[0], (ast.List, ast.Name))
                        and "git" in ast.unparse(n.args[0]).split(",")[0]
                        and "timeout" not in {k.arg for k in n.keywords}):
                    kotu.append(f"{os.path.relpath(f, KOK)}:{n.lineno}")
        self.assertEqual(kotu, [])


if __name__ == "__main__":
    unittest.main()
