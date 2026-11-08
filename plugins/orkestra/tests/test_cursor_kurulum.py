"""I-018: Cursor kurulumunun sessiz kırıkları ve host'tan bağımsız oturum kimliği.

Kök neden (08.11.2026): Orkestra Cursor Shell'inde `orkestra` komutu ve Claude'a özgü oturum değişkeni olmadan kuruluyor;
doktor bunu görmüyordu ve ölçüm Claude oturumunun PATH'iyle yapılınca 'komut var' diye yanıltıyordu.
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import cursor_kur  # noqa: E402
import doktor  # noqa: E402
import ork_lib as L  # noqa: E402


def _eklenti(kok, skill_sayisi, mcp=True):
    for i in range(skill_sayisi):
        d = os.path.join(kok, "skills", f"s{i}")
        os.makedirs(d)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: s\n---\n")
    if mcp:
        with open(os.path.join(kok, ".mcp.json"), "w", encoding="utf-8") as f:
            f.write("{}")


class OturumKimligi(unittest.TestCase):
    def test_claude_degiskeni(self):
        self.assertEqual(L.oturum_kimligi({"CLAUDE_CODE_SESSION_ID": "c1"}), "c1")

    def test_cursor_degiskeni_yedek(self):
        self.assertEqual(L.oturum_kimligi({"CURSOR_CONVERSATION_ID": "k1"}), "k1")

    def test_oncelik_ve_acik_degisken(self):
        o = {"CURSOR_CONVERSATION_ID": "k1", "CLAUDE_CODE_SESSION_ID": "c1", "ORKESTRA_OTURUM": "x"}
        self.assertEqual(L.oturum_kimligi(o), "x")
        del o["ORKESTRA_OTURUM"]
        self.assertEqual(L.oturum_kimligi(o), "c1")

    def test_bos_ve_yok(self):
        self.assertIsNone(L.oturum_kimligi({"CLAUDE_CODE_SESSION_ID": "  "}))
        self.assertIsNone(L.oturum_kimligi({}))


class Taban(unittest.TestCase):
    def setUp(self):
        self.ev = tempfile.mkdtemp(prefix="ork_ck_ev_")
        self.eklenti = tempfile.mkdtemp(prefix="ork_ck_ek_")
        self.proje = tempfile.mkdtemp(prefix="ork_ck_pr_")
        os.makedirs(os.path.join(self.ev, ".cursor"))
        _eklenti(self.eklenti, 3)
        self.bin = tempfile.mkdtemp(prefix="ork_ck_bin_")
        self.yamalar = [
            mock.patch.object(doktor.os.path, "expanduser", return_value=self.ev),
            mock.patch.object(doktor, "_EKLENTI_KOKU", self.eklenti),
        ]
        for y in self.yamalar:
            y.start()

    def tearDown(self):
        for y in self.yamalar:
            y.stop()
        for d in (self.ev, self.eklenti, self.proje, self.bin):
            shutil.rmtree(d, ignore_errors=True)

    def _kos(self, path_dizinleri):
        with mock.patch.object(doktor, "_kabuk_path_dizinleri", return_value=path_dizinleri):
            return doktor.k_cursor_kurulum(doktor.Baglam(proje=self.proje))

    def _orkestra_komutu(self):
        ad = "orkestra.cmd" if sys.platform == "win32" else "orkestra"
        yol = os.path.join(self.bin, ad)
        with open(yol, "w", encoding="utf-8") as f:
            f.write("")
        os.chmod(yol, 0o755)


class CursorKurulum(Taban):
    def test_iz_yoksa_atlandi(self):
        shutil.rmtree(os.path.join(self.ev, ".cursor"))
        self.assertEqual(self._kos([]).durum, "atlandi")

    def test_komut_path_te_yoksa_uyari(self):
        s = self._kos([self.bin])
        self.assertEqual(s.durum, "uyari")
        self.assertIn("`orkestra` komutu yok", s.mesaj)

    def test_komut_path_teyse_temiz(self):
        self._orkestra_komutu()
        self.assertEqual(self._kos([self.bin]).durum, "gecti")

    def test_bayat_yerel_kopya(self):
        self._orkestra_komutu()
        yerel = os.path.join(self.ev, ".cursor", "plugins", "local", "orkestra")
        _eklenti(yerel, 1, mcp=False)
        s = self._kos([self.bin])
        self.assertEqual(s.durum, "uyari")
        self.assertIn("1/3 skill", s.mesaj)
        self.assertIn(".mcp.json yok", s.mesaj)

    def test_guncel_yerel_kopya_temiz(self):
        self._orkestra_komutu()
        _eklenti(os.path.join(self.ev, ".cursor", "plugins", "local", "orkestra"), 3)
        self.assertEqual(self._kos([self.bin]).durum, "gecti")

    def test_cift_yukleme_izi(self):
        self._orkestra_komutu()
        _eklenti(os.path.join(self.ev, ".cursor", "plugins", "local", "orkestra"), 3)
        os.makedirs(os.path.join(self.ev, ".claude", "plugins", "cache", "pazar", "orkestra"))
        s = self._kos([self.bin])
        self.assertEqual(s.durum, "uyari")
        self.assertIn("iki kez yüklenir", s.mesaj)

    def test_kayitli_ve_onarim_var(self):
        k = [x for x in doktor.KONTROLLER if x.id == "cursor_kurulum"]
        self.assertEqual(len(k), 1)
        self.assertIsNotNone(k[0].onar)


def _yaz(yol, icerik):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        f.write(icerik)


class KopyaEsleme(Taban):
    """Yerel Cursor kopyası bayatsa doktor B sınıfı onarımla, yedek alarak yeniler; geri alınabilir."""

    def setUp(self):
        super().setUp()
        self.yedek = tempfile.mkdtemp(prefix="ork_ck_yedek_")
        self.yerel = os.path.join(self.ev, ".cursor", "plugins", "local", "orkestra")
        _eklenti(self.eklenti, 0)  # skill'ler setUp'ta var; yalnız adaptör dosyasını ekle
        _yaz(os.path.join(self.eklenti, "scripts", "cursor_hook.py"), "def kabuk_komutu_duzelt(g, c): pass\n")
        _yaz(os.path.join(self.eklenti, "tests", "t.py"), "x")  # kopyalanmaz
        _yaz(os.path.join(self.eklenti, "scripts", "__pycache__", "a.pyc"), "x")  # kopyalanmaz
        self.yamalar.append(mock.patch.object(doktor.cfg, "ev_dizini", return_value=self.yedek))
        self.yamalar[-1].start()
        self._orkestra_komutu()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.yedek, ignore_errors=True)

    def _bayat_yerel(self):
        _eklenti(self.yerel, 3)
        _yaz(os.path.join(self.yerel, "scripts", "cursor_hook.py"), "eski adaptor\n")
        _yaz(os.path.join(self.yerel, "ozel.txt"), "kullanıcı dosyası")

    def test_fark_ve_haric(self):
        self._bayat_yerel()
        eksik, degisen = cursor_kur.fark(self.eklenti, self.yerel)
        self.assertEqual(degisen, ["scripts/cursor_hook.py"])
        self.assertEqual(eksik, [])
        self.assertNotIn("tests/t.py", cursor_kur.dosyalar(self.eklenti))
        self.assertFalse(any("__pycache__" in g for g in cursor_kur.dosyalar(self.eklenti)))

    def test_ayni_skill_sayisinda_bile_adaptor_farki_yakalanir(self):
        self._bayat_yerel()
        s = self._kos([self.bin])
        self.assertEqual(s.durum, "uyari")
        self.assertIn("kaynaktan farklı", s.mesaj)

    def test_onarim_yedekler_gunceller_geri_alir(self):
        self._bayat_yerel()
        s = self._kos([self.bin])
        o = doktor.o_cursor_kurulum(doktor.Baglam(proje=self.proje), s)
        self.assertEqual(o.sinif, "B")
        self.assertIn("kabuk_komutu_duzelt", open(os.path.join(self.eklenti, "scripts", "cursor_hook.py"), encoding="utf-8").read())
        mesaj = o.uygula()
        self.assertIn("güncellendi", mesaj)
        self.assertEqual(open(os.path.join(self.yerel, "scripts", "cursor_hook.py"), encoding="utf-8").read(),
                         "def kabuk_komutu_duzelt(g, c): pass\n")
        self.assertTrue(os.path.isfile(os.path.join(self.yerel, "ozel.txt")))  # fazlalığa dokunulmaz
        self.assertEqual(self._kos([self.bin]).durum, "gecti")
        self.assertIn("geri yüklendi", doktor._geri_al_uygula(o.geri_al))
        self.assertEqual(open(os.path.join(self.yerel, "scripts", "cursor_hook.py"), encoding="utf-8").read(), "eski adaptor\n")

    def test_guncel_kopyaya_dokunmaz(self):
        self._bayat_yerel()
        cursor_kur.guncelle(self.eklenti, self.yerel, self.yedek)
        mesaj, yedek = cursor_kur.guncelle(self.eklenti, self.yerel, self.yedek)
        self.assertIsNone(yedek)
        self.assertIn("zaten güncel", mesaj)

    def test_yedek_sayisi_sinirli(self):
        for i in range(cursor_kur.YEDEK_SAYISI + 2):
            os.makedirs(os.path.join(self.yedek, f"2026010{i}-000000", "orkestra"))
        self._bayat_yerel()
        cursor_kur.guncelle(self.eklenti, self.yerel, self.yedek)
        kalan = sorted(os.listdir(self.yedek))
        self.assertEqual(len(kalan), cursor_kur.YEDEK_SAYISI)
        self.assertNotIn("20260100-000000", kalan)

    def test_baglanti_hedefe_dokunulmaz(self):
        with mock.patch.object(cursor_kur, "baglanti_mi", return_value=True):
            mesaj, yedek = cursor_kur.guncelle(self.eklenti, self.yerel, self.yedek)
        self.assertIsNone(yedek)
        self.assertIn("bağlantı", mesaj)

    def test_adaptor_yaziyorsa_path_eksigi_uyari_degil(self):
        s = self._kos([])  # PATH'te orkestra yok, kaynak adaptör komutu yazıyor
        self.assertEqual(s.durum, "gecti")

    def test_adaptor_yazmiyorsa_ya_da_kapaliysa_uyari(self):
        with mock.patch.dict(os.environ, {"ORKESTRA_CURSOR_KOMUT_YAZ": "0"}):
            self.assertEqual(self._kos([]).durum, "uyari")
        _yaz(os.path.join(self.eklenti, "scripts", "cursor_hook.py"), "eski\n")
        self.assertEqual(self._kos([]).durum, "uyari")


class BOnayi(unittest.TestCase):
    """Arka plan doktoru B sınıfı onarım bulunca sormaz ve çökmez (NUL aygıtı Windows'ta isatty() True döner)."""

    def test_eof_onay_vermemis_sayilir(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            self.assertFalse(doktor._b_onayi_sor("x"))

    def test_evet_yaniti(self):
        with mock.patch("builtins.input", return_value="e"):
            self.assertTrue(doktor._b_onayi_sor("x"))
        with mock.patch("builtins.input", return_value=""):
            self.assertFalse(doktor._b_onayi_sor("x"))

    def test_arka_plan_koşusu_sormaz(self):
        a = doktor.argparse.Namespace(cursor_sonda=False, geri_al=False, proje=None, duzelt=True, evet=False, json=False,
                                      arka_plan=True, kuru=False)
        yakala = {}
        with mock.patch.object(doktor.sys, "stdin") as g,                 mock.patch.object(doktor, "kos", side_effect=lambda *x, **k: yakala.update(k) or {"zorunlu_hata": False}),                 mock.patch.object(doktor, "metin", return_value=""):
            g.isatty.return_value = True
            doktor.calistir(a)
        self.assertIsNone(yakala["onay"])


if __name__ == "__main__":
    unittest.main()
