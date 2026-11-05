"""I-401 P4: UserPromptSubmit bağlamında sabit satırlar ardışık turda yinelenmez, değişen satır geçer, yenileme çalışır."""
import os
import sys
import tempfile

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import baglam_tekil as bt  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _tekil_acik(monkeypatch):
    monkeypatch.delenv("ORKESTRA_HOOK_TEKIL", raising=False)  # diğer test modülleri kapatmış olabilir


SABIT ="KAYNAK: dosya, tablo, kayıt, ayar, ürün iddiasına bu turda bak; erişilebilir veri varken bakmadım deme."
DEGISEN = "Durum: I-401 · sıradaki: uygulama P{n} (todo {n}/16) ve yeterince uzun bir satır olsun diye eklenen metin"


def test_sabit_satir_ikinci_turda_atlanir_degisen_gecer(tmp_path):
    sd = str(tmp_path)
    ilk = bt.suz(sd, "o1", SABIT + "\n" + DEGISEN.format(n=1))
    assert SABIT in ilk and "P1" in ilk
    ikinci = bt.suz(sd, "o1", SABIT + "\n" + DEGISEN.format(n=2))
    assert SABIT not in ikinci and "P2" in ikinci


def test_yenileme_sonrasi_satir_yeniden_eklenir(tmp_path):
    sd = str(tmp_path)
    bt.suz(sd, "o1", SABIT)
    for _ in range(bt.YENILEME - 1):
        assert bt.suz(sd, "o1", SABIT) == ""
    assert bt.suz(sd, "o1", SABIT) == SABIT


def test_oturumlar_birbirinden_bagimsiz(tmp_path):
    sd = str(tmp_path)
    bt.suz(sd, "o1", SABIT)
    assert bt.suz(sd, "o2", SABIT) == SABIT


def test_kisa_satir_tekillestirilmez(tmp_path):
    sd = str(tmp_path)
    bt.suz(sd, "o1", "kısa satır")
    assert bt.suz(sd, "o1", "kısa satır") == "kısa satır"


def test_kapatma_ve_bozuk_durum_metni_degistirmez(tmp_path, monkeypatch):
    sd = str(tmp_path)
    bt.suz(sd, "o1", SABIT)
    monkeypatch.setenv("ORKESTRA_HOOK_TEKIL", "0")
    assert bt.suz(sd, "o1", SABIT) == SABIT
    monkeypatch.delenv("ORKESTRA_HOOK_TEKIL")
    os.makedirs(os.path.join(sd, "baglam_tekil"), exist_ok=True)
    with open(os.path.join(sd, "baglam_tekil", "o3.json"), "w") as f:
        f.write("{bozuk")
    assert bt.suz(sd, "o3", SABIT) == SABIT
