"""
CR-19 — Retenções PIS/COFINS na fonte prescritas ou com prescrição iminente.

Base legal:
  Art. 168, I do CTN (Lei 5.172/1966) — prazo decadencial de 5 anos para
    pedido de restituição/compensação, contado da data do pagamento indevido
    (i.e., da data da retenção — DT_RET).
  Art. 74 da Lei 9.430/1996 — PER/DCOMP como instrumento de compensação.
  IN RFB 1.252/2012 — leiaute; F600 e F700 vigentes desde ago/2013 (CLAUDE.md §5.2).

Execução: apenas no período mais recente importado do ano-calendário,
para evitar duplicatas no diagnóstico anual consolidado.

Janela de alerta: retentions que prescrevem em <= 12 meses (urgência alta).
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade
from src.rules.retencoes_fonte import verificar_saldo_retencao

logger = logging.getLogger(__name__)
CODIGO_REGRA = "CR-19"
DEPENDENCIAS_SPED = ["efd_contribuicoes"]

_DATA_DIAGNOSTICO: date | None = None
_MESES_ALERTA = 12


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    """
    Varre historicamente todos os F600/F700 importados para o CNPJ × ano-calendário,
    identificando retenções com saldo positivo que já prescreveram ou prescreverão
    em até 12 meses. Só executa no período mais recente para evitar duplicatas.
    """
    meses = repo.consultar_meses_importados(conn, cnpj, ano_calendario)
    if not meses or ano_mes != max(meses):
        # Só dispara no último mês importado — evita repetição nos meses anteriores
        return [], []

    hoje = _DATA_DIAGNOSTICO or date.today()
    f600_rows = repo.consultar_f600_historico(conn, cnpj, ano_calendario)
    f700_rows = repo.consultar_f700_historico(conn, cnpj, ano_calendario)

    oportunidades: list[Oportunidade] = []
    divergencias: list[Divergencia] = []

    for tributo, rows, registro in [
        ("PIS", f600_rows, "F600"),
        ("COFINS", f700_rows, "F700"),
    ]:
        for row in rows:
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
            if resultado is None:
                continue  # saldo zero

            from datetime import datetime
            try:
                dt_presc = datetime.strptime(resultado.data_prescricao, "%Y-%m-%d").date()
                delta_dias = (dt_presc - hoje).days
                meses_restantes = delta_dias // 30
            except ValueError:
                continue

            evidencia_base = {
                "bloco": "F",
                "registro": registro,
                "linha_arquivo": resultado.linha_arquivo,
                "arquivo_origem": resultado.arquivo_origem,
                "cnpj_declarante": cnpj,
                "ano_mes": row.get("ano_mes", ano_mes),
                "campos_chave": {
                    "tributo": tributo,
                    "dt_ret": resultado.dt_ret,
                    "cnpj_fonte_pag": resultado.cnpj_fonte_pag,
                    "cod_rec": resultado.cod_rec,
                    "saldo_nao_compensado": float(resultado.saldo_nao_compensado),
                    "data_prescricao": resultado.data_prescricao,
                    "meses_restantes": meses_restantes,
                },
            }

            if resultado.prescrito:
                saldo = resultado.saldo_nao_compensado
                divergencias.append(
                    Divergencia(
                        codigo_regra=CODIGO_REGRA,
                        descricao=(
                            f"Retenção {tributo} prescrita: R$ {saldo:.2f} "
                            f"(DT_RET {resultado.dt_ret}, fonte {resultado.cnpj_fonte_pag}). "
                            "Prazo quinquenal expirado (CTN art. 168 I) — "
                            "direito à compensação/restituição perdido."
                        ),
                        severidade="critico",
                        evidencia=[{**evidencia_base, "campos_chave": {
                            **evidencia_base["campos_chave"],
                            "saldo_perdido": float(saldo),
                        }}],
                    )
                )
            elif meses_restantes <= _MESES_ALERTA:
                saldo = resultado.saldo_nao_compensado
                oportunidades.append(
                    Oportunidade(
                        codigo_regra=CODIGO_REGRA,
                        descricao=(
                            f"Retenção {tributo} com prescrição iminente: "
                            f"R$ {saldo:.2f} prescre em {resultado.data_prescricao} "
                            f"(~{meses_restantes} meses). "
                            "Acionar PER/DCOMP imediatamente (art. 74 Lei 9.430/1996)."
                        ),
                        severidade="alto",
                        valor_impacto_conservador=saldo,
                        valor_impacto_maximo=saldo,
                        evidencia=[evidencia_base],
                    )
                )

    logger.info(
        "CR-19 %s AC=%d: %d F600 + %d F700 analisados → %d urgentes, %d prescritas",
        cnpj, ano_calendario, len(f600_rows), len(f700_rows),
        len(oportunidades), len(divergencias),
    )
    return oportunidades, divergencias
