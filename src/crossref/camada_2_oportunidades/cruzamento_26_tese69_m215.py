"""
Cruzamento CR-26 — Tese 69 via ajuste de base M215/M615 (abordagem agregada).

Base legal: RE 574.706/PR (Tema 69 STF); Lei 10.637/2002 art. 1º;
            Lei 10.833/2003 art. 1º; IN RFB 1.252/2012.
            Leiaute EFD-Contribuições 3.1.0 (vigente desde jan/2019, CLAUDE.md §5.2):
            o registro M215 foi criado para operacionalizar a exclusão do ICMS na
            base de PIS/COFINS de forma agregada por período (método alternativo
            ao item-a-item via C170/CR-07).
            Parecer SEI 7698/2021/ME — operacionalização da Tese 69 pela PGFN.

Condição de ativação: DT_INI >= 2019-01-01.

Lógica:
    Compara Σ VL_ICMS dos C170 elegíveis (CSTs Tese 69) com Σ VL_AJ_BC das
    reduções de M215 declaradas no período.
    Gap = Σ VL_ICMS - Σ M215.VL_AJ_BC(IND_AJ_BC="0")

    Conservador: assume M215 reductions ARE all Tema 69 → menor gap (crédito
                 máximo às M215 reduções).
    Máximo: assume M215 reductions are NOT Tema 69 → maior gap (ignora M215).

Complementaridade com CR-07:
    CR-07 detecta item-a-item em C170. CR-26 fornece perspectiva agregada via
    M215, útil quando a empresa usa o método de ajuste de base para parte dos
    períodos e o método item-a-item para outros.
"""

from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade
from src.rules.tese_69_ajuste_base import calcular_gap_m215

CODIGO_REGRA = "CR-26"


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    """
    Detecta gap residual de ICMS não excluído da base de PIS/COFINS comparando
    C170 com M215/M615 declarados (método agregado, leiaute 3.1.0+).
    """
    # Obtém data de início do período para verificar elegibilidade
    ctx_row = conn.execute(
        "SELECT dt_ini_periodo FROM efd_contrib_0000"
        " WHERE cnpj_declarante=? AND ano_mes=? LIMIT 1",
        (cnpj, ano_mes),
    ).fetchone()
    if ctx_row is None:
        return [], []

    dt_ini = ctx_row["dt_ini_periodo"]  # YYYY-MM-DD

    # Dados necessários
    c170_items = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    m215_reducoes = repo.consultar_m215_reducoes(conn, cnpj, ano_mes)
    m615_reducoes = repo.consultar_m615_reducoes(conn, cnpj, ano_mes)

    resultado = calcular_gap_m215(c170_items, m215_reducoes, m615_reducoes, dt_ini)
    if resultado is None:
        return [], []

    evidencia = {
        "bloco": "M",
        "registro": "M215",
        "arquivo_origem": c170_items[0].get("arquivo_origem", "") if c170_items else "",
        "linha_arquivo": 0,
        "cnpj_declarante": cnpj,
        "ano_mes": ano_mes,
        "campos_chave": {
            "soma_icms_c170": float(resultado["soma_icms_c170"]),
            "soma_m215_reducoes": float(resultado["soma_m215_reducoes"]),
            "soma_m615_reducoes": float(resultado["soma_m615_reducoes"]),
            "gap_pis": float(resultado["gap_pis"]),
            "gap_cofins": float(resultado["gap_cofins"]),
            "aliq_pis_ponderada": float(resultado["aliq_pis_ponderada"]),
            "aliq_cofins_ponderada": float(resultado["aliq_cofins_ponderada"]),
            "qtd_itens_elegiveis_c170": resultado["qtd_itens_elegiveis"],
        },
    }

    op = Oportunidade(
        codigo_regra=CODIGO_REGRA,
        descricao=(
            f"Período {ano_mes}: Σ ICMS nos C170 elegíveis = "
            f"R$ {float(resultado['soma_icms_c170']):.2f}; "
            f"M215 reduções = R$ {float(resultado['soma_m215_reducoes']):.2f}. "
            f"Gap residual: impacto conservador R$ {float(resultado['valor_impacto_conservador']):.2f} "
            f"/ máximo R$ {float(resultado['valor_impacto_maximo']):.2f}."
        ),
        severidade="alto",
        valor_impacto_conservador=resultado["valor_impacto_conservador"],
        valor_impacto_maximo=resultado["valor_impacto_maximo"],
        evidencia=[evidencia],
    )

    return [op], []
