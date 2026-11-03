"""Niyet defteri hook bağı (ADR-0156): mesajda yönerge, kısa onayda yok, kapalıyken yok, Stop'ta gölge kaydı."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import hook  # noqa: E402
import niyet  # noqa: E402
import niyet_defteri_kapi as NK  # noqa: E402
import ork_lib as L  # noqa: E402

UZUN = "Niyet defteri kurulsun ve close bunu okusun, ham mesaj da hiçbir yere kopyalanmasın lütfen"


class HookBagi(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.sd = os.path.join(self.t.name, "durum")
        os.makedirs(self.sd)
        p = mock.patch.object(niyet, "NIYET_YOLU", os.path.join(self.t.name, "niyet.jsonl"))
        p.start()
        self.addCleanup(p.stop)
        os.environ.pop("ORKESTRA_NIYET_DEFTERI", None)

    def baglam(self, prompt, **ek):
        cikti = []
        with mock.patch.object(hook.L, "durum_dizini", return_value=self.sd), \
                mock.patch.object(hook.L, "hook_cikti", side_effect=cikti.append), \
                mock.patch.object(hook, "asili_uyari", return_value=""), \
                mock.patch.object(hook, "_yonlendirme_ipucu", return_value=""):
            hook.user_prompt_submit({"session_id": "o1", "cwd": "C:/proje_deneme", "prompt": prompt, **ek})
        return "\n".join(c["hookSpecificOutput"]["additionalContext"] for c in cikti if c and "hookSpecificOutput" in c)

    def test_yonerge_uzun_mesajda_var_ve_300_karakteri_gecmez(self):
        b = self.baglam(UZUN)
        self.assertIn("NİYET DEFTERİ (ADR-0156)", b)
        y = NK.yonerge(self.sd, "o1-0001", UZUN)
        self.assertTrue(0 < len(y) <= 300, len(y))

    def test_kisa_onay_yonerge_almaz(self):
        self.assertNotIn("NİYET DEFTERİ", self.baglam("evet yap"))

    def test_kapali_env_yonerge_almaz(self):
        os.environ["ORKESTRA_NIYET_DEFTERI"] = "0"
        try:
            self.assertNotIn("NİYET DEFTERİ", self.baglam(UZUN))
        finally:
            del os.environ["ORKESTRA_NIYET_DEFTERI"]

    def test_alt_ajan_yonerge_almaz(self):
        self.assertNotIn("NİYET DEFTERİ", self.baglam(UZUN, agent_id="a1"))

    def test_hata_hook_u_dusurmez(self):
        with mock.patch.object(NK, "yonerge", side_effect=RuntimeError("x")):
            b = self.baglam(UZUN)  # istisna dışarı sızmaz, diğer bağlam parçaları gelir
        self.assertNotIn("NİYET DEFTERİ", b)

    def test_stop_niyetsiz_istegi_golgeye_yazar(self):
        self.baglam(UZUN)
        self.assertTrue(NK.stop_kontrol(self.sd, "o1"))
        g = [k for k in L.jsonl_oku(os.path.join(self.sd, "gunluk.jsonl")) if k.get("tur") == "kapi_golge" and k.get("kapi") == "niyet_defteri"]
        self.assertEqual(len(g), 1)


if __name__ == "__main__":
    unittest.main()
