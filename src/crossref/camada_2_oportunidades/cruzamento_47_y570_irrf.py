"""CR-47 — Y570 (ECF IRRF e CSRF retidos): retenções não compensadas.

Base legal:
  Art. 30 da Lei 10.833/2003 — retenção de CSLL, PIS, COFINS e IR sobre pagamentos
  a PJ por órgãos, autarquias e fundações federais.
  Art. 64 da Lei 9.430/1996 — retenção de IR por órgãos da administração federal.
  Art. 34 e 35 da Lei 10.833/2003 — retenção por outras pessoas jurídicas.
  Lei 9.430/1996, art. 6º — compensação do IRRF retido na fonte com o IRPJ apurado.
  Lei 7.689/1988, art. 4º — compensação do CSRF retido com a CSLL apurada.
  Y570: Demonstrativo do IRRF e CSLL Retidos na Fonte. Cada linha = uma natureza/período.
  CR-47: somatório de VL_IR_RET e VL_CSLL_RET × compensações declaradas no IRPJ/CSLL.
  Retenções declaradas na ECF mas não compensadas = crédito recuperável.
  ADE Cofis 02/2026 §21.
  Vigência: desde AC 2014.

Lógica:
  1. Soma VL_IR_RET e VL_CSLL_RET de todos os Y570 do ano.
  2. Se total > threshold (R$ 1.000) → Oportunidade: verificar se as retenções foram
     integralmente compensadas no IRPJ/CSLL apurado do ano.
     (Cruzamento completo com DCTFWeb/EFD-Reinf é futuro — CLAUDE.md §13.)
  3. Total indica a magnitude do crédito potencial não aproveitado.

Dependência: ecf apenas (CLAUDE.md §18.6 Sprint 8).
modo_degradado_suportado: N/A — ECF isolada.
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-47"
_THRESHOLD_RETENCAO = Decimal("1000")  # R$ 1.000 mínimo para reportar


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecf"])
    if disp["ecf"] != "importada":
        return [], []

    y570_registros = repo.consultar_ecf_y570(conn, cnpj, ano_calendario)
    if not y570_registros:
        return [], []

    total_ir_ret = sum(
        Decimal(str(r.get("vl_ir_ret") or 0)) for r in y570_registros
    )
    total_csll_ret = sum(
        Decimal(str(r.get("vl_csll_ret") or 0)) for r in y570_registros
    )
    total_ret = total_ir_ret + total_csll_ret

    if total_ret < _THRESHOLD_RETENCAO:
        return [], []

    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=(
                f"Y570 registra retenções na fonte no AC {ano_calendario}: "
                f"IRRF = R$ {float(total_ir_ret):,.2f}, "
                f"CSRF = R$ {float(total_csll_ret):,.2f} "
                f"(total R$ {float(total_ret):,.2f}, {len(y570_registros)} linha(s)). "
                f"Verificar se as retenções foram integralmente compensadas no "
                f"IRPJ/CSLL apurado do ano "
                f"(art. 6º Lei 9.430/1996 e art. 4º Lei 7.689/1988). "
                f"Retenções não compensadas são crédito recuperável via PER/DCOMP "
                f"(prescrição: 5 anos, CTN art. 168, I)."
            ),
            severidade="alto",
            valor_impacto_conservador=total_ret,
            valor_impacto_maximo=total_ret,
            evidencia=[{
                "registro": "Y570",
                "arquivo": y570_registros[0].get("arquivo_origem", ""),
                "linha": y570_registros[0].get("linha_arquivo"),
                "campos_chave": {
                    "total_ir_ret": float(total_ir_ret),
                    "total_csll_ret": float(total_csll_ret),
                    "total_retencoes": float(total_ret),
                    "qtd_linhas_y570": len(y570_registros),
                    "ano_calendario": ano_calendario,
                },
            }],
        )
    ]

    return oportunidades, []
