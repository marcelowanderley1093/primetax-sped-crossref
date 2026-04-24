"""CR-37 — CFOP exportação (EFD ICMS/IPI) × CST_PIS/COFINS (EFD-Contribuições).

Base legal:
  Art. 5º, I e II da Lei 10.637/2002 e Lei 10.833/2003: receitas de exportação
  são não tributadas pelo PIS/COFINS.
  CST_PIS/CST_COFINS '06' (operações de tributação suspensa — exportação direta) e
  '07' (operações de alíquota zero — saídas ao exterior) são os códigos corretos
  para operações de exportação no regime não-cumulativo.
  CFOP série '7xxx' na EFD ICMS/IPI identifica operações de exportação.
  Coerência entre os dois SPEDs (CLAUDE.md §8.3, cruzamento 37): uma operação de
  exportação declarada no SPED Fiscal deve ter o CST correspondente na EFD-Contrib.
  Vigência: Lei 10.637/2002 e Lei 10.833/2003 (regime não-cumulativo).

Lógica:
  Para cada C170 na EFD ICMS/IPI com CFOP início '7':
    Verificar se há C170 correspondente na EFD-Contribuições (mesmo período)
    com CST_PIS NÃO ∈ {'06', '07'} E VL_BC_PIS > 0.
    Se sim → inconsistência: exportação tributada na EFD-Contrib → Oportunidade.

  Implementação pragmática Sprint 6: comparação em nível de período (não item a item),
  pois o COD_ITEM pode ter formatação diferente entre os dois SPEDs. O cruzamento
  sinaliza a existência de operações de exportação no ICMS sem a classificação
  correta na EFD-Contrib para o período inteiro.

Dependência: efd_icms (CLAUDE.md §18).
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-37"

_CST_EXPORTACAO = frozenset({"06", "07"})


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["efd_icms"])
    if disp["efd_icms"] != "importada":
        return [], []

    icms_exportacao = repo.consultar_icms_c170_exportacao(conn, cnpj, ano_mes)
    if not icms_exportacao:
        return [], []

    cfops_exportacao = {r["cfop"] for r in icms_exportacao if r.get("cfop")}

    contrib_c170 = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    if not contrib_c170:
        return [], []

    contrib_exportacao_errado = [
        r for r in contrib_c170
        if r.get("cfop", "")[:1] == "7"
        and str(r.get("cst_pis") or "").strip() not in _CST_EXPORTACAO
        and float(r.get("vl_bc_pis") or 0) > 0
    ]

    if not contrib_exportacao_errado:
        return [], []

    cfops_contrib_errado = list({r["cfop"] for r in contrib_exportacao_errado if r.get("cfop")})
    soma_bc_pis = sum(
        Decimal(str(r.get("vl_bc_pis") or 0)) for r in contrib_exportacao_errado
    )

    descricao = (
        f"EFD ICMS/IPI registra CFOPs de exportação {sorted(cfops_exportacao)}"
        f" mas EFD-Contrib tem {len(contrib_exportacao_errado)} item(ns)"
        f" com CFOP exportação e CST_PIS não em {{06,07}} (VL_BC_PIS total:"
        f" R$ {float(soma_bc_pis):.2f}). Verificar se receita de exportação está"
        f" sendo incorretamente tributada por PIS/COFINS."
    )

    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            valor_impacto_conservador=Decimal("0"),
            valor_impacto_maximo=soma_bc_pis,
            evidencia=[{
                "registro": "C170",
                "arquivo": contrib_exportacao_errado[0]["arquivo_origem"],
                "linha": contrib_exportacao_errado[0]["linha_arquivo"],
                "campos_chave": {
                    "cfops_exportacao_icms": sorted(cfops_exportacao),
                    "cfops_contrib_errado": cfops_contrib_errado,
                    "qtd_itens_cst_errado": len(contrib_exportacao_errado),
                    "soma_vl_bc_pis_afetado": float(soma_bc_pis),
                    "ano_mes": ano_mes,
                },
            }],
        )
    ]
    return oportunidades, []
