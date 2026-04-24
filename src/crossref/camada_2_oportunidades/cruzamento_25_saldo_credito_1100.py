"""CR-25 — Saldo de crédito acumulado disponível para compensação (1100/1500).

Base legal:
  Art. 3º da Lei 10.637/2002: crédito PIS não utilizado pode ser objeto de
  ressarcimento (§ 4º) ou compensação com tributos administrados pela RFB (§ 5º).
  Art. 3º da Lei 10.833/2003: idem para COFINS.
  Lei 9.430/1996, art. 74 (redação da Lei 10.637/2002): compensação de créditos
  escriturados e não aproveitados.
  IN RFB 1.717/2017 (DComp): procedimento de compensação de créditos apurados
  na escrituração.

Lógica do cruzamento:
  1100.SLD_CRED_FIM > R$ 1,00 → saldo de crédito PIS acumulado ao fim do período
  disponível para compensação ou ressarcimento, mas ainda não aproveitado.
  1500.SLD_CRED_FIM > R$ 1,00 → idem para COFINS.
  Severidade cresce com o valor: acima de R$ 10.000 = 'alto'.
"""

from decimal import Decimal

CODIGO_REGRA = "CR-25"

_LIMIAR = Decimal("1.00")
_ALTO = Decimal("10000.00")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Oportunidade

    regs_1100 = repo.consultar_1100_por_periodo(conn, cnpj, ano_mes)
    regs_1500 = repo.consultar_1500_por_periodo(conn, cnpj, ano_mes)

    oportunidades = []

    for r in regs_1100:
        saldo = Decimal(str(r.get("sld_cred_fim") or 0))
        if saldo <= _LIMIAR:
            continue
        severidade = "alto" if saldo >= _ALTO else "medio"
        cod_cred = r.get("cod_cred") or ""
        descricao = (
            f"1100 linha {r['linha_arquivo']}: saldo de crédito PIS acumulado"
            f" R$ {float(saldo):.2f} (COD_CRED={cod_cred}) disponível para"
            f" compensação/ressarcimento. Verificar DComp pendente."
        )
        oportunidades.append(Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade=severidade,
            valor_impacto_conservador=saldo,
            valor_impacto_maximo=saldo,
            evidencia=[{
                "registro": "1100",
                "arquivo": r["arquivo_origem"],
                "linha": r["linha_arquivo"],
                "campos_chave": {
                    "cod_cred": cod_cred,
                    "sld_cred_fim": float(saldo),
                    "per_apu_cred": r.get("per_apu_cred") or "",
                    "orig_cred": r.get("orig_cred") or "",
                },
            }],
        ))

    for r in regs_1500:
        saldo = Decimal(str(r.get("sld_cred_fim") or 0))
        if saldo <= _LIMIAR:
            continue
        severidade = "alto" if saldo >= _ALTO else "medio"
        cod_cred = r.get("cod_cred") or ""
        descricao = (
            f"1500 linha {r['linha_arquivo']}: saldo de crédito COFINS acumulado"
            f" R$ {float(saldo):.2f} (COD_CRED={cod_cred}) disponível para"
            f" compensação/ressarcimento. Verificar DComp pendente."
        )
        oportunidades.append(Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade=severidade,
            valor_impacto_conservador=saldo,
            valor_impacto_maximo=saldo,
            evidencia=[{
                "registro": "1500",
                "arquivo": r["arquivo_origem"],
                "linha": r["linha_arquivo"],
                "campos_chave": {
                    "cod_cred": cod_cred,
                    "sld_cred_fim": float(saldo),
                    "per_apu_cred": r.get("per_apu_cred") or "",
                    "orig_cred": r.get("orig_cred") or "",
                },
            }],
        ))

    return oportunidades, []
