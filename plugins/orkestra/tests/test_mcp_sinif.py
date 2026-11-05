"""MCP kullanım sınıfı ve kapsam (I-397, ADR-0155): hafif sunucu kullanıcı düzeyine, ağır ve tarayıcı proje düzeyine kurulur."""
import json
import os
import sys

import pytest

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import mcp_kimlik as mk  # noqa: E402
from komutlar import mcp as M  # noqa: E402

HAFIF = {"sequential-thinking", "memory", "context7"}


def test_p1_eklenti_kaydinin_her_girdisi_sinif_tasir(tmp_path):
    kayit = mk.kayit_oku(str(tmp_path))
    assert len(kayit) == 19
    assert all(g.get("sinif") in mk.SINIFLAR for g in kayit.values())
    assert {ad for ad, g in kayit.items() if g["sinif"] == "hafif"} == HAFIF


def test_p1_gecersiz_sinif_reddedilir():
    with pytest.raises(mk.KayitHata, match="sinif"):
        mk.dogrula("t", {"komut": ["x"], "sinif": "dev"})


def test_p1_eklenti_kaydinda_sinifsiz_girdi_reddedilir(tmp_path, monkeypatch):
    eklenti = tmp_path / "eklenti"
    (eklenti / "ayarlar").mkdir(parents=True)
    (eklenti / "ayarlar" / "mcp_kimlik.json").write_text(json.dumps({"mcp": {"x": {"komut": ["x"]}}}), encoding="utf-8")
    monkeypatch.setattr(mk, "EKLENTI", str(eklenti))
    with pytest.raises(mk.KayitHata, match="sinif"):
        mk.kayit_oku(str(tmp_path / "proje"))


def test_p1_proje_ezmesi_sinifsiz_olabilir(tmp_path):
    proje = tmp_path / "proje"
    (proje / ".claude" / "orkestra").mkdir(parents=True)
    (proje / ".claude" / "orkestra" / "mcp_kimlik.json").write_text(
        json.dumps({"mcp": {"ozel": {"komut": ["x"]}}}), encoding="utf-8")
    assert "ozel" in mk.kayit_oku(str(proje))


def test_p2_kapsam_sinifa_gore():
    assert M.kapsam({"sinif": "hafif"}) == "user"
    assert M.kapsam({"sinif": "agir"}) == "project"
    assert M.kapsam({"sinif": "tarayici"}) == "project"
    assert M.kapsam({}) == "project"          # sınıfsız (proje ezmesi) güvenli tarafta: proje düzeyi


def test_p2_secimsiz_kur_yalniz_hafif_ve_hepsi_user_sayisi_hafife_esit(tmp_path):
    kayit = mk.kayit_oku(str(tmp_path))
    bos = type("A", (), {"hepsi": False, "mcp": None})()
    adlar = M._adlar(bos, kayit, secimsiz="hafif")
    assert set(adlar) == HAFIF
    assert set(M._adlar(bos, kayit)) == set(kayit)      # config üretimi seçimsizken hepsini üretir (yük oluşturmaz)
    sonuc = M.kur(adlar, kuru=True, kayit=kayit, hepsi=True)
    user = [d for _, d in sonuc if d.startswith("kuru:") and "--scope user" in d]
    assert len(user) == 3 and not [d for _, d in sonuc if "--scope project" in d]

    tum = M.kur(sorted(kayit), kuru=True, kayit=kayit, hepsi=True)
    user = [d for _, d in tum if d.startswith("kuru:") and "--scope user" in d]
    proje = [d for _, d in tum if d.startswith("kuru:") and "--scope project" in d]
    assert len(user) == 3 and len(proje) >= 1
    assert not [d for d in user if " playwright " in d or " chrome-devtools " in d]


def test_p2_agir_sunucu_proje_kapsaminda(tmp_path):
    kayit = mk.kayit_oku(str(tmp_path))
    kom = M.ekle_komutu("playwright", kayit)
    assert kom[kom.index("--scope") + 1] == "project"
    kom = M.ekle_komutu("memory", kayit)
    assert kom[kom.index("--scope") + 1] == "user"


def test_p3_goc_yalniz_hafif_olmayan_kullanici_kayitlarini_kaldirir(tmp_path):
    kayit = mk.kayit_oku(str(tmp_path))
    kullanici = ["memory", "playwright", "chrome-devtools", "bilinmeyen-ozel", "sequential-thinking"]
    satirlar, dokunulmayan = M.goc_komutlari(kayit, kullanici)
    kaldirilan = [s for s in satirlar if s.startswith("claude mcp remove --scope user ")]
    assert {s.split()[-1] for s in kaldirilan} == {"playwright", "chrome-devtools"}
    assert dokunulmayan == ["bilinmeyen-ozel"]
    assert any(s.startswith("orkestra mcp kur --mcp playwright") for s in satirlar)


def test_p3_goc_cikti_degersiz_ve_kayit_dosyasini_yazmaz(tmp_path, monkeypatch, capsys):
    sir = "SAHTE-DEGER-123"
    cj = tmp_path / "claude.json"
    cj.write_text(json.dumps({"mcpServers": {"playwright": {"command": "npx", "env": {"K": sir}},
                                             "memory": {"command": "npx"}}}), encoding="utf-8")
    once = cj.read_bytes()
    monkeypatch.setenv("ORKESTRA_CLAUDE_JSON", str(cj))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    M.cmd_goc(type("A", (), {"kuru": True})())
    cikti = capsys.readouterr().out
    assert sir not in cikti and "claude mcp remove --scope user playwright" in cikti
    assert "remove --scope user memory" not in cikti
    assert cj.read_bytes() == once


def _s(pid, ppid, ad):
    return {"pid": pid, "ppid": ppid, "cmd": f'python C:/x/scripts/mcp_kimlik.py {ad}'}


def test_p6_sayim_oturum_basina_ve_toplam():
    surecler = [_s(1, 100, "memory"), _s(2, 100, "playwright"), _s(3, 200, "memory"),
                {"pid": 9, "ppid": 100, "cmd": "python baska.py"}]
    o = M.sayim(surecler)
    assert o["toplam"] == 3 and o["oturum_sayisi"] == 2
    assert o["oturum_basina"] == {"100": 2, "200": 1} and o["en_cok"] == 2


def test_p6_olc_kayit_disi_kullanici_sunucularini_ayri_bildirir(tmp_path):
    kayit = mk.kayit_oku(str(tmp_path))
    assert M.kayit_disi(kayit, ["memory", "pgmcp", "ozel"]) == ["pgmcp", "ozel"]


def test_p6_olc_cli_json_basar_degersiz(tmp_path, monkeypatch, capsys):
    cj = tmp_path / "claude.json"
    cj.write_text(json.dumps({"mcpServers": {"memory": {"command": "x", "env": {"K": "GIZLI-9"}}, "pgmcp": {}}}), encoding="utf-8")
    monkeypatch.setenv("ORKESTRA_CLAUDE_JSON", str(cj))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr(M, "_surecler", lambda: [_s(1, 7, "memory"), _s(2, 7, "context7")])
    M.cmd_olc(None)
    cikti = capsys.readouterr().out
    d = json.loads(cikti)
    assert d["toplam"] == 2 and d["kayit_disi_kullanici_sunuculari"] == ["pgmcp"] and "GIZLI-9" not in cikti


def test_p6_sayim_bos_liste():
    assert M.sayim([]) == {"toplam": 0, "oturum_sayisi": 0, "oturum_basina": {}, "en_cok": 0}
