"""Çöken oturum kaydı (I-397 P5, ADR-0155): masaüstü uygulamasının main.log satırlarından çıkış kodları hata defterine girer."""
import os
import sys

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(KOK, "scripts"))
import cokus_kaydi as CK  # noqa: E402
import hata_en_cok as HE  # noqa: E402
import ork_lib as L  # noqa: E402

LOG = (
    "2026-11-05 08:31:56 [info] [permissionMode] spawn local_f76ddada-7b00 mode=auto\n"
    "2026-11-05 08:32:10 [error] Session local_ba434a9a-c047-4d40 query error: Error: Claude Code process exited with code 3221226505\n"
    "  at somewhere (file.js:1:1)\n"
    "2026-11-05 08:32:10 [error] Session local_f76ddada-7b00-456f query error: Error: Claude Code process exited with code 3221226505\n"
    "2026-11-05 09:10:00 [error] Session local_aaaaaaaa-0000 query error: Error: Claude Code process exited with code 1\n"
    "2026-11-05 09:11:00 [info] baska bir satir exited with code 7\n"
)


def test_ayristir_yalniz_oturum_cikis_satirlarini_alir():
    olaylar = CK.ayristir(LOG)
    assert [(o["oturum"], o["kod"]) for o in olaylar] == [
        ("local_ba434a9a", 3221226505), ("local_f76ddada", 3221226505), ("local_aaaaaaaa", 1)]
    assert olaylar[0]["zaman"].startswith("2026-11-05T08:32:10")


def test_tara_deftere_yazar_ve_ikinci_kosu_tekrar_yazmaz(tmp_path):
    log = tmp_path / "main.log"
    log.write_text(LOG, encoding="utf-8")
    sd = str(tmp_path / "durum")
    os.makedirs(sd)
    assert CK.tara(sd, str(log)) == 3
    assert CK.tara(sd, str(log)) == 0
    satirlar = [r for r in L.jsonl_oku(os.path.join(sd, "hata.jsonl")) if r.get("kaynak") == "cokus"]
    assert len(satirlar) == 3 and all("0x" in r["imza"] or "kod 1" in r["imza"] for r in satirlar)


def test_hata_en_cok_cokus_kaynagini_sayar_ve_ayni_kodu_birlestirir(tmp_path):
    log = tmp_path / "main.log"
    log.write_text(LOG, encoding="utf-8")
    sd = str(tmp_path / "durum")
    os.makedirs(sd)
    CK.tara(sd, str(log))
    satirlar = HE.birlestir(sd, kaynak="cokus")
    en = satirlar[0]
    assert en["kaynak"] == "cokus" and en["sayi"] == 2 and "3221226505" in en["imza"] and "0xC0000409" in en["imza"]
    assert any(r["kaynak"] == "cokus" for r in HE.birlestir(sd))          # kaynaksız görünümde de yer alır


def test_log_yoksa_ya_da_okunamazsa_sessiz_sifir(tmp_path):
    sd = str(tmp_path)
    assert CK.tara(sd, str(tmp_path / "yok.log")) == 0


def test_buyuk_logda_yalniz_son_baytlar_okunur(tmp_path):
    log = tmp_path / "main.log"
    log.write_text("x" * 5000 + "\n" + LOG, encoding="utf-8")
    sd = str(tmp_path / "durum")
    os.makedirs(sd)
    assert CK.tara(sd, str(log), son_bayt=len(LOG.encode("utf-8")) + 10) == 3
