"""Parsers para Bloco Y da ECF — Informações Gerais (Y570).

Base legal: ADE Cofis 02/2026 §21; Lei 9.430/1996 — retenções na fonte.
Y570: Demonstrativo do IRRF e CSLL Retidos na Fonte.
Cada linha representa retenções de uma natureza/período específico.
CR-47: somatório de VL_IR_RET e VL_CSLL_RET × compensações declaradas no IRPJ/CSLL.
"""

from decimal import Decimal

from src.models.registros import RegEcfY570


def _d(s: str) -> Decimal:
    return Decimal(s.replace(",", ".")) if s.strip() else Decimal("0")


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_y570(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfY570:
    return RegEcfY570(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="Y570",
        per_apu=_g(campos, 2),
        nat_rend=_g(campos, 3),
        vl_ir_ret=_d(_g(campos, 4)),
        vl_csll_ret=_d(_g(campos, 5)),
    )
