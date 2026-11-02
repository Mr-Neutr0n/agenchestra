"""Başvuru dokümanı kaynakla senkron kalır: kapsam, güncellik (üç negatif vaka) ve docs/README.md ad denetimi."""
import json
import os
import re
import shutil
import sys

import pytest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import dokuman_uret as du  # noqa: E402


def _alt_dizinler(ad):
    return sorted(d for d in os.listdir(os.path.join(KOK, ad)) if os.path.isfile(os.path.join(KOK, ad, d, "SKILL.md")))


def _satirlar(sayfa):
    return [x for x in du.uret()[sayfa].splitlines() if x.startswith("| `")]


def test_her_skill_ve_ajan_basvuruda_ve_aciklamasi_dolu():
    adlar = _alt_dizinler("skills")
    assert [x.split("`")[1] for x in _satirlar("skiller")] == adlar
    ajanlar = sorted(f[:-3] for f in os.listdir(os.path.join(KOK, "agents")) if f.endswith(".md"))
    assert [x.split("`")[1] for x in _satirlar("ajanlar")] == ajanlar
    assert not [x for x in _satirlar("skiller") + _satirlar("ajanlar") if du.ACIKLAMA_YOK in x]


def test_aciklamasiz_ayar_gorunur_ve_sayisi_dogru():
    metin = du.uret()["ayarlar"]
    ayarlar = [f for f in os.listdir(os.path.join(KOK, "ayarlar")) if f.endswith(".json")]
    bos = 0
    for f in ayarlar:
        with open(os.path.join(KOK, "ayarlar", f), encoding="utf-8") as fh:
            d = json.load(fh)
        bos += not (isinstance(d, dict) and str(d.get("aciklama", "")).strip())
    assert f"Toplam {len(ayarlar)} ayar; `{du.ACIKLAMA_YOK}` işaretli: {bos}." in metin


def test_diskteki_basvuru_guncel():
    assert du.eskimis() == []


def test_kontrol_elle_bozulmus_sayfada_eskimis_der(tmp_path):
    for ad, ic in du.uret().items():
        (tmp_path / f"{ad}.md").write_text(ic, encoding="utf-8")
    assert du.eskimis(tmp_path) == []
    (tmp_path / "skiller.md").write_text("elle bozuldu\n", encoding="utf-8")
    assert du.eskimis(tmp_path) == ["skiller"]


def test_kontrol_skill_eklenince_ve_ayar_silinince_farkli_uretir(tmp_path, monkeypatch):
    for d in ("skills", "ayarlar"):
        shutil.copytree(os.path.join(KOK, d), tmp_path / d)
    monkeypatch.setattr(du, "KOK", tmp_path)
    once_skill, once_ayar = du.skiller(), du.ayarlar()
    yeni = tmp_path / "skills" / "yeni-deneme"
    yeni.mkdir()
    (yeni / "SKILL.md").write_text("---\nname: yeni-deneme\ndescription: Deneme skill.\n---\n", encoding="utf-8")
    assert du.skiller() != once_skill and "yeni-deneme" in du.skiller()
    os.remove(tmp_path / "ayarlar" / sorted(os.listdir(tmp_path / "ayarlar"))[0])
    assert du.ayarlar() != once_ayar


def test_docs_readme_adlari_kaynakta_var():
    with open(os.path.join(KOK, "docs", "README.md"), encoding="utf-8") as f:
        metin = f.read()
    kodlar = set(re.findall(r"`([^`\n]+)`", metin))
    ajanlar = {f[:-3] for f in os.listdir(os.path.join(KOK, "agents")) if f.endswith(".md")}
    with open(os.path.join(KOK, "hooks", "hooks.json"), encoding="utf-8") as f:
        d = json.load(f)
    olaylar = set(d.get("hooks", d))
    komutlar = set(re.search(r"\{([^}]+)\}", du.cli()).group(1).split(",")) if re.search(r"\{([^}]+)\}", du.cli()) else set()
    eksik = []
    for k in kodlar:
        if re.fullmatch(r"(isci-t\d|denetci|triyaj|test-yazari|arastirmaci)", k) and k not in ajanlar:
            eksik.append(k)
        if re.fullmatch(r"[A-Z][A-Za-z]+(Submit|Use|Start|Stop|End|Compact|Change|Failure)", k) and k not in olaylar:
            eksik.append(k)
        if k.startswith("orkestra ") and komutlar and k.split()[1] not in komutlar and not k.startswith("orkestra --"):
            eksik.append(k)
        if re.fullmatch(r"(scripts|hooks|kurallar|ayarlar|standartlar)/[\w./-]+\.(py|json|md)", k) and not os.path.exists(os.path.join(KOK, k)):
            eksik.append(k)
    assert eksik == []
    for baglanti in re.findall(r"\]\(([^)#]+)\)", metin):
        assert os.path.exists(os.path.join(KOK, "docs", baglanti)), baglanti
