"""
Sync das tabelas dinâmicas RFB (CLAUDE.md §2, §6, §11).

Mantém o snapshot de `data/tabelas-dinamicas-rfb/` sincronizado com os arquivos
publicados pela Receita Federal (Portal SPED). Três subcomandos:

    list      Mostra a estrutura esperada e o que está presente/ausente.
    fetch     Baixa uma tabela de uma URL indicada e extrai no destino.
    validate  Verifica se todas as tabelas esperadas estão presentes.

Uso:
    python -m scripts.baixar_tabelas_dinamicas list
    python -m scripts.baixar_tabelas_dinamicas fetch <url> --destino <subdir>
    python -m scripts.baixar_tabelas_dinamicas validate

Motivo do modelo manual-URL:
  As URLs da RFB mudam sem aviso e exigem navegação no Portal SPED para
  obter o link correto de cada ano-calendário. Em vez de embutir URLs que
  envelhecem rapidamente, o script aceita a URL como argumento (o operador
  copia do Portal SPED).

Referências legais:
  Decreto 6.022/2007 (SPED); ADE Cofis 01/2026 (ECD); ADE Cofis 02/2026 (ECF).
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path


# --------------------------------------------------------------------
# Estrutura esperada do snapshot (CLAUDE.md §2, §6)
# --------------------------------------------------------------------

_BASE_DIR = Path("data/tabelas-dinamicas-rfb")

# Estrutura esperada: cada entrada é (sub_caminho, descrição_curta).
# A ECF evolui por ano-calendário; a EFD-Contribuições tem tabelas fixas.
_ESTRUTURA_ESPERADA: list[tuple[str, str]] = [
    # ECF — Leiaute 11 (AC 2024)
    ("ecf/ac-2024/", "Tabelas dinâmicas da ECF AC 2024 (Leiaute 11)"),
    # ECF — Leiaute 12 (AC 2025)
    ("ecf/ac-2025/", "Tabelas dinâmicas da ECF AC 2025 (Leiaute 12)"),
    # EFD-Contribuições — tabelas externas (CST, NAT_BC_CRED, códigos de ajuste)
    ("efd-contribuicoes/", "Tabelas externas da EFD-Contribuições"),
]


# --------------------------------------------------------------------
# list
# --------------------------------------------------------------------

def cmd_list() -> int:
    print(f"Estrutura esperada em {_BASE_DIR}:\n")
    for subpath, descricao in _ESTRUTURA_ESPERADA:
        alvo = _BASE_DIR / subpath
        if alvo.exists() and any(alvo.iterdir()):
            qtd = sum(1 for _ in alvo.rglob("*") if _.is_file())
            marcador = f"[OK — {qtd} arquivo(s)]"
        elif alvo.exists():
            marcador = "[VAZIO]"
        else:
            marcador = "[AUSENTE]"
        print(f"  {marcador:30s} {subpath}")
        print(f"    {descricao}")
    print()
    print("Para baixar uma tabela:")
    print("  python -m scripts.baixar_tabelas_dinamicas fetch <url> --destino ecf/ac-2025/")
    return 0


# --------------------------------------------------------------------
# fetch
# --------------------------------------------------------------------

def cmd_fetch(url: str, destino: str, *, extrair_zip: bool = True) -> int:
    alvo = _BASE_DIR / destino
    alvo.mkdir(parents=True, exist_ok=True)

    nome_arquivo = url.rsplit("/", 1)[-1] or "tabela.bin"
    destino_arquivo = alvo / nome_arquivo

    print(f"Baixando: {url}")
    print(f"  → {destino_arquivo}")

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "PrimetaxSpedCrossref/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp, \
             destino_arquivo.open("wb") as fout:
            shutil.copyfileobj(resp, fout)
    except Exception as exc:
        print(f"Falha no download: {exc}", file=sys.stderr)
        return 1

    tamanho = destino_arquivo.stat().st_size
    print(f"  Baixado ({tamanho} bytes)")

    if extrair_zip and nome_arquivo.lower().endswith(".zip"):
        print(f"Extraindo ZIP em {alvo}...")
        try:
            with zipfile.ZipFile(destino_arquivo) as zf:
                zf.extractall(alvo)
                membros = zf.namelist()
            print(f"  Extraídos {len(membros)} arquivo(s)")
        except zipfile.BadZipFile:
            print("  Aviso: arquivo baixado não é ZIP válido — mantido como está.")

    return 0


# --------------------------------------------------------------------
# validate
# --------------------------------------------------------------------

def cmd_validate() -> int:
    ausentes = []
    vazios = []
    ok = []
    for subpath, _descricao in _ESTRUTURA_ESPERADA:
        alvo = _BASE_DIR / subpath
        if not alvo.exists():
            ausentes.append(subpath)
        elif not any(alvo.iterdir()):
            vazios.append(subpath)
        else:
            ok.append(subpath)

    print(f"Diretórios OK:        {len(ok)}")
    print(f"Diretórios vazios:    {len(vazios)}")
    print(f"Diretórios ausentes:  {len(ausentes)}")
    if vazios:
        print("\nVazios (precisam de download):")
        for p in vazios:
            print(f"  - {p}")
    if ausentes:
        print("\nAusentes (precisam ser criados + baixados):")
        for p in ausentes:
            print(f"  - {p}")

    return 0 if not (ausentes or vazios) else 1


# --------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="baixar_tabelas_dinamicas",
        description="Sync das tabelas dinâmicas RFB para data/tabelas-dinamicas-rfb/",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("list", help="Listar estrutura esperada e estado atual")

    p_fetch = sub.add_parser("fetch", help="Baixar tabela de URL para subdiretório")
    p_fetch.add_argument("url", help="URL completa da tabela (Portal SPED)")
    p_fetch.add_argument(
        "--destino", required=True,
        help="Subcaminho dentro de data/tabelas-dinamicas-rfb/ (ex: ecf/ac-2025/)",
    )
    p_fetch.add_argument(
        "--sem-extrair", action="store_true",
        help="Não tentar extrair automaticamente arquivos ZIP",
    )

    sub.add_parser("validate", help="Validar que a estrutura esperada está completa")

    args = parser.parse_args()

    if args.comando == "list":
        sys.exit(cmd_list())
    elif args.comando == "fetch":
        sys.exit(cmd_fetch(args.url, args.destino, extrair_zip=not args.sem_extrair))
    elif args.comando == "validate":
        sys.exit(cmd_validate())


if __name__ == "__main__":
    main()
