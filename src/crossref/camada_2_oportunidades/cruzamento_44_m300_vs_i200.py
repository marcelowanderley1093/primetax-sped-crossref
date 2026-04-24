"""CR-44 — M300/M350 (ECF e-Lalur/e-Lacs) × I200 (ECD): rastreabilidade de lançamentos.

Base legal:
  Lei 12.973/2014 (art. 8º, §2º) — as adições e exclusões do Lucro Real devem ser
  rastreáveis até os lançamentos contábeis específicos da ECD quando vinculadas a fatos
  contábeis (IND_RELACAO in {2, 3}).
  IN RFB 1.700/2017 (art. 18) — M312/M362 contêm o NUM_LCTO do Diário (ECD I200)
  correspondente a cada linha do e-Lalur/e-Lacs com fundamento contábil.
  ADE Cofis 02/2026 §12.
  Vigência: desde AC 2014 (criação do e-Lalur eletrônico).

Lógica:
  1. Carrega M300 com IND_RELACAO in {'2','3'} (tem vinculação contábil).
  2. Carrega M312 (NUM_LCTO vinculado a cada M300).
  3. Carrega set de NUM_LCTO da ECD (I200).
  4. M312.NUM_LCTO ausente na ECD → lançamento do e-Lalur sem respaldo contábil.
  5. M300 com IND_RELACAO 2/3 mas sem M312 → adição/exclusão sem vinculação registrada.

Dependência: ecd (CLAUDE.md §18).
modo_degradado_suportado: False — exige NUM_LCTO individual (CLAUDE.md §16.3).
"""

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-44"


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecf", "ecd"])
    if disp["ecf"] != "importada" or disp["ecd"] != "importada":
        return [], []

    m300_registros = repo.consultar_ecf_m300(conn, cnpj, ano_calendario)
    m312_registros = repo.consultar_ecf_m312(conn, cnpj, ano_calendario)
    ecd_num_lcto = repo.consultar_ecd_num_lcto_set(conn, cnpj, ano_calendario)

    if not m300_registros:
        return [], []

    # M300 com vinculação contábil declarada (IND_RELACAO 2 ou 3)
    m300_vinculados = [
        r for r in m300_registros
        if r.get("ind_relacao") in ("2", "3")
    ]
    if not m300_vinculados:
        return [], []

    # M312 indexados por m300_linha_arquivo
    m312_por_m300: dict[int, list[str]] = {}
    for r in m312_registros:
        linha_m300 = r.get("m300_linha_arquivo", 0)
        m312_por_m300.setdefault(linha_m300, []).append(r.get("num_lcto", ""))

    # Detecta M300 com IND_RELACAO contábil mas sem NUM_LCTO na ECD
    orfaos = []
    for m300 in m300_vinculados:
        linha = m300["linha_arquivo"]
        num_lctos = m312_por_m300.get(linha, [])
        if not num_lctos:
            # M300 declara vinculação mas não tem M312 → sem evidência contábil
            orfaos.append({
                "tipo": "sem_m312",
                "m300": m300,
                "num_lctos": [],
            })
        else:
            # Tem M312, mas NUM_LCTO não existe na ECD
            ausentes = [n for n in num_lctos if n and n not in ecd_num_lcto]
            if ausentes:
                orfaos.append({
                    "tipo": "num_lcto_ausente_ecd",
                    "m300": m300,
                    "num_lctos": ausentes,
                })

    if not orfaos:
        return [], []

    oportunidades = []
    for caso in orfaos[:10]:  # limita evidências para legibilidade
        m300 = caso["m300"]
        tipo = caso["tipo"]
        if tipo == "sem_m312":
            msg = (
                f"M300 linha {m300['linha_arquivo']}: CODIGO={m300.get('codigo')} "
                f"TIPO_LAN={m300.get('tipo_lancamento')} IND_RELACAO={m300.get('ind_relacao')} "
                f"— vinculação contábil declarada mas sem registro M312 correspondente. "
                f"AC {ano_calendario}."
            )
        else:
            msg = (
                f"M300 linha {m300['linha_arquivo']}: CODIGO={m300.get('codigo')} "
                f"— NUM_LCTO(s) {caso['num_lctos']} presentes em M312 "
                f"mas ausentes na ECD I200 do AC {ano_calendario}. "
                f"Rastreabilidade do e-Lalur comprometida."
            )
        oportunidades.append(
            Oportunidade(
                codigo_regra=CODIGO_REGRA,
                descricao=msg,
                severidade="medio",
                valor_impacto_conservador=0,
                valor_impacto_maximo=0,
                evidencia=[{
                    "registro": "M300/M312 × I200",
                    "arquivo": m300.get("arquivo_origem", ""),
                    "linha": m300["linha_arquivo"],
                    "campos_chave": {
                        "codigo": m300.get("codigo"),
                        "tipo_lancamento": m300.get("tipo_lancamento"),
                        "ind_relacao": m300.get("ind_relacao"),
                        "valor": m300.get("valor"),
                        "tipo_problema": tipo,
                        "num_lctos_ausentes": caso["num_lctos"],
                        "ano_calendario": ano_calendario,
                    },
                }],
            )
        )

    return oportunidades, []
