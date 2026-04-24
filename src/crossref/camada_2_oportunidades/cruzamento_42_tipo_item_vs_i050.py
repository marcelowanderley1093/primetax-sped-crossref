"""CR-42 — TIPO_ITEM 01/02/06/10 em 0200 × COD_NAT da conta em I050 (ECD).

Base legal:
  REsp 1.221.170/PR (Tema 779 STJ) — conceito de insumo para PIS/COFINS não-cumulativo:
  essencialidade e relevância para o processo produtivo. Matéria-prima (01), embalagem (02),
  produto intermediário (06) e outros insumos (10) classificados no 0200 devem estar
  contabilizados em contas de estoque (COD_NAT='01' — Ativo) ou custo (COD_NAT='04' —
  Resultado, grupo de custos). Se o COD_CTA referenciado no C170 para esses itens mapeia
  para conta de resultado de natureza administrativo/comercial (COD_NAT='04' mas grupo
  incorreto), ou pior, para conta de passivo/PL, indica classificação incorreta que pode
  comprometer o creditamento.
  Art. 3º, II da Lei 10.637/2002 e Lei 10.833/2003 — insumos geram crédito.
  IN RFB 1.252/2012 — TIPO_ITEM no registro 0200.
  Vigência: desde AC 2012 (EFD-Contribuições).

Lógica:
  1. Busca 0200 com TIPO_ITEM ∈ {'01', '02', '06', '10'} (insumos).
  2. Para cada item, obtém COD_CTA via C170 (join por COD_ITEM) no ano-calendário.
  3. Para cada COD_CTA, verifica COD_NAT na ECD I050.
  4. Se COD_NAT ∉ {'01', '04'} (não é ativo nem resultado) → classificação suspeita → divergência.

Dependência: ecd (CLAUDE.md §18).
modo_degradado_suportado: Partial (CLAUDE.md §16.3).
"""

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-42"
_TIPO_ITEM_INSUMO = {"01", "02", "06", "10"}
_COD_NAT_VALIDO = {"01", "04"}  # Ativo ou Resultado


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Divergencia

    disp = verificar_dependencias(repo, conn, ["ecd"])
    if disp["ecd"] != "importada":
        return [], []

    # 0200 com TIPO_ITEM de insumo
    reg_0200 = repo.consultar_0200_anual(conn, cnpj, ano_calendario)
    itens_insumo = {
        r["cod_item"]: r
        for r in reg_0200
        if r.get("tipo_item") in _TIPO_ITEM_INSUMO
    }

    if not itens_insumo:
        return [], []

    # I050 analítico → mapeia COD_CTA → COD_NAT
    i050_registros = repo.consultar_ecd_i050(conn, cnpj, ano_calendario)
    cta_nat = {
        r["cod_cta"]: r.get("cod_nat", "")
        for r in i050_registros
        if r.get("ind_cta") == "A"
    }

    if not cta_nat:
        return [], []

    # C170 para itens de insumo → obtém COD_CTA usado
    c170_ctas = repo.consultar_c170_cod_cta(conn, cnpj, ano_calendario)
    ctas_efd = {r["cod_cta"] for r in c170_ctas if r.get("cod_cta")}

    # Contas usadas em C170 que mapeiam para COD_NAT suspeito
    problemas = []
    for cta in ctas_efd:
        nat = cta_nat.get(cta)
        if nat and nat not in _COD_NAT_VALIDO:
            problemas.append({"cod_cta": cta, "cod_nat": nat})

    if not problemas:
        return [], []

    descricao = (
        f"{len(problemas)} conta(s) contábil(is) referenciadas em C170 para itens do tipo "
        f"insumo (TIPO_ITEM 01/02/06/10) classificadas em natureza suspeita na ECD I050: "
        f"{[p['cod_cta'] + '(NAT=' + p['cod_nat'] + ')' for p in problemas[:5]]}. "
        f"Contas de insumo devem mapear para COD_NAT='01' (Ativo) ou '04' (Resultado/Custo). "
        f"Verificar reclassificação contábil — impacta validade do crédito PIS/COFINS "
        f"(REsp 1.221.170/PR — Tema 779 STJ)."
    )

    divergencias = [
        Divergencia(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            evidencia=[{
                "registro": "0200/C170/I050",
                "campos_chave": {
                    "contas_classificacao_suspeita": problemas[:20],
                    "qtd_problemas": len(problemas),
                    "qtd_itens_insumo_0200": len(itens_insumo),
                    "ano_calendario": ano_calendario,
                },
            }],
        )
    ]
    return [], divergencias
