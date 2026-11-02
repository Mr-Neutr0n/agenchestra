"""Maliyet defterinin transkript usage alanlarıyla mutabakatı (USD, token, süre). Salt okuma."""
import glob
import json
import os

import ork_lib as L

USD_ESIK = 2.0     # oturum başına izin verilen USD farkı (%)
SURE_ESIK = 10.0   # süre sapması işaret eşiği (%)


def _yuzde(defter, gercek):
    if not gercek:
        return 0.0 if not defter else 100.0
    return (defter - gercek) / gercek * 100.0


def fork_mu(ana_yol: str) -> bool:
    """Bölünmüş (fork) oturum transkripti üst oturumun satırlarını da taşır: dosyada birden çok sessionId vardır."""
    kimlikler = set()
    with open(ana_yol, "rb") as f:
        for ham in f:
            try:
                sid = json.loads(ham.decode("utf-8", errors="replace")).get("sessionId")
            except json.JSONDecodeError:
                continue
            if sid:
                kimlikler.add(sid)
                if len(kimlikler) > 1:
                    return True
    return False


def _toplam(ozetler):
    t = {"usd": 0.0, "token": 0, "ttl5": 0, "ttl1": 0, "ttl_ayrimsiz": 0}
    for o in ozetler:
        t["usd"] += o["toplam"]["maliyet_usd"]
        t["token"] += sum(o["toplam"][k] for k in ("giris", "cikis", "onbellek_okuma", "onbellek_yazma"))
        t["ttl5"] += o["ttl"]["5dk"]
        t["ttl1"] += o["ttl"]["1sa"]
        t["ttl_ayrimsiz"] += o["ttl"]["ayrimsiz"]
    return t


def _span_ms(o):
    return L.sure_ms(o["ilk_zaman"], o["son_zaman"]) or 0


def oturum_mutabakat(oid, satirlar, pdir):
    """satirlar: oturumun defter satırları (okuma anı düzeltmesi uygulanmış)."""
    ana = os.path.join(pdir, oid + ".jsonl")
    if not os.path.exists(ana):
        return {"oturum": oid, "durum": "transkript-yok"}
    ozetler = [L.transkript_oku(ana, 0, yan_zincir=False)]
    alt_ozet = {}
    for alt in sorted(glob.glob(os.path.join(pdir, oid, "subagents", "agent-*.jsonl"))):
        aid = os.path.basename(alt)[len("agent-"):-6]
        alt_ozet[aid] = L.transkript_oku(alt)
        ozetler.append(alt_ozet[aid])
    t = _toplam(ozetler)
    d_usd = sum(r.get("maliyet_usd", 0) or 0 for r in satirlar)
    d_tok = sum((r.get("giris") or 0) + (r.get("cikis") or 0) + (r.get("onbellek_okuma") or 0) + (r.get("onbellek_yazma") or 0) for r in satirlar)
    ttl_top = t["ttl5"] + t["ttl1"]
    alt_defter_ms = sum(r.get("sure_ms") or 0 for r in satirlar if r.get("agent_id"))
    alt_gercek_ms = sum(_span_ms(o) for o in alt_ozet.values())
    ana_defter_ms = sum(r.get("sure_ms") or 0 for r in satirlar if not r.get("agent_id"))
    fork = fork_mu(ana)
    eksik = sorted({r["agent_id"] for r in satirlar if r.get("agent_id")} - set(alt_ozet))
    durum = "fork" if fork else "alt-transkript-eksik" if eksik else "tamam"  # defterde olup diskte transkripti kalmayan alt ajan: kıyas tamamlanamaz
    return {
        "oturum": oid, "durum": durum, "fork": fork, "eksik_alt_ajan": len(eksik),
        "alt_ajan_sayisi": len(alt_ozet),
        "defter_usd": round(d_usd, 4), "transkript_usd": round(t["usd"], 4), "fark_usd_yuzde": round(_yuzde(d_usd, t["usd"]), 2),
        "defter_token": d_tok, "transkript_token": t["token"], "fark_token_yuzde": round(_yuzde(d_tok, t["token"]), 2),
        "defter_cikis": sum(r.get("cikis") or 0 for r in satirlar), "transkript_cikis": sum(o["toplam"]["cikis"] for o in ozetler),
        "ttl_5dk_payi": round(t["ttl5"] / ttl_top, 4) if ttl_top else None,
        "ttl_1sa_payi": round(t["ttl1"] / ttl_top, 4) if ttl_top else None,
        "alt_defter_sure_ms": alt_defter_ms, "alt_transkript_sure_ms": alt_gercek_ms,
        "alt_sure_sapma_yuzde": round(_yuzde(alt_defter_ms, alt_gercek_ms), 2),
        "ana_defter_sure_ms": ana_defter_ms, "ana_transkript_aralik_ms": _span_ms(ozetler[0]),
        "sure_isaret": bool(alt_gercek_ms) and abs(_yuzde(alt_defter_ms, alt_gercek_ms)) > SURE_ESIK,
    }


def mutabakat(sd, proje, oturum=None, en_az_usd=0.0):
    pdir = L.proje_oturum_dizini(proje)
    gruplar = {}
    for r in L.maliyet_kayitlari(sd):
        if r.get("oturum"):
            gruplar.setdefault(r["oturum"], []).append(r)
    sonuc = []
    for oid, sat in sorted(gruplar.items()):
        if oturum and oid != oturum:
            continue
        if sum(r.get("maliyet_usd", 0) or 0 for r in sat) < en_az_usd:
            continue
        sonuc.append(oturum_mutabakat(oid, sat, pdir))
    return sonuc


def ozet(sonuc):
    olculen = [s for s in sonuc if s["durum"] == "tamam"]
    alt_yok = [s for s in olculen if not s["alt_ajan_sayisi"]]
    gecen = lambda k: [s for s in k if abs(s["fark_usd_yuzde"]) <= USD_ESIK]
    return {
        "oturum": len(sonuc), "olculen": len(olculen), "fork_disi_birakilan": sum(1 for s in sonuc if s["durum"] == "fork"),
        "transkript_yok": sum(1 for s in sonuc if s["durum"] == "transkript-yok"),
        "alt_transkript_eksik": sum(1 for s in sonuc if s["durum"] == "alt-transkript-eksik"),
        "alt_ajansiz": len(alt_yok), "alt_ajansiz_gecen": len(gecen(alt_yok)),
        "alt_ajanli": len(olculen) - len(alt_yok), "alt_ajanli_gecen": len(gecen([s for s in olculen if s["alt_ajan_sayisi"]])),
        "sure_isaretli": sum(1 for s in olculen if s["sure_isaret"]),
    }
