"""
Cruzamento 03 — Presença e validade do registro 0110.

Base legal: IN RFB 1.252/2012, leiaute EFD-Contribuições — o registro 0110
  é obrigatório e define o regime de apuração (COD_INC_TRIB) e o método de
  apropriação de créditos (IND_APRO_CRED), que são contexto global de toda a
  escrituração do período.

  COD_INC_TRIB válidos: "1" (não-cumulativo), "2" (cumulativo), "3" (ambos).
  IND_APRO_CRED válidos: "1" (direta), "2" (rateio proporcional).

Camada: 1 — Integridade estrutural.
"""

import logging

from src.models.registros import Divergencia

logger = logging.getLogger(__name__)

CODIGO_REGRA = "CI-03"
SEVERIDADE = "alto"

_COD_INC_TRIB_VALIDOS = frozenset({"1", "2", "3"})
_IND_APRO_CRED_VALIDOS = frozenset({"1", "2"})


def executar(
    repo,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> list[Divergencia]:
    divergencias: list[Divergencia] = []

    reg = repo.consultar_0110(conn, cnpj, ano_mes)

    if reg is None:
        logger.warning("CI-03 %s %d: 0110 ausente", cnpj, ano_mes)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao="0110 ausente — parâmetros de regime não declarados",
                severidade=SEVERIDADE,
                evidencia=[{"cnpj_declarante": cnpj, "ano_mes": ano_mes}],
            )
        )
        return divergencias

    cod_inc_trib = reg.get("cod_inc_trib", "")
    ind_apro_cred = reg.get("ind_apro_cred", "")

    if cod_inc_trib not in _COD_INC_TRIB_VALIDOS:
        msg = f"COD_INC_TRIB inválido: {cod_inc_trib!r} (esperado 1, 2 ou 3)"
        logger.warning("CI-03 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"0110 inválido — {msg}",
                severidade=SEVERIDADE,
                evidencia=[{
                    "cnpj_declarante": cnpj, "ano_mes": ano_mes,
                    "linha_arquivo": reg.get("linha_arquivo"),
                    "campo": "COD_INC_TRIB", "valor": cod_inc_trib,
                }],
            )
        )

    if ind_apro_cred not in _IND_APRO_CRED_VALIDOS:
        msg = f"IND_APRO_CRED inválido: {ind_apro_cred!r} (esperado 1 ou 2)"
        logger.warning("CI-03 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"0110 inválido — {msg}",
                severidade=SEVERIDADE,
                evidencia=[{
                    "cnpj_declarante": cnpj, "ano_mes": ano_mes,
                    "linha_arquivo": reg.get("linha_arquivo"),
                    "campo": "IND_APRO_CRED", "valor": ind_apro_cred,
                }],
            )
        )

    return divergencias
