"""CR-41 — I200 extemporâneos (ECD) × 1100/1500 (EFD-Contribuições): rastreabilidade.

Base legal:
  ITG 2000 (R1) do CFC — lançamentos extemporâneos (IND_LCTO='X') registram fatos
  contábeis de períodos anteriores, reconhecidos dentro do exercício corrente por
  impossibilidade técnica de retificação da ECD anterior.
  Art. 3º Lei 10.637/2002 e Lei 10.833/2003 — créditos de PIS/COFINS de períodos
  anteriores podem ser aproveitados de forma extemporânea (Reg 1100/1500 da EFD-Contrib,
  campo PER_APU_CRED diferente do período atual).
  IN RFB 1.252/2012 §16 — crédito extemporâneo deve ser informado no 1100/1500.
  Tripé de rastreabilidade: lançamento contábil extemporâneo (ECD I200.IND_LCTO='X')
  sem contrapartida em crédito extemporâneo (EFD-Contrib 1100/1500 com PER_APU_CRED
  de período anterior) indica: (a) crédito PIS/COFINS não aproveitado, ou (b) inconsistência
  entre a contabilidade e a escrituração fiscal.
  Vigência: Leiaute 9 da ECD (AC 2020+) para IND_LCTO='X'.

Lógica:
  1. Busca I200.IND_LCTO='X' na ECD do ano-calendário.
  2. Busca 1100/1500 na EFD-Contrib do mesmo ano com PER_APU_CRED diferente do
     ano-calendário corrente (= crédito extemporâneo declarado).
  3. Se há I200 extemporâneos mas nenhum 1100/1500 extemporâneo → Oportunidade.

Dependência: ecd (CLAUDE.md §18).
modo_degradado_suportado: False (CLAUDE.md §16.3) — lançamento individual é irredutível.
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-41"


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecd"])
    if disp["ecd"] != "importada":
        return [], []

    # I200 com IND_LCTO='X' na ECD
    i200_ext = repo.consultar_ecd_i200_extemporaneos(conn, cnpj, ano_calendario)
    if not i200_ext:
        return [], []

    soma_vl_ext = sum(
        Decimal(str(r.get("vl_lcto") or 0)) for r in i200_ext
    )

    # 1100/1500 na EFD-Contrib — verifica se há créditos extemporâneos declarados
    # PER_APU_CRED no formato MMAAAA; extemporâneo = ano diferente do corrente
    ano_str = str(ano_calendario)
    recs_1100 = repo.consultar_1100_anual(conn, cnpj, ano_calendario)
    recs_1500 = repo.consultar_1500_anual(conn, cnpj, ano_calendario)

    def _eh_extemporaneo(per_apu_cred: str) -> bool:
        if not per_apu_cred or len(per_apu_cred) < 4:
            return False
        return per_apu_cred[-4:] != ano_str

    tem_credito_ext = any(
        _eh_extemporaneo(str(r.get("per_apu_cred") or ""))
        for r in recs_1100 + recs_1500
    )

    if tem_credito_ext:
        return [], []

    descricao = (
        f"ECD registra {len(i200_ext)} lançamento(s) extemporâneo(s) "
        f"(I200.IND_LCTO='X', total R$ {float(soma_vl_ext):,.2f}) no AC {ano_calendario}. "
        f"A EFD-Contribuições não apresenta créditos extemporâneos correspondentes "
        f"(1100/1500 com PER_APU_CRED de ano anterior). "
        f"Verificar se há crédito de PIS/COFINS não aproveitado relativo a esses "
        f"lançamentos extemporâneos (art. 3º Lei 10.637/2002 e Lei 10.833/2003)."
    )

    primeiro = i200_ext[0]
    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            valor_impacto_conservador=Decimal("0"),
            valor_impacto_maximo=Decimal("0"),
            evidencia=[{
                "registro": "I200",
                "arquivo": primeiro["arquivo_origem"],
                "linha": primeiro["linha_arquivo"],
                "campos_chave": {
                    "qtd_lancamentos_extemporaneos": len(i200_ext),
                    "soma_vl_lcto_ext": float(soma_vl_ext),
                    "tem_credito_extemporaneo_efd": False,
                    "ano_calendario": ano_calendario,
                },
            }],
        )
    ]
    return oportunidades, []
