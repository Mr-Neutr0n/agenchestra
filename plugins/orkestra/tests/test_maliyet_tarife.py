"""ADR-0133: defter okuma yolu ayrımsız satırlarda önbellek yazmayı ajan türüne göre fiyatlar.

`py -3.13 -m pytest plugins/orkestra/tests/test_maliyet_tarife.py -q -p no:cacheprovider`

- K1 alt ajan 'tur' satırı (damgasız ya da eski '1sa' damgalı) 5dk fiyatıyla okunur.
- K2 ana ajan 'tur' satırı 1sa fiyatıyla kalır.
- K3 gerçek ayrımlı hook satırı değişmez.
- K4 ham maliyet.jsonl dosyası okuma sonrası aynı kalır.
- K5 'hook-artik' satırı alt ajanda 5dk ile fiyatlanır.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import ork_lib as L  # noqa: E402

M = "claude-opus-5-5"


def usd(yazma, tarife):
    f = L.model_fiyati(M)
    return round((10 * f["giris"] + 5 * f["cikis"] + 100 * f["onbellek_okuma"] + yazma * f["onbellek_yazma_" + tarife]) / 1e6, 6)


def satir(oturum, agent_id, kaynak="tur", tarife=None, yazma=1_000_000, usd_=0.0, **ek):
    r = {"zaman": "2026-11-01T10:00:00+03:00", "oturum": oturum, "agent_id": agent_id, "model": M, "giris": 10, "cikis": 5,
         "onbellek_okuma": 100, "onbellek_yazma": yazma, "maliyet_usd": usd_, "kaynak": kaynak}
    if tarife:
        r["tarife"] = tarife
    r.update(ek)
    return r


class TestOkumaTarife(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp(prefix="ork_tarife_")

    def tearDown(self):
        shutil.rmtree(self.sd, ignore_errors=True)

    def oku(self, satirlar):
        yol = os.path.join(self.sd, "maliyet.jsonl")
        with open(yol, "w", encoding="utf-8", newline="\n") as f:
            for r in satirlar:
                f.write(json.dumps(r) + "\n")
        self.ham = open(yol, "rb").read()
        out = L._maliyet_kayitlari_oku(yol, duzeltme=False)
        self.assertEqual(open(yol, "rb").read(), self.ham, "ham defter değişmemeli")
        return out

    def test_k1_alt_ajan_tur_5dk(self):
        for tarife in (None, "1sa"):
            with self.subTest(tarife=tarife):
                out = self.oku([satir("o1", "agent-a", tarife=tarife)])
                self.assertEqual(out[0]["maliyet_usd"], usd(1_000_000, "5dk"))

    def test_k2_ana_ajan_tur_1sa(self):
        out = self.oku([satir("o1", None, tarife="1sa", usd_=usd(1_000_000, "1sa")), satir("o1", None)])
        self.assertEqual([r["maliyet_usd"] for r in out], [usd(1_000_000, "1sa")] * 2)

    def test_k3_hook_satiri_degismez(self):
        out = self.oku([satir("o1", "agent-b", kaynak="hook", usd_=7.77)])
        self.assertEqual(out[0]["maliyet_usd"], 7.77)

    def test_k5_artik_satiri_alt_ajanda_5dk(self):
        r = L._artik_satiri(satir("o1", "agent-c", kaynak="hook"), {"giris": 10, "cikis": 5, "onbellek_okuma": 100, "onbellek_yazma": 1_000_000})
        self.assertEqual(r["maliyet_usd"], usd(1_000_000, "5dk"))
        r = L._artik_satiri(satir("o1", None, kaynak="hook"), {"giris": 10, "cikis": 5, "onbellek_okuma": 100, "onbellek_yazma": 1_000_000})
        self.assertEqual(r["maliyet_usd"], usd(1_000_000, "1sa"))

    def test_tarife_yardimcisi(self):
        self.assertEqual(L.onbellek_tarifesi("agent-x"), "5dk")
        self.assertEqual(L.onbellek_tarifesi(None), "1sa")


if __name__ == "__main__":
    unittest.main()
