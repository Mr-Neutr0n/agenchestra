"""UserPromptSubmit bağlamında aynı sabit satırın her turda yinelenmesini önler (I-401 P4).

Neden: hook'un sabit hatırlatmaları (KAYNAK, YOL, NİYET, KABUK ...) her mesajda aynı metinle eklenir; eklenen metin
sohbet bağlamında kalır ve sonraki her API çağrısında yeniden okunur. Aynı satırın ikinci kopyası yeni bilgi taşımaz.

Davranış: oturum başına görülen satırların özeti tutulur; aynı satır son `YENILEME` tur içinde görüldüyse atlanır,
daha eskiyse yeniden eklenir (hatırlatma tazelenir). Değişen satır (bütçe, durum, iş kimliği) her zaman geçer.
Çıktı yalnız azalır; hata olursa metin aynen döner. `ORKESTRA_HOOK_TEKIL=0` kapatır. Atlanan karakter sayısı
`gunluk.jsonl`'a `tur=baglam_tekil` olarak yazılır (ölçüm için).
"""
from __future__ import annotations

import hashlib
import json
import os

import ork_lib as L

YENILEME = 6      # bir satır en çok bu kadar tur atlanır, sonra yeniden eklenir
EN_AZ_UZUNLUK = 60  # kısa satırlar (başlık, ayraç) tekilleştirilmez
SATIR_SAYISI_SINIRI = 400  # oturum durumu dosyasının büyümesini sınırlar


def _yol(sd: str, oturum: str) -> str:
    guvenli = "".join(c for c in str(oturum) if c.isalnum() or c in "-_")[:64] or "yok"
    return os.path.join(sd, "baglam_tekil", f"{guvenli}.json")


def _oku(yol: str) -> dict:
    try:
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def suz(sd: str | None, oturum: str | None, ek: str | None, yenileme: int = YENILEME) -> str:
    """`ek` içinde son `yenileme` turda zaten verilmiş satırları çıkarır; hata ya da kapalıysa `ek` aynen döner."""
    if not sd or not oturum or not ek or os.environ.get("ORKESTRA_HOOK_TEKIL") == "0":
        return ek or ""
    try:
        yol = _yol(sd, oturum)
        durum = _oku(yol)
        tur = int(durum.get("tur") or 0) + 1
        gorulen = durum.get("gorulen") if isinstance(durum.get("gorulen"), dict) else {}
        cikti, atlanan = [], 0
        for satir in ek.split("\n"):
            if len(satir.strip()) < EN_AZ_UZUNLUK:
                cikti.append(satir)
                continue
            h = hashlib.sha1(satir.strip().encode("utf-8")).hexdigest()[:12]
            if h in gorulen and tur - int(gorulen[h]) < yenileme:
                atlanan += len(satir) + 1
                continue
            gorulen[h] = tur
            cikti.append(satir)
        if len(gorulen) > SATIR_SAYISI_SINIRI:  # en eski görülenleri at
            for h, _ in sorted(gorulen.items(), key=lambda kv: kv[1])[: len(gorulen) - SATIR_SAYISI_SINIRI]:
                gorulen.pop(h, None)
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        L.atomik_yaz(yol, json.dumps({"tur": tur, "gorulen": gorulen}))
        if atlanan:
            try:
                L.jsonl_ekle(os.path.join(sd, "gunluk.jsonl"),
                             {"zaman": L.simdi(), "oturum": oturum, "tur": "baglam_tekil", "atlanan": atlanan, "kalan": len("\n".join(cikti))})
            except Exception:
                pass
        sonuc = "\n".join(cikti).strip("\n")
        return sonuc
    except Exception:
        return ek
