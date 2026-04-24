"""CR-13 — Ausência de F100 em empresa não-cumulativa com operações no período.

Base legal:
  Art. 3º da Lei 10.637/2002 e art. 3º da Lei 10.833/2003: o rol de créditos admitidos
  inclui aluguéis de prédios, máquinas e equipamentos (inciso IV), armazenagem de mercadoria
  e frete na operação de venda (inciso IX), entre outros. Esses valores são declarados
  exclusivamente no registro F100 (Demais Documentos e Operações) quando não há NF-e
  correspondente no bloco C.
  IN RFB 1.252/2012: F100 obrigatório para operações não representadas por documento fiscal
  do bloco C (ex: notas de débito, faturas, contratos de aluguel).

Lógica do cruzamento:
  Se 0110.COD_INC_TRIB = '1' (não-cumulativo) E M200.VL_REC_BRT_TOTAL > 0 E F100 ausente
  para o período → empresa não-cumulativa com receita declarada mas sem créditos de
  operações diversas. Oportunidade analítica de baixa certeza — auditor deve verificar
  se há aluguéis, fretes e serviços aptos a crédito não declarados.
  Impacto: R$ 0,00 (indeterminado sem acesso às despesas do período).
"""

from decimal import Decimal

CODIGO_REGRA = "CR-13"


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Oportunidade

    # Verifica regime tributário (não-cumulativo)
    param = repo.consultar_0110(conn, cnpj, ano_mes)
    if not param:
        return [], []
    cod_inc_trib = str(param.get("cod_inc_trib") or "").strip()
    if cod_inc_trib != "1":
        return [], []

    # Verifica se há receita declarada (M200)
    m200 = repo.consultar_m200_por_periodo(conn, cnpj, ano_mes)
    if not m200:
        return [], []
    vl_rec = Decimal(str(m200.get("vl_rec_brt_total") or 0))
    if vl_rec <= Decimal("0.01"):
        return [], []

    # Verifica ausência de F100
    qtd_f100 = repo.contar_f100_por_periodo(conn, cnpj, ano_mes)
    if qtd_f100 > 0:
        return [], []

    descricao = (
        f"Período {ano_mes}: empresa não-cumulativa (COD_INC_TRIB=1) com"
        f" VL_REC_BRT_TOTAL=R$ {float(vl_rec):.2f} mas sem nenhum registro F100."
        f" Verificar se há aluguéis, fretes, armazenagem ou outros serviços"
        f" aptos a crédito PIS/COFINS não declarados."
    )
    oportunidades = [Oportunidade(
        codigo_regra=CODIGO_REGRA,
        descricao=descricao,
        severidade="baixo",
        valor_impacto_conservador=Decimal("0"),
        valor_impacto_maximo=Decimal("0"),
        evidencia=[{
            "registro": "0110 + M200",
            "arquivo": m200.get("arquivo_origem") or "",
            "linha": m200.get("linha_arquivo") or 0,
            "campos_chave": {
                "cod_inc_trib": cod_inc_trib,
                "vl_rec_brt_total": float(vl_rec),
                "qtd_f100": qtd_f100,
            },
        }],
    )]
    return oportunidades, []
