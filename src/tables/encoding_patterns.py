"""
Padrões de mojibake característicos de arquivos Latin1 decodificados como UTF-8.
Usados pela política de detecção de encoding (CLAUDE.md §7.2.1, Verificação C).

Se uma dessas sequências aparece em campos de texto de um arquivo decodificado como Latin1,
é forte indicativo de que o arquivo é UTF-8 sendo incorretamente interpretado como Latin1.
"""

# Sequências de mojibake Latin1-como-UTF-8 para caracteres acentuados portugueses.
# Cada entrada é uma sequência que, se aparecer no texto decodificado como Latin1,
# indica que o arquivo original era UTF-8 (cada acentuado em UTF-8 começa com \xc3
# ou \xc2 que, em Latin1, viram Ã ou Â).
#
# Lista alinhada com paridade v6 arquivada: pares específicos apenas, sem prefixos
# soltos (Ã sozinho gerava falso positivo em qualquer Ã legítimo Latin1, ex: ÇÃO em
# MANUTENÇÃO/LOCAÇÃO).
MOJIBAKE_LATIN1_COMO_UTF8: list[str] = [
    # Vogais acentuadas minúsculas
    "Ã§",   # ç
    "Ã£",   # ã
    "Ã¡",   # á
    "Ã¢",   # â
    "Ã ",   # à (atenção: termina com espaço)
    "Ã©",   # é
    "Ãª",   # ê
    "Ã­",   # í
    "Ã®",   # î
    "Ã³",   # ó
    "Ãµ",   # õ
    "Ã´",   # ô
    "Ãº",   # ú
    "Ã»",   # û
    "Ã¨",   # è
    "Ã±",   # ñ
    # Maiúsculas
    "Ã‡",   # Ç
    "ÃƒÃ ",  # Ã (mojibake duplo, raro)
    # Prefixo \xc2 (NBSP, símbolos não-quebráveis)
    "Â ",   # NBSP
    "Â°",   # graus (Nº como N°)
    "Â§",   # parágrafo
    # Aspas/apóstrofes curvos CP-1252 (mantidos da lista anterior; úteis para
    # arquivos copiados/colados de Word com encoding intermediário corrompido)
    "â€œ",  # "  (aspas curvas)
    "â€™",  # '  (apóstrofe curvo)
]

# Threshold: quantas ocorrências no arquivo inteiro já indicam encoding errado.
THRESHOLD_MOJIBAKE = 5
