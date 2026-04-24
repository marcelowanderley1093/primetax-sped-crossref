"""
Regra: Tese 69 (RE 574.706/PR) via ajuste de base M215/M615 (CR-26).

Base legal:
    RE 574.706/PR (Tema 69 STF) — exclusão do ICMS da base de PIS/COFINS.
    Lei 10.637/2002, art. 1º; Lei 10.833/2003, art. 1º.
    IN RFB 1.252/2012 — EFD-Contribuições, registros M215/M615 (ajustes de base).
    Leiaute EFD-Contribuições 3.1.0, vigente a partir de 01/01/2019 (CLAUDE.md §5.2):
    o registro M215 foi criado precisamente para operacionalizar a exclusão do ICMS
    na base de PIS/COFINS de forma agregada por período (em oposição ao método
    item-a-item via C170, que é detectado pelo CR-07).
    Parecer SEI 7698/2021/ME — operacionalização da Tese 69 pela PGFN.

Lógica:
    Para o período (cnpj × ano_mes), soma o VL_ICMS dos C170 elegíveis (CSTs Tese 69,
    saídas) como proxy do ICMS que deveria ter sido excluído da base.
    Compara com as reduções declaradas em M215 (IND_AJ_BC="0").

    Gap = Σ VL_ICMS(C170 elegíveis) − Σ VL_AJ_BC(M215 reduções)

    Se gap > 0:
        valor_impacto_conservador: gap × alíquotas ponderadas
            (assume que TODAS as M215 reduções correspondem ao ICMS → menor oportunidade)
        valor_impacto_maximo: Σ VL_ICMS × alíquotas ponderadas
            (assume que NENHUMA M215 redução corresponde ao ICMS → maior oportunidade)

Condição de ativação:
    Somente para DT_INI >= 2019-01-01 (leiaute 3.1.0+). Para períodos anteriores,
    o método item-a-item via CR-07 é suficiente.
"""

from decimal import Decimal

from src.tables.cst_pis import CST_TESE_69

_ALIQ_COFINS_MEDIA = Decimal("0.076")
_ALIQ_PIS_MEDIA = Decimal("0.0165")


def calcular_gap_m215(
    c170_items: list[dict],
    m215_reducoes: list[dict],
    m615_reducoes: list[dict],
    dt_ini: str,
) -> dict | None:
    """
    Calcula a oportunidade residual de ICMS não excluído da base (abordagem agregada).

    Args:
        c170_items: Registros C170 do período (todos os CSTs).
        m215_reducoes: M215 com IND_AJ_BC="0" do período.
        m615_reducoes: M615 com IND_AJ_BC="0" do período.
        dt_ini: Data de início do período "YYYY-MM-DD" para verificar elegibilidade.

    Returns:
        Dict com campos de oportunidade, ou None se sem gap ou período não elegível.
    """
    # Cruzamento 26 só é relevante para leiaute 3.1.0+ (jan/2019).
    # Para períodos anteriores, CR-07 (C170 item-a-item) é o método correto.
    if dt_ini < "2019-01-01":
        return None

    # Filtra C170 elegíveis: saídas com CST Tese 69
    elegíveis = [
        r for r in c170_items
        if r.get("cst_pis", "").strip() in CST_TESE_69
        and r.get("ind_oper", "1") == "1"  # default "1" quando vem de consulta SQL
    ]

    # Para C170 da tabela SQL, ind_oper vem do C100 pai — a tabela não armazena
    # ind_oper diretamente. Usa os registros como vieram; o cruzamento 07 já faz
    # o join. Aqui não filtramos por ind_oper (sem a coluna no c170 da DB).
    # Recalcula sem filtro ind_oper já que c170 não tem essa coluna:
    elegíveis = [
        r for r in c170_items
        if r.get("cst_pis", "").strip() in CST_TESE_69
    ]

    if not elegíveis:
        return None

    # Soma do ICMS declarado nos itens elegíveis
    soma_icms = Decimal("0")
    soma_vl_pis = Decimal("0")
    soma_vl_cofins = Decimal("0")
    soma_vl_bc_pis = Decimal("0")

    for r in elegíveis:
        soma_icms += Decimal(str(r.get("vl_icms", 0) or 0))
        soma_vl_pis += Decimal(str(r.get("vl_pis", 0) or 0))
        soma_vl_cofins += Decimal(str(r.get("vl_cofins", 0) or 0))
        soma_vl_bc_pis += Decimal(str(r.get("vl_bc_pis", 0) or 0))

    if soma_icms <= 0:
        return None

    # Soma das reduções de base já declaradas via M215/M615
    soma_m215 = sum(
        Decimal(str(r.get("vl_aj_bc", 0) or 0)) for r in m215_reducoes
    )
    soma_m615 = sum(
        Decimal(str(r.get("vl_aj_bc", 0) or 0)) for r in m615_reducoes
    )

    # Gap conservador: assume que M215/M615 já cobrem o ICMS
    gap_pis_conservador = max(Decimal("0"), soma_icms - soma_m215)
    gap_cofins_conservador = max(Decimal("0"), soma_icms - soma_m615)

    # Alíquota ponderada de PIS (usa média dos itens se disponível, senão padrão)
    if soma_vl_bc_pis > 0:
        aliq_pis_pond = (soma_vl_pis / soma_vl_bc_pis).quantize(Decimal("0.0001"))
    else:
        aliq_pis_pond = _ALIQ_PIS_MEDIA

    if soma_vl_bc_pis > 0:
        # Usa COFINS com mesma base (proporcional)
        soma_vl_cofins_pond = sum(
            Decimal(str(r.get("vl_cofins", 0) or 0)) for r in elegíveis
        )
        soma_vl_bc_cofins_pond = sum(
            Decimal(str(r.get("vl_bc_cofins", 0) or 0)) for r in elegíveis
        )
        if soma_vl_bc_cofins_pond > 0:
            aliq_cofins_pond = (soma_vl_cofins_pond / soma_vl_bc_cofins_pond).quantize(
                Decimal("0.0001")
            )
        else:
            aliq_cofins_pond = _ALIQ_COFINS_MEDIA
    else:
        aliq_cofins_pond = _ALIQ_COFINS_MEDIA

    # Impacto conservador: sobre o gap (ICMS não coberto por M215)
    imp_pis_conserv = (gap_pis_conservador * aliq_pis_pond).quantize(Decimal("0.01"))
    imp_cofins_conserv = (gap_cofins_conservador * aliq_cofins_pond).quantize(Decimal("0.01"))
    impacto_conservador = imp_pis_conserv + imp_cofins_conserv

    if impacto_conservador <= 0:
        return None

    # Impacto máximo: sobre todo o ICMS (ignora M215 — assume que M215 é por outras razões)
    imp_pis_max = (soma_icms * aliq_pis_pond).quantize(Decimal("0.01"))
    imp_cofins_max = (soma_icms * aliq_cofins_pond).quantize(Decimal("0.01"))
    impacto_maximo = imp_pis_max + imp_cofins_max

    return {
        "soma_icms_c170": soma_icms,
        "soma_m215_reducoes": soma_m215,
        "soma_m615_reducoes": soma_m615,
        "gap_pis": gap_pis_conservador,
        "gap_cofins": gap_cofins_conservador,
        "aliq_pis_ponderada": aliq_pis_pond,
        "aliq_cofins_ponderada": aliq_cofins_pond,
        "valor_impacto_conservador": impacto_conservador,
        "valor_impacto_maximo": impacto_maximo,
        "qtd_itens_elegiveis": len(elegíveis),
    }
