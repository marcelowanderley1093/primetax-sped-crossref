"""
Cruzamento CR-09 — Tese 69 em D201 (documentos de serviços de transporte).

Base legal: RE 574.706/PR (Tema 69 STF); Lei 10.637/2002 art. 1º;
            Lei 10.833/2003 art. 1º; Seção 12 do Manual EFD-Contribuições
            (nos registros D201/D205, o ICMS deve reduzir VL_BC_PIS/VL_BC_COFINS
            diretamente, pois não há campo VL_ICMS separado no bloco D).
Vigência da tese: a partir de 15/03/2017 (modulação do RE 574.706).

Detecção qualitativa (impacto = 0):
    D201 com CST_PIS ∈ {01,02,03,05}, IND_OPER == "1" (saída),
    VL_ITEM > 0 e VL_BC_PIS == VL_ITEM (tolerância R$ 0,01). Quando a base
    de cálculo do PIS é igual ao valor total do serviço, o ICMS sobre o
    transporte não foi excluído.

Limitação: impacto monetário requer cruzamento com EFD ICMS/IPI para obter
    o VL_ICMS específico do serviço de transporte (Sprint 6+).
"""

from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade
from src.rules.tese_69_consolidados import check_d201_tese69

CODIGO_REGRA = "CR-09"


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    """
    Detecta documentos de serviços de transporte (D201) onde o ICMS não foi
    excluído da base de PIS.

    Retorna lista de Oportunidade com valor_impacto_conservador=0 (qualitativo)
    e lista vazia de Divergencia.
    """
    items = repo.consultar_d201_por_periodo(conn, cnpj, ano_mes)
    oportunidades: list[Oportunidade] = []

    for item in items:
        ev = check_d201_tese69(item)
        if ev is None:
            continue

        oportunidades.append(
            Oportunidade(
                codigo_regra=CODIGO_REGRA,
                descricao=(
                    f"D201 (transporte) com CST_PIS={ev['cst_pis']}, "
                    f"VL_ITEM={ev['vl_item']:.2f}: VL_BC_PIS==VL_ITEM indica "
                    f"ICMS possivelmente incluído na base de PIS. "
                    f"Impacto monetário requer cruzamento com EFD ICMS/IPI (Sprint 6+)."
                ),
                severidade="medio",
                valor_impacto_conservador=Decimal("0"),
                valor_impacto_maximo=Decimal("0"),
                evidencia=[ev],
            )
        )

    return oportunidades, []
