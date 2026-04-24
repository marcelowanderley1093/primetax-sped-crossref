"""
Padrões de mojibake característicos de arquivos Latin1 decodificados como UTF-8.
Usados pela política de detecção de encoding (CLAUDE.md §7.2.1, Verificação C).

Se uma dessas sequências aparece em campos de texto de um arquivo decodificado como Latin1,
é forte indicativo de que o arquivo é UTF-8 sendo incorretamente interpretado como Latin1.
"""

# Sequências de mojibake Latin1-como-UTF-8 para caracteres acentuados portugueses.
# Cada entrada é (byte_sequence_em_latin1, caracter_original_utf8).
MOJIBAKE_LATIN1_COMO_UTF8: list[str] = [
    "Ã§",   # ç  (U+00E7)
    "Ã£",   # ã  (U+00E3)
    "Ãª",   # ê  (U+00EA)
    "Ã¡",   # á  (U+00E1)
    "Ã³",   # ó  (U+00F3)
    "Ã©",   # é  (U+00E9)
    "Ã­",   # í  (U+00ED)
    "Ãº",   # ú  (U+00FA)
    "Ã‡",   # Ç  (U+00C7)
    "Ã£o",  # ão (sequência comum em português)
    "Ã",    # À  (U+00C0) — prefixo mais genérico, usar com threshold maior
    "â€œ",  # "  (U+201C) — aspas curvas
    "â€™",  # '  (U+2019) — apóstrofe curvo
]

# Threshold: quantas ocorrências no arquivo inteiro já indicam encoding errado.
THRESHOLD_MOJIBAKE = 5
