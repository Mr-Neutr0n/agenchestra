"""orkestra komutları: mcp (MCP kaydı ve config; ADR-0096). Hiçbir komut sır değeri yazmaz.

`orkestra mcp liste`                         kayıtlı MCP'ler ve kimlik durumu (var/yok; değer yok)
`orkestra mcp config [--mcp AD] [--hedef H]` config üretir: `json` (mcpServers, Claude Desktop/.mcp.json biçimi)
                                            ya da `claude-code` (claude mcp add komutları); yalnız sarmalayıcı komutunu taşır
`orkestra mcp kur [--mcp AD | --hepsi]`      `claude mcp add` ile kaydeder; kapsam kullanım sınıfından gelir (ADR-0155): hafif → user,
                                            agir ve tarayici → project (.mcp.json). Seçimsiz çağrı yalnız hafif olanları kurar.
                                            `--kuru`: yalnız komutu göster
`orkestra mcp goc [--kuru]`                  kullanıcı kaydındaki hafif olmayan sunucuları kaldıran ve proje kaydına alan komut listesi
                                            (yalnız yazar; ~/.claude.json'a dokunmaz, çalıştırma kullanıcıya aittir)
`orkestra mcp olc`                           canlı MCP sarmalayıcı süreçlerini oturum başına sayar (JSON)
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys

from komutlar._ortak import hata

_BETIK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp_kimlik.py"))


def _mk():
    sys.path.insert(0, os.path.dirname(_BETIK))
    import mcp_kimlik as MK
    return MK


def betik_yolu() -> str:
    """Config'e yazılan sarmalayıcı yolu; eklenti güncellemesinde değişen önbellek yolu yerine ORKESTRA_MCP_BETIK ile sabitlenebilir."""
    return os.environ.get("ORKESTRA_MCP_BETIK") or _BETIK


def sunucu_girdisi(ad: str) -> dict:
    """Tek MCP'nin config girdisi: yalnız sarmalayıcı komutu ve MCP adı. Kayıttaki hiçbir alan (ortam dâhil) buraya geçmez."""
    return {"command": "python", "args": [betik_yolu().replace("\\", "/"), ad]}


def config_json(kayit: dict, adlar: list) -> dict:
    return {"mcpServers": {ad: sunucu_girdisi(ad) for ad in adlar}}


def kapsam(girdi: dict | None) -> str:
    """Kayıt girdisinin `claude mcp add --scope` değeri: yalnız hafif sınıf kullanıcı düzeyine gider (ADR-0155).
    Sınıfsız girdi (proje ezmesi) ve ağır/tarayıcı sınıfı proje düzeyindedir; belirsizlikte yük her oturuma yazılmaz."""
    return "user" if (girdi or {}).get("sinif") == "hafif" else "project"


def ekle_komutu(ad: str, kayit: dict | None = None) -> list:
    g = sunucu_girdisi(ad)
    return ["claude", "mcp", "add", "--scope", kapsam((kayit or {}).get(ad)), ad, "--", g["command"], *g["args"]]


def kimlik_durumu(girdi: dict, yukle) -> str:
    """'gerekmez', 'var' ya da 'yok: servis.ANAHTAR,...' (yalnız ad; değer okunmaz yazılmaz)."""
    ortam = girdi.get("ortam") or {}
    if not ortam:
        return "gerekmez"
    MK = _mk()
    onbellek, eksik = {}, []
    for a in ortam.values():
        servis, ad_ = MK.anahtar_coz(girdi, a)
        if servis not in onbellek:
            try:
                onbellek[servis] = yukle(servis)
            except Exception:
                onbellek[servis] = {}
        if ad_ not in onbellek[servis]:
            eksik.append(f"{servis}.{ad_}")
    return "var" if not eksik else "yok: " + ", ".join(eksik)


def eksik_gerek(girdi: dict, bul=shutil.which) -> list:
    """Kayıttaki `gerek` komutlarından PATH'te bulunmayanlar (ADR-0097)."""
    return [g for g in girdi.get("gerek") or [] if not bul(g)]


def _kayit():
    MK = _mk()
    try:
        return MK.kayit_oku()
    except MK.KayitHata as e:
        hata(str(e))


def _adlar(a, kayit: dict, secimsiz: str = "hepsi") -> list:
    """`secimsiz`: --mcp ve --hepsi yokken ne seçilir. config için `hepsi` (yalnız üretir), kur için `hafif` (ADR-0155)."""
    if getattr(a, "hepsi", False):
        return sorted(kayit)
    if not getattr(a, "mcp", None):
        if secimsiz == "hafif":  # yalnız her oturumda açılması ucuz olanlar kurulur
            return sorted(ad for ad, g in kayit.items() if g.get("sinif") == "hafif")
        return sorted(kayit)
    yok = [x for x in a.mcp if x not in kayit]
    if yok:
        hata(f"kayıtta olmayan MCP: {', '.join(yok)} (kayıtlı: {', '.join(sorted(kayit))})")
    return list(a.mcp)


