"""close skill'inin çıkarıcısı niyet defterini okur (ADR-0156); defter yoksa transkript çıkarımı bozulmaz."""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

AD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AD, "..", "scripts"))
import niyet_defteri as ND  # noqa: E402

spec = importlib.util.spec_from_file_location("sohbet_cikar", os.path.join(AD, "..", "skills", "close", "scripts", "sohbet_cikar.py"))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)


class Defter(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ork_closed_")
        self.yol = os.path.join(self.d, ND.DOSYA)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_guncel_durum_ve_kanit_okunur(self):
        ND.ekle(self.d, "o1", "o1-0001", "istek", "Defter kurulsun", kriter="close defterden okur")
        ND.ekle(self.d, "o1", "o1-0001", "kisit", "Ham mesaj saklanmasın")
        ND.durum_yaz(self.d, "o1", "o1-0001/1", "karsilandi", kanit="tests yeşil")
        ND.ekle(self.d, "o2", "o2-0001", "istek", "Başka sohbet")
        r = sc.defter_oku("o1", self.yol)
        self.assertEqual([(k["id"], k["durum"], k["kanit"]) for k in r],
                         [("o1-0001/1", "karsilandi", "tests yeşil"), ("o1-0001/2", "acik", None)])

    def test_defter_yoksa_bos(self):
        self.assertEqual(sc.defter_oku("o1", os.path.join(self.d, "yok.jsonl")), [])

    def test_cikar_ciktiya_niyet_defteri_ekler(self):
        ND.ekle(self.d, "o", "o-0001", "istek", "Defter kurulsun")
        kayit = os.path.join(self.d, "o.jsonl")
        with open(kayit, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "timestamp": "t1", "message": {"content": "ilk istek"}}) + "\n")
        cikti = os.path.join(self.d, "girdi.json")
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            sc.cikar(kayit, cikti, self.yol)
        veri = json.load(open(cikti, encoding="utf-8"))
        self.assertEqual([k["id"] for k in veri["niyet_defteri"]], ["o-0001/1"])
        self.assertEqual(veri["kullanici_mesaji"], 1)  # transkript yolu bozulmadı


if __name__ == "__main__":
    unittest.main()
