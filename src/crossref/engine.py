"""
Motor de cruzamentos — Sprint 8.

Orquestra a execução dos cruzamentos da Camada 1 (integridade), Camada 2
(oportunidades) e Camada 3 (consistência) para um CNPJ × ano-calendário.

CLAUDE.md §9: `primetax-sped import` roda Camada 1; `diagnose` roda Camadas 2 e 3.
Sprint 1: CR-01 a CR-07. Sprint 2: CR-08, CR-09, CR-26. Sprint 3: CR-16, CR-17, CR-19, CR-31.
Sprint 4: CR-14, CR-15, CR-22, CR-27, CR-28, CR-29, CR-30.
Sprint 5: CR-10, CR-11, CR-12, CR-13, CR-18, CR-20, CR-21, CR-23, CR-25, CR-32, CR-33, CR-34.
Sprint 6: CR-35, CR-36, CR-37 (EFD ICMS/IPI × EFD-Contribuições).
Sprint 7: CR-38, CR-39, CR-40, CR-41, CR-42 (ECD × EFD-Contribuições).
Sprint 8: CR-43, CR-44, CR-45, CR-46, CR-47 (ECF × ECD e ECF isolada).
"""

import logging
from decimal import Decimal

from src.crossref.camada_1_integridade import (
    cruzamento_01_bloco9,
    cruzamento_02_unicidade_m,
    cruzamento_03_presenca_0110,
    cruzamento_04_0110_0111,
    cruzamento_05_hierarquia,
    cruzamento_06_coerencia_speds,
)
from src.crossref.camada_2_oportunidades import (
    cruzamento_07_tese69_c170,
    cruzamento_08_tese69_c181,
    cruzamento_09_tese69_d201,
    cruzamento_10_cst_aliquota_c170,
    cruzamento_11_tipo_item_cfop_insumo,
    cruzamento_12_cst_70_75_auditoria,
    cruzamento_13_ausencia_f100,
    cruzamento_14_f120_depreciacao,
    cruzamento_15_f130_aquisicao,
    cruzamento_16_retencoes_pis_f600,
    cruzamento_17_retencoes_cofins_f700,
    cruzamento_18_f800_evento_corporativo,
    cruzamento_19_retencoes_prescritas,
    cruzamento_20_credito_presumido_setorial,
    cruzamento_21_frete_subcontratado,
    cruzamento_22_f150_estoque,
    cruzamento_23_cst_98_99_imobilizado,
    cruzamento_25_saldo_credito_1100,
    cruzamento_26_tese69_m215,
    cruzamento_27_imob_uso_vedado,
    cruzamento_28_rateio_vs_direto,
    cruzamento_35_ciap_vs_f120_f130,
    cruzamento_36_h010_vs_f150,
    cruzamento_37_cfop_exportacao,
    cruzamento_38_i155_vs_m200,
    cruzamento_39_j150_vs_m210,
    cruzamento_40_cod_cta_vs_i050,
    cruzamento_41_lancamento_extemporaneo,
    cruzamento_42_tipo_item_vs_i050,
    cruzamento_43_k155_vs_i155,
    cruzamento_44_m300_vs_i200,
    cruzamento_45_parte_b_estagnada,
    cruzamento_46_x480_vs_m300,
    cruzamento_47_y570_irrf,
    cruzamento_48_avisos_ecf_9100,
    cruzamento_49_x460_lei_do_bem,
)
from src.crossref.camada_3_consistencia import (
    cruzamento_29_m100_m200_fluxo_pis,
    cruzamento_30_m500_m600_fluxo_cofins,
    cruzamento_31_bc_pis_vs_m210,
    cruzamento_32_bc_pis_vs_m105,
    cruzamento_33_bc_cofins_vs_m610,
    cruzamento_34_bc_cofins_vs_m505,
)
from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade

logger = logging.getLogger(__name__)

_CRUZAMENTOS_CAMADA1 = [
    cruzamento_01_bloco9,
    cruzamento_02_unicidade_m,
    cruzamento_03_presenca_0110,
    cruzamento_04_0110_0111,
    cruzamento_05_hierarquia,
    cruzamento_06_coerencia_speds,
]

