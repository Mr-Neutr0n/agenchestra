"""I-401 P16: durum çubuğu bağlam boyutunu gösterir; 120k sarı, 150k kırmızı + devir önerisi; bilinmiyorsa satır bozulmaz."""
import json
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import kota  # noqa: E402


def girdi_cw(n):
    return {"model": {"display_name": "Sonnet"}, "context_window": {"current_usage": {"input_tokens": 10, "cache_read_input_tokens": n, "cache_creation_input_tokens": 0}}}


def test_alti_renksiz_sari_kirmizi_basamaklari():
    assert kota.baglam_parcasi(90_000) == "bağlam 90k"
    assert "devir yaklaşıyor" in kota.baglam_parcasi(130_000) and "\x1b[33m" in kota.baglam_parcasi(130_000)
    k = kota.baglam_parcasi(180_000)
    assert "DEVİR ÖNER" in k and "/orkestra:devir" in k and "\x1b[1;31m" in k


def test_satir_context_window_girdisini_kullanir():
    s = kota.satir(girdi_cw(210_000), None)
    assert "bağlam 210k" in s and "Sonnet" in s


def test_transkriptten_okur(tmp_path):
    tr = tmp_path / "t.jsonl"
    tr.write_text(json.dumps({"type": "assistant", "timestamp": "2026-11-05T10:00:00Z",
                              "message": {"model": "m", "usage": {"input_tokens": 5, "cache_read_input_tokens": 120_000, "cache_creation_input_tokens": 0}}}) + "\n",
                  encoding="utf-8")
    assert kota._baglam_tokeni({"transcript_path": str(tr)}) == 120_005


def test_bilinmeyen_baglam_satiri_bozmaz():
    assert kota.baglam_parcasi(None) == ""
    s = kota.satir({"model": {"display_name": "Opus"}, "transcript_path": "yok.jsonl"}, None)
    assert "Opus" in s and "bağlam" not in s
