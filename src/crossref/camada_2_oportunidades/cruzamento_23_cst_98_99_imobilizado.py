"""CR-23 — CST 98/99 em C170 para itens de ativo imobilizado.

Base legal:
  Art. 3º, VI da Lei 10.637/2002 e art. 3º, VI da Lei 10.833/2003: crédito sobre
  máquinas, equipamentos e outros bens incorporados ao ativo imobilizado adquiridos
  ou fabricados para locação a terceiros, ou para utilização na produção de bens
  destinados à venda ou na prestação de serviços.
  IN RFB 1.252/2012: créditos sobre aquisição de bens do ativo imobilizado devem
  ser escriturados nos registros F120 (depreciação) ou F130 (aquisição), e não no
  bloco C com CST 98/99 (operações com tratamento diferenciado ou regimes especiais).

Lógica do cruzamento:
  C170 com CST_PIS 98 ou 99 + VL_BC_PIS > 0 + VL_PIS = 0 →
  possível crédito sobre ativo imobilizado escriturado incorretamente no bloco C
  em vez de nos registros F120/F130. Divergência: classificação errada impede
  o aproveitamento correto (F120/F130 permitem crédito integral ou parcelado).
"""

from decimal import Decimal

CODIGO_REGRA = "CR-23"

_CST_ESPECIAL = {"98", "99"}
_ZERO = Decimal("0.01")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Divergencia

    registros = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    divergencias = []
    for r in registros:
        cst_pis = str(r.get("cst_pis") or "").strip().zfill(2)
        if cst_pis not in _CST_ESPECIAL:
            continue

        vl_bc = Decimal(str(r.get("vl_bc_pis") or 0))
        vl_pis = Decimal(str(r.get("vl_pis") or 0))

        if vl_bc <= _ZERO:
            continue
        if vl_pis > _ZERO:
            continue

        descricao = (
            f"C170 linha {r['linha_arquivo']}: CST_PIS {cst_pis} (tratamento especial)"
            f" com VL_BC_PIS={float(vl_bc):.2f} e VL_PIS=0. Se tratar de ativo"
            f" imobilizado, escriturar em F120/F130 — não em C170 (IN RFB 1.252/2012)."
        )
        divergencias.append(Divergencia(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            evidencia=[{
                "registro": "C170",
                "arquivo": r["arquivo_origem"],
                "linha": r["linha_arquivo"],
                "campos_chave": {
                    "cst_pis": cst_pis,
                    "vl_bc_pis": float(vl_bc),
                    "vl_pis": float(vl_pis),
                    "cfop": r.get("cfop") or "",
                },
            }],
        ))

    return [], divergencias
