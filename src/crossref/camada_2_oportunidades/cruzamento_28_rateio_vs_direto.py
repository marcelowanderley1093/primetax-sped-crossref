"""CR-28 — Avaliação do método de apropriação de créditos: rateio proporcional vs. direto.

Base legal:
  Art. 3º, §§ 7º e 8º da Lei 10.637/2002 e art. 3º, §§ 7º e 8º da Lei 10.833/2003:
  a PJ que aufere receitas tributadas e não-tributadas pode optar entre apropriação direta
  (IND_APRO_CRED=1) ou rateio proporcional (IND_APRO_CRED=2) para os créditos vinculados
  a operações de uso misto.
  Opção pelo rateio é declarada no registro 0110; os percentuais estão em 0111
  (rec_brt_ncum_trib_mi / rec_brt_total).

Lógica do cruzamento (oportunidade analítica):
  Se 0110.IND_APRO_CRED = 2 (rateio proporcional) → sinaliza que a PJ está usando rateio.
  Como a avaliação de qual método é vantajoso exige análise específica do mix de receitas
  (fora do escopo de cruzamento automático sem a ECD), CR-28 retorna Oportunidade analítica
  com impacto zero para que o auditor avalie manualmente.
  Não dispara se IND_APRO_CRED = 1 ou se o registro 0110 está ausente.
"""

from decimal import Decimal


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    reg_0110 = repo.consultar_0110(conn, cnpj, ano_mes)
    if reg_0110 is None:
        return [], []

    ind_apro = str(reg_0110.get("ind_apro_cred") or "").strip()
    if ind_apro != "2":
        return [], []

    reg_0111 = repo.consultar_0111(conn, cnpj, ano_mes)

    pct_trib = None
    if reg_0111:
        rec_total = float(reg_0111.get("rec_brt_total") or 0)
        rec_trib = float(reg_0111.get("rec_brt_ncum_trib_mi") or 0)
        if rec_total > 0:
            pct_trib = rec_trib / rec_total * 100

    descricao = (
        f"0110.IND_APRO_CRED=2 — PJ usa rateio proporcional para apropriação de créditos PIS/COFINS."
    )
    if pct_trib is not None:
        descricao += f" Percentual de receita tributada (0111): {pct_trib:.1f}%."
    descricao += (
        " Avaliar se a mudança para apropriação direta (método alternativo) resultaria em"
        " créditos superiores — especialmente em períodos com alta concentração de receitas"
        " tributadas ou com bens de uso exclusivo na atividade-fim."
    )

    return [
        Oportunidade(
            codigo_regra="CR-28",
            descricao=descricao,
            severidade="baixo",
            valor_impacto_conservador=Decimal("0"),
            valor_impacto_maximo=Decimal("0"),
            evidencia=[{
                "registro": "0110",
                "arquivo": reg_0110["arquivo_origem"],
                "linha": reg_0110["linha_arquivo"],
                "campos_chave": {
                    "ind_apro_cred": ind_apro,
                    "percentual_receita_tributada": pct_trib,
                    "tem_0111": reg_0111 is not None,
                },
            }],
        )
    ], []
