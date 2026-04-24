"""
CR-16 — Retenções de PIS/Pasep na fonte não-compensadas (F600).

Base legal:
  Art. 30 da Lei 10.833/2003 — retenção na fonte sobre pagamentos entre PJs
  Art. 33 da Lei 10.833/2003 — compensação com débitos próprios
  Art. 34 da Lei 10.833/2003 — ressarcimento quando retenção exceder débitos
  IN RFB 1.252/2012 — leiaute EFD-Contribuições; registro F600 vigente desde ago/2013.

Severidade: alto — saldo positivo corresponde a crédito direto recuperável via PER/DCOMP.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade
from src.rules.retencoes_fonte import verificar_saldo_retencao

logger = logging.getLogger(__name__)
CODIGO_REGRA = "CR-16"
DEPENDENCIAS_SPED = ["efd_contribuicoes"]

_DATA_DIAGNOSTICO: date | None = None  # substituível em testes


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    """Analisa F600 do período buscando retenções PIS com saldo não-compensado."""
    registros = repo.consultar_f600_por_periodo(conn, cnpj, ano_mes)
    hoje = _DATA_DIAGNOSTICO or date.today()
    oportunidades: list[Oportunidade] = []

    for row in registros:
        resultado = verificar_saldo_retencao(
            ind_nat_ret=row["ind_nat_ret"],
            dt_ret_str=row["dt_ret"],
            vl_ret_apu=Decimal(str(row["vl_ret_apu"])),
            vl_ret_per=Decimal(str(row["vl_ret_per"])),
            vl_ret_dcomp=Decimal(str(row["vl_ret_dcomp"])),
            cod_rec=row["cod_rec"],
            ind_nat_rec=row["ind_nat_rec"],
            cnpj_fonte_pag=row["cnpj_fonte_pag"],
            linha_arquivo=row["linha_arquivo"],
            arquivo_origem=row["arquivo_origem"],
            data_diagnostico=hoje,
        )
        if resultado is None or resultado.prescrito:
            continue  # zero saldo ou prescrito → CR-19 trata

        saldo = resultado.saldo_nao_compensado
        oportunidades.append(
            Oportunidade(
                codigo_regra=CODIGO_REGRA,
                descricao=(
                    f"Retenção PIS na fonte com saldo não-compensado de "
                    f"R$ {saldo:.2f} (DT_RET {resultado.dt_ret}, "
                    f"CNPJ fonte {resultado.cnpj_fonte_pag}). "
                    "Recuperável via PER/DCOMP (art. 33 Lei 10.833/2003) "
                    "ou ressarcimento (art. 34)."
                ),
                severidade="alto",
                valor_impacto_conservador=saldo,
                valor_impacto_maximo=saldo,
                evidencia=[{
                    "bloco": "F",
                    "registro": "F600",
                    "linha_arquivo": resultado.linha_arquivo,
                    "arquivo_origem": resultado.arquivo_origem,
                    "cnpj_declarante": cnpj,
                    "ano_mes": ano_mes,
                    "campos_chave": {
                        "dt_ret": resultado.dt_ret,
                        "cnpj_fonte_pag": resultado.cnpj_fonte_pag,
                        "cod_rec": resultado.cod_rec,
                        "ind_nat_ret": resultado.ind_nat_ret,
                        "saldo_nao_compensado": float(saldo),
                        "data_prescricao": resultado.data_prescricao,
                    },
                }],
            )
        )

    logger.info("CR-16 %s %d: %d F600 analisados, %d oportunidades",
                cnpj, ano_mes, len(registros), len(oportunidades))
    return oportunidades, []
