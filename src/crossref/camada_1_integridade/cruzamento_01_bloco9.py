"""
Cruzamento 01 — Integridade do Bloco 9 / 9900.

Base legal: IN RFB 1.252/2012, art. 4º — o arquivo deve conter o registro
  9900 com a quantidade exata de cada tipo de registro presente no arquivo,
  e o 9999 deve declarar o total de linhas.

Camada: 1 — Integridade estrutural.
Cruzamento análogo para EFD ICMS/IPI, ECD e ECF ativado em Sprints 6-8.
"""

import logging

from src.models.registros import Divergencia

logger = logging.getLogger(__name__)

CODIGO_REGRA = "CI-01"
DESCRICAO_BASE = "Integridade Bloco 9 — contagem de registros diverge do declarado em 9900"
SEVERIDADE = "alto"


def executar(
    repo,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> list[Divergencia]:
    """
    Compara as quantidades declaradas nos registros 9900 com as contagens
    reais de cada tipo de registro no banco para este (cnpj, ano_mes).

    Limitação Sprint 1: só verifica os registros cujas tabelas existem no
    schema atual (0000, 0110, 0111, C100, C170, M200, M600, 9900).
    """
    divergencias: list[Divergencia] = []

    contagens_db = _contar_registros_db(repo, conn, cnpj, ano_mes)
    regs_9900 = repo.consultar_9900(conn, cnpj, ano_mes)

    for row in regs_9900:
        reg_blc = row["reg_blc"]
        qtd_dec = row["qtd_reg_blc"]
        qtd_real = contagens_db.get(reg_blc, None)

        if qtd_real is None:
            # Registro não tem tabela dedicada — ignorar para Sprint 1
            continue

        if qtd_real != qtd_dec:
            msg = (
                f"{reg_blc}: 9900 declara {qtd_dec} registro(s),"
                f" banco contém {qtd_real}"
            )
            logger.warning("CR-01 %s %d: %s", cnpj, ano_mes, msg)
            divergencias.append(
                Divergencia(
                    codigo_regra=CODIGO_REGRA,
                    descricao=f"{DESCRICAO_BASE} — {msg}",
                    severidade=SEVERIDADE,
                    evidencia=[{
                        "cnpj_declarante": cnpj,
                        "ano_mes": ano_mes,
                        "registro_9900": reg_blc,
                        "qtd_declarada": qtd_dec,
                        "qtd_real_banco": qtd_real,
                    }],
                )
            )

    return divergencias


def _contar_registros_db(repo, conn, cnpj: str, ano_mes: int) -> dict[str, int]:
    """Conta registros por tipo nas tabelas do Sprint 1."""
    tabelas = {
        "0000": "efd_contrib_0000",
        "0110": "efd_contrib_0110",
        "0111": "efd_contrib_0111",
        "C100": "efd_contrib_c100",
        "C170": "efd_contrib_c170",
        "M200": "efd_contrib_m200",
        "M600": "efd_contrib_m600",
        "9900": "efd_contrib_9900",
    }
    resultado: dict[str, int] = {}
    for reg_tipo, tabela in tabelas.items():
        row = conn.execute(
            f"SELECT COUNT(*) FROM {tabela}"
            " WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        resultado[reg_tipo] = row[0] if row else 0
    return resultado
