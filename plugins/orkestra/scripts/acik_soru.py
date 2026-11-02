"""Açık soru yakalama (P-053): ajanın kullanıcıya sorduğu soruyu onay deposuna `soru` kaydı olarak açar, yanıtlanınca kapatır.

Hook'lar yalnız ince çağrı yapar (hook.py). Kayıt mantığı ve yaşam döngüsü onay.py'dedir. Alt ajan ve auto modu soru
sormaz (P-029 madde 4, ADR-0086), bu yüzden yakalama yalnız ana ajan ve auto dışı oturumda çalışır. ORKESTRA_ACIK_SORU=0 kapatır.
Hata hook'u düşürmez: her giriş noktası sessiz döner."""
from __future__ import annotations

import os
import re

import onay
import secim_ekrani_hatirlatma as SH


def acik() -> bool:
    return os.environ.get("ORKESTRA_ACIK_SORU") != "0"


def _etiket(e) -> str:
    return str(e.get("label") if isinstance(e, dict) else e or "").strip()


def arac_sorulari(arac: str, girdi) -> list[tuple[str, list[str]]]:
    """Araç çağrısındaki sorular: [(soru metni, seçenek etiketleri)]. AskUserQuestion ve dolu `ask` alanlı wrap_up."""
    girdi = girdi if isinstance(girdi, dict) else {}
    if arac == "AskUserQuestion":
        out = []
        for s in girdi.get("questions") or []:
            if isinstance(s, dict) and str(s.get("question") or "").strip():
                out.append((str(s["question"]).strip(), [_etiket(o) for o in s.get("options") or [] if _etiket(o)]))
        return out
    if arac == "wrap_up" or arac.endswith("__wrap_up"):
        ask = str(girdi.get("ask") or "").strip()
        if ask:
            return [(ask, [_etiket(a) for a in girdi.get("actions") or [] if _etiket(a)])]
    return []


def yakala(sd: str, arac: str, girdi, oturum, agent_id=None, is_id=None) -> int:
    """PreToolUse: ana ajanın sorusunu açık soru olarak kaydeder. Kaydedilen soru sayısını döner."""
    if agent_id or not oturum or not acik():
        return 0
    try:
        import izin_politikasi
        if izin_politikasi._auto_modu(sd, oturum):
            return 0
        n = 0
        for soru, secenekler in arac_sorulari(arac, girdi):
            onay.soru_ac(sd, soru, secenekler, oturum=oturum, kaynak=arac, is_id=is_id)
            n += 1
        return n
    except Exception:  # noqa: BLE001
        return 0


def ekran_yaniti(sd: str, girdi, yanit, oturum, agent_id=None) -> int:
    """PostToolUse AskUserQuestion: yanıtlanan sorular kapanır; iptal ve boş yanıtta soru açık kalır."""
    if agent_id or not acik():
        return 0
    try:
        import is_onay
        n = 0
        for soru, _ in arac_sorulari("AskUserQuestion", girdi):
            etiketler = is_onay.ekran_yaniti(yanit, soru)
            if etiketler and onay.soru_yanitla_metinle(sd, oturum, soru, "; ".join(etiketler)[:200], kim="kullanici"):
                n += 1
        return n
    except Exception:  # noqa: BLE001
        return 0


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def mesaj_yaniti(sd: str, oturum, mesaj: str) -> int:
    """UserPromptSubmit: mesaj, bu oturumdaki açık sorunun düğme etiketiyle aynıysa (wrap_up düğmesi) soru kapanır."""
    if not acik() or not oturum or not (mesaj or "").strip():
        return 0
    try:
        m, n = _norm(mesaj), 0
        for k in onay.acik_sorular(sd, oturum):
            if any(_norm(e) == m for e in k.get("secenekler") or []):
                onay.soru_yanitla(sd, k["id"], mesaj.strip()[:200], kim="kullanici")
                n += 1
        return n
    except Exception:  # noqa: BLE001
        return 0


def metin_sorusu(yanit) -> str:
    """Düz metin yanıtın karar sorusu cümlesi (son `?` cümlesi, yoksa ''), kod blokları atılır."""
    m = SH._kodsuz(yanit or "").strip()
    cumleler = [c.strip(" \t\"'“”*_)") for c in re.split(r"(?<=[.!?:])\s+|\n+", m) if c.strip()]
    for c in reversed(cumleler):
        if c.endswith("?"):
            return c[:300]
    return ""


def metin_kaydet(sd: str, yanit, oturum, agent_id=None, is_id=None) -> bool:
    """Stop: yanıt düz metinle karar sorduysa (seçim ekranı ihlali) soru `metin` kaynağıyla açık kalır."""
    if agent_id or not oturum or not acik():
        return False
    try:
        soru = metin_sorusu(yanit)
        if not soru:
            return False
        onay.soru_ac(sd, soru, [], oturum=oturum, kaynak="metin", is_id=is_id)
        return True
    except Exception:  # noqa: BLE001
        return False
