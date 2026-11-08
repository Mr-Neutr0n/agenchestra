"""I-421: bağsız oturumda yazılan yol tek net açık işle örtüşüyorsa kapı oturumu o işe bağlar (mod ihlal);
golge modda yalnız kapi_golge kaydı düşer ve ret sürer; belirsiz eşleşmede ve kapalıyken ret sürer.
Her vaka gerçek pre_tool_use hook'unu çağırır."""
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_bagsiz_kabuk_yazimi import OTURUM, _Kabuk  # noqa: E402

import hook  # noqa: E402
import is_kaydi  # noqa: E402


def _mod_yaz(sd, mod):
    with open(os.path.join(sd, hook.BAGSIZ_OTOMATIK_KAPI + ".json"), "w", encoding="utf-8") as f:
        json.dump({"mod": mod}, f)


class BagsizOtomatikBaglanma(_Kabuk):
    def yol(self, ad="rapor.md"):
        return os.path.join(self.proje, "isler", "001-fatura", ad)

    def bagli_is(self):
        return hook._bagli_is(self.sd, OTURUM)

    def test_ihlal_modunda_tek_net_eslesme_baglar(self):
        _mod_yaz(self.sd, "ihlal")
        deny, neden = self.pre("Write", self.yol())
        self.assertFalse(deny, neden)
        self.assertEqual(self.bagli_is(), self.a["id"])

    def test_golge_modunda_baglamaz_ve_kayit_duser(self):
        _mod_yaz(self.sd, "golge")
        deny, neden = self.pre("Write", self.yol())
        self.assertTrue(deny)
        self.assertIn("orkestra is devam", neden)
        self.assertIsNone(self.bagli_is())
        kayit = [k for k in self.gunluk("kapi_golge") if k.get("kapi") == hook.BAGSIZ_OTOMATIK_KAPI]
        self.assertEqual(len(kayit), 1)

    def test_belirsiz_eslesmede_ret_surer(self):
        _mod_yaz(self.sd, "ihlal")
        is_kaydi.is_ac(self.sd, "Fatura raporlama arşivi", os.path.join(self.proje, "isler", "002-fatura-arsiv"))
        deny, _ = self.pre("Write", self.yol())
        self.assertTrue(deny)
        self.assertIsNone(self.bagli_is())

    def test_eslesmeyen_yolda_ret_surer(self):
        _mod_yaz(self.sd, "ihlal")
        deny, _ = self.pre("Write", self.kod())
        self.assertTrue(deny)
        self.assertIsNone(self.bagli_is())

    def test_env_ile_kapatilinca_ret_surer(self):
        _mod_yaz(self.sd, "ihlal")
        with mock.patch.dict(os.environ, {"ORKESTRA_BAGSIZ_OTOMATIK_BAGLA": "0"}):
            deny, _ = self.pre("Write", self.yol())
        self.assertTrue(deny)
        self.assertIsNone(self.bagli_is())

    def test_net_esleme_esikleri(self):
        n = hook._bagsiz_net_esleme
        self.assertEqual(n([{"id": "I-1", "puan": 0.7}], {}), "I-1")
        self.assertIsNone(n([{"id": "I-1", "puan": 0.5}], {}))
        self.assertIsNone(n([{"id": "I-1", "puan": 0.7}, {"id": "I-2", "puan": 0.65}], {}))
        self.assertEqual(n([{"id": "I-1", "puan": 0.9}, {"id": "I-2", "puan": 0.3}], {}), "I-1")
        self.assertIsNone(n([], {}))


if __name__ == "__main__":
    unittest.main()
