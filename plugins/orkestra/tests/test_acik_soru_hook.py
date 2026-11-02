"""P-053 / P2: soru yakalama, kapama ve bağlam satırı (hook yardımcıları + hook.py bağlantısı)."""
import os
import subprocess
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_onay import Temel, onay  # noqa: E402
import acik_soru  # noqa: E402

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
EKRAN = {"questions": [{"question": "Kurayım mı?", "options": [{"label": "Kur"}, {"label": "Önce liste"}]}]}


class TestAcikSoruHook(Temel):
    def test_askuserquestion_yakalanir(self):
        self.assertEqual(acik_soru.yakala(self.sd, "AskUserQuestion", EKRAN, "o1"), 1)
        k = onay.acik_sorular(self.sd, "o1")[0]
        self.assertEqual(k["secenekler"], ["Kur", "Önce liste"])

    def test_wrap_up_yalniz_dolu_ask(self):
        self.assertEqual(acik_soru.yakala(self.sd, "wrap_up", {"recap": "x"}, "o1"), 0)
        self.assertEqual(acik_soru.yakala(self.sd, "mcp__ccd_turn__wrap_up",
                                          {"ask": "Push edeyim mi?", "actions": [{"label": "Push"}]}, "o1"), 1)

    def test_alt_ajan_ve_auto_yakalamaz(self):
        self.assertEqual(acik_soru.yakala(self.sd, "AskUserQuestion", EKRAN, "o1", agent_id="a1"), 0)
        with mock.patch("izin_politikasi._auto_modu", return_value=True):
            self.assertEqual(acik_soru.yakala(self.sd, "AskUserQuestion", EKRAN, "o1"), 0)
        self.assertEqual(onay.acik_sorular(self.sd), [])

    def test_ekran_yaniti_kapatir_iptal_kapatmaz(self):
        acik_soru.yakala(self.sd, "AskUserQuestion", EKRAN, "o1")
        self.assertEqual(acik_soru.ekran_yaniti(self.sd, EKRAN, {"answers": {}}, "o1"), 0)
        self.assertEqual(len(onay.acik_sorular(self.sd)), 1)
        self.assertEqual(acik_soru.ekran_yaniti(self.sd, EKRAN, {"answers": {"Kurayım mı?": "Kur"}}, "o1"), 1)
        self.assertEqual(onay.acik_sorular(self.sd), [])

    def test_dugme_mesaji_kapatir(self):
        acik_soru.yakala(self.sd, "wrap_up", {"ask": "Push edeyim mi?", "actions": [{"label": "Push et"}]}, "o1")
        self.assertEqual(acik_soru.mesaj_yaniti(self.sd, "o1", "baska bir sey"), 0)
        self.assertEqual(acik_soru.mesaj_yaniti(self.sd, "o1", "Push et"), 1)
        self.assertEqual(onay.acik_sorular(self.sd), [])

    def test_metin_sorusu(self):
        y = "Sınıf listesi hazır. Kurmaya başlayayım mı, yoksa önce listeyi görelim mi?"
        self.assertTrue(acik_soru.metin_kaydet(self.sd, y, "o1"))
        self.assertEqual(onay.acik_sorular(self.sd)[0]["kaynak"], "metin")
        self.assertFalse(acik_soru.metin_kaydet(self.sd, "Bitti.", "o1"))

    def test_kapali_ortam(self):
        with mock.patch.dict(os.environ, {"ORKESTRA_ACIK_SORU": "0"}):
            self.assertEqual(acik_soru.yakala(self.sd, "AskUserQuestion", EKRAN, "o1"), 0)

    def test_acik_soru_yokken_baglam_eki_sifir(self):
        self.assertEqual(onay.acik_soru_satiri(self.sd, "o1"), "")

    def test_hook_baglantisi_var(self):
        h = open(os.path.join(SCRIPTS, "hook.py"), encoding="utf-8").read()
        for parca in ("acik_soru.yakala(", "acik_soru.ekran_yaniti(", "acik_soru.mesaj_yaniti(", "acik_soru.metin_kaydet("):
            self.assertIn(parca, h)

    def test_cli_soru_komutlari(self):
        a = onay.soru_ac(self.sd, "CLI sorusu?", oturum="o1")
        env = dict(os.environ, PYTHONUTF8="1")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "orkestra.py"), "onay", "soru-liste"],
                           cwd=self.proje, capture_output=True, text=True, env=env, encoding="utf-8")
        self.assertIn(a["id"], r.stdout, r.stderr)
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "orkestra.py"), "onay", "soru-kapat", a["id"]],
                           cwd=self.proje, capture_output=True, text=True, env=env, encoding="utf-8")
        self.assertIn("iptal", r.stdout, r.stderr)


if __name__ == "__main__":
    unittest.main()
