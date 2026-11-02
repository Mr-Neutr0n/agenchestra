"""I-347 P1: istek kümeleme. Etiketli örnek: tests/veri/skill_kume_ornek.jsonl (36 istek, 4 iş türü + 12 tekil; sentetik).

Eşik seçimi örneğin ilk yarısında, doğrulama ikinci yarıda yapılır (aşırı uyumu görmek için).
"""
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import skill_kume as K  # noqa: E402
import sayac  # noqa: E402

with open(os.path.join(KOK, "tests", "veri", "skill_kume_ornek.jsonl"), encoding="utf-8") as _f:
    ORNEK = [json.loads(s) for s in _f if s.strip()]


def kesinlik(satirlar, esik):
    """Aynı kümeye giren istek çiftlerinin aynı etikete sahip oranı (precision), kümelenen çift sayısı."""
    ks = K.kumele(satirlar, esik)
    by = {r["metin"][:160]: r["etiket"] for r in satirlar}
    dogru = toplam = 0
    for c in ks:
        et = [by[o] for o in c["ornekler"]]
        for i in range(len(et)):
            for j in range(i + 1, len(et)):
                toplam += 1
                dogru += et[i] == et[j]
    return (dogru / toplam if toplam else 1.0), toplam


class KumeTest(unittest.TestCase):
    def test_orneklem_yeterli(self):
        self.assertGreaterEqual(len(ORNEK), 30)

    def test_kesinlik_iki_yarida(self):
        a, b = ORNEK[:len(ORNEK) // 2], ORNEK[len(ORNEK) // 2:]
        for yari in (a, b):
            p, n = kesinlik(yari, K.BENZERLIK)
            self.assertGreaterEqual(p, 0.8)
            self.assertGreater(n, 0)

    def test_gercek_isler_adayi_olur(self):
        ks = K.kumele(ORNEK)
        adet = sorted((c["adet"] for c in ks), reverse=True)
        self.assertGreaterEqual(sum(1 for x in adet if x >= sayac.ESIK), 3)

    def test_bildirim_ve_sistem_metni_sayilmaz(self):
        r = [{"zaman": "2026-10-01T10:%02d" % i, "metin": m} for i, m in enumerate(
            ["<task-notification> arka plan görevi bitti", "<system-reminder> bağlam", "onayla", "yap"] * 3)]
        self.assertEqual(K.kumele(r), [])

    def test_mevcut_skill_isaretlenir(self):
        r = [dict(x) for x in ORNEK if x["etiket"] == "jira"]
        a = K.adaylar(K.kumele(r), 5, ["jira-story-yaz"])
        self.assertTrue(a and a[0]["mevcut_skill"] == ["jira-story-yaz"])

    def test_sayac_zit_eylem_ve_farkli_nesne_birlesmez(self):
        sd = tempfile.mkdtemp()
        sayac.artir(sd, "stok raporu çıkar")
        for m in ("stok raporu sil", "satış raporu çıkar", "müşteri raporu çıkar"):
            sayac.artir(sd, m)
        with open(os.path.join(sd, "sayac.json"), encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)), 4)

    def test_sayac_serbest_metni_en_yakina_baglar(self):
        sd = tempfile.mkdtemp()
        for m in ("değişiklikleri commitle ve özetini yaz", "değişiklikleri commitle, özetini yaz",
                  "şu değişiklikleri commitle ve özetini yaz"):
            sayac.artir(sd, sayac.anahtar(m))
        v = json.load(open(os.path.join(sd, "sayac.json"), encoding="utf-8"))
        self.assertEqual(len(v), 1)
        self.assertEqual(list(v.values())[0]["sayi"], 3)


if __name__ == "__main__":
    unittest.main()
