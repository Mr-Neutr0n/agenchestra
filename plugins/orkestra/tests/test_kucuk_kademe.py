"""Küçük iş kademesi (ADR-0150, gölge): is.json `kademe: kucuk` taşıyan işte ağır plan eksikleri `kapi_golge` olarak yazılır.

Davranış değişmez: eksikler aynen döner. Kademesiz iş ve eksiksiz küçük iş günlüğe yazmaz.
"""
import json
import os
import sys
import unittest
from unittest import mock

import test_cekirdek as TC

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import is_sirasi as S  # noqa: E402

AGIR = ["P1: **Önce:** alanı yok", "P1: **Üretim noktası:** alanı yok"]


class KucukKademe(unittest.TestCase):
    def setUp(self):
        TC.Cekirdek.setUp(self)
        self._ortam = mock.patch.dict(os.environ, {"ORKESTRA_SIRA_KAPISI": "1"})
        self._ortam.start()

    def tearDown(self):
        self._ortam.stop()
        TC.Cekirdek.tearDown(self)

    def is_klasoru(self, kademe=None, ad="001-deneme"):
        k = os.path.join(self.proje, "Claude_Orkestrasyon", ad)
        os.makedirs(k)
        kayit = {"id": "I-" + ad[:3], "sira": S.SIRA_ADI}
        if kademe:
            kayit["kademe"] = kademe
        with open(os.path.join(k, "is.json"), "w", encoding="utf-8") as f:
            json.dump(kayit, f)
        return k

    def olaylar(self):
        yol = os.path.join(self.sd, "gunluk.jsonl")
        if not os.path.exists(yol):
            return []
        with open(yol, encoding="utf-8") as f:
            return [json.loads(s) for s in f if s.strip()]

    def golgeler(self):
        return [o for o in self.olaylar() if "kucuk_kademe" in json.dumps(o, ensure_ascii=False)]

    def test_kucuk_is_golge_yazar_ve_eksikleri_degistirmez(self):
        k = self.is_klasoru("kucuk")
        self.assertTrue(S.kucuk_kademe_mi(k))
        self.assertEqual(S.kucuk_kademe_golge(k, list(AGIR)), AGIR)
        self.assertEqual(len(self.golgeler()), 1)

    def test_kademesiz_is_yazmaz(self):
        k = self.is_klasoru()
        self.assertFalse(S.kucuk_kademe_mi(k))
        self.assertEqual(S.kucuk_kademe_golge(k, list(AGIR)), AGIR)
        self.assertEqual(self.golgeler(), [])

    def test_eksiksiz_kucuk_is_yazmaz(self):
        k = self.is_klasoru("kucuk")
        self.assertEqual(S.kucuk_kademe_golge(k, []), [])
        self.assertEqual(self.golgeler(), [])

    def test_baska_kademe_degeri_kucuk_degil(self):
        self.assertFalse(S.kucuk_kademe_mi(self.is_klasoru("buyuk")))

    def test_plan_eksikleri_sirasi_ve_icerigi_ayni(self):
        k = self.is_klasoru("kucuk")
        with open(os.path.join(k, "plan.md"), "w", encoding="utf-8") as f:
            f.write("# Plan\n\n## 4. Plan maddeleri\n\n### P1 x\n\n**Ne:** y\n\n")
        with mock.patch.dict(os.environ, {"ORKESTRA_SIRA_KAPISI": "1"}):
            kucuk = S.plan_eksikleri(k)
            with open(os.path.join(k, "is.json"), "w", encoding="utf-8") as f:
                json.dump({"id": "I-001", "sira": S.SIRA_ADI}, f)
            normal = S.plan_eksikleri(k)
        self.assertEqual(kucuk, normal)


if __name__ == "__main__":
    unittest.main()
