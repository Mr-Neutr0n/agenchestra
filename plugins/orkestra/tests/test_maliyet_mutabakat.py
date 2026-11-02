"""I-336: defter netlemesi çift saymaz; `orkestra maliyet mutabakat` defteri transkript usage'ıyla sınar.

`py -3.13 -m pytest plugins/orkestra/tests/test_maliyet_mutabakat.py -q -p no:cacheprovider`

- K1 tur sayacı eşli span'de komşunun token'ını taşıyorsa eşsiz hook span'inin artığından düşülür (çift sayım yok).
- K2 mutabakat: transkriptle birebir eşleşen oturum fark 0, TTL payı karışık kullanımı yansıtır.
- K3 mutabakat: fork (birden çok sessionId) kıyas dışı; K4 diskte alt ajan transkripti olmayan oturum işaretlenir.
- K5 süre: alt ajan sure_ms'i transkript aralığından %10'dan çok saparsa işaretlenir.
"""
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import ork_lib as L  # noqa: E402
import maliyet_mutabakat as MM  # noqa: E402

M = "claude-sonnet-5-5"


def satir(**k):
    r = {"oturum": "o1", "agent_id": None, "model": M, "giris": 0, "cikis": 0, "onbellek_okuma": 0, "onbellek_yazma": 0}
    r.update(k)
    return r


def mesaj(mid, sid, c5=0, c1=0, ts="2026-11-01T10:00:00.000Z", cikis=10):
    return {"type": "assistant", "sessionId": sid, "timestamp": ts, "uuid": mid,
            "message": {"id": mid, "model": M, "content": [], "usage": {
                "input_tokens": 1, "output_tokens": cikis, "cache_read_input_tokens": 100,
                "cache_creation_input_tokens": c5 + c1, "cache_creation": {"ephemeral_5m_input_tokens": c5, "ephemeral_1h_input_tokens": c1}}}}


class TestNetleme(unittest.TestCase):
    def test_k1_tur_fazlasi_artigi_dusurur(self):
        hook = [satir(kaynak="hook", span_id="o1-0003.t1", onbellek_yazma=600), satir(kaynak="hook", span_id="o1-0003.t2", onbellek_yazma=10)]
        tur = [satir(kaynak="tur", span_id="o1-0003.t2", onbellek_yazma=70)]
        art = L._hook_artigi(hook + tur, {("o1", None)})
        # hook toplamı 610; tur 70 + artık = 610 olmalı (eski davranış: 70 + 600 = 670)
        self.assertEqual(70 + sum(a["onbellek_yazma"] for a in art), 610)


class TestMutabakat(unittest.TestCase):
    def kur(self, ana_satirlar, alt=None):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "o1.jsonl"), "w", encoding="utf-8") as f:
            for s in ana_satirlar:
                f.write(json.dumps(s) + "\n")
        for aid, satirlar in (alt or {}).items():
            os.makedirs(os.path.join(d, "o1", "subagents"), exist_ok=True)
            with open(os.path.join(d, "o1", "subagents", f"agent-{aid}.jsonl"), "w", encoding="utf-8") as f:
                for s in satirlar:
                    f.write(json.dumps(s) + "\n")
        return d

    def defter(self, usd, **k):
        return [satir(maliyet_usd=usd, **k)]

    def test_k2_eslesme_ve_ttl_payi(self):
        d = self.kur([mesaj("m1", "o1", c5=300, c1=700)])
        o = L.transkript_oku(os.path.join(d, "o1.jsonl"), 0, yan_zincir=False)
        s = MM.oturum_mutabakat("o1", self.defter(o["toplam"]["maliyet_usd"], giris=1, cikis=10, onbellek_okuma=100, onbellek_yazma=1000), d)
        self.assertEqual(s["durum"], "tamam")
        self.assertEqual(s["fark_usd_yuzde"], 0.0)
        self.assertEqual(s["fark_token_yuzde"], 0.0)
        self.assertEqual((s["ttl_5dk_payi"], s["ttl_1sa_payi"]), (0.3, 0.7))

    def test_k3_fork_kiyas_disi(self):
        d = self.kur([mesaj("m1", "ust"), mesaj("m2", "o1")])
        s = MM.oturum_mutabakat("o1", self.defter(1.0), d)
        self.assertEqual(s["durum"], "fork")

    def test_k4_alt_transkript_eksik(self):
        d = self.kur([mesaj("m1", "o1")])
        s = MM.oturum_mutabakat("o1", self.defter(1.0, agent_id="abc"), d)
        self.assertEqual(s["durum"], "alt-transkript-eksik")

    def test_k5_sure_sapmasi_isaretlenir(self):
        alt = [mesaj("a1", "o1", ts="2026-11-01T10:00:00.000Z"), mesaj("a2", "o1", ts="2026-11-01T10:00:10.000Z")]
        d = self.kur([mesaj("m1", "o1")], {"abc": alt})
        s = MM.oturum_mutabakat("o1", self.defter(1.0, agent_id="abc", sure_ms=20000), d)
        self.assertEqual(s["alt_transkript_sure_ms"], 10000)
        self.assertTrue(s["sure_isaret"])
        s2 = MM.oturum_mutabakat("o1", self.defter(1.0, agent_id="abc", sure_ms=10500), d)
        self.assertFalse(s2["sure_isaret"])


if __name__ == "__main__":
    unittest.main()
