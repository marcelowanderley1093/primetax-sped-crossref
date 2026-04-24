"""
Cruzamento CR-08 — Tese 69 em C181 (NFC-e consolidada).

Base legal: RE 574.706/PR (Tema 69 STF); Lei 10.637/2002 art. 1º;
            Lei 10.833/2003 art. 1º; Seção 12 do Manual EFD-Contribuições
            (nos registros C181/C185, a exclusão do ICMS deve ocorrer via
            VL_DESC, e não há campo VL_ICMS separado).
Vigência da tese: a partir de 15/03/2017 (modulação do RE 574.706).

Detecção qualitativa (impacto = 0):
    C181 com CST_PIS ∈ {01,02,03,05}, IND_OPER == "1" (saída),
    VL_ITEM > 0 e VL_DESC == 0. O zero em VL_DESC indica que a empresa
    não realizou qualquer dedução na base, sugerindo que o ICMS está
    incluído em VL_BC_PIS.

Limitação: impacto monetário requer cruzamento com EFD ICMS/IPI para obter
    o VL_ICMS da NFC-e (Sprint 6+). Por enquanto, retorna valor = 0 como
    sinalização qualitativa para revisão pelo auditor.
"""

from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade
from src.rules.tese_69_consolidados import check_c181_tese69

CODIGO_REGRA = "CR-08"


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    """
    Detecta NFC-e consolidadas (C181) onde o ICMS não foi excluído da base de PIS.

    Retorna lista de Oportunidade com valor_impacto_conservador=0 (qualitativo)
    e lista vazia de Divergencia.
    """
    items = repo.consultar_c181_por_periodo(conn, cnpj, ano_mes)
    oportunidades: list[Oportunidade] = []

    for item in items:
        ev = check_c181_tese69(item)
        if ev is None:
            continue

        oportunidades.append(
            Oportunidade(
                codigo_regra=CODIGO_REGRA,
                descricao=(
                    f"NFC-e C181 com CST_PIS={ev['cst_pis']}, VL_ITEM={ev['vl_item']:.2f}: "
                    f"VL_DESC=0 indica ICMS possivelmente incluído na base de PIS. "
                    f"Impacto monetário requer cruzamento com EFD ICMS/IPI (Sprint 6+)."
                ),
                severidade="medio",
                valor_impacto_conservador=Decimal("0"),
                valor_impacto_maximo=Decimal("0"),
                evidencia=[ev],
            )
        )

    return oportunidades, []
