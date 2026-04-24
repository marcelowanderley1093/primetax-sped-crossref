"""
Reconciliação de plano de contas entre ECD e demais SPEDs (CLAUDE.md §16).

Três estados possíveis para cada CNPJ × ano-calendário (§16.2):
  "integra"   — IND_MUDANC_PC='0', OU IND_MUDANC_PC='1' com Bloco C completo
                (C050 cobre ≥ 50% das contas analíticas do I050 E ≥ 1 C155).
  "suspeita"  — IND_MUDANC_PC='1' com Bloco C parcial (cobertura < 50% ou sem C155).
  "ausente"   — IND_MUDANC_PC='1' sem Bloco C (C050 e C155 ambos vazios).

Decisão de design (§16.1):
  - Proibido inferência textual sobre NOME_CTA (fuzzy matching, LLM, Levenshtein).
  - Reconciliação opera apenas em campos estruturados declarados.
  - Fallback por COD_NAT quando o cruzamento suporta modo degradado.

Base legal:
  Decreto 6.022/2007 (SPED); IN RFB 2.003/2021 (ECD); ADE Cofis 01/2026 (Leiaute 9).
"""

from __future__ import annotations

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Threshold de cobertura de C050 sobre I050 analítico (§16.2)
_THRESHOLD_COBERTURA_C050 = 0.5


def classificar_reconciliacao(repo, conn, cnpj: str, ano_calendario: int) -> str | None:
    """
    Classifica o estado da reconciliação de plano de contas de uma ECD.

    Regras (§16.2):
      - IND_MUDANC_PC='0' → "integra"
      - IND_MUDANC_PC='1' + C050 cobre ≥50% de I050 analítico + ≥1 C155 → "integra"
      - IND_MUDANC_PC='1' + algum dado em Bloco C mas não completo → "suspeita"
      - IND_MUDANC_PC='1' + Bloco C vazio → "ausente"

    Overrides manuais (§16.6):
      Quando há overrides importados via `reconciliacao-import` cobrindo
      ≥50% das contas analíticas do I050, o estado é elevado para "integra"
      (o auditor forneceu a reconciliação que o Bloco C não trouxe).

    Returns:
        "integra" | "suspeita" | "ausente" | None
        None quando não há ECD 0000 importada para o CNPJ × ano.
    """
    ind_mudanc_pc = repo.consultar_ecd_ind_mudanc_pc(conn, cnpj, ano_calendario)
    if ind_mudanc_pc is None:
        return None  # ECD não importada

    if ind_mudanc_pc.strip() in ("0", ""):
        return "integra"

    # IND_MUDANC_PC = '1' — houve mudança. Avaliar completude do Bloco C.
    qtd_c050 = repo.contar_ecd_c050(conn, cnpj, ano_calendario)
    qtd_c155 = repo.contar_ecd_c155(conn, cnpj, ano_calendario)
    qtd_i050_analitico = repo.contar_ecd_i050_analitico(conn, cnpj, ano_calendario)

    # Cobertura do Bloco C: razão C050 / I050 analítico.
    cobertura_ok = (
        qtd_i050_analitico > 0
        and (qtd_c050 / qtd_i050_analitico) >= _THRESHOLD_COBERTURA_C050
    )

    if cobertura_ok and qtd_c155 >= 1:
        return "integra"

    # Overrides manuais §16.6: promove a "integra" quando a cobertura manual
    # supre o Bloco C ausente/parcial.
    qtd_overrides = repo.contar_reconciliacao_overrides(conn, cnpj, ano_calendario)
    if qtd_overrides > 0 and qtd_i050_analitico > 0:
        if (qtd_overrides / qtd_i050_analitico) >= _THRESHOLD_COBERTURA_C050:
            return "integra"

    if qtd_c050 == 0 and qtd_c155 == 0 and qtd_overrides == 0:
        return "ausente"
    return "suspeita"


def resolver_cod_cta(
    repo, conn, cnpj: str, ano_calendario: int, cod_cta: str
) -> str | None:
    """
    Retorna a COD_CTA canônica para uso em joins inter-SPED.

    Lookup em três passos (§16.4 + §16.6):
      1. Se há override manual com cod_cta_atual == cod_cta → retorna cod_cta
         (o override confirma o mapeamento; a conta é conhecida no plano novo).
      2. Se há override manual com cod_cta_antigo == cod_cta → retorna o
         cod_cta_atual correspondente (a conta informada é do plano antigo
         e foi reclassificada para o código atual).
      3. Reconciliação 'integra' → passthrough (a conta é válida sem mapeamento).
      4. Caso contrário → None (cruzamento deve operar em modo degradado).
    """
    for o in repo.consultar_reconciliacao_overrides(conn, cnpj, ano_calendario):
        if o.get("cod_cta_atual") == cod_cta:
            return cod_cta
        if o.get("cod_cta_antigo") == cod_cta:
            return o.get("cod_cta_atual")

    estado = classificar_reconciliacao(repo, conn, cnpj, ano_calendario)
    if estado == "integra":
        return cod_cta
    return None


def consultar_plano_contas_natureza(
    repo, conn, cnpj: str, ano_calendario: int
) -> dict[str, str]:
    """
    Retorna mapa `cod_cta → cod_nat` a partir do I050 da ECD.

    cod_nat segue a tabela oficial do Leiaute 9:
      01=Ativo, 02=Passivo, 03=PL, 04=Resultado, 05=Compensação, 09=Outras.
    """
    mapa: dict[str, str] = {}
    for row in repo.consultar_ecd_i050(conn, cnpj, ano_calendario):
        cod_cta = (row.get("cod_cta") or "").strip()
        cod_nat = (row.get("cod_nat") or "").strip()
        if cod_cta and cod_nat:
            mapa[cod_cta] = cod_nat
    return mapa


def consultar_plano_contas_combinado(
    repo, conn, cnpj: str, ano_calendario: int
) -> dict[str, str]:
    """
    Combina I050 (plano atual) + C050 (plano antigo recuperado) em mapa cod_cta→cod_nat.

    I050 tem precedência: quando uma mesma COD_CTA aparece em ambos os planos (raro
    mas possível), o cod_nat do plano atual prevalece. Usado pelos cruzamentos em
    modo degradado (§16.3) para não perder contas que ainda têm saldo em I155 mas
    cujo código é pré-mudança e não está mais no I050.
    """
    mapa = consultar_plano_contas_natureza(repo, conn, cnpj, ano_calendario)
    for row in repo.consultar_ecd_c050(conn, cnpj, ano_calendario):
        cod_cta = (row.get("cod_cta") or "").strip()
        cod_nat = (row.get("cod_nat") or "").strip()
        if cod_cta and cod_nat and cod_cta not in mapa:
            mapa[cod_cta] = cod_nat
    return mapa


def agregar_por_natureza(
    saldos_por_cod_cta: dict[str, Decimal],
    plano_contas: dict[str, str],
) -> dict[str, Decimal]:
    """
    Converte `{cod_cta: saldo}` em `{cod_nat: saldo_agregado}` usando o plano.

    Contas presentes em `saldos_por_cod_cta` mas ausentes em `plano_contas`
    são agrupadas sob `cod_nat = "99"` (não-identificada). Isso preserva
    rastreabilidade: o auditor vê quanto valor ficou fora do mapeamento.
    """
    agregado: dict[str, Decimal] = {}
    for cod_cta, saldo in saldos_por_cod_cta.items():
        cod_nat = plano_contas.get(cod_cta, "99")
        agregado[cod_nat] = agregado.get(cod_nat, Decimal("0")) + Decimal(str(saldo))
    return agregado
