"""CR-38 — I155 (ECD) × M200/M600 (EFD-Contribuições): receita contábil vs receita fiscal.

Base legal:
  Art. 1º da Lei 10.637/2002 e art. 1º da Lei 10.833/2003 (PIS/COFINS não-cumulativo):
  a base de cálculo é a receita bruta total, conforme definida na Lei 9.718/1998.
  RE 574.706/PR (Tema 69) — o ICMS não compõe a receita bruta para fins de PIS/COFINS.
  A receita contábil (soma de créditos em contas de resultado COD_NAT='04' da ECD)
  deve ser compatível com a receita fiscal declarada no M200.VL_REC_BRT_TOTAL da EFD-Contrib.
  Se M200 > I155 em mais de 5% → indica que o EFD-Contrib inclui ICMS ou outras exclusões
  indevidas na base, ou que há receita não contabilizada — forte sinal para Tese 69.
  Vigência: Lei 10.637/2002 (PIS) e Lei 10.833/2003 (COFINS), desde AC 2003.

Lógica:
  1. Soma VL_REC_BRT_TOTAL de todos os M200 do ano-calendário (EFD-Contrib).
  2. Soma VL_CRED de I155 onde I050.COD_NAT='04' (contas de resultado, natureza crédito)
     para o mesmo CNPJ e ano-calendário (ECD).
  3. Se |M200_total - I155_total| / max(I155_total, 1) > 0.05 (threshold 5%)
     E M200_total > I155_total → Oportunidade: revisar base PIS/COFINS.

Dependência: ecd (CLAUDE.md §18).
modo_degradado_suportado: True (CLAUDE.md §16.3).
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias
from src.crossref.common.reconciliacao_plano_contas import (
    classificar_reconciliacao,
    consultar_plano_contas_combinado,
    consultar_plano_contas_natureza,
)

CODIGO_REGRA = "CR-38"
MODO_DEGRADADO_SUPORTADO = True
_THRESHOLD_DIVERGENCIA = Decimal("0.05")  # 5%


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecd"])
    if disp["ecd"] != "importada":
        return [], []

    # Soma M200.VL_REC_BRT_TOTAL do ano inteiro (EFD-Contrib)
    m200_registros = repo.consultar_m200_anual(conn, cnpj, ano_calendario)
    if not m200_registros:
        return [], []

    receita_efd = sum(
        Decimal(str(r.get("vl_rec_brt_total") or 0)) for r in m200_registros
    )
    if receita_efd <= 0:
        return [], []

    # Escolhe a estratégia de classificação conforme reconciliação do plano de contas (§16.3).
    reconc = classificar_reconciliacao(repo, conn, cnpj, ano_calendario)
    modo_degradado = reconc in ("suspeita", "ausente")

    if modo_degradado:
        plano = consultar_plano_contas_combinado(repo, conn, cnpj, ano_calendario)
    else:
        plano = consultar_plano_contas_natureza(repo, conn, cnpj, ano_calendario)

    contas_resultado = {cta for cta, nat in plano.items() if nat == "04"}

    # Soma VL_CRED de I155 para contas de resultado (COD_NAT='04') do ano inteiro (ECD)
    i155_registros = repo.consultar_ecd_i155_anual(conn, cnpj, ano_calendario)

    receita_ecd = sum(
        Decimal(str(r.get("vl_cred") or 0))
        for r in i155_registros
        if r.get("cod_cta") in contas_resultado
    )

    if receita_ecd <= 0:
        return [], []

    diferenca = receita_efd - receita_ecd
    if diferenca <= 0:
        return [], []

    proporcao = diferenca / receita_ecd
    if proporcao <= _THRESHOLD_DIVERGENCIA:
        return [], []

    sufixo_modo = (
        f" [modo degradado — reconciliação '{reconc}']" if modo_degradado else ""
    )
    descricao = (
        f"Receita fiscal (M200) de R$ {float(receita_efd):,.2f} excede receita contábil "
        f"(ECD I155 — contas de resultado) de R$ {float(receita_ecd):,.2f} em "
        f"{float(proporcao) * 100:.1f}% no AC {ano_calendario}{sufixo_modo}. "
        f"Indica possível inclusão indevida de ICMS ou outros valores na base de PIS/COFINS "
        f"(Tese 69 — RE 574.706/PR). Verificar composição do M200.VL_REC_BRT_TOTAL."
    )

    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="alto",
            valor_impacto_conservador=Decimal("0"),
            valor_impacto_maximo=Decimal("0"),
            evidencia=[{
                "registro": "M200/I155",
                "arquivo": m200_registros[0]["arquivo_origem"],
                "linha": m200_registros[0]["linha_arquivo"],
                "campos_chave": {
                    "receita_efd_m200": float(receita_efd),
                    "receita_ecd_i155": float(receita_ecd),
                    "diferenca": float(diferenca),
                    "proporcao_pct": round(float(proporcao) * 100, 1),
                    "qtd_meses_m200": len(m200_registros),
                    "qtd_contas_resultado_ecd": len(contas_resultado),
                    "ano_calendario": ano_calendario,
                    "modo_execucao": "degradado" if modo_degradado else "integra",
                    "reconciliacao_plano_contas": reconc,
                },
            }],
        )
    ]
    return oportunidades, []
