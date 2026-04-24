"""CR-46 — X480 (ECF benefícios fiscais) × M300 (ECF exclusões e-Lalur): benefício perdido.

Base legal:
  Lei 11.196/2005 (Lei do Bem) — incentivos fiscais à P&D (art. 17-26).
  Lei 9.249/1995, art. 10 — isenção de lucros e dividendos.
  Lei 9.532/1997, art. 11 e 12 — incentivos fiscais regionais (SUDAM/SUDENE).
  IN RFB 1.700/2017 (art. 129 e seguintes) — dedutibilidades e exclusões específicas.
  ADE Cofis 02/2026 §20: X480 lista benefícios fiscais utilizados pela PJ.
  Cada benefício declarado em X480 com valor > 0 deve ter contrapartida em M300
  como exclusão (TIPO_LANCAMENTO='E') ou, para certos incentivos de subvenção,
  como redução de base.
  Se X480 tem benefício utilizado mas M300 não tem exclusão → benefício perdido.
  Vigência: desde AC 2014.

Lógica:
  1. Carrega X480 com VALOR > 0 (benefícios com valor utilizado).
  2. Carrega M300 com TIPO_LANCAMENTO='E' (exclusões do e-Lalur).
  3. Se há X480 com valor > 0 mas nenhuma exclusão no M300 → alerta geral de benefício não aproveitado.
  4. Se há X480 com valor > 0 E M300 tem exclusões → verificação por código quando possível.

Dependência: ecf apenas (CLAUDE.md §18.6 Sprint 8).
modo_degradado_suportado: N/A — ECF isolada.
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-46"
_THRESHOLD_VALOR = Decimal("1000")  # R$ 1.000 mínimo para reportar


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecf"])
    if disp["ecf"] != "importada":
        return [], []

    x480_registros = repo.consultar_ecf_x480(conn, cnpj, ano_calendario)
    m300_registros = repo.consultar_ecf_m300(conn, cnpj, ano_calendario)

    if not x480_registros:
        return [], []

    # Filtra X480 com valor utilizado acima do threshold
    x480_com_valor = [
        r for r in x480_registros
        if Decimal(str(r.get("valor") or 0)) > _THRESHOLD_VALOR
    ]
    if not x480_com_valor:
        return [], []

    # Set de CODIGOs com exclusão em M300
    codigos_exclusao_m300 = {
        r.get("codigo", "")
        for r in m300_registros
        if r.get("tipo_lancamento") == "E"
    }

    total_excluido_m300 = sum(
        Decimal(str(r.get("valor") or 0))
        for r in m300_registros
        if r.get("tipo_lancamento") == "E"
    )

    oportunidades = []

    if total_excluido_m300 == Decimal("0"):
        # Nenhuma exclusão no M300 apesar de benefícios declarados no X480
        total_x480 = sum(Decimal(str(r.get("valor") or 0)) for r in x480_com_valor)
        oportunidades.append(
            Oportunidade(
                codigo_regra=CODIGO_REGRA,
                descricao=(
                    f"X480 declara {len(x480_com_valor)} benefício(s) fiscal(is) com "
                    f"valor total de R$ {float(total_x480):,.2f} no AC {ano_calendario}, "
                    f"mas o e-Lalur (M300) não contém nenhuma exclusão (TIPO_LANCAMENTO='E'). "
                    f"Benefícios fiscais declarados sem aproveitamento no cálculo do IRPJ. "
                    f"Verificar códigos: {[r.get('codigo') for r in x480_com_valor[:5]]}."
                ),
                severidade="alto",
                valor_impacto_conservador=total_x480,
                valor_impacto_maximo=total_x480,
                evidencia=[{
                    "registro": "X480 × M300",
                    "arquivo": x480_com_valor[0].get("arquivo_origem", ""),
                    "linha": x480_com_valor[0].get("linha_arquivo"),
                    "campos_chave": {
                        "qtd_x480_com_valor": len(x480_com_valor),
                        "total_x480": float(total_x480),
                        "total_exclusoes_m300": 0.0,
                        "codigos_x480": [r.get("codigo") for r in x480_com_valor],
                        "ano_calendario": ano_calendario,
                    },
                }],
            )
        )
    else:
        # Tem exclusões em M300 mas verifica X480 sem correspondência por código
        x480_sem_exclusao = [
            r for r in x480_com_valor
            if r.get("codigo", "") not in codigos_exclusao_m300
        ]
        for r in x480_sem_exclusao:
            valor = Decimal(str(r.get("valor") or 0))
            oportunidades.append(
                Oportunidade(
                    codigo_regra=CODIGO_REGRA,
                    descricao=(
                        f"X480: benefício CODIGO={r.get('codigo')} "
                        f"({r.get('descricao', '')}) "
                        f"com valor R$ {float(valor):,.2f} "
                        f"não possui exclusão correspondente em M300 "
                        f"no AC {ano_calendario}."
                    ),
                    severidade="medio",
                    valor_impacto_conservador=valor,
                    valor_impacto_maximo=valor,
                    evidencia=[{
                        "registro": "X480 × M300",
                        "arquivo": r.get("arquivo_origem", ""),
                        "linha": r.get("linha_arquivo"),
                        "campos_chave": {
                            "codigo": r.get("codigo"),
                            "descricao": r.get("descricao"),
                            "valor": float(valor),
                            "codigos_exclusao_m300": list(codigos_exclusao_m300)[:10],
                            "ano_calendario": ano_calendario,
                        },
                    }],
                )
            )

    return oportunidades, []
