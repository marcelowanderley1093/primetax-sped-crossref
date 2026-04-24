"""CR-27 — Bens imobilizados classificados como uso vedado (IND_UTIL=9) com crédito lançado.

Base legal:
  Art. 3º, VI da Lei 10.637/2002 e Lei 10.833/2003: o crédito sobre ativo imobilizado
  é restrito a bens utilizados na produção de bens ou prestação de serviços (IND_UTIL ∈ {1,2,3}).
  Bens de uso "Outros" (IND_UTIL=9), como imóveis administrativos, equipamentos de escritório,
  veículos gerenciais, não geram direito a crédito.
  Autuação corriqueira em que o contribuinte lança crédito sobre bens vedados.

Lógica do cruzamento (divergência — risco):
  F120 ou F130 com IND_UTIL_BEM_IMOB = 9 E VL_PIS > 0 → crédito indevido → Divergencia.

Nota: bens com IND_UTIL=9 e VL_PIS=0 estão corretos — não disparam.
Nota 2: bens com IND_UTIL ∈ {1,2,3} e VL_PIS=0 são oportunidades → CR-14 e CR-15.
"""

from decimal import Decimal


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Divergencia

    f120s = repo.consultar_f120_por_periodo(conn, cnpj, ano_mes)
    f130s = repo.consultar_f130_por_periodo(conn, cnpj, ano_mes)

    divergencias = []

    for r in f120s:
        ind_util = str(r["ind_util_bem_imob"] or "").strip()
        if ind_util != "9":
            continue
        vl_pis = Decimal(str(r["vl_pis"] or 0))
        if vl_pis <= Decimal("0.01"):
            continue

        vl_cofins = Decimal(str(r["vl_cofins"] or 0))
        descricao = (
            f"F120 — bem '{r.get('desc_bem_imob') or r.get('ident_bem_imob')}':"
            f" IND_UTIL=9 (uso vedado) mas VL_PIS={float(vl_pis):.2f} foi lançado."
            f" Crédito pode ser glosado em fiscalização."
        )
        divergencias.append(
            Divergencia(
                codigo_regra="CR-27",
                descricao=descricao,
                severidade="alto",
                evidencia=[{
                    "registro": "F120",
                    "arquivo": r["arquivo_origem"],
                    "linha": r["linha_arquivo"],
                    "campos_chave": {
                        "desc_bem_imob": r.get("desc_bem_imob") or "",
                        "ident_bem_imob": r.get("ident_bem_imob") or "",
                        "ind_util_bem_imob": ind_util,
                        "vl_pis_indevido": float(vl_pis),
                        "vl_cofins_indevido": float(vl_cofins),
                    },
                }],
            )
        )

    for r in f130s:
        ind_util = str(r["ind_util_bem_imob"] or "").strip()
        if ind_util != "9":
            continue
        vl_pis = Decimal(str(r["vl_pis"] or 0))
        if vl_pis <= Decimal("0.01"):
            continue

        vl_cofins = Decimal(str(r["vl_cofins"] or 0))
        descricao = (
            f"F130 — bem '{r.get('desc_bem_imob') or r.get('ident_bem_imob')}':"
            f" IND_UTIL=9 (uso vedado) mas VL_PIS={float(vl_pis):.2f} foi lançado."
            f" Crédito pode ser glosado em fiscalização."
        )
        divergencias.append(
            Divergencia(
                codigo_regra="CR-27",
                descricao=descricao,
                severidade="alto",
                evidencia=[{
                    "registro": "F130",
                    "arquivo": r["arquivo_origem"],
                    "linha": r["linha_arquivo"],
                    "campos_chave": {
                        "desc_bem_imob": r.get("desc_bem_imob") or "",
                        "ident_bem_imob": r.get("ident_bem_imob") or "",
                        "ind_util_bem_imob": ind_util,
                        "vl_pis_indevido": float(vl_pis),
                        "vl_cofins_indevido": float(vl_cofins),
                    },
                }],
            )
        )

    return [], divergencias
