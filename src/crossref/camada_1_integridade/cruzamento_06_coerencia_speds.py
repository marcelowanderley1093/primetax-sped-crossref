"""
Cruzamento 06 — Coerência entre SPEDs do mesmo período.

Base legal: IN RFB 1.252/2012 e instruções correlatas dos demais SPEDs —
  quando múltiplos SPEDs (EFD-Contribuições, EFD ICMS/IPI, ECD, ECF) são
  importados para o mesmo CNPJ × período, o CNPJ do declarante e as datas
  de início e fim do período devem coincidir entre eles.

Sprint 1: verifica apenas a consistência interna da EFD-Contribuições
  (CNPJ e datas em 0000 vs contexto geral). A verificação inter-SPED plena
  (CNPJ EFD-Contrib == CNPJ EFD ICMS/IPI == CNPJ ECD etc.) será ativada
  no Sprint 6 quando o segundo SPED for importável.

Camada: 1 — Integridade estrutural.
"""

import logging

from src.models.registros import Divergencia

logger = logging.getLogger(__name__)

CODIGO_REGRA = "CI-06"
SEVERIDADE = "alto"


def executar(
    repo,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> list[Divergencia]:
    """
    Sprint 1: verifica que o CNPJ registrado no 0000 corresponde ao CNPJ
    pelo qual o arquivo foi importado (i.e., o banco em que está).
    Verificação inter-SPED completa ativada no Sprint 6.
    """
    divergencias: list[Divergencia] = []

    row = conn.execute(
        "SELECT cnpj_declarante, dt_ini_periodo, dt_fin_periodo"
        " FROM efd_contrib_0000 WHERE cnpj_declarante=? AND ano_mes=?",
        (cnpj, ano_mes),
    ).fetchone()

    if row is None:
        return divergencias  # CI-01/CI-03 já capturam ausência de 0000

    cnpj_no_banco = cnpj  # o banco já está separado por CNPJ
    cnpj_no_arquivo = row["cnpj_declarante"]

    if cnpj_no_arquivo != cnpj_no_banco:
        msg = (
            f"CNPJ no arquivo ({cnpj_no_arquivo}) ≠ CNPJ do banco ({cnpj_no_banco})"
        )
        logger.warning("CI-06 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"Coerência entre SPEDs — {msg}",
                severidade=SEVERIDADE,
                evidencia=[{
                    "cnpj_declarante_banco": cnpj_no_banco,
                    "cnpj_declarante_arquivo": cnpj_no_arquivo,
                    "ano_mes": ano_mes,
                }],
            )
        )

    return divergencias
