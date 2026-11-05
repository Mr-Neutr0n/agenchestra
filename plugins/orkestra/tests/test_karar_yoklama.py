"""P-056 etkilenen karar yoklaması: plan maddesinde `**Etkilenen karar:**` alanı; yalnız gölge ölçer, engellemez.
`py -3.13 -m pytest -q plugins/orkestra/tests/test_karar_yoklama.py`
"""
import json
import os
import sys
import unittest
from unittest import mock

import test_cekirdek as TC

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import is_sirasi as S  # noqa: E402

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALT = "**Alternatifler:**\n\n- Seçilen: a. Neden: b.\n- Elenen: c. Neden elendi: d.\n"


def plan(karar="**Etkilenen karar:** kuralın kapsamı\n\n", n=1):
    govde = "".join(f"### P{i} Madde\n\n**Dayanak:** MD §1\n\n{karar}{ALT}\n**Kabul:** x\n\n" for i in range(1, n + 1))
    return f"# Plan\n\n## 4. Plan maddeleri\n\n{govde}"


class EtkilenenKarar(unittest.TestCase):
    setUp = TC.Cekirdek.setUp
    tearDown = TC.Cekirdek.tearDown

    def is_klasoru(self, plan_metni, kalite=True):
        k = os.path.join(self.proje, "Claude_Orkestrasyon", "001-deneme")
        os.makedirs(k)
        with open(os.path.join(k, "is.json"), "w", encoding="utf-8") as f:
            json.dump({"id": "I-001", "sira": S.SIRA_ADI, "kalite": kalite}, f)
        with open(os.path.join(k, "plan.md"), "w", encoding="utf-8") as f:
            f.write(plan_metni)
        return k

    def ortam(self, **ek):
        return mock.patch.dict(os.environ, {"ORKESTRA_SIRA_KAPISI": "1", "ORKESTRA_BIC_KAPISI": "1", **ek})

    def test_ayar_golge(self):
        with open(os.path.join(KOK, "ayarlar", "etkilenen_karar.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["mod"], "golge")

    def test_alanli_plan_eksiksiz(self):
        with self.ortam():
            self.assertEqual(S.karar_eksikleri(self.is_klasoru(plan())), [])

    def test_alansiz_madde_bir_uyari(self):
        with self.ortam():
            e = S.karar_eksikleri(self.is_klasoru(plan(karar="")))
        self.assertEqual(len(e), 1)
        self.assertIn("P1", e[0])

    def test_bos_alan_uyarilir(self):
        with self.ortam():
            e = S.karar_eksikleri(self.is_klasoru(plan(karar="**Etkilenen karar:**\n\n")))
        self.assertEqual(len(e), 1)

    def test_kalitesiz_is_kapsam_disi(self):
        with self.ortam():
            self.assertEqual(S.karar_eksikleri(self.is_klasoru(plan(karar=""), kalite=False)), [])

    def test_alan_alternatif_sayimini_bozmaz(self):
        with self.ortam():
            k = self.is_klasoru(plan())
            self.assertEqual(S.bic_eksikleri(k)[:1] and [x for x in S.bic_eksikleri(k) if "Alternatifler" in x and "P1" in x], [])

    def test_uyari_engellemez_ve_kapi_golge_yazar(self):
        with self.ortam():
            k = self.is_klasoru(plan(karar=""))
            self.assertIsNone(S.karar_uyari(k))
        yol = os.path.join(self.sd, "gunluk.jsonl")
        with open(yol, encoding="utf-8") as f:
            kayit = [json.loads(s) for s in f if "etkilenen_karar" in s]
        self.assertEqual(len(kayit), 1)
        self.assertEqual(kayit[0]["tur"], "kapi_golge")

    def test_geriye_donuk_oran(self):
        """5 maddelik planda 2 alansız: uyarı oranı 2/5 (ölçüm biçimi)."""
        metin = plan(n=3) + "".join(f"### P{i} Madde\n\n**Dayanak:** MD §1\n\n{ALT}\n**Kabul:** x\n\n" for i in (4, 5))
        with self.ortam():
            e = S.karar_eksikleri(self.is_klasoru(metin))
        self.assertEqual(len(e), 2)

    def test_sablonlar_alani_tasir(self):
        for ad in ("plan_sirali.md", "plan_dogrulamali.md"):
            with open(os.path.join(KOK, "sablonlar", ad), encoding="utf-8") as f:
                self.assertIn("**Etkilenen karar:**", f.read(), ad)

    def test_denetci_ve_standart_alani_sorar(self):
        for yol in (("agents", "denetci.md"), ("standartlar", "best_in_class.md")):
            with open(os.path.join(KOK, *yol), encoding="utf-8") as f:
                self.assertIn("Etkilenen karar", f.read(), yol[-1])

    def test_enjeksiyon_plan_metni_alani_sayar_ve_sinir(self):
        with open(os.path.join(KOK, "ayarlar", "uretim_enjeksiyonu.json"), encoding="utf-8") as f:
            d = json.load(f)
        plan_esleme = [e for e in d["eslemeler"] if e["tur"] == "plan"][0]
        self.assertIn("Etkilenen karar", plan_esleme["metin"])
        self.assertLessEqual(len(plan_esleme["metin"]), d["metin_max"])


if __name__ == "__main__":
    unittest.main()
