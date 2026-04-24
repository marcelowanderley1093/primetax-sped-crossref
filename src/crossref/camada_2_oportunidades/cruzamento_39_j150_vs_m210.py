"""CR-39 — J150 (DRE-ECD) × M210/M610 (EFD-Contribuições): receitas não-operacionais na base.

Base legal:
  Art. 1º da Lei 10.637/2002 e art. 1º da Lei 10.833/2003 — base de cálculo PIS/COFINS
  não-cumulativo: receita bruta de venda de bens e prestação de serviços.
  Receita financeira, aluguel recebido e ganho de capital são tributados por alíquotas
  específicas (Decreto 8.426/2015: 0,65%/4% sobre receita financeira) ou podem ser
  excluídas da base dependendo do regime.
  Se J150 da ECD registra receitas financeiras ou ganhos de capital mas o M210 da
  EFD-Contrib não usa os CST e alíquotas corretos para essas receitas → possível
  tributação indevida (alíquota plena de 1,65%/7,6% em vez de 0,65%/4%) ou exclusão
  indevida.
  Vigência: Decreto 8.426/2015 (01/07/2015) para receitas financeiras de PJ não-cumulativa.

Lógica:
  1. Identifica J150 da DRE (J005.ID_DEM='02') com IND_GRP_DRE='07' (receitas financeiras)
     ou IND_GRP_DRE='08' (outros rendimentos/ganhos) com VL_CTA_FIN > threshold.
  2. Verifica M210 do mesmo ano se há contribuição com COD_CONT para receita financeira
     (CST='99' — outras receitas, ou CST='73'/'75' para alíquotas de 0,65%).
  3. Se J150 registra receita financeira significativa mas M210 não tem linha dedicada → fires.

Dependência: ecd (CLAUDE.md §18).
modo_degradado_suportado: True (CLAUDE.md §16.3).
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias
from src.crossref.common.reconciliacao_plano_contas import classificar_reconciliacao

CODIGO_REGRA = "CR-39"
MODO_DEGRADADO_SUPORTADO = True
_THRESHOLD_RECEITA_FIN = Decimal("5000")   # mínimo para disparar (evita ruído em centavos)

# IND_GRP_DRE que indicam receitas fora da receita operacional bruta
_GRP_DRE_NAOOPERACIONAL = {"07", "08", "09"}


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecd"])
    if disp["ecd"] != "importada":
        return [], []

    j150_dre = repo.consultar_ecd_j150_dre(conn, cnpj, ano_calendario)
    if not j150_dre:
        return [], []

    # Identifica linhas com receitas não-operacionais relevantes na DRE
    linhas_nao_op = [
        r for r in j150_dre
        if r.get("ind_grp_dre") in _GRP_DRE_NAOOPERACIONAL
        and float(r.get("vl_cta_fin") or 0) > 0
    ]

    if not linhas_nao_op:
        return [], []

    soma_nao_op = sum(
        Decimal(str(r.get("vl_cta_fin") or 0)) for r in linhas_nao_op
    )

    if soma_nao_op < _THRESHOLD_RECEITA_FIN:
        return [], []

    # Verifica M210 — se há contribuição com COD_CONT indicando alíquota reduzida
    # COD_CONT para receita financeira em PJ não-cumulativa usa CST '70'/'73'/'75'
    m210_registros = repo.consultar_m210_anual(conn, cnpj, ano_calendario)
    cst_m210 = {r.get("cod_cont", "")[:2] for r in m210_registros}

    # CST indicativos de alíquota reduzida (receita financeira, aluguel, etc.)
    cst_nao_operacional = {"70", "73", "75", "98", "99"}
    tem_cst_adequado = bool(cst_m210 & cst_nao_operacional)

    if tem_cst_adequado:
        return [], []

    # CR-39 opera por IND_GRP_DRE (agregação já natureza-level da DRE), portanto
    # produz o mesmo resultado em modo integral ou degradado (§16.3). Quando a
    # reconciliação está comprometida, o campo `modo_execucao` sinaliza para o
    # auditor que a análise seguiu sem reconciliação granular do plano.
    reconc = classificar_reconciliacao(repo, conn, cnpj, ano_calendario)
    modo_degradado = reconc in ("suspeita", "ausente")
    sufixo = f" [modo degradado — reconciliação '{reconc}']" if modo_degradado else ""

    descricao = (
        f"DRE (ECD J150) registra R$ {float(soma_nao_op):,.2f} em receitas "
        f"não-operacionais (grupos DRE: {sorted(set(r.get('ind_grp_dre') for r in linhas_nao_op))}) "
        f"no AC {ano_calendario}{sufixo}. O M210 da EFD-Contribuições não apresenta linha com CST "
        f"de alíquota reduzida para receita financeira (CSTs 70/73/75) ou outras receitas (98/99). "
        f"Verificar se receitas financeiras estão sendo tributadas à alíquota plena (1,65%/7,6%) "
        f"em vez da alíquota específica (0,65%/4% — Decreto 8.426/2015)."
    )

    primeiro = linhas_nao_op[0]
    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            valor_impacto_conservador=Decimal("0"),
            valor_impacto_maximo=Decimal("0"),
            evidencia=[{
                "registro": "J150",
                "arquivo": primeiro["arquivo_origem"],
                "linha": primeiro["linha_arquivo"],
                "campos_chave": {
                    "soma_receita_nao_operacional": float(soma_nao_op),
                    "qtd_linhas_j150_nao_op": len(linhas_nao_op),
                    "grupos_dre": sorted({r.get("ind_grp_dre") for r in linhas_nao_op}),
                    "cst_m210_encontrados": sorted(cst_m210),
                    "ano_calendario": ano_calendario,
                    "modo_execucao": "degradado" if modo_degradado else "integra",
                    "reconciliacao_plano_contas": reconc,
                },
            }],
        )
    ]
    return oportunidades, []
