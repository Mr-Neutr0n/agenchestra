"""ADR-0151: Bash sözdizimi kapısı (scripts/bash_sozdizimi.py). Elle durumlar ve gerçek geçmiş komutların tekrar oynatması.

Tekrar oynatma korpusu çalışma zamanında okunur, depoya yazılmaz: `ORKESTRA_BASH_KORPUS` (klasör) ya da varsayılan
`~/.claude/projects/*/` altındaki oturum kayıtları (*.jsonl). Bash aracı (tool_use name=Bash) komutu ile sonucu
(tool_result) eşlenir. Korpus ya da bash yoksa test atlanır ve sayılar yazılır.
`PYTHONUTF8=1 python -m pytest -q plugins/orkestra/tests/test_bash_sozdizimi.py -s`
"""
import concurrent.futures
import glob
import json
import os
import random
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import bash_sozdizimi as BS  # noqa: E402

AYAR = os.path.join(KOK, "ayarlar", "bash_sozdizimi.json")
MODUL = os.path.join(KOK, "scripts", "bash_sozdizimi.py")

DENGESIZ = ['echo "a', "echo 'a", 'echo `date', 'printf "%s\\n" "x" >> R.md && echo "y', 'if true; then echo x',
            'for i in 1 2; do echo $i', 'echo $(ls', 'x=( 1 2']
GECERLI = ['echo "a b"', "echo 'tek'", 'ls -la | head -3', 'cd /c/x && git status --short',
           'python -c "print(1)"', "cat <<'EOF'\nx 'y' \"z\"\nEOF", 'echo "C:\\Users\\x"',
           'grep -E "a|b" dosya', 'ls !(x)', '[[ -f x ]] && echo y', 'echo "$(date +%F)"']