_CRUZAMENTOS_CAMADA2 = [
    cruzamento_07_tese69_c170,
    cruzamento_08_tese69_c181,
    cruzamento_09_tese69_d201,
    cruzamento_10_cst_aliquota_c170,
    cruzamento_11_tipo_item_cfop_insumo,
    cruzamento_12_cst_70_75_auditoria,
    cruzamento_13_ausencia_f100,
    cruzamento_14_f120_depreciacao,
    cruzamento_15_f130_aquisicao,
    cruzamento_16_retencoes_pis_f600,
    cruzamento_17_retencoes_cofins_f700,
    cruzamento_18_f800_evento_corporativo,
    cruzamento_19_retencoes_prescritas,
    cruzamento_20_credito_presumido_setorial,
    cruzamento_21_frete_subcontratado,
    cruzamento_22_f150_estoque,
    cruzamento_23_cst_98_99_imobilizado,
    cruzamento_25_saldo_credito_1100,
    cruzamento_26_tese69_m215,
    cruzamento_27_imob_uso_vedado,
    cruzamento_28_rateio_vs_direto,
    cruzamento_35_ciap_vs_f120_f130,
    cruzamento_36_h010_vs_f150,
    cruzamento_37_cfop_exportacao,
    cruzamento_38_i155_vs_m200,
    cruzamento_39_j150_vs_m210,
    cruzamento_40_cod_cta_vs_i050,
    cruzamento_41_lancamento_extemporaneo,
    cruzamento_42_tipo_item_vs_i050,
    cruzamento_43_k155_vs_i155,
    cruzamento_44_m300_vs_i200,
    cruzamento_45_parte_b_estagnada,
    cruzamento_46_x480_vs_m300,
    cruzamento_47_y570_irrf,
    cruzamento_48_avisos_ecf_9100,
    cruzamento_49_x460_lei_do_bem,
]

_CRUZAMENTOS_CAMADA3 = [
    cruzamento_29_m100_m200_fluxo_pis,
    cruzamento_30_m500_m600_fluxo_cofins,
    cruzamento_31_bc_pis_vs_m210,
    cruzamento_32_bc_pis_vs_m105,
    cruzamento_33_bc_cofins_vs_m610,
    cruzamento_34_bc_cofins_vs_m505,
]


