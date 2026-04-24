"""CR-18 — Crédito recebido em evento corporativo (F800) — verificar aproveitamento.

Base legal:
  Art. 3º, §4º da Lei 10.637/2002 e art. 3º, §4º da Lei 10.833/2003: permite a
  transferência de créditos PIS/COFINS em operações de incorporação, fusão, cisão
  e extinção de pessoa jurídica.
  IN RFB 900/2008: regulamenta a transferência de créditos em eventos societários.
  F800.IND_NAT_TRANSF: 01=Incorporação, 02=Fusão, 03=Cisão, 04=Extinção.

Lógica do cruzamento:
  F800.VL_CRED_PIS_TRANS > 0 → crédito PIS recebido de outra PJ em evento societário.
  Verificar: (a) se o crédito foi registrado no Bloco 1 (1100/1500) como saldo disponível;
             (b) se o evento societário está documentado (CNPJ transferidor e data).
  Oportunidade: garantir que o crédito recebido está sendo aproveitado integralmente.
"""

from decimal import Decimal

CODIGO_REGRA = "CR-18"

_IND_NAT = {"01": "Incorporação", "02": "Fusão", "03": "Cisão", "04": "Extinção"}


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Oportunidade

    registros = repo.consultar_f800_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []
    for r in registros:
        vl_cred_pis = Decimal(str(r.get("vl_cred_pis_trans") or 0))
        vl_cred_cofins = Decimal(str(r.get("vl_cred_cofins_trans") or 0))

        if vl_cred_pis <= Decimal("0.01"):
            continue

        nat = _IND_NAT.get(str(r.get("ind_nat_transf") or "").strip(), "evento societário")
        cnpj_transf = r.get("cnpj_transf") or ""
        dt_transf = r.get("dt_transf") or ""

        descricao = (
            f"F800 linha {r['linha_arquivo']}: crédito PIS de R$ {float(vl_cred_pis):.2f}"
            f" recebido por {nat} do CNPJ {cnpj_transf} em {dt_transf}."
            f" Verificar aproveitamento no Bloco 1 (1100/1500)."
        )
        oportunidades.append(Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="alto",
            valor_impacto_conservador=vl_cred_pis,
            valor_impacto_maximo=vl_cred_pis + vl_cred_cofins,
            evidencia=[{
                "registro": "F800",
                "arquivo": r["arquivo_origem"],
                "linha": r["linha_arquivo"],
                "campos_chave": {
                    "ind_nat_transf": r.get("ind_nat_transf") or "",
                    "cnpj_transf": cnpj_transf,
                    "dt_transf": dt_transf,
                    "vl_cred_pis_trans": float(vl_cred_pis),
                    "vl_cred_cofins_trans": float(vl_cred_cofins),
                },
            }],
        ))

    return oportunidades, []
