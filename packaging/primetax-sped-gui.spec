# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Primetax SPED Cross-Reference GUI.

Modo: --onedir (pasta dist/primetax-sped-gui/ contendo .exe + dependências).
Por que onedir: startup rápido, debug fácil, e o app espera rodar a
partir da raiz do projeto Primetax — onde data/tabelas-dinamicas-rfb/
está versionado. Onefile quebraria os caminhos relativos do parser ECF.

Recursos não-Python embutidos no bundle:
  - src/db/schema.sql              (lido por Repositorio.bootstrap)
  - src/db/migrations/*.sql        (migrações aditivas idempotentes)

Recursos NÃO embutidos (ficam fora do bundle, ao lado do exe):
  - data/tabelas-dinamicas-rfb/    (públicas, versionadas no repo)
  - data/input/, output/, db/      (do auditor, criados em runtime)
"""

from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH).parent  # type: ignore[name-defined]


def _migrations_data():
    """Lista de tuplas (origem_no_disco, destino_relativo_no_bundle)."""
    out = [(str(PROJECT_ROOT / "src/db/schema.sql"), "src/db")]
    migrations_dir = PROJECT_ROOT / "src/db/migrations"
    for sql in sorted(migrations_dir.glob("*.sql")):
        out.append((str(sql), "src/db/migrations"))
    return out


a = Analysis(
    [str(PROJECT_ROOT / "src/gui/app.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=_migrations_data(),
    hiddenimports=[
        # Garante que todos os parsers/regras carreguem mesmo se forem
        # importados dinamicamente em runtime.
        "src.parsers.ecd",
        "src.parsers.ecf",
        "src.parsers.efd_contribuicoes",
        "src.parsers.efd_icms_ipi",
        "src.crossref.engine",
        "src.reports.excel_diagnostico",
        "src.reports.word_parecer",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Reduz tamanho — módulos de teste/dev não devem ir no exe
        "pytest",
        "pytest_qt",
        "pytest_cov",
        "PyInstaller",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="primetax-sped-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # sem UPX — antivírus tendem a marcar binários comprimidos
    console=False,        # app GUI — sem janela de console no Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=None,         # adicionar quando .ico estiver disponível
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="primetax-sped-gui",
)
