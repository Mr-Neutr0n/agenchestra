"""ADR-0169: iddia-kaynak kapısı hook entegrasyonu (hook.py _iddia_kaynak_yanit). Gölge: günlüğe yazar, engellemez."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))


class HookTesti(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp()
        self.dokum = os.path.join(self.sd, "t.jsonl")
        satirlar = [
            {"type": "user", "timestamp": "t", "message": {"content": "kaç koşu?"}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "wc -l x"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "42 x"}]}},
        ]
        with open(self.dokum, "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(s) for s in satirlar))

    def tearDown(self):
        shutil.rmtree(self.sd, ignore_errors=True)

    def _satirlar(self):
        yol = os.path.join(self.sd, "gunluk.jsonl")
        return [json.loads(s) for s in open(yol, encoding="utf-8")] if os.path.exists(yol) else []

    def test_kaynaksiz_sayi_kapi_golge_yazar(self):
        import hook
        hook._iddia_kaynak_yanit(self.sd, "o1", {"transcript_path": self.dokum,
                                                  "last_assistant_message": "Toplam 135 koşu (Ölçüm çıktısı)."})
        son = self._satirlar()[-1]
        self.assertEqual((son["tur"], son["kapi"]), ("kapi_golge", "iddia_kaynak"))
        self.assertEqual(son["bulgu_sayilari"], {"sayi_kaynaksiz": 1})

    def test_dogrulanmis_sayi_sessiz(self):
        import hook
        hook._iddia_kaynak_yanit(self.sd, "o1", {"transcript_path": self.dokum,
                                                  "last_assistant_message": "Toplam 42 koşu (Ölçüm çıktısı)."})
        self.assertEqual(self._satirlar(), [])

    def test_kapali_env_sessiz(self):
        import hook
        with mock.patch.dict(os.environ, {"ORKESTRA_KANIT_KAPISI": "0"}):
            hook._iddia_kaynak_yanit(self.sd, "o1", {"transcript_path": self.dokum,
                                                      "last_assistant_message": "Toplam 135 koşu (Ölçüm çıktısı)."})
        self.assertEqual(self._satirlar(), [])


if __name__ == "__main__":
    unittest.main()