class Motor:
    def __init__(self, repo: Repositorio):
        self.repo = repo

    def executar_camada1(
        self, conn, cnpj: str, ano_mes: int, ano_calendario: int
    ) -> list[Divergencia]:
        """Executa todos os cruzamentos de integridade para um período."""
        divergencias: list[Divergencia] = []
        for modulo in _CRUZAMENTOS_CAMADA1:
            try:
                divs = modulo.executar(self.repo, conn, cnpj, ano_mes, ano_calendario)
                divergencias.extend(divs)
            except Exception as exc:
                logger.error(
                    "Erro no %s para %s/%d: %s",
                    modulo.CODIGO_REGRA, cnpj, ano_mes, exc,
                )
        return divergencias

    def executar_camada2(
        self, conn, cnpj: str, ano_mes: int, ano_calendario: int
    ) -> tuple[list[Oportunidade], list[Divergencia]]:
        """Executa todos os cruzamentos de oportunidades para um período."""
        todas_ops: list[Oportunidade] = []
        todas_divs: list[Divergencia] = []
        for modulo in _CRUZAMENTOS_CAMADA2:
            try:
                ops, divs = modulo.executar(self.repo, conn, cnpj, ano_mes, ano_calendario)
                todas_ops.extend(ops)
                todas_divs.extend(divs)
            except Exception as exc:
                logger.error(
                    "Erro no %s para %s/%d: %s",
                    modulo.CODIGO_REGRA, cnpj, ano_mes, exc,
                )
        return todas_ops, todas_divs

    def executar_camada3(
        self, conn, cnpj: str, ano_mes: int, ano_calendario: int
    ) -> tuple[list[Oportunidade], list[Divergencia]]:
        """Executa todos os cruzamentos de consistência intra-SPED para um período."""
        todas_ops: list[Oportunidade] = []
        todas_divs: list[Divergencia] = []
        for modulo in _CRUZAMENTOS_CAMADA3:
            try:
                ops, divs = modulo.executar(self.repo, conn, cnpj, ano_mes, ano_calendario)
                todas_ops.extend(ops)
                todas_divs.extend(divs)
            except Exception as exc:
                logger.error(
                    "Erro no %s para %s/%d: %s",
                    modulo.CODIGO_REGRA, cnpj, ano_mes, exc,
                )
        return todas_ops, todas_divs

    def diagnosticar_ano(self, ano_calendario: int) -> dict:
        """
        Executa diagnóstico completo (Camadas 1 e 2) para todos os meses
        importados no ano-calendário. Retorna sumário.

        Para clientes com ECF/ECD mas sem EFD-Contribuições (ex: Simples Nacional
        que entregou ECF voluntariamente), usa o período sintético {ano}01 para
        permitir execução dos cruzamentos anuais (CR-43 a CR-47).
        """
        cnpj = self.repo.cnpj
        conn = self.repo.conexao()
        try:
            meses = self.repo.consultar_meses_importados(conn, cnpj, ano_calendario)
            if not meses:
                # Verifica se há dados de SPEDs anuais (ECF ou ECD) antes de desistir.
                ctx = self.repo.consultar_sped_contexto(conn)
                tem_anual = ctx and (
                    ctx.get("disponibilidade_ecf") == "importada"
                    or ctx.get("disponibilidade_ecd") == "importada"
                )
                if not tem_anual:
                    logger.warning("Nenhum dado importado para CNPJ=%s AC=%d", cnpj, ano_calendario)
                    return {"cnpj": cnpj, "ano_calendario": ano_calendario, "meses": []}
                # Período sintético: permite cruzamentos anuais (ECF/ECD) rodarem.
                meses = [ano_calendario * 100 + 1]
                logger.info(
                    "Sem EFD-Contribuições; usando período sintético %d para cruzamentos anuais",
                    meses[0],
                )

            # Bug-005 — DELETE prévio em re-diagnóstico. Cada chamada de
            # diagnosticar_ano gera um snapshot fresh; rows anteriores
            # (incluindo anotações de auditor revisado_em/nota) são
            # apagadas. Limitação consciente — ver
            # docs/debitos-conhecidos.md entrada Bug-005.
            with conn:
                qtd_op_apagadas, qtd_div_apagadas = (
                    self.repo.deletar_diagnostico_anterior(
                        conn, cnpj, ano_calendario,
                    )
                )
            if qtd_op_apagadas + qtd_div_apagadas > 0:
                logger.info(
                    "Re-diagnóstico para CNPJ=%s AC=%d: %d oportunidades + "
                    "%d divergências antigas removidas (Bug-005 fix; "
                    "anotações prévias também perdidas)",
                    cnpj, ano_calendario, qtd_op_apagadas, qtd_div_apagadas,
                )

            resultado_por_mes = []
            for ano_mes in meses:
                divs_c1 = self.executar_camada1(conn, cnpj, ano_mes, ano_calendario)
                ops_c2, divs_c2 = self.executar_camada2(conn, cnpj, ano_mes, ano_calendario)
                ops_c3, divs_c3 = self.executar_camada3(conn, cnpj, ano_mes, ano_calendario)

                todas_ops = ops_c2 + ops_c3
                todas_divs = divs_c1 + divs_c2 + divs_c3

                with conn:
                    for div in todas_divs:
                        self.repo.inserir_divergencia(conn, div, cnpj, ano_mes, ano_calendario)
                    for op in todas_ops:
                        self.repo.inserir_oportunidade(conn, op, cnpj, ano_mes, ano_calendario)

                imp_cons = sum(
                    (op.valor_impacto_conservador for op in todas_ops), Decimal("0")
                )
                imp_max = sum(
                    (op.valor_impacto_maximo for op in todas_ops), Decimal("0")
                )

                resultado_por_mes.append({
                    "ano_mes": ano_mes,
                    "divergencias_camada1": len(divs_c1),
                    "oportunidades_camada2": len(ops_c2),
                    "divergencias_camada2": len(divs_c2),
                    "oportunidades_camada3": len(ops_c3),
                    "divergencias_camada3": len(divs_c3),
                    "impacto_conservador": float(imp_cons),
                    "impacto_maximo": float(imp_max),
                })

                logger.info(
                    "Diagnóstico %s %d: C1div=%d C2op=%d C3op=%d impacto=R$%.2f~R$%.2f",
                    cnpj, ano_mes, len(divs_c1), len(ops_c2), len(ops_c3),
                    float(imp_cons), float(imp_max),
                )

        finally:
            conn.close()

        return {
            "cnpj": cnpj,
            "ano_calendario": ano_calendario,
            "meses": resultado_por_mes,
        }
