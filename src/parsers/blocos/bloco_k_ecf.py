"""Parsers para Bloco K da ECF — saldos contábeis (K155, K355).

Base legal: ADE Cofis 02/2026 §10; REGRA_COMPATIBILIDADE_K155_E155.
K155: contas patrimoniais (COD_NAT 01/02/03) pós-encerramento.
K355: contas de resultado (COD_NAT 04) antes do encerramento.
CR-43: K155/K355 × I155 (ECD) — consistência de saldos.
"""

from decimal import Decimal

from src.models.registros import RegEcfK155, RegEcfK355


def _d(s: str) -> Decimal:
    return Decimal(s.replace(",", ".")) if s.strip() else Decimal("0")


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_k155(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfK155:
    return RegEcfK155(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="K155",
        cod_cta=_g(campos, 2),
        cod_ccus=_g(campos, 3),
        vl_sld_ini=_d(_g(campos, 4)),
        ind_vl_sld_ini=_g(campos, 5),
        vl_deb=_d(_g(campos, 6)),
        vl_cred=_d(_g(campos, 7)),
        vl_sld_fin=_d(_g(campos, 8)),
        ind_vl_sld_fin=_g(campos, 9),
    )


def parsear_k355(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfK355:
    return RegEcfK355(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="K355",
        cod_cta=_g(campos, 2),
        cod_ccus=_g(campos, 3),
        vl_sld_ini=_d(_g(campos, 4)),
        ind_vl_sld_ini=_g(campos, 5),
        vl_deb=_d(_g(campos, 6)),
        vl_cred=_d(_g(campos, 7)),
        vl_sld_fin=_d(_g(campos, 8)),
        ind_vl_sld_fin=_g(campos, 9),
    )