def cmd_liste(a):
    kayit = _kayit()
    import kimlik as K
    for ad in sorted(kayit):
        eksik = eksik_gerek(kayit[ad])
        gerek = "; gerek: " + ", ".join(f"{g} yok" for g in eksik) if eksik else ""
        print(f"{ad}: kimlik {kimlik_durumu(kayit[ad], K.yukle)}; sinif {kayit[ad].get('sinif', '-')}; komut {kayit[ad]['komut'][0]}{gerek}")


def cmd_config(a):
    kayit = _kayit()
    adlar = _adlar(a, kayit)
    if a.hedef == "claude-code":
        for ad in adlar:
            print(" ".join(shlex.quote(x) for x in ekle_komutu(ad, kayit)))
    else:
        print(json.dumps(config_json(kayit, adlar), indent=2, ensure_ascii=False))


def _calistirilabilir(komut: list) -> list:
    """Windows'ta `claude` bir .cmd kısayolu olabilir; subprocess düz adı bulamaz, PATHEXT ile çözülen yol kullanılır."""
    yol = shutil.which(komut[0])
    return [yol or komut[0]] + list(komut[1:])


def kur(adlar: list, calistir=subprocess.run, kuru: bool = False, kayit: dict | None = None,
        hepsi: bool = False, bul=shutil.which) -> list:
    """(ad, durum) listesi. Zaten kayıtlıysa dokunmaz ('zaten kayıtlı'); `calistir` testte yerine konur.
    Ön koşulu (`gerek`) eksik MCP: `hepsi` ise atlanır ('atlandı: uv yok'), tek tek istenmişse uyarıp yine kaydedilir."""
    sonuc = []
    for ad in adlar:
        eksik = eksik_gerek((kayit or {}).get(ad, {}), bul)
        yok = ", ".join(f"{g} yok" for g in eksik)
        if eksik and hepsi:
            sonuc.append((ad, f"atlandı: {yok}"))
            continue
        komut = ekle_komutu(ad, kayit)
        if kuru:
            sonuc.append((ad, "kuru: " + " ".join(shlex.quote(x) for x in komut)))
            continue
        if calistir(_calistirilabilir(["claude", "mcp", "get", ad]), capture_output=True).returncode == 0:
            sonuc.append((ad, "zaten kayıtlı"))
            continue
        r = calistir(_calistirilabilir(komut), capture_output=True)
        durum = "eklendi" if r.returncode == 0 else f"hata (çıkış kodu {r.returncode})"
        sonuc.append((ad, durum + (f" (uyarı: {yok})" if eksik and r.returncode == 0 else "")))
    return sonuc


def cmd_kur(a):
    kayit = _kayit()
    adlar = _adlar(a, kayit, secimsiz="hafif")
    if not a.kuru and not shutil.which("claude"):
        hata("claude komutu bulunamadı (Claude Code kurulu ve PATH'te olmalı)")
    sonuc = kur(adlar, kuru=a.kuru, kayit=kayit, hepsi=bool(a.hepsi or not a.mcp))
    for ad, durum in sonuc:
        print(f"{ad}: {durum}")
    if any(d.startswith("hata") for _, d in sonuc):
        raise SystemExit(1)


def _kullanici_kaydi() -> list:
    """`~/.claude.json` kullanıcı düzeyindeki MCP adları. Yalnız anahtar adları okunur; komut ve ortam değerleri hiçbir yere taşınmaz."""
    yol = os.environ.get("ORKESTRA_CLAUDE_JSON") or os.path.join(os.path.expanduser("~"), ".claude.json")
    try:
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return []
    mcp = d.get("mcpServers") if isinstance(d, dict) else None
    return sorted(mcp) if isinstance(mcp, dict) else []


def goc_komutlari(kayit: dict, kullanici: list) -> tuple:
    """(satırlar, dokunulmayanlar). Kullanıcı düzeyinde kayıtlı ve hafif olmayan her sunucu için kaldırma komutu ve
    proje dizininde çalıştırılacak kurulum komutu; hafif olanlar kalır, kayıtta olmayanlara dokunulmaz (ADR-0155)."""
    satirlar, dokunulmayan = [], []
    for ad in kullanici:
        g = kayit.get(ad)
        if g is None:
            dokunulmayan.append(ad)
        elif g.get("sinif") != "hafif":
            satirlar.append(f"claude mcp remove --scope user {shlex.quote(ad)}")
            satirlar.append(f"orkestra mcp kur --mcp {shlex.quote(ad)}   # yalnız gerektiren projenin dizininde")
    return satirlar, dokunulmayan


