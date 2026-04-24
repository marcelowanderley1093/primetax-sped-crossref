"""Parsers para Bloco X da ECF — Informações Econômicas (X460, X480).

Base legal: ADE Cofis 02/2026 §20; Lei 11.196/2005 (Lei do Bem) e outras leis de benefício.
X460: Inovação Tecnológica — dispêndios com P&D pela Lei do Bem.
X480: Benefícios Fiscais Parte I — códigos da tabela dinâmica X480.
CR-46: X480 com valor > 0 × M300 exclusões — verificar aproveitamento.
CR-49: X460 com valor > 0 × M300 exclusões (30-60%) — verificar aproveitamento Lei do Bem.
"""

from decimal import Decimal

from src.models.registros import RegEcfX460, RegEcfX480


def _d(s: str) -> Decimal:
    return Decimal(s.replace(",", ".")) if s.strip() else Decimal("0")


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_x460(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfX460:
    return RegEcfX460(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="X460",
        codigo=_g(campos, 2),
        descricao=_g(campos, 3),
        valor=_d(_g(campos, 4)),
    )


def parsear_x480(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfX480:
    return RegEcfX480(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="X480",
        codigo=_g(campos, 2),
        descricao=_g(campos, 3),
        valor=_d(_g(campos, 4)),
        ind_valor=_g(campos, 5),
    )
