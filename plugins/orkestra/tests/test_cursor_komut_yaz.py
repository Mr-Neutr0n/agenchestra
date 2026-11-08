"""I-018 / ADR-0172: Cursor Shell'inde `orkestra` PATH'te olmadığından preToolUse komutu eklentinin CLI betiğine açık yolla yazar."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import cursor_hook as C  # noqa: E402

ON = 'python "X/orkestra.py"'


class YenidenYaz(unittest.TestCase):
    def y(self, komut):
        return C.komutu_yeniden_yaz(komut, ON)

    def test_basit(self):
        self.assertEqual(self.y("orkestra is liste"), ON + " is liste")

    def test_tek_sozcuk(self):
        self.assertEqual(self.y("orkestra"), ON)

    def test_zincir_her_komut_konumu(self):
        self.assertEqual(self.y("orkestra a; orkestra b && orkestra c | orkestra d"),
                         f"{ON} a; {ON} b && {ON} c | {ON} d")

    def test_cagri_operatoru_ve_parantez(self):
        self.assertEqual(self.y("& orkestra x"), f"& {ON} x")
        self.assertEqual(self.y("(orkestra x)"), f"({ON} x)")

    def test_tirnak_icine_dokunmaz(self):
        for k in ('echo "orkestra x"', "echo 'a; orkestra b'", 'git commit -m "fix; orkestra y"'):
            self.assertEqual(self.y(k), k)

    def test_argumana_ve_benzer_sozcuge_dokunmaz(self):
        for k in ("ls orkestra", "xorkestra a", "orkestra.cmd a", "orkestrax a", "python scripts/orkestra.py a", "cat orkestra/README.md"):
            self.assertEqual(self.y(k), k)

    def test_kacisli_tirnak(self):
        k = r'echo "a \" ; orkestra b" ; orkestra c'
        self.assertEqual(self.y(k), r'echo "a \" ; orkestra b" ; ' + ON + " c")

    def test_satir_sonu(self):
        self.assertEqual(self.y("echo a\norkestra b"), "echo a\n" + ON + " b")


class Duzelt(unittest.TestCase):
    def test_hook_cikti_yoksa_orijinal_komut_yazilir(self):
        g = {"tool_name": "Shell", "tool_input": {"command": "orkestra kart liste", "cwd": "C:/x"}}
        o = C.kabuk_komutu_duzelt(g, {})
        self.assertTrue(o["updated_input"]["command"].endswith(" kart liste"))
        self.assertIn("orkestra.py", o["updated_input"]["command"])
        self.assertEqual(o["updated_input"]["cwd"], "C:/x")
        self.assertNotIn("permission", o)  # politikaya karışmaz: yalnız komut yolu değişir

    def test_hook_updated_input_uzerine_yazilir(self):
        g = {"tool_name": "Shell", "tool_input": {"command": "orkestra is ac x"}}
        cikti = {"permission": "allow", "updated_input": {"command": "orkestra is ac x --ajan-id ana --ajan-tipi ana"}}
        o = C.kabuk_komutu_duzelt(g, cikti)
        self.assertTrue(o["updated_input"]["command"].endswith("is ac x --ajan-id ana --ajan-tipi ana"))
        self.assertIn("orkestra.py", o["updated_input"]["command"])
        self.assertEqual(o["permission"], "allow")

    def test_red_edilene_dokunmaz(self):
        g = {"tool_name": "Shell", "tool_input": {"command": "orkestra x"}}
        cikti = {"permission": "deny", "user_message": "n"}
        self.assertEqual(C.kabuk_komutu_duzelt(g, cikti), cikti)

    def test_shell_disi_arac_ve_orkestrasiz_komut(self):
        self.assertEqual(C.kabuk_komutu_duzelt({"tool_name": "Write", "tool_input": {"command": "orkestra x"}}, {}), {})
        self.assertEqual(C.kabuk_komutu_duzelt({"tool_name": "Shell", "tool_input": {"command": "git status"}}, {}), {})

    def test_kapatma_degiskeni(self):
        g = {"tool_name": "Shell", "tool_input": {"command": "orkestra x"}}
        with mock.patch.dict(os.environ, {"ORKESTRA_CURSOR_KOMUT_YAZ": "0"}):
            self.assertEqual(C.kabuk_komutu_duzelt(g, {}), {})

    def test_cli_onegi_betik_var_ve_ileri_bolu(self):
        onek = C.cli_onegi()
        self.assertTrue(onek.startswith('python "') and onek.endswith('orkestra.py"'))
        self.assertNotIn("\\", onek)
        yol = onek[len('python "'):-1]
        self.assertTrue(os.path.isfile(yol), yol)


class UctanUca(unittest.TestCase):
    """calistir(): sahte hook.py `--ajan-id` ekleyip allow döner; adaptör çıktısı komutu açık yolla taşır."""

    def test_calistir(self):
        with tempfile.TemporaryDirectory() as d:
            sahte = os.path.join(d, "hook.py")
            with open(sahte, "w", encoding="utf-8") as f:
                f.write("import sys,json\n"
                        "g=json.loads(sys.stdin.read())\n"
                        "ti=dict(g['tool_input']); ti['command']+=' --ajan-id ana --ajan-tipi ana'\n"
                        "print(json.dumps({'hookSpecificOutput':{'permissionDecision':'allow','updatedInput':ti}}))\n")
            ham = json.dumps({"tool_name": "Shell", "tool_input": {"command": "orkestra niyetler goster"},
                              "workspace_roots": [d]}).encode()
            with mock.patch.dict(os.environ, {"ORKESTRA_CURSOR_HOOK_PY": sahte}):
                metin, kod, _hata = C.calistir("preToolUse", ham)
            o = json.loads(metin)
            self.assertEqual(kod, 0)
            self.assertEqual(o["permission"], "allow")
            self.assertTrue(o["updated_input"]["command"].startswith('python "'))
            self.assertTrue(o["updated_input"]["command"].endswith("niyetler goster --ajan-id ana --ajan-tipi ana"))


class Tekil(unittest.TestCase):
    """Aynı olayı kardeş Orkestra kopyaları birlikte alınca hook.py bir kez koşar, hepsi aynı çıktıyı yazar."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ork_tekil_")
        self.yama = mock.patch.dict(os.environ, {"ORKESTRA_CURSOR_TEKIL_DIZIN": self.d})
        self.yama.start()
        self.sayac = []

    def tearDown(self):
        self.yama.stop()
        import shutil
        shutil.rmtree(self.d, ignore_errors=True)

    def _fn(self, olay, ham):
        self.sayac.append(1)
        return '{"permission":"allow"}', 0, "uyari"

    HAM = json.dumps({"tool_name": "Shell", "tool_input": {"command": "orkestra x"}}).encode()

    def test_ikinci_kopya_calistirmaz_ayni_cikti(self):
        a = C.tekil("preToolUse", self.HAM, self._fn)
        b = C.tekil("preToolUse", self.HAM, self._fn)
        self.assertEqual(len(self.sayac), 1)
        self.assertEqual(a[:2], b[:2])
        self.assertEqual(b[2], "")

    def test_farkli_yuk_ayri_calisir(self):
        C.tekil("preToolUse", self.HAM, self._fn)
        C.tekil("preToolUse", self.HAM.replace(b"x", b"y"), self._fn)
        self.assertEqual(len(self.sayac), 2)

    def test_eski_kilit_yeni_olay_sayilir(self):
        C.tekil("preToolUse", self.HAM, self._fn)
        for ad in os.listdir(self.d):
            yol = os.path.join(self.d, ad)
            os.utime(yol, (1, 1))
        C.tekil("preToolUse", self.HAM, self._fn)
        self.assertEqual(len(self.sayac), 2)

    def test_atlanan_olay_kilitsiz(self):
        ham = json.dumps({"tool_name": "Read"}).encode()
        C.tekil("preToolUse", ham, self._fn)
        C.tekil("preToolUse", ham, self._fn)
        self.assertEqual(len(self.sayac), 2)

    def test_kapatma_degiskeni(self):
        with mock.patch.dict(os.environ, {"ORKESTRA_CURSOR_TEKIL": "0"}):
            C.tekil("preToolUse", self.HAM, self._fn)
            C.tekil("preToolUse", self.HAM, self._fn)
        self.assertEqual(len(self.sayac), 2)

    def test_sahip_hata_verirse_kardes_beklemeden_calisir(self):
        def kotu(olay, ham):
            raise RuntimeError("x")
        with self.assertRaises(RuntimeError):
            C.tekil("preToolUse", self.HAM, kotu)
        C.tekil("preToolUse", self.HAM, self._fn)
        self.assertEqual(len(self.sayac), 1)

    def test_eszamanli_surecler_tek_calisir(self):
        import subprocess
        sayac = os.path.join(self.d, "sayac.txt")
        kod = ("import sys,time,json;sys.path.insert(0,%r);import cursor_hook as C\n"
               "def f(o,h):\n open(%r,'a').write('1');time.sleep(0.4);return '{}',0,''\n"
               "print(C.tekil('preToolUse',sys.stdin.buffer.read(),f)[0])\n") % (os.path.join(KOK, "scripts"), sayac)
        ps = [subprocess.Popen([sys.executable, "-c", kod], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               env=dict(os.environ)) for _ in range(3)]
        for p in ps:
            p.stdin.write(self.HAM)
            p.stdin.close()
        cikis = [p.stdout.read().strip() for p in ps]
        for p in ps:
            p.wait()
        self.assertEqual(open(sayac).read(), "1")
        self.assertEqual(cikis, [b"{}"] * 3)


if __name__ == "__main__":
    unittest.main()
