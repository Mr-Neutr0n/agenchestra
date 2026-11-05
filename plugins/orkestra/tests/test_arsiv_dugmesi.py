"""ADR-0170: arşiv düğmesi (scripts/arsiv_dugmesi.py). Hepsi geçici durum dizininde koşar."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import arsiv_dugmesi as AD  # noqa: E402

WRAP = "mcp__ccd_turn__wrap_up"
PLAN = "mcp__ccd_turn__update_plan"


def _satir(tur, icerik, **ek):
    return json.dumps({"type": tur, "message": {"content": icerik}, **ek}, ensure_ascii=False)


def _transkript(klasor, araclar, kullanici="iş yap"):
    yol = os.path.join(klasor, "t.jsonl")
    satirlar = [_satir("user", kullanici)]
    for ad in araclar:
        satirlar.append(_satir("assistant", [{"type": "tool_use", "name": ad, "input": {}}]))
    with open(yol, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar))
    return yol


class DugmeGirdisi(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp()
        self.addCleanup(os.environ.__setitem__, "ORKESTRA_ARSIV_DUGMESI", os.environ.get("ORKESTRA_ARSIV_DUGMESI", "0"))
        os.environ["ORKESTRA_ARSIV_DUGMESI"] = "1"

    def test_is_yoksa_arsiv_eklenir(self):  # S1
        yeni = AD.dugme_girdisi(WRAP, {"recap": "Bitti."}, self.sd, "o1")
        self.assertEqual(yeni["actions"], [{"action": "archive"}])
        self.assertEqual(yeni["ask"], "Sohbet arşivlensin mi?")  # ask'siz kutu çizilmez
        self.assertEqual(yeni["recap"], "Bitti.")

    def test_ask_doluysa_degismez(self):  # S2
        self.assertIsNone(AD.dugme_girdisi(WRAP, {"recap": "x", "ask": "Karar?"}, self.sd, "o1"))

    def test_actions_varsa_degismez(self):
        self.assertIsNone(AD.dugme_girdisi(WRAP, {"recap": "x", "actions": [{"label": "Yap"}]}, self.sd, "o1"))

    def test_acik_is_varsa_degismez(self):
        with mock.patch.object(AD, "acik_is", return_value="açık kart K1"):
            self.assertIsNone(AD.dugme_girdisi(WRAP, {"recap": "x"}, self.sd, "o1"))

    def test_baska_arac_alt_ajan_ve_kapali(self):
        self.assertIsNone(AD.dugme_girdisi("Edit", {"recap": "x"}, self.sd, "o1"))
        self.assertIsNone(AD.dugme_girdisi(WRAP, {"recap": "x"}, self.sd, "o1", agent_id="a1"))
        os.environ["ORKESTRA_ARSIV_DUGMESI"] = "0"
        try:
            self.assertIsNone(AD.dugme_girdisi(WRAP, {"recap": "x"}, self.sd, "o1"))
        finally:
            os.environ["ORKESTRA_ARSIV_DUGMESI"] = "1"


class StopTetik(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp()
        self.addCleanup(os.environ.__setitem__, "ORKESTRA_ARSIV_DUGMESI", os.environ.get("ORKESTRA_ARSIV_DUGMESI", "0"))
        os.environ["ORKESTRA_ARSIV_DUGMESI"] = "1"

    def test_calisma_turu_wrap_up_siz_tetikler(self):  # S3
        t = _transkript(self.sd, [PLAN, "Edit"])
        self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1"), "plan_acik")
        t = _transkript(self.sd, ["Edit"])
        self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1"), "degisiklik")

    def test_wrap_up_varsa_tetiklemez(self):
        t = _transkript(self.sd, [PLAN, WRAP])
        self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1"), "")

    def test_acik_is_soru_ve_salt_okuma_tetiklemez(self):
        t = _transkript(self.sd, ["Edit"])
        with mock.patch.object(AD, "acik_is", return_value="iş I-1 todo'sunda 2 açık madde"):
            self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1"), "")
        self.assertEqual(AD.stop_tetik(t, "Devam edeyim mi?", self.sd, "o1"), "")
        self.assertEqual(AD.stop_tetik(_transkript(self.sd, ["Read", "Grep"]), "Cevap.", self.sd, "o1"), "")
        t = _transkript(self.sd, ["Edit", "AskUserQuestion"])
        self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1"), "")

    def test_arka_plan_alt_ajan_ve_kapali(self):
        t = _transkript(self.sd, ["Edit"])
        self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1", {"background_tasks": [1]}), "")
        self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1", {"agent_id": "a"}), "")
        os.environ["ORKESTRA_ARSIV_DUGMESI"] = "0"
        try:
            self.assertEqual(AD.stop_tetik(t, "Bitti.", self.sd, "o1"), "")
        finally:
            os.environ["ORKESTRA_ARSIV_DUGMESI"] = "1"

    def test_onceki_turun_wrap_up_i_sayilmaz(self):
        yol = os.path.join(self.sd, "t2.jsonl")
        satirlar = [_satir("user", "bir"), _satir("assistant", [{"type": "tool_use", "name": WRAP, "input": {}}]),
                    _satir("user", "iki"), _satir("assistant", [{"type": "tool_use", "name": "Edit", "input": {}}])]
        with open(yol, "w", encoding="utf-8") as f:
            f.write("\n".join(satirlar))
        self.assertEqual(AD.stop_tetik(yol, "Bitti.", self.sd, "o1"), "degisiklik")


if __name__ == "__main__":
    unittest.main()


class HookBaglantisi(unittest.TestCase):
    """P2: PreToolUse güncel girdiyi koyar; izin ask'e düşecekse reddeder; Stop block eder."""

    def setUp(self):
        import hook
        self.hook = hook
        self.sd = tempfile.mkdtemp()
        self.addCleanup(os.environ.__setitem__, "ORKESTRA_ARSIV_DUGMESI", os.environ.get("ORKESTRA_ARSIV_DUGMESI", "0"))
        os.environ["ORKESTRA_ARSIV_DUGMESI"] = "1"
        hook._GUNCEL_GIRDI = None
        hook._VARSAYILAN_IZIN = ""
        hook._IZIN_KIPI = ""

    def test_izinli_kipte_updated_input(self):
        self.hook._VARSAYILAN_IZIN = "genis"
        self.hook._arsiv_dugmesi_kapisi(WRAP, {"recap": "Bitti."}, self.sd, "o1", None)
        self.assertEqual(self.hook._GUNCEL_GIRDI["actions"], [{"action": "archive"}])
        self.assertTrue(self.hook._GUNCEL_GIRDI["ask"])

    def test_ask_e_dusen_kipte_ret(self):
        with mock.patch.object(self.hook, "reddet", side_effect=SystemExit) as r:
            with self.assertRaises(SystemExit):
                self.hook._arsiv_dugmesi_kapisi(WRAP, {"recap": "Bitti."}, self.sd, "o1", None)
        self.assertIn("archive", r.call_args[0][0])
        self.assertIsNone(self.hook._GUNCEL_GIRDI)

    def test_ask_dolu_girdi_dokunulmaz(self):
        self.hook._VARSAYILAN_IZIN = "genis"
        self.hook._arsiv_dugmesi_kapisi(WRAP, {"recap": "x", "ask": "Karar?"}, self.sd, "o1", None)
        self.assertIsNone(self.hook._GUNCEL_GIRDI)

    def test_stop_block_ve_ikinci_denemede_gecer(self):
        t = _transkript(self.sd, [PLAN, "Edit"])
        inp = {"transcript_path": t, "last_assistant_message": "Bitti."}
        with mock.patch.object(self.hook.L, "hook_cikti", side_effect=SystemExit) as c:
            with self.assertRaises(SystemExit):
                self.hook._arsiv_dugmesi_yanit(self.sd, "o1", inp)
        self.assertEqual(c.call_args[0][0]["decision"], "block")
        with mock.patch.object(self.hook.L, "hook_cikti") as c:
            self.hook._arsiv_dugmesi_yanit(self.sd, "o1", dict(inp, stop_hook_active=True))
        c.assert_not_called()
