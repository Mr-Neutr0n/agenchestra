"""Çıktı kanalı envanteri (I-364, ADR-0157): hook.py'deki çıkış noktalarını tarar, standartlar/cikti_kanallari.md üretir.

Sayı elle yazılmaz: taranan kanal sayısı belgedeki kanal sayısıdır. `python scripts/cikti_kanallari.py` belgeyi yeniden yazar,
`--kontrol` belge ile taramanın uyuşmadığını bildirir (çıkış kodu 1). Model çağırmaz.
"""
from __future__ import annotations

import os
import re
import sys

_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_YOLU = os.path.join(_KOK, "scripts", "hook.py")
BELGE_YOLU = os.path.join(_KOK, "standartlar", "cikti_kanallari.md")

# (kanal adı, hook.py'de aranan kalıp, alıcı, düğme var mı, not)
HOOK_KANALLARI = [
    ("additionalContext", r"additionalContext", "model", "hayır",
     "Modele bağlam; kullanıcı görmez. Model cümleyi kendi sözleriyle yazar, biçim güvenilmez."),
    ("systemMessage", r"systemMessage", "kullanıcı", "hayır",
     "Kullanıcıya doğrudan sabit metin; model araya girmez. Düğme taşıyamaz."),
    ("decision block", r"[\"']decision[\"']\s*:\s*[\"']block[\"']", "model", "hayır",
     "Turu zorla sürdürür; reason modele gider."),
    ("permissionDecision", r"permissionDecision[\"']\s*:", "araç çağrısı", "hayır",
     "allow, deny ya da ask; ask kullanıcıya onay sordurur (düğmeyi uygulama çizer)."),
]
MODEL_KANALLARI = [
    ("düz metin", "kullanıcı", "hayır", "Serbest yanıt; biçim modele bağlı."),
    ("düğmeli seçim", "kullanıcı", "evet", "wrap_up actions ya da AskUserQuestion; yalnız model çağırabilir."),
    ("dosya gönderimi", "kullanıcı", "hayır", "SendUserFile; belge içeriği sohbete yazılmaz."),
]


def tara(hook_metni: str | None = None) -> list[tuple[str, int]]:
    """Her hook kanalı için hook.py'deki geçiş sayısı; sayısı 0 olan kanal listeye girmez."""
    if hook_metni is None:
        with open(HOOK_YOLU, encoding="utf-8") as f:
            hook_metni = f.read()
    sonuc = []
    for ad, kalip, *_ in HOOK_KANALLARI:
        n = len(re.findall(kalip, hook_metni))
        if n:
            sonuc.append((ad, n))
    return sonuc


def uret(hook_metni: str | None = None) -> str:
    bulunan = dict(tara(hook_metni))
    satirlar = ["# Çıktı kanalları", "",
                f"Hook kanalı sayısı: {len(bulunan)} (hook.py taramasından üretilir; elle düzenlenmez).",
                f"Model kanalı sayısı: {len(MODEL_KANALLARI)}.", "", "## Hook kanalları", ""]
    for ad, _k, alici, dugme, not_ in HOOK_KANALLARI:
        if ad not in bulunan:
            continue
        satirlar += [f"### {ad}", "", f"- **Alıcı:** {alici}", f"- **Düğme:** {dugme}",
                     f"- **hook.py'de geçiş:** {bulunan[ad]}", f"- **Not:** {not_}", ""]
    satirlar += ["## Model kanalları", ""]
    for ad, alici, dugme, not_ in MODEL_KANALLARI:
        satirlar += [f"### {ad}", "", f"- **Alıcı:** {alici}", f"- **Düğme:** {dugme}", f"- **Not:** {not_}", ""]
    satirlar += ["## Kural", "",
                 "- Kullanıcıya dönük uyarı sabit `systemMessage` ile gider; seçim gerekiyorsa model düğmeyle sunar (ADR-0157).",
                 "- Düğmenin çıkması modelde zorlanmaz, yalnız `additionalContext` yönergesiyle istenir.", ""]
    return "\n".join(satirlar)


# Hook'a bağlı kanalların örnek içeriği (demo yalnız gösterir, hook çalıştırmaz)
_ORNEK = {
    "additionalContext": "Orkestra: devir uyarısı kullanıcıya gösterildi; cümleyi yeniden yazma. (modele gider, kullanıcı görmez)",
    "systemMessage": "Orkestra: oturum uzadı.\nÖlçü: önceki tur 11.9 M token önbellek okudu\n"
                     "Öneri: sonraki iş için yeni sohbet daha ucuz\nSeçenek: `/orkestra:devir` ile yeni sohbet ya da burada sürdür.",
    "decision block": "reason: <hook'un turu sürdürme gerekçesi> (modele gider, tur devam eder)",
    "permissionDecision": "ask: riskli bir araç çağrısı için uygulama onay penceresini çizer.",
}


def demo() -> str:
    """7 kanalı numaralı sırayla gösterir: önce hook kanalları, sonra model kanalları."""
    bulunan = {ad for ad, _ in tara()}
    satirlar, n = ["Çıktı kanalları demosu", ""], 0
    for ad, _k, alici, dugme, _not in HOOK_KANALLARI:
        if ad in bulunan:
            n += 1
            satirlar += [f"{n}. {ad} (alıcı: {alici}, düğme: {dugme})", f"   Örnek: {_ORNEK[ad]}", ""]
    for ad, alici, dugme, not_ in MODEL_KANALLARI:
        n += 1
        satirlar += [f"{n}. {ad} (alıcı: {alici}, düğme: {dugme})", f"   {not_}", ""]
    return "\n".join(satirlar)


def kontrol() -> bool:
    try:
        with open(BELGE_YOLU, encoding="utf-8") as f:
            return f.read() == uret()
    except OSError:
        return False


def main(argv: list[str]) -> int:
    if "--demo" in argv:
        print(demo())
        return 0
    if "--kontrol" in argv:
        ok = kontrol()
        print("uyumlu" if ok else "belge taramayla uyuşmuyor")
        return 0 if ok else 1
    with open(BELGE_YOLU, "w", encoding="utf-8", newline="\n") as f:
        f.write(uret())
    print(f"yazıldı: {BELGE_YOLU} (hook kanalı: {len(tara())})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
