"""ADR-0153 (P-045): yapamam kanıt kapısı (scripts/yapamam_kaniti.py, hook.py _yapamam_yanit). Gölge: yalnız ölçer.
`python -m pytest -q plugins/orkestra/tests/test_yapamam_kaniti.py`
Derlem olcum_yapamam_20261102.md olaylarından türetilen yapay metinlerdir (mekanizma testi, kalibrasyon sayılır); gerçek
doğruluk gölge penceredeki canlı tetiklerle ölçülür (ayarda gecis_esigi).
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import yapamam_kaniti as Y  # noqa: E402

POZITIF = [
    "Bu Atlassian sitesine yazamam, yetkim yok.",
    "Portal ayarını yapamam, kullanıcı eklemeli.",
    "Azure'a erişimim yok.",
    "Bu işi yapılamaz, çünkü kapı kapalı.",
    "Cosmos'a erişemiyorum.",
    "Aracım yok, bu yüzden bakamadım.",
    "Docker'ı çalıştıramıyorum.",
    "Yazma konusunda iznim yok.",
]
NEGATIF = [
    "Denendi: Resolve-DnsName çıktısı boş. Engel: VPN bağlı değil; yapamam.",
    "Atlassian çağrısı 403 döndü, yazamam.",
    "Silme push'u P-020 gereği yapılamaz.",
    "Kural metni: \"yapamam\" cümlesi kanıt taşır.",
    "`yapamam` kalıbı ayarda durur.",
    "Her şey tamam, sonuç yazıldı.",
    "Kimlik klasörüne bakmadım, doğrulanmadı; yetkim yok olabilir.",
    "",
]


class KapiTest(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.sd, True)

    def test_pozitif_yakalanir(self):
        for m in POZITIF:
            with self.subTest(m=m):
                self.assertTrue(Y.degerlendir(m, self.sd), m)

    def test_negatif_yakalanmaz(self):
        for m in NEGATIF:
            with self.subTest(m=m):
                self.assertEqual(Y.degerlendir(m, self.sd), {}, m)

    def test_kapali_env(self):
        with mock.patch.dict(os.environ, {"ORKESTRA_YAPAMAM_KANITI": "0"}):
            self.assertEqual(Y.degerlendir(POZITIF[0], self.sd), {})

    def test_proje_ezmesi_kapali(self):
        with open(os.path.join(self.sd, Y.PROJE_DOSYA), "w", encoding="utf-8") as f:
            json.dump({"mod": "kapali"}, f)
        self.assertEqual(Y.degerlendir(POZITIF[0], self.sd), {})

    def test_mod_golge_varsayilan(self):
        self.assertEqual(Y.mod(Y.ayar_oku()), "golge")

    def test_alinti_cumle(self):
        b = Y.degerlendir("Önce hazırlık. Azure'a erişimim yok. Sonra devam.", self.sd)
        self.assertEqual(b["alinti"], "Azure'a erişimim yok.")

    def test_hook_gunluge_yazar(self):
        import hook
        yol = os.path.join(self.sd, "gunluk.jsonl")
        hook._yapamam_yanit(self.sd, "o1", {"last_assistant_message": POZITIF[0]})
        satirlar = [json.loads(s) for s in open(yol, encoding="utf-8")]
        self.assertEqual(satirlar[-1]["tur"], "kapi_golge")
        self.assertEqual(satirlar[-1]["kapi"], "yapamam_kaniti")
        hook._yapamam_yanit(self.sd, "o1", {"last_assistant_message": NEGATIF[0]})
        self.assertEqual(len(open(yol, encoding="utf-8").readlines()), 1)


if __name__ == "__main__":
    unittest.main()
