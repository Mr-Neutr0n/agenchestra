"""orkestra komutları: `niyetler` — niyet defteri (ADR-0156): ekle, durum, liste, rapor."""
from __future__ import annotations

import json

import niyet_defteri as ND
import niyet_defteri_kapi as NK
import ork_lib as L
from komutlar._ortak import hata, oturum_id, sd_gerekli


def _oturum(a) -> str | None:
    o = a.oturum or oturum_id()
    return None if o == "-" else o


def cmd_niyetler_ekle(a):
    sd = sd_gerekli()
    oturum = _oturum(a)
    if not oturum:
        return hata("oturum kimliği bulunamadı (CLAUDE_CODE_SESSION_ID yok); --oturum ver.")
    istek = a.istek or L.istek_id_oku(sd, oturum)
    if not istek:
        return hata("istek kimliği bulunamadı; --istek ver.")
    try:
        kimlik = ND.ekle(sd, oturum, istek, a.tur, a.ne, kriter=a.kriter, kisit=a.kisit, ilgili=a.ilgili)
    except ValueError as e:
        return hata(str(e))
    print(kimlik)


def cmd_niyetler_durum(a):
    sd = sd_gerekli()
    oturum = _oturum(a)
    if not oturum:
        return hata("oturum kimliği bulunamadı; --oturum ver.")
    try:
        ND.durum_yaz(sd, oturum, a.id, a.durum, kanit=a.kanit)
    except ValueError as e:
        return hata(str(e))
    print(f"{a.id} → {a.durum}")


def cmd_niyetler_liste(a):
    sd = sd_gerekli()
    oturum = _oturum(a)
    if not oturum:
        return hata("oturum kimliği bulunamadı; --oturum ver.")
    niyetler = ND.guncel(sd, oturum)
    if a.json:
        print(json.dumps(niyetler, ensure_ascii=False, indent=2))
        return
    if not niyetler:
        print("Bu sohbette kayıtlı niyet yok.")
        return
    for k in niyetler:
        kanit = f" [{k['kanit']}]" if k.get("kanit") else ""
        kriter = f" → {k['kriter']}" if k.get("kriter") else ""
        print(f"{k['id']} {k['niyet_tur']} {k['durum']}: {k['ne']}{kriter}{kanit}")
    s = ND.sayim(sd, oturum)
    print(f"toplam {s['toplam']}: açık {s['acik']}, karşılandı {s['karsilandi']}, kısmen {s['kismen']}, vazgeçildi {s['vazgecildi']}")


def cmd_niyetler_rapor(a):
    r = NK.rapor(sd_gerekli())
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    oran = "-" if r["oran"] is None else f"%{r['oran'] * 100:.0f}"
    alt = "-" if r["wilson_alt"] is None else f"%{r['wilson_alt'] * 100:.0f}"
    print(f"anlamlı istek: {r['n']} (en az {r['n_min']} gerekir); niyet yazılan: {r['yazilan']} ({oran}), istek başına ort. {r['ortalama_niyet']}; Wilson alt sınır: {alt} (en az %{r['wilson_alt_min'] * 100:.0f})")
    print(f"etiketleyici: {r['etiketleyici']}")
    print("ihlal geçişi: " + ("hazır" if r["gecis_hazir"] else "hazır değil"))


def kaydet(alt):
    p = alt.add_parser("niyetler", help="niyet defteri: ekle, durum, liste, rapor (ADR-0156)")
    p.add_argument("--yardım", action="help", help="bu yardımı gösterir")
    s = p.add_subparsers(dest="niyetler_komut", required=True)
    d = s.add_parser("ekle", help="mesajdan çıkan bir niyeti kaydeder (her niyet için bir kez çağır)")
    d.add_argument("tur", choices=ND.TURLER, help="istek, kisit, revize, vazgec ya da soru")
    d.add_argument("ne", help="niyet, tek cümle (sır yazma; ham mesajı yapıştırma)")
    d.add_argument("--kriter", help="bitince ekranda görülecek sonuç")
    d.add_argument("--kisit", help="niyetin taşıdığı kısıt")
    d.add_argument("--ilgili", help="revize/vazgec için önceki niyetin kimliği")
    d.add_argument("--istek", help="istek kimliği (varsayılan: oturumun son isteği)")
    d.add_argument("--oturum")
    d.set_defaults(f=cmd_niyetler_ekle)
    d = s.add_parser("durum", help="niyetin durumunu yazar; karsilandi ve kismen kanıt ister")
    d.add_argument("id")
    d.add_argument("durum", choices=ND.DURUMLAR)
    d.add_argument("--kanit", help="dosya:satır, komut çıktısı ya da sayı")
    d.add_argument("--oturum")
    d.set_defaults(f=cmd_niyetler_durum)
    d = s.add_parser("liste", help="sohbetin niyetleri, güncel durum ve kanıtla")
    d.add_argument("--oturum")
    d.add_argument("--json", action="store_true")
    d.set_defaults(f=cmd_niyetler_liste)
    d = s.add_parser("rapor", help="niyet yazılma (kapsama) oranı ve Wilson alt sınırı (gölge→ihlal ölçüsü)")
    d.add_argument("--json", action="store_true")
    d.set_defaults(f=cmd_niyetler_rapor)
