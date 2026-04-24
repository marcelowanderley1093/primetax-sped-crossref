"""
Anonimizador de SPEDs — produz fixtures sintéticas a partir de arquivos reais.

Uso:
    python -m scripts.anonimizar_sped <entrada> <saida> [--seed INT] [--preservar-cnpj]

Estratégia (CLAUDE.md §10 — privacidade paranóica):
  1. Detecta o tipo de SPED (EFD-Contrib, EFD ICMS/IPI, ECD, ECF) pelo registro 0000.
  2. Substitui CNPJ, CPF e nomes por valores sintéticos determinísticos
     baseados em hash do original (mesma entrada → mesma saída).
  3. Preserva estrutura, valores monetários, datas, códigos (CST, CFOP, COD_CTA,
     NCM, etc.) — esses são necessários para que o fixture exercite os cruzamentos.
  4. Produz um CNPJ sintético válido (dígitos verificadores corretos) para
     não ser rejeitado por validações estruturais.

Não usa bibliotecas externas (apenas stdlib). Processamento linha-a-linha
suporta SPEDs de qualquer tamanho.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


# --------------------------------------------------------------------
# Geração determinística de CNPJ/CPF sintéticos
# --------------------------------------------------------------------

def _hash_int(valor: str, seed: int, modulo: int) -> int:
    h = hashlib.sha256(f"{seed}:{valor}".encode("utf-8")).hexdigest()
    return int(h, 16) % modulo


def _digitos_cnpj(base12: str) -> str:
    """Calcula os 2 dígitos verificadores de um CNPJ a partir dos 12 primeiros."""
    def _dv(digs: str, pesos: list[int]) -> str:
        soma = sum(int(d) * p for d, p in zip(digs, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)
    dv1 = _dv(base12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    dv2 = _dv(base12 + dv1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return dv1 + dv2


def _cnpj_sintetico(cnpj_original: str, seed: int) -> str:
    """Gera CNPJ válido de 14 dígitos a partir de hash determinístico."""
    # Mantém o sufixo '0001' (matriz) para realismo nos fixtures.
    raiz = str(_hash_int(cnpj_original, seed, 10**8)).zfill(8)
    base = raiz + "0001"
    return base + _digitos_cnpj(base)


def _digitos_cpf(base9: str) -> str:
    def _dv(digs: str, peso_inicial: int) -> str:
        soma = sum(int(d) * (peso_inicial - i) for i, d in enumerate(digs))
        resto = (soma * 10) % 11
        return "0" if resto == 10 else str(resto)
    dv1 = _dv(base9, 10)
    dv2 = _dv(base9 + dv1, 11)
    return dv1 + dv2


def _cpf_sintetico(cpf_original: str, seed: int) -> str:
    base = str(_hash_int(cpf_original, seed, 10**9)).zfill(9)
    return base + _digitos_cpf(base)


# --------------------------------------------------------------------
# Substituição de nomes
# --------------------------------------------------------------------

_SUFIXOS_NOME = ["SA", "LTDA", "EIRELI", "ME", "EPP"]


def _nome_sintetico(nome_original: str, seed: int) -> str:
    """Substitui nome preservando aproximadamente o comprimento e sufixo societário."""
    if not nome_original:
        return nome_original
    sufixo = ""
    for s in _SUFIXOS_NOME:
        if nome_original.upper().rstrip().endswith(" " + s):
            sufixo = " " + s
            break
    token = _hash_int(nome_original, seed, 10**6)
    return f"EMPRESA TESTE {token:06d}{sufixo}".upper()


# --------------------------------------------------------------------
# Detecção do tipo de SPED e regras de anonimização por registro 0000
# --------------------------------------------------------------------

def _detectar_tipo(primeira_linha_0000: list[str]) -> str:
    """Retorna: ecf | ecd | efd_icms | efd_contrib | desconhecido."""
    if len(primeira_linha_0000) < 3:
        return "desconhecido"
    marcador = primeira_linha_0000[2].strip().upper()
    if marcador == "LECF":
        return "ecf"
    if marcador == "LECD":
        return "ecd"
    cnpj7 = primeira_linha_0000[7].strip() if len(primeira_linha_0000) > 7 else ""
    cnpj9 = primeira_linha_0000[9].strip() if len(primeira_linha_0000) > 9 else ""
    if cnpj7.isdigit() and len(cnpj7) == 14:
        return "efd_icms"
    if cnpj9.isdigit() and len(cnpj9) == 14:
        return "efd_contrib"
    return "desconhecido"


# Posições (0-indexed) dos campos CNPJ e NOME no registro 0000 de cada SPED
_POS_0000 = {
    "efd_contrib": {"cnpj": 9, "nome": 8},
    "efd_icms":    {"cnpj": 7, "nome": 6},
    "ecd":         {"cnpj": 6, "nome": 5},
    "ecf":         {"cnpj": 4, "nome": 5},
}


# --------------------------------------------------------------------
# Anonimização linha a linha
# --------------------------------------------------------------------

_RE_CNPJ = re.compile(r"(?<!\d)(\d{14})(?!\d)")
_RE_CPF = re.compile(r"(?<!\d)(\d{11})(?!\d)")
# Nomes: sequência de 15+ chars contendo letras (aceita acentos) entre pipes.
_RE_NOME = re.compile(r"\|([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ \-\.&/']{14,})\|")


def _anonimizar_campo_cnpj(valor: str, mapa: dict[str, str], seed: int) -> str:
    if not valor or not valor.isdigit() or len(valor) != 14:
        return valor
    if valor not in mapa:
        mapa[valor] = _cnpj_sintetico(valor, seed)
    return mapa[valor]


def _anonimizar_campo_nome(valor: str, mapa: dict[str, str], seed: int) -> str:
    if not valor or len(valor) < 3:
        return valor
    if valor not in mapa:
        mapa[valor] = _nome_sintetico(valor, seed)
    return mapa[valor]


def _anonimizar_linha(
    linha: str,
    tipo_sped: str,
    mapa_cnpj: dict[str, str],
    mapa_cpf: dict[str, str],
    mapa_nome: dict[str, str],
    seed: int,
    preservar_cnpj_declarante: bool = False,
) -> str:
    if not linha.startswith("|") or not linha.strip():
        return linha

    campos = linha.split("|")
    if len(campos) < 2:
        return linha
    reg = campos[1].strip().upper()

    # Tratamento estrutural do 0000 — posições conhecidas.
    # O mapa_cnpj já contém identidade para o declarante quando
    # preservar_cnpj_declarante=True, portanto _anonimizar_campo_cnpj
    # retornará o mesmo CNPJ naquele caso.
    if reg == "0000" and tipo_sped in _POS_0000:
        pos_cnpj = _POS_0000[tipo_sped]["cnpj"]
        pos_nome = _POS_0000[tipo_sped]["nome"]
        if pos_cnpj < len(campos):
            campos[pos_cnpj] = _anonimizar_campo_cnpj(
                campos[pos_cnpj].strip(), mapa_cnpj, seed
            )
        if pos_nome < len(campos):
            campos[pos_nome] = _anonimizar_campo_nome(
                campos[pos_nome].strip(), mapa_nome, seed
            )
        return "|".join(campos)

    # Tratamento genérico (registros 0150, C100, etc.):
    # substitui qualquer campo que seja CNPJ (14 dígitos) ou CPF (11 dígitos).
    novos = [campos[0], campos[1]]
    for campo in campos[2:]:
        valor = campo.strip()
        if valor.isdigit() and len(valor) == 14:
            novos.append(_anonimizar_campo_cnpj(valor, mapa_cnpj, seed))
        elif valor.isdigit() and len(valor) == 11:
            if valor not in mapa_cpf:
                mapa_cpf[valor] = _cpf_sintetico(valor, seed)
            novos.append(mapa_cpf[valor])
        elif _RE_NOME.match("|" + valor + "|"):
            novos.append(_anonimizar_campo_nome(valor, mapa_nome, seed))
        else:
            novos.append(campo)
    return "|".join(novos)


# --------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------

def anonimizar(
    entrada: Path,
    saida: Path,
    *,
    seed: int = 42,
    preservar_cnpj_declarante: bool = False,
    encoding: str = "latin-1",
) -> dict[str, int]:
    """
    Anonimiza um SPED inteiro. Retorna sumário com contagens.

    Args:
        entrada: Caminho do SPED real.
        saida: Caminho do SPED anonimizado.
        seed: Inteiro usado no hash (muda → saída diferente).
        preservar_cnpj_declarante: Se True, mantém o CNPJ do 0000 inalterado.
        encoding: Padrão Latin-1 (histórico SPED). Use 'utf-8' se souber que é.
    """
    # Primeira passada: detectar tipo e capturar CNPJ do declarante
    tipo_sped = "desconhecido"
    cnpj_declarante = ""
    with entrada.open(encoding=encoding, errors="replace") as f:
        for linha in f:
            campos = linha.strip().split("|")
            if len(campos) >= 2 and campos[1].strip().upper() == "0000":
                tipo_sped = _detectar_tipo(campos)
                if tipo_sped in _POS_0000:
                    pos_cnpj = _POS_0000[tipo_sped]["cnpj"]
                    if pos_cnpj < len(campos):
                        cnpj_declarante = campos[pos_cnpj].strip()
                break

    mapa_cnpj: dict[str, str] = {}
    mapa_cpf: dict[str, str] = {}
    mapa_nome: dict[str, str] = {}
    total_linhas = 0

    # Se o operador pediu para preservar o CNPJ do declarante, o mapeamento
    # identidade garante que o mesmo CNPJ é mantido em todos os registros
    # (0150, C100 como remetente, etc.), não só no 0000.
    if preservar_cnpj_declarante and cnpj_declarante:
        mapa_cnpj[cnpj_declarante] = cnpj_declarante

    saida.parent.mkdir(parents=True, exist_ok=True)
    with entrada.open(encoding=encoding, errors="replace") as f_in, \
         saida.open("w", encoding=encoding, newline="") as f_out:
        for linha in f_in:
            total_linhas += 1
            linha_anon = _anonimizar_linha(
                linha.rstrip("\r\n"),
                tipo_sped,
                mapa_cnpj, mapa_cpf, mapa_nome,
                seed,
                preservar_cnpj_declarante,
            )
            f_out.write(linha_anon + "\n")

    return {
        "tipo_sped": tipo_sped,
        "linhas_processadas": total_linhas,
        "cnpjs_substituidos": len(mapa_cnpj),
        "cpfs_substituidos": len(mapa_cpf),
        "nomes_substituidos": len(mapa_nome),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="anonimizar_sped",
        description="Anonimiza SPED real para produzir fixture de teste.",
    )
    parser.add_argument("entrada", help="Arquivo SPED real (.txt)")
    parser.add_argument("saida", help="Caminho do arquivo anonimizado")
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Seed determinístico para o hash (padrão: 42)",
    )
    parser.add_argument(
        "--preservar-cnpj", action="store_true",
        help="Mantém CNPJ do declarante intacto (usar com cautela — arrisca PII)",
    )
    parser.add_argument(
        "--encoding", default="latin-1",
        help="Encoding do arquivo (padrão: latin-1)",
    )

    args = parser.parse_args()
    entrada = Path(args.entrada)
    saida = Path(args.saida)

    if not entrada.exists():
        print(f"Arquivo não encontrado: {entrada}", file=sys.stderr)
        sys.exit(1)
    if saida.resolve() == entrada.resolve():
        print("Saída não pode ser igual à entrada — recuse por segurança.", file=sys.stderr)
        sys.exit(1)

    sumario = anonimizar(
        entrada, saida,
        seed=args.seed,
        preservar_cnpj_declarante=args.preservar_cnpj,
        encoding=args.encoding,
    )

    print(f"Anonimização concluída: {saida}")
    for k, v in sumario.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