class _Ortam(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp(prefix="ork_bs_")
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        os.environ.pop("ORKESTRA_BASH_SOZDIZIMI", None)
        BS._BASH_ONBELLEK.clear()

    def tearDown(self):
        self._env.stop()
        BS._BASH_ONBELLEK.clear()
        shutil.rmtree(self.sd, ignore_errors=True)

    def proje(self, d):
        with open(os.path.join(self.sd, BS.PROJE_DOSYA), "w", encoding="utf-8") as f:
            f.write(d if isinstance(d, str) else json.dumps(d))


def bash_var():
    return bool(BS.bash_yolu(BS.ayar_oku()))


class TestAyar(unittest.TestCase):
    def test_ayar_alanlari_ve_golge(self):
        with open(AYAR, encoding="utf-8") as f:
            a = json.load(f)
        for k in ("mod", "bash_yollari", "zaman_asimi_sn", "ret_kaliplari", "uzunluk_en_cok", "satir_esigi",
                  "uzun_betik_kaliplari", "yonerge", "ret_metni", "golge_metni", "uzun_betik_metni"):
            self.assertIn(k, a)
        self.assertEqual(a["mod"], "golge")  # P-028: yeni kapı gölgede açılır
        self.assertEqual(a["zaman_asimi_sn"], 2)
        self.assertTrue(os.path.isfile(os.path.join(KOK, a["yonerge"])))

    def test_yonerge_30_satiri_asmaz(self):
        with open(os.path.join(KOK, "standartlar", "bash_komut_yazimi.md"), encoding="utf-8") as f:
            self.assertLessEqual(len(f.read().splitlines()), 30)

    def test_modulde_kalip_sabiti_yok(self):
        import ast
        with open(MODUL, encoding="utf-8") as f:
            agac = ast.parse(f.read())
        belge = {id(n.value) for n in ast.walk(agac) if isinstance(n, ast.Expr)}  # docstring ifadeleri
        for d in ast.walk(agac):
            if isinstance(d, ast.Constant) and isinstance(d.value, str) and id(d) not in belge:
                for w in ("unexpected eof", "syntax error", "program files", "git", "python"):
                    self.assertNotIn(w, d.value.lower(), f"modülde kalıp sabiti: {d.value[:60]!r}")


@unittest.skipUnless(bash_var(), "bash bulunamadı")
class TestElle(_Ortam):
    def setUp(self):
        super().setUp()
        self.proje({"zaman_asimi_sn": 15})  # yük altında bash başlangıcı 2 sn'yi aşabilir; aşım yolu ayrı testte

    def test_dengesiz_reddedilir(self):
        for k in DENGESIZ:
            with self.subTest(k=k):
                b = BS.denetle(k, self.sd)
                self.assertIsNotNone(b, k)
                self.assertEqual(b["sinif"], "sozdizimi")

    def test_gecerli_gecer(self):
        for k in GECERLI:
            with self.subTest(k=k):
                self.assertIsNone(BS.denetle(k, self.sd), k)

    def test_crlf_gecer(self):
        self.assertIsNone(BS.denetle("if true; then\r\n  echo x\r\nfi\r\n", self.sd))

    def test_windows_yollari_gecer(self):
        for k in ['cd "C:\\Mert\\McD" && dir', "ls C:\\\\Users\\\\PC", 'python "C:\\Users\\PC\\x y\\a.py"']:
            with self.subTest(k=k):
                self.assertIsNone(BS.denetle(k, self.sd))

    def test_bos_ve_none_gecer(self):
        for k in ("", "   ", None, 12):
            self.assertIsNone(BS.denetle(k, self.sd))

    def test_komut_kosulmaz(self):
        hedef = os.path.join(self.sd, "isaret.txt").replace("\\", "/")
        self.assertIsNone(BS.denetle(f'echo "x" > "{hedef}"', self.sd))
        self.assertFalse(os.path.exists(hedef))

    def test_ret_metni_yonergeyi_ve_write_u_soyler(self):
        a = BS.ayar_oku(self.sd)
        m = BS.ret_metni(BS.denetle('echo "a', self.sd), a)
        self.assertIn("Write", m)
        self.assertIn("bash_komut_yazimi.md", m)
        self.assertIn("unexpected EOF", m)


class TestGecisYollari(_Ortam):
    def test_bash_bulunamazsa_gecer(self):
        self.proje({"bash_yollari": [], "haric_yol_kaliplari": [".*"]})
        self.assertIsNone(BS.denetle('echo "a', self.sd))

    def test_zaman_asiminda_gecer(self):
        import subprocess
        with mock.patch.object(BS, "bash_yolu", return_value="bash"), \
                mock.patch.object(BS.subprocess, "run", side_effect=subprocess.TimeoutExpired("bash", 2)):
            self.assertIsNone(BS.denetle('echo "a', self.sd))

    def test_baska_sinif_hata_gecer(self):
        class R:
            returncode = 1
            stderr = "bash: bir uyarı".encode()
        with mock.patch.object(BS, "bash_yolu", return_value="bash"), mock.patch.object(BS.subprocess, "run", return_value=R()):
            self.assertIsNone(BS.denetle('echo "a', self.sd))

    def test_ortam_degiskeni_ve_kapali(self):
        os.environ["ORKESTRA_BASH_SOZDIZIMI"] = "0"
        self.assertIsNone(BS.denetle("x" * 9000, self.sd))
        self.assertEqual(BS.mod(BS.ayar_oku(self.sd)), "kapali")
        os.environ.pop("ORKESTRA_BASH_SOZDIZIMI")
        self.proje({"mod": "kapali"})
        self.assertIsNone(BS.denetle("x" * 9000, self.sd))

    def test_bozuk_proje_ayari_varsayilana_duser(self):
        self.proje("{bozuk")
        self.assertEqual(BS.mod(BS.ayar_oku(self.sd)), "golge")

    def test_uzunluk_sinifi(self):
        a = BS.ayar_oku(self.sd)
        sinir = a["uzunluk_en_cok"]
        self.assertIsNone(BS.uzunluk_bulgusu("a" * sinir, a))
        b = BS.uzunluk_bulgusu("'" * (sinir // 4 + 1), a)  # tek tırnak kaçışla büyür
        self.assertEqual(b["sinif"], "uzunluk")


class TestUzunBetik(_Ortam):
    def test_esik_ustu_python_c_heredoc_bash_c(self):
        govde = "\n".join(f"x{i} = {i}" for i in range(25))
        for k in (f'python -c "\n{govde}\n"', f"python - <<'EOF'\n{govde}\nEOF", f"bash -c '\n{govde}\n'",
                  f'py -3.13 -I -c "\n{govde}\n"'):
            with self.subTest(k=k[:20]):
                m = BS.uzun_betik_metni(k, self.sd)
                self.assertIn("Write", m)
                self.assertIn("bash_komut_yazimi.md", m)

    def test_esik_alti_ve_betiksiz_bos(self):
        self.assertEqual(BS.uzun_betik_metni("python -c \"print(1)\"", self.sd), "")
        self.assertEqual(BS.uzun_betik_metni("\n".join(["echo x"] * 30), self.sd), "")

    def test_kapali_bos(self):
        os.environ["ORKESTRA_BASH_SOZDIZIMI"] = "0"
        self.assertEqual(BS.uzun_betik_metni("python -c \"\n" + "x\n" * 30 + "\"", self.sd), "")


# ---------------------------------------------------------------- gerçek geçmiş komutlarla tekrar oynatma

# Kabuğun kendi hatası: satır başında (çıktıdaki JSON/metin alıntısı sayılmaz) ve sonuç hata işaretli.
_KABUK_EOF = re.compile(r"^(?:/usr/bin/)?bash(?:\.exe)?: (?:eval|-c): line \d+: unexpected EOF", re.M)
_C_SINIFI = re.compile(r"^(?:/usr/bin/)?bash(?:\.exe)?: -c: line \d+: unexpected EOF", re.M)
ORNEK = 320          # üç kuralı: 0 ret / n → %95 üst sınır 3/n; 320 → %0,94 (≤ %1)


def korpus_klasorleri():
    k = os.environ.get("ORKESTRA_BASH_KORPUS")
    if k:
        return [k] if os.path.isdir(k) else []
    return [d for d in glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "*")) if os.path.isdir(d)]


def korpus_oku():
    """(başarılı komutlar, [(komut, sonuç metni)] kabuk 'unexpected EOF' sonuçlu). Yalnız bellekte tutulur."""
    basari, eof = [], []
    for kl in korpus_klasorleri():
        for yol in glob.glob(os.path.join(kl, "*.jsonl")):
            komutlar, sonuc = {}, {}
            try:
                with open(yol, encoding="utf-8", errors="replace") as f:
                    for s in f:
                        kullan = '"Bash"' in s and '"tool_use"' in s
                        if not kullan and '"tool_result"' not in s:
                            continue
                        try:
                            d = json.loads(s)
                        except ValueError:
                            continue
                        icerik = (d.get("message") or {}).get("content") if isinstance(d, dict) else None
                        if not isinstance(icerik, list):
                            continue
                        for c in icerik:
                            if not isinstance(c, dict):
                                continue
                            if c.get("type") == "tool_use" and c.get("name") == "Bash":
                                komut = (c.get("input") or {}).get("command")
                                if isinstance(komut, str):
                                    komutlar[c.get("id")] = komut
                            elif c.get("type") == "tool_result" and c.get("tool_use_id") in komutlar:
                                m = c.get("content")
                                if isinstance(m, list):
                                    m = " ".join(str(x.get("text", "")) for x in m if isinstance(x, dict))
                                sonuc[c["tool_use_id"]] = (bool(c.get("is_error")), str(m or ""))
            except OSError:
                continue
            for i, (hata, metin) in sonuc.items():
                if hata and _KABUK_EOF.search(metin):
                    eof.append((komutlar[i], metin))
                elif not hata:
                    basari.append(komutlar[i])
    return basari, eof


_KORPUS = None


def korpus():
    global _KORPUS
    if _KORPUS is None:
        _KORPUS = korpus_oku()
    return _KORPUS


def toplu_denetle(komutlar, ayar):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as h:
        return list(h.map(lambda k: BS.denetle(k, ayar=ayar), komutlar))


@unittest.skipUnless(bash_var(), "bash bulunamadı")
class TestTekrarOynatma(unittest.TestCase):
    def setUp(self):
        os.environ.pop("ORKESTRA_BASH_SOZDIZIMI", None)
        # Paralel tekrar oynatmada süre sınırı gevşetilir: ölçülen ayrıştırıcı kararıdır, yük altındaki başlangıç süresi değil.
        self.ayar = dict(BS.ayar_oku(), zaman_asimi_sn=15)
        basari, eof = korpus()
        if len(basari) < ORNEK:
            print(f"\n[tekrar oynatma] korpus yetersiz: başarılı={len(basari)} eof={len(eof)}; atlandı")
            self.skipTest("korpus yetersiz")
        self.basari, self.eof = basari, eof

    def test_basarili_komutlarda_sahte_ret_sifir(self):
        # Uzunluk sınıfı ucuzdur: bütün başarılı komutlarda sayılır.
        uzun = [k for k in self.basari if BS.uzunluk_bulgusu(BS._normal(k), self.ayar)]
        # Ayrıştırma: bash'e gerçekten giden (tetik karakterli) komutlardan sabit tohumla ORNEK örnek.
        tetik = [k for k in self.basari if re.search(self.ayar["tetik_kalibi"], k)]
        orn = random.Random(20261102).sample(tetik, min(ORNEK, len(tetik)))
        ret = [k for k, b in zip(orn, toplu_denetle(orn, self.ayar)) if b]
        print(f"\n[tekrar oynatma] başarılı={len(self.basari)} uzunluk_sahte_ret={len(uzun)} | "
              f"ayrıştırma örnek={len(orn)} sahte_ret={len(ret)} üst_sınır(3/n)={3 / max(len(orn), 1):.4f}")
        self.assertEqual(uzun, [])
        self.assertGreaterEqual(len(orn), 300)
        self.assertEqual(ret, [], [r[:120] for r in ret])

    def test_unexpected_eof_sonuclu_komutlar_reddedilir(self):
        sonuc = toplu_denetle([k for k, _ in self.eof], self.ayar)
        c_sinifi = [(k, m, b) for (k, m), b in zip(self.eof, sonuc) if _C_SINIFI.search(m)]
        eval_sinifi = [(k, m, b) for (k, m), b in zip(self.eof, sonuc) if not _C_SINIFI.search(m)]
        for k, _, b in eval_sinifi:
            if not b:
                print(f"  [eval sınıfı, yakalanmadı] {k[:100]!r}")
        yakalanan = sum(1 for b in sonuc if b)
        print(f"\n[tekrar oynatma] eof={len(self.eof)} ret={yakalanan} | -c sınıfı={len(c_sinifi)} "
              f"ret={sum(1 for *_, b in c_sinifi if b)} | eval sınıfı={len(eval_sinifi)} "
              f"ret={sum(1 for *_, b in eval_sinifi if b)}")
        self.assertGreaterEqual(len(self.eof), 3)
        # -c sınıfı: kabuğun kendi ayrıştırması ya da komut satırı sınırı; tamamı ret.
        self.assertEqual([k[:120] for k, _, b in c_sinifi if not b], [])


if __name__ == "__main__":
    unittest.main()
