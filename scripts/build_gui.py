"""
Build script — empacota a GUI Primetax SPED Cross-Reference via PyInstaller.

Uso:
    python scripts/build_gui.py [--clean]

Saída em `dist/primetax-sped-gui/`. O executável é
`dist/primetax-sped-gui/primetax-sped-gui.exe` (Windows).

Premissa: rode SEMPRE da raiz do projeto. O exe gerado também espera
rodar a partir da raiz (lê data/tabelas-dinamicas-rfb/ e cria
data/db/, data/output/ relativos ao cwd).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "packaging" / "primetax-sped-gui.spec"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clean", action="store_true",
        help="Remove dist/ e build/ antes de empacotar.",
    )
    args = parser.parse_args()

    if not SPEC.exists():
        print(f"ERRO: spec não encontrado em {SPEC}", file=sys.stderr)
        return 2

    if args.clean:
        for p in (ROOT / "dist", ROOT / "build"):
            if p.exists():
                print(f"Removendo {p}...")
                shutil.rmtree(p, ignore_errors=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC),
        "--noconfirm",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
    ]
    print("Executando:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    sys.exit(main())
