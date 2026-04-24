"""
Tabela CST-PIS/Pasep — Código de Situação Tributária.
Fonte: Anexo Único da IN RFB nº 1.009/2010, reproduzido no Manual da EFD-Contribuições.

Organização:
  00-09: Saídas / Receitas (débito)
  49:    Outras saídas
  50-56: Entradas com direito a crédito — não-cumulativo
  60-66: Entradas com crédito presumido
  70-75: Entradas sem direito a crédito
  98-99: Outras entradas / Outras situações
"""

DESCRICOES: dict[str, str] = {
    "01": "Op. tributável (BC = valor op. — alíq. básica)",
    "02": "Op. tributável (BC = valor op. — alíq. diferenciada)",
    "03": "Op. tributável (BC = qtd vendida × alíq. por unidade)",
    "04": "Op. tributável (tributação monofásica — incidência zero)",
    "05": "Op. tributável por substituição tributária",
    "06": "Op. tributável (alíq. zero)",
    "07": "Op. isenta da contribuição",
    "08": "Op. sem incidência da contribuição",
    "09": "Op. com suspensão da contribuição",
    "49": "Outras saídas",
    "50": "Op. com direito a crédito — vinc. exclus. receita tributada no merc. int.",
    "51": "Op. com direito a crédito — vinc. exclus. receita não tributada no merc. int.",
    "52": "Op. com direito a crédito — vinc. exclus. receita de exportação",
    "53": "Op. com direito a crédito — vinc. a receitas tributadas e não-tributadas",
    "54": "Op. com direito a crédito — vinc. a receitas tributadas no merc. int. e de export.",
    "55": "Op. com direito a crédito — vinc. a receitas não-tributadas no merc. int. e de export.",
    "56": "Op. com direito a crédito — vinc. a receitas tributadas e não-tributadas no merc. int. e export.",
    "60": "Crédito presumido — op. de aquisição vinc. exclus. receita tributada no merc. int.",
    "61": "Crédito presumido — op. de aquisição vinc. exclus. receita não-tributada no merc. int.",
    "62": "Crédito presumido — op. de aquisição vinc. exclus. receita de exportação",
    "63": "Crédito presumido — op. de aquisição vinc. a receitas tributadas e não-tributadas",
    "64": "Crédito presumido — op. de aquisição vinc. a receitas tributadas no merc. int. e export.",
    "65": "Crédito presumido — op. de aquisição vinc. a receitas não-tributadas no merc. int. e export.",
    "66": "Crédito presumido — op. de aquisição vinc. a receitas tributadas e não-tributadas no merc. int. e export.",
    "70": "Op. de aquisição sem direito a crédito",
    "71": "Op. de aquisição não tributável",
    "72": "Op. de aquisição com isenção",
    "73": "Op. de aquisição a alíq. zero",
    "74": "Op. de aquisição sem incidência da contribuição",
    "75": "Op. de aquisição por substituição tributária",
    "98": "Outras entradas de bens/serviços",
    "99": "Outras entradas",
}

# CSTs que representam débito (saídas / receitas tributadas)
CST_DEBITO: frozenset[str] = frozenset({"01", "02", "03", "04", "05", "06", "07", "08", "09", "49"})

# CSTs com direito a crédito (não-cumulativo)
CST_CREDITO: frozenset[str] = frozenset({
    "50", "51", "52", "53", "54", "55", "56",
    "60", "61", "62", "63", "64", "65", "66",
})

# CSTs sem direito a crédito (aquisição vedada — candidatos a reclassificação, cruzamento 12)
CST_SEM_CREDITO: frozenset[str] = frozenset({"70", "71", "72", "73", "74", "75"})

# CSTs que ativam a Tese 69 em C170 (saídas tributadas com base ad valorem)
# Base legal: RE 574.706/PR (Tema 69 STF) + Parecer SEI 7698/2021/ME (PGFN)
CST_TESE_69: frozenset[str] = frozenset({"01", "02", "03", "05"})


def eh_valido(cst: str) -> bool:
    return cst in DESCRICOES


def descricao(cst: str) -> str:
    return DESCRICOES.get(cst, f"CST desconhecido: {cst}")
