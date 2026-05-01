"""Validação de Bloco 9 — registros 9900 (totalizadores) e 9999 (encerramento).

Contrato SPED §3.3 (Manual EFD): o Bloco 9 totaliza por tipo de registro
declarado (9900) e número total de linhas (9999). O parser deve cruzar
o que o arquivo declara com o que ele de fato contém — divergência
indica arquivo corrompido, parsing incompleto, ou retransmissão errada.

Função pública usada por todos os 4 parsers SPED (EFD-Contribuições,
ECD, EFD ICMS/IPI, ECF). Lógica extraída byte-a-byte do código original
inline em efd_contribuicoes.py para garantir paridade de comportamento.
"""

from src.models.registros import Reg9900, Reg9999


def validar_bloco9(
    contagens_reais: dict[str, int],
    regs_9900: list[Reg9900],
    reg9999: Reg9999 | None,
    total_linhas_sped: int,
) -> tuple[dict[str, int], list[str]]:
    """Cruza contagens declaradas no Bloco 9 com contagens reais parseadas.

    Args:
        contagens_reais: dict[reg_tipo, qtd] acumulado durante o parsing
            (uma entrada por linha SPED válida — chave é o registro do
            campo [1]).
        regs_9900: lista de registros 9900 parseados (1 por reg_blc declarado).
        reg9999: registro 9999 parseado (ou None se ausente).
        total_linhas_sped: contagem de linhas que começam com `|` (linhas
            SPED válidas), pois 9999.QTD_LIN do PVA conta apenas estas.
            Linhas físicas que não começam com `|` (ex.: continuação
            Base64 do conteúdo RTF embutido em J801 — Termo de
            Encerramento de ECD) NÃO são contabilizadas. Caller deve
            calcular como `sum(1 for l in linhas_raw if l.startswith("|"))`.

    Returns:
        (contagens_declaradas, divergencias)
        - contagens_declaradas: dict[reg_tipo, qtd_dec] derivado de regs_9900
        - divergencias: lista de strings descrevendo cada divergência
          (vazia se Bloco 9 íntegro).

    A string da divergência preserva o caractere ≠ (U+2260) idêntica ao
    original em efd_contribuicoes.py para paridade byte-a-byte.
    """
    contagens_declaradas = {r.reg_blc: r.qtd_reg_blc for r in regs_9900}
    divergencias: list[str] = []

    for reg_dec, qtd_dec in contagens_declaradas.items():
        qtd_real = contagens_reais.get(reg_dec, 0)
        if qtd_real != qtd_dec:
            divergencias.append(
                f"{reg_dec}: declarado={qtd_dec} real={qtd_real}"
            )

    if reg9999 and reg9999.qtd_lin != total_linhas_sped:
        divergencias.append(
            f"9999.QTD_LIN={reg9999.qtd_lin} ≠ linhas lidas={total_linhas_sped}"
        )

    return contagens_declaradas, divergencias
