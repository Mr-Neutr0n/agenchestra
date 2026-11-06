"""ADR-0171 L1: dağıtıcı/sınıflayıcı aday listesi koddan türetilir."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import yol_dallanma as YD  # noqa: E402


class YolDallanma(unittest.TestCase):
    def test_dagitici_ve_rota_dosya_satirla_bulunur(self):
        with tempfile.TemporaryDirectory() as k:
            os.makedirs(os.path.join(k, "agent", "nodes"))
            with open(os.path.join(k, "agent", "runtime.py"), "w", encoding="utf-8") as f:
                f.write("def x():\n    pass\n\ndef dispatch_query(q):\n    return classify(q)\n\ndef classify(q):\n    return 1\n")
            with open(os.path.join(k, "agent", "nodes", "route.py"), "w", encoding="utf-8") as f:
                f.write("def route_question(s):\n    return dispatch_query(s)\n")
            with open(os.path.join(k, "agent", "bozuk.py"), "w", encoding="utf-8") as f:
                f.write("def (:\n")
            r = {(x["dosya"], x["ad"]): x for x in YD.tara(k)}
            self.assertEqual(r[("agent/runtime.py", "dispatch_query")]["satir"], 4)
            self.assertEqual(r[("agent/nodes/route.py", "route_question")]["satir"], 1)
            self.assertEqual(r[("agent/runtime.py", "dispatch_query")]["cagri"], 1)
            self.assertIn("agent/runtime.py:4 `dispatch_query`", YD.metin(k))

    def test_aday_yoksa_elle_bul_notu(self):
        with tempfile.TemporaryDirectory() as k:
            self.assertIn("Aday yok", YD.metin(k))


if __name__ == "__main__":
    unittest.main()
