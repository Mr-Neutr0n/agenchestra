"""UserPromptSubmit refleks girdisi (ADR-0149): hook.py'yi yüklemez, günlük kilidine girmez.

Eşleşirse `decision: block` + çıktı basar; ön eksiz istemde, hatada ya da eşleşmemede sessizce 0 ile çıkar (istem modele gider).
Yalnız standart kütüphane; refleks modülü ön ek eşleşmeden içe aktarılmaz.
"""
import json
import os
import sys


def main() -> int:
    try:
        if os.environ.get("ORKESTRA_REFLEKS") == "0":
            return 0
        g = json.loads(sys.stdin.read() or "{}")
        istem = g.get("prompt") if isinstance(g, dict) else None
        if not isinstance(istem, str) or not istem.lstrip().startswith("/"):
            return 0
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import refleks
        cikti = refleks.denetle(istem, g.get("cwd"))
        if cikti:
            sys.stdout.write(json.dumps(cikti, ensure_ascii=True))
    except Exception:  # noqa: BLE001 — hızlı yol hiçbir istemi kaybettirmez
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
