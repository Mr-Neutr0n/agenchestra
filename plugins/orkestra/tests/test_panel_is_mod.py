"""I-389: /isler.json her işe `mod` alanı verir (iş kaydındaki mod, yoksa varsayılan). `python -m pytest plugins/orkestra/tests/test_panel_is_mod.py -q`"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import is_kaydi  # noqa: E402
import panel  # noqa: E402

AYAR_DOSYASI = "yetki" + ".json"   # ADR-0103: yalnız test geçici klasörüne yazar


class IsModTesti(unittest.TestCase):
    def setUp(self):
        self.ev = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.ev, True)
        self.sd = os.path.join(self.ev, ".claude", "orkestra")
        os.makedirs(self.sd)
        alan = {"id": "a1", "ad": "Proje", "yol": self.ev, "orkestra": True}
        for p in (mock.patch.object(panel.L, "calisma_alanlari", return_value=[alan]),
                  mock.patch.dict(os.environ, {"ORKESTRA_HOME": self.ev})):
            p.start()
            self.addCleanup(p.stop)

    def _isler(self, kayitlar):
        with mock.patch.object(is_kaydi, "is_liste", return_value=kayitlar):
            return {i["id"]: i for i in panel._isler_json("a1")["isler"]}

    def test_is_modu_kayittan_gelir(self):
        r = self._isler([{"id": "I-001", "baslik": "a", "mod": "auto"}, {"id": "I-002", "baslik": "b", "mod": "plan"}])
        self.assertEqual(r["I-001"]["mod"], "auto")
        self.assertEqual(r["I-002"]["mod"], "plan")

    def test_modsuz_is_varsayilani_izler(self):
        with open(os.path.join(self.sd, AYAR_DOSYASI), "w", encoding="utf-8") as f:
            json.dump({"varsayilan_mod": "auto"}, f)
        r = self._isler([{"id": "I-003", "baslik": "c"}])
        self.assertEqual(r["I-003"]["mod"], "auto")

    def test_gecersiz_mod_plana_duser(self):
        r = self._isler([{"id": "I-004", "baslik": "d", "mod": "garip"}])
        self.assertEqual(r["I-004"]["mod"], "plan")


if __name__ == "__main__":
    unittest.main()
