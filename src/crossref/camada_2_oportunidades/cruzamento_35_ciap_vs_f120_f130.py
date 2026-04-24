"""CR-35 — CIAP (G125) × F120/F130: crédito PIS/COFINS não aproveitado sobre imobilizado.

Base legal:
  Art. 3º, VI e VII da Lei 10.637/2002 (PIS) e Lei 10.833/2003 (COFINS):
  encargos de depreciação (F120) e aquisição de imobilizado (F130) geram crédito.
  Art. 20 §§5º-7º ADCT (CF/88) e Ajuste SINIEF 8/1997 (CIAP): o mesmo bem
  imobilizado que gera crédito de ICMS via CIAP deve também gerar crédito de
  PIS/COFINS quando destinado à produção de bens ou prestação de serviços.
  Divergência entre G125 (CIAP-ICMS) e F120/F130 (crédito PIS/COFINS) indica
  que o bem está sendo reconhecido para ICMS mas não para PIS/COFINS → oportunidade.
  Vigência: 01/2003 (PIS) e 02/2004 (COFINS), Leiaute EFD ICMS/IPI desde 01/2011.

Lógica:
  Se G125.VL_PARC_PASS > 0 no período
  E não há nenhum F120 nem F130 no mesmo período na EFD-Contribuições
  → Oportunidade: crédito PIS/COFINS sobre imobilizado possivelmente não aproveitado.

Dependência: efd_icms (CLAUDE.md §18).
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-35"


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["efd_icms"])
    if disp["efd_icms"] != "importada":
        return [], []

    g125_registros = repo.consultar_icms_g125_por_periodo(conn, cnpj, ano_mes)
    if not g125_registros:
        return [], []

    parcelas_ativas = [
        r for r in g125_registros
        if float(r.get("vl_parc_pass") or 0) > 0
    ]
    if not parcelas_ativas:
        return [], []

    f120_registros = repo.consultar_f120_por_periodo(conn, cnpj, ano_mes)
    f130_registros = repo.consultar_f130_por_periodo(conn, cnpj, ano_mes)
    tem_f120_ou_f130 = bool(f120_registros or f130_registros)

    if tem_f120_ou_f130:
        return [], []

    soma_parc_pass = sum(
        Decimal(str(r.get("vl_parc_pass") or 0)) for r in parcelas_ativas
    )
    qtd_bens = len({r.get("ident_bem") or r.get("cod_ind_bem") for r in parcelas_ativas})

    descricao = (
        f"CIAP — {qtd_bens} bem(ns) com parcela ICMS de R$ {float(soma_parc_pass):.2f}"
        f" sendo apropriada em {ano_mes // 100:02d}/{ano_mes % 100}"
        f" sem correspondência em F120/F130 (crédito PIS/COFINS sobre imobilizado)."
        f" Verificar se bem destina-se à produção/serviços e se há crédito não aproveitado."
    )

    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            valor_impacto_conservador=Decimal("0"),
            valor_impacto_maximo=Decimal("0"),
            evidencia=[{
                "registro": "G125",
                "arquivo": parcelas_ativas[0]["arquivo_origem"],
                "linha": parcelas_ativas[0]["linha_arquivo"],
                "campos_chave": {
                    "qtd_bens_ciap": qtd_bens,
                    "soma_vl_parc_pass": float(soma_parc_pass),
                    "tem_f120": bool(f120_registros),
                    "tem_f130": bool(f130_registros),
                    "ano_mes": ano_mes,
                },
            }],
        )
    ]
    return oportunidades, []
