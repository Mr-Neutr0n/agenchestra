"""P-053 / P4: /onaylar.json açık soruyu taşır, POST /onay soru-yanit ve soru-kapat ile düşer; arayüz grubu app.js'te."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_panel_onay import PanelOnay  # noqa: E402
import onay  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "app.js")


class TestAcikSoruPanel(PanelOnay):
    def onaylar(self):
        d, b = self.istek("GET", "/onaylar.json?alan=alan-x")
        self.assertEqual(d, 200)
        return json.loads(b)

    def bekleyen_sorular(self):
        return [k for k in self.onaylar()["kayitlar"] if k["tur"] == "soru" and k["durum"] == "bekliyor"]

    def test_json_soruyu_tasir_yanit_dusurur(self):
        a = onay.soru_ac(self.sd, "Kurayım mı?", ["Kur", "Önce liste"], oturum="o1")
        self.assertEqual([k["id"] for k in self.bekleyen_sorular()], [a["id"]])
        d, b = self.post("alan-x", {"islem": "soru-yanit", "id": a["id"], "yanit": "Kur"})
        self.assertEqual(d, 200, b)
        self.assertEqual(self.bekleyen_sorular(), [])

    def test_kapat(self):
        a = onay.soru_ac(self.sd, "Gerek yok mu?", oturum="o1")
        d, b = self.post("alan-x", {"islem": "soru-kapat", "id": a["id"], "not": "gerek yok"})
        self.assertEqual(d, 200, b)
        self.assertEqual(self.bekleyen_sorular(), [])

    def test_soru_olmayan_kayit_ve_bos_yanit_reddedilir(self):
        k = onay.iste(self.sd, "Karar", "m", oturum="o1")
        self.assertEqual(self.post("alan-x", {"islem": "soru-kapat", "id": k["id"]})[0], 400)
        a = onay.soru_ac(self.sd, "Boş?", oturum="o1")
        self.assertEqual(self.post("alan-x", {"islem": "soru-yanit", "id": a["id"], "yanit": ""})[0], 400)
        self.assertEqual(len(self.bekleyen_sorular()), 1)

    def test_sayac_soruyu_sayar(self):
        onay.soru_ac(self.sd, "Sayılsın mı?", oturum="o1")
        self.assertEqual(self.onaylar()["sayac"]["tur"]["soru"], 1)

    def test_arayuz_grubu_var(self):
        js = open(APP, encoding="utf-8").read()
        for parca in ("grup('Açık sorular', g.soru)", "k.tur === 'soru'", "soru-yanit", "soru-kapat", "Gerek yok"):
            self.assertIn(parca, js)


if __name__ == "__main__":
    unittest.main()
