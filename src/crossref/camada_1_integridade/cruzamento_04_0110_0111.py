"""
Cruzamento 04 — Consistência 0110 × 0111.

Base legal: IN RFB 1.252/2012, leiaute EFD-Contribuições:
  Se 0110.IND_APRO_CRED = "2" (rateio proporcional), o registro 0111
    (detalhamento da receita bruta por natureza) é obrigatório.
  Se 0110.IND_APRO_CRED = "1" (apropriação direta), o 0111 não deve existir
    — sua presença indica erro de preenchimento.

Camada: 1 — Integridade estrutural.
"""

import logging

from src.models.registros import Divergencia

logger = logging.getLogger(__name__)

CODIGO_REGRA = "CI-04"
SEVERIDADE = "medio"


def executar(
    repo,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> list[Divergencia]:
    divergencias: list[Divergencia] = []

    reg_0110 = repo.consultar_0110(conn, cnpj, ano_mes)
    if reg_0110 is None:
        return divergencias  # CI-03 já reporta ausência do 0110

    ind_apro_cred = reg_0110.get("ind_apro_cred", "")
    reg_0111 = repo.consultar_0111(conn, cnpj, ano_mes)
    tem_0111 = reg_0111 is not None

    if ind_apro_cred == "2" and not tem_0111:
        msg = (
            "IND_APRO_CRED=2 (rateio proporcional) exige registro 0111,"
            " que está ausente"
        )
        logger.warning("CI-04 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"Inconsistência 0110×0111 — {msg}",
                severidade=SEVERIDADE,
                evidencia=[{
                    "cnpj_declarante": cnpj, "ano_mes": ano_mes,
                    "ind_apro_cred": ind_apro_cred, "0111_presente": False,
                }],
            )
        )

    if ind_apro_cred == "1" and tem_0111:
        msg = (
            "IND_APRO_CRED=1 (apropriação direta) não deve ter 0111,"
            " mas o registro está presente"
        )
        logger.warning("CI-04 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"Inconsistência 0110×0111 — {msg}",
                severidade="baixo",
                evidencia=[{
                    "cnpj_declarante": cnpj, "ano_mes": ano_mes,
                    "ind_apro_cred": ind_apro_cred, "0111_presente": True,
                    "0111_linha": reg_0111.get("linha_arquivo") if reg_0111 else None,
                }],
            )
        )

    return divergencias