def cmd_goc(a):
    kayit = _kayit()
    satirlar, dokunulmayan = goc_komutlari(kayit, _kullanici_kaydi())
    if not satirlar:
        print("göç gerekmez: kullanıcı düzeyinde hafif olmayan kayıtlı sunucu yok")
    for s in satirlar:
        print(s)
    if dokunulmayan:
        print("# kayıtta olmayan, dokunulmadı: " + ", ".join(dokunulmayan))


def sayim(surecler: list) -> dict:
    """Süreç listesinden (`pid`, `ppid`, `cmd`) MCP sarmalayıcılarını (mcp_kimlik.py) oturum (ebeveyn süreç) başına sayar.
    Sarmalayıcının ebeveyni de sarmalayıcıysa (Windows python kısayolu) tek sayılır."""
    sar = [s for s in surecler if "mcp_kimlik.py" in str(s.get("cmd", ""))]
    pidler = {s["pid"] for s in sar}
    oturum: dict = {}
    for s in sar:
        if s["ppid"] in pidler:
            continue
        oturum[str(s["ppid"])] = oturum.get(str(s["ppid"]), 0) + 1
    return {"toplam": sum(oturum.values()), "oturum_sayisi": len(oturum), "oturum_basina": oturum,
            "en_cok": max(oturum.values(), default=0)}


def _surecler() -> list:
    """Çalışan süreçlerin (pid, ppid, cmd) anlık görüntüsü; okunamazsa boş liste."""
    try:
        if os.name == "nt":
            ps = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*mcp_kimlik.py*' } | "
                  "Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress")
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                               encoding="utf-8", timeout=60)
            d = json.loads(r.stdout) if r.stdout.strip() else []
            d = [d] if isinstance(d, dict) else d
            return [{"pid": x["ProcessId"], "ppid": x["ParentProcessId"], "cmd": x.get("CommandLine") or ""} for x in d]
        r = subprocess.run(["ps", "-eo", "pid=,ppid=,args="], capture_output=True, text=True, timeout=30)
        cikti = []
        for satir in r.stdout.splitlines():
            parca = satir.split(None, 2)
            if len(parca) == 3 and parca[0].isdigit() and parca[1].isdigit():
                cikti.append({"pid": int(parca[0]), "ppid": int(parca[1]), "cmd": parca[2]})
        return cikti
    except Exception:
        return []


def kayit_disi(kayit: dict, kullanici: list) -> list:
    """Kullanıcı düzeyinde kayıtlı ama eklenti kaydında olmayan sunucular: sarmalayıcıdan geçmezler, `sayim` bunları saymaz."""
    return [ad for ad in kullanici if ad not in kayit]


def cmd_olc(a):
    d = sayim(_surecler())
    d["kayit_disi_kullanici_sunuculari"] = kayit_disi(_kayit(), _kullanici_kaydi())   # yalnız ad; sayıma dahil değil
    print(json.dumps(d, ensure_ascii=False, indent=2))


def kaydet(alt):
    p = alt.add_parser("mcp", help="MCP kaydı: kimlikli sarmalayıcı config'i üret ve kur (değer yazmaz)").add_subparsers(dest="alt", required=True)
    p.add_parser("liste", help="kayıtlı MCP'ler ve kimlik durumu").set_defaults(f=cmd_liste)
    c = p.add_parser("config", help="config üret (yalnız sarmalayıcı komutu; sır yok)")
    c.add_argument("--mcp", action="append", help="MCP adı (tekrarlanabilir; yoksa hepsi)")
    c.add_argument("--hedef", choices=["json", "claude-code"], default="json")
    c.set_defaults(f=cmd_config)
    k = p.add_parser("kur", help="claude mcp add ile kaydet; kapsam sınıftan gelir (hafif: user, diğerleri: project)")
    k.add_argument("--mcp", action="append", help="MCP adı (tekrarlanabilir)")
    k.add_argument("--hepsi", action="store_true", help="kayıttaki hepsi (seçimsiz çağrı yalnız hafif olanları kurar)")
    k.add_argument("--kuru", action="store_true", help="komutu çalıştırmadan göster")
    k.set_defaults(f=cmd_kur)
    g = p.add_parser("goc", help="kullanıcı kaydındaki hafif olmayan sunucuları kaldıran komut listesi (yalnız yazar)")
    g.add_argument("--kuru", action="store_true", help="varsayılan davranış: komut çalıştırılmaz, yalnız listelenir")
    g.set_defaults(f=cmd_goc)
    o = p.add_parser("olc", help="canlı MCP sarmalayıcı süreçlerini oturum başına say (JSON)")
    o.set_defaults(f=cmd_olc)
