"""CR-36 — H010.VL_ITEM_IR × F150: crédito sobre estoque de abertura não aproveitado.

Base legal:
  Art. 3º §1º da Lei 10.637/2002 (PIS) e Lei 10.833/2003 (COFINS):
  crédito presumido sobre estoque de abertura de bens adquiridos de pessoa jurídica
  para revenda ou utilizados como insumo.
  Manual EFD ICMS/IPI v3.2.2 — H010.VL_ITEM_IR: 'O montante desse imposto
  [ICMS recuperável], destacado em nota fiscal, deve ser excluído do valor dos
  estoques para efeito do imposto de renda.'
  VL_ITEM_IR > 0 sinaliza que o item tem ICMS excluído → inventário com valor
  ajustado para IR/CSLL → candidato a crédito PIS/COFINS sobre estoque (F150).
  Vigência: regime não-cumulativo PIS (01/2003) e COFINS (02/2004).

Lógica:
  Se existem H010 com VL_ITEM_IR > 0 no período
  E não há F150 na EFD-Contribuições para o mesmo período
  → Oportunidade: crédito presumido sobre estoque de abertura possivelmente não aproveitado.

Dependência: efd_icms (CLAUDE.md §18).
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-36"


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["efd_icms"])
    if disp["efd_icms"] != "importada":
        return [], []

    h010_registros = repo.consultar_icms_h010_por_periodo(conn, cnpj, ano_mes)
    if not h010_registros:
        return [], []

    itens_com_ir = [
        r for r in h010_registros
        if float(r.get("vl_item_ir") or 0) > 0
    ]
    if not itens_com_ir:
        return [], []

    f150_registros = repo.consultar_f150_por_periodo(conn, cnpj, ano_mes)
    if f150_registros:
        return [], []

    soma_vl_item_ir = sum(
        Decimal(str(r.get("vl_item_ir") or 0)) for r in itens_com_ir
    )
    qtd_itens = len(itens_com_ir)

    descricao = (
        f"H010 — {qtd_itens} item(ns) com VL_ITEM_IR total de R$ {float(soma_vl_item_ir):.2f}"
        f" (inventário com ICMS excluído para fins IR) sem F150 na EFD-Contribuições."
        f" Verificar se há direito a crédito presumido sobre estoque de abertura (art. 3º §1º"
        f" Lei 10.637/2002 e Lei 10.833/2003)."
    )

    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            valor_impacto_conservador=Decimal("0"),
            valor_impacto_maximo=Decimal("0"),
            evidencia=[{
                "registro": "H010",
                "arquivo": itens_com_ir[0]["arquivo_origem"],
                "linha": itens_com_ir[0]["linha_arquivo"],
                "campos_chave": {
                    "qtd_itens_com_vl_item_ir": qtd_itens,
                    "soma_vl_item_ir": float(soma_vl_item_ir),
                    "tem_f150": False,
                    "ano_mes": ano_mes,
                },
            }],
        )
    ]
    return oportunidades, []
