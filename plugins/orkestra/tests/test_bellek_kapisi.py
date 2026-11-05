"""Açılışta bellek uyarısı (I-397 P4, ADR-0155, P-028): eşik altında tek satır uyarı, gölge modda günlük; engel yok."""
import json
import os
import sys

import pytest

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import bellek_kapisi as BK  # noqa: E402

AYAR = {"mod": "golge", "bos_ram_gb_esik": 1.0, "commit_yuzde_esik": 90}


@pytest.fixture(autouse=True)
def _kapi_acik(monkeypatch):
    monkeypatch.delenv("ORKESTRA_BELLEK_KAPISI", raising=False)   # conftest testlerde kapatır; bu dosya kapıyı sınar


def test_esik_yuksek_verilince_uyari_cikar_dusuk_verilince_cikmaz():
    olcum = {"bos_ram_gb": 3.0, "commit_yuzde": 50.0}
    assert BK.degerlendir(olcum, {**AYAR, "bos_ram_gb_esik": 100}) is not None
    assert BK.degerlendir(olcum, {**AYAR, "bos_ram_gb_esik": 1}) is None


def test_commit_esigi_uyari_uretir():
    uyari = BK.degerlendir({"bos_ram_gb": 8.0, "commit_yuzde": 94.0}, AYAR)
    assert uyari and "commit" in uyari and "94" in uyari


def test_uyari_tek_satir_ve_degerleri_icerir():
    u = BK.degerlendir({"bos_ram_gb": 0.1, "commit_yuzde": 92.0}, AYAR)
    assert "\n" not in u and "0,1" in u


def test_olcum_yoksa_uyari_yok():
    assert BK.degerlendir(None, AYAR) is None


def test_gercek_olcum_makul_aralikta():
    o = BK.olc()
    if o is None:      # desteklenmeyen platform
        return
    assert o["bos_ram_gb"] > 0 and 0 < o["commit_yuzde"] <= 100


def test_oturum_basi_golge_modda_gunluge_yazar_ve_satir_doner(tmp_path):
    sd = str(tmp_path)
    satir = BK.oturum_basi(sd, "oturum-1", {"bos_ram_gb": 0.1, "commit_yuzde": 95.0}, AYAR)
    assert satir and "Bellek" in satir
    kayitlar = [json.loads(s) for s in open(os.path.join(sd, "gunluk.jsonl"), encoding="utf-8")]
    turler = {(k["tur"], k.get("kapi")) for k in kayitlar}
    assert ("bellek_olcum", None) in turler and ("kapi_golge", "bellek_kapisi") in turler


def test_oturum_basi_yeterli_bellekte_yalniz_olcum_yazar(tmp_path):
    sd = str(tmp_path)
    assert BK.oturum_basi(sd, "o", {"bos_ram_gb": 6.0, "commit_yuzde": 40.0}, AYAR) == ""
    kayitlar = [json.loads(s) for s in open(os.path.join(sd, "gunluk.jsonl"), encoding="utf-8")]
    assert [k["tur"] for k in kayitlar] == ["bellek_olcum"]


def test_kapali_mod_ve_ortam_degiskeni_hicbir_sey_yapmaz(tmp_path, monkeypatch):
    assert BK.oturum_basi(str(tmp_path), "o", {"bos_ram_gb": 0.1, "commit_yuzde": 99.0}, {**AYAR, "mod": "kapali"}) == ""
    assert not os.path.exists(os.path.join(str(tmp_path), "gunluk.jsonl"))
    monkeypatch.setenv("ORKESTRA_BELLEK_KAPISI", "0")
    assert BK.oturum_basi(str(tmp_path), "o", {"bos_ram_gb": 0.1, "commit_yuzde": 99.0}, AYAR) == ""


def test_esik_golge_verisinden_yuzdelikle_turetilir():
    assert BK.esik_oner([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 10) == 1.0
    assert BK.esik_oner([], 10) is None


def test_ayar_dosyasi_gecerli_ve_golge():
    a = BK.ayar_oku()
    assert a["mod"] == "golge" and a["bos_ram_gb_esik"] > 0 and 0 < a["commit_yuzde_esik"] <= 100
