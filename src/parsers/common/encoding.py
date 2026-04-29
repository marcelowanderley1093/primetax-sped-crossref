"""
Política de detecção de encoding em arquivos SPED.
Implementa a estratégia canônica descrita em CLAUDE.md §7.2.1:
  1. Tentativa estrita UTF-8
  2. Fallback Latin1
  3. Validação semântica (CNPJ, tokens estruturais, mojibake)
  4. Registro de encoding e confiança
  5. Confirmação explícita em casos suspeitos
"""

import logging
import re
import time
from pathlib import Path
from typing import NamedTuple

from src.tables.encoding_patterns import MOJIBAKE_LATIN1_COMO_UTF8, THRESHOLD_MOJIBAKE

logger = logging.getLogger(__name__)


class ResultadoEncoding(NamedTuple):
    encoding: str        # "utf8" ou "latin1"
    confianca: str       # "alto", "validado", "suspeito"
    motivo: str          # descrição do caminho de detecção


def detectar_encoding(
    caminho: Path,
    *,
    override: str = "auto",
    prompt_operador: bool = True,
) -> ResultadoEncoding:
    """
    Detecta o encoding de um arquivo SPED.

    Args:
        caminho: Caminho para o arquivo SPED.
        override: "auto" (detecta), "utf8" (força), "latin1" (força).
        prompt_operador: Se True, pede confirmação quando confiança = suspeito.

    Returns:
        ResultadoEncoding com encoding, confiança e motivo.

    Raises:
        ValueError: Se o arquivo for irrecuperável (Verificações A ou B falham em Latin1).
    """
    if override not in ("auto", "utf8", "latin1"):
        raise ValueError(f"override inválido: {override!r}. Use 'auto', 'utf8' ou 'latin1'.")

    inicio = time.monotonic()

    if override != "auto":
        resultado = _aplicar_override(caminho, override)
        _registrar_log(caminho, resultado, inicio)
        return resultado

    resultado = _detectar_automatico(caminho, prompt_operador)
    _registrar_log(caminho, resultado, inicio)
    return resultado


def _detectar_automatico(caminho: Path, prompt_operador: bool) -> ResultadoEncoding:
    # Passo 1: tentativa estrita UTF-8
    try:
        linhas = caminho.read_text(encoding="utf-8", errors="strict").splitlines()
        resultado = ResultadoEncoding("utf8", "alto", "UTF-8 estrito sem erros de decode")
        return resultado
    except UnicodeDecodeError:
        pass

    # Passo 2: fallback Latin1 (nunca gera exceção)
    # Truncamento em |9999| (Passo 0) descarta blob da assinatura PVA antes
    # das Verificações A/B/C — sem isso, mojibake do PKCS#7 dispara
    # falso-positivo na Verificação C.
    conteudo = caminho.read_text(encoding="latin1", errors="strict")
    conteudo = _truncar_em_9999(conteudo)
    linhas = conteudo.splitlines()

    # Passo 3: validação semântica
    ok_a, msg_a = _verificar_cnpj(linhas)
    ok_b, msg_b = _verificar_tokens_estruturais(linhas)
    ok_c, msg_c = _verificar_ausencia_mojibake(linhas)

    if not ok_a or not ok_b:
        raise ValueError(
            f"Arquivo {caminho.name} rejeitado: encoding não reconhecível ou arquivo corrompido. "
            f"Verificação A (CNPJ): {'OK' if ok_a else msg_a}. "
            f"Verificação B (tokens): {'OK' if ok_b else msg_b}. "
            "Verifique a origem do arquivo com o cliente."
        )

    if ok_c:
        return ResultadoEncoding("latin1", "validado", "Latin1 com validação semântica completa")

    # Confiança suspeita: passou A e B mas falhou em C (mojibake)
    resultado = ResultadoEncoding("latin1", "suspeito", f"Mojibake detectado: {msg_c}")

    if prompt_operador:
        _confirmar_com_operador(caminho, linhas, resultado)

    return resultado


def _aplicar_override(caminho: Path, encoding: str) -> ResultadoEncoding:
    codec = "utf-8" if encoding == "utf8" else "latin1"
    try:
        conteudo = caminho.read_text(encoding=codec, errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Override --encoding {encoding} falhou no arquivo {caminho.name}: {exc}"
        ) from exc
    conteudo = _truncar_em_9999(conteudo)
    linhas = conteudo.splitlines()

    ok_a, msg_a = _verificar_cnpj(linhas)
    ok_b, msg_b = _verificar_tokens_estruturais(linhas)
    if not ok_a or not ok_b:
        raise ValueError(
            f"Arquivo {caminho.name} rejeitado mesmo com override {encoding!r}. "
            f"Verificação A: {'OK' if ok_a else msg_a}. "
            f"Verificação B: {'OK' if ok_b else msg_b}."
        )

    _, msg_c = _verificar_ausencia_mojibake(linhas)
    confianca = "validado" if not msg_c else "suspeito"
    return ResultadoEncoding(encoding, confianca, f"Override explícito {encoding!r}")


# ---------------------------------------------------------------------------
# Truncamento em |9999| (Passo 0 da CLAUDE.md §7.2.1)
# ---------------------------------------------------------------------------


_RE_LINHA_9999 = re.compile(r"^\|9999\|\d+\|", re.MULTILINE)
"""Linha do registro 9999: |9999|QTD_LIN|. QTD_LIN é numérica obrigatória."""


def _truncar_em_9999(conteudo: str) -> str:
    """Trunca o conteúdo logo após a linha do registro 9999.

    Arquivos transmitidos pelo PVA da RFB têm assinatura digital PKCS#7
    (CMS SignedData, OID 1.2.840.113549.1.7.2) anexada após o registro
    9999, marcada pelo prefixo `SBRCAAEPDR`. Esse blob é binário e bytes
    arbitrários decodificados como Latin1 podem formar strings que começam
    com '|' — o que enganaria as Verificações B e C.

    A linha 9999 é o último registro estrutural do SPED por definição
    (IN RFB 1.252/2012, Manual EFD-Contribuições). Tudo após o newline
    que segue o |9999|N| é descartado para validação de encoding.

    Se o arquivo não tem |9999|, retorna o conteúdo intocado — cabe às
    verificações reportar o problema apropriadamente.
    """
    m = _RE_LINHA_9999.search(conteudo)
    if m is None:
        return conteudo
    fim = m.end()
    # Inclui o terminador de linha (\r\n, \n ou EOF).
    if fim < len(conteudo) and conteudo[fim] == "\r":
        fim += 1
    if fim < len(conteudo) and conteudo[fim] == "\n":
        fim += 1
    return conteudo[:fim]


def _verificar_cnpj(linhas: list[str]) -> tuple[bool, str]:
    """Verificação A: campo CNPJ do 0000 deve ser 14 dígitos ASCII.

    Posições conhecidas do CNPJ no registro 0000 por SPED:
      - EFD-Contribuições, ECF: campos[9]
      - EFD ICMS/IPI, ECD:       campos[7]
    A verificação tenta todas as posições conhecidas para ser agnóstica ao tipo de SPED:
      - EFD-Contribuições, EFD ICMS/IPI antiga: campos[9]
      - EFD ICMS/IPI: campos[7]
      - ECD: campos[6]
      - ECF: campos[4] (após REG, NOME_ESC='LECF', COD_VER, vem CNPJ)
    """
    _POSICOES_CNPJ = (9, 7, 6, 4)
    for linha in linhas[:50]:
        campos = linha.split("|")
        if len(campos) > 1 and campos[1] == "0000":
            for pos in _POSICOES_CNPJ:
                if len(campos) > pos:
                    cnpj = campos[pos].strip()
                    if cnpj and len(cnpj) == 14 and cnpj.isdigit():
                        return True, "OK"
            # 0000 encontrado mas CNPJ não estava em nenhuma posição conhecida
            for pos in _POSICOES_CNPJ:
                if len(campos) > pos:
                    cnpj = campos[pos].strip()
                    if cnpj and not cnpj.isdigit():
                        return False, f"CNPJ não-numérico no 0000: {cnpj!r}"
            return True, "0000 encontrado mas CNPJ ausente (não bloqueia)"
    return True, "0000 não encontrado nas primeiras 50 linhas (não bloqueia)"


def _verificar_tokens_estruturais(linhas: list[str]) -> tuple[bool, str]:
    """Verificação B: separador | e identificadores de registro devem ser ASCII puro."""
    if not linhas:
        return False, "Arquivo vazio"
    for i, linha in enumerate(linhas[:20]):
        if not linha.startswith("|"):
            return False, f"Linha {i+1} não começa com '|': {linha[:30]!r}"
        try:
            linha.encode("ascii")
            # Linhas com campos de texto (NOME etc.) podem ter non-ASCII — não bloquear
        except UnicodeEncodeError:
            pass  # Non-ASCII em campos de texto é esperado
        campos = linha.split("|")
        if len(campos) < 2:
            return False, f"Linha {i+1} sem separador |: {linha[:30]!r}"
        reg = campos[1]
        if not reg.replace("_", "").isalnum():
            return False, f"Identificador de registro inválido linha {i+1}: {reg!r}"
    return True, "OK"


def _verificar_ausencia_mojibake(linhas: list[str]) -> tuple[bool, str]:
    """Verificação C: conta ocorrências de mojibake característico."""
    texto = "\n".join(linhas)
    total = sum(texto.count(pat) for pat in MOJIBAKE_LATIN1_COMO_UTF8)
    if total >= THRESHOLD_MOJIBAKE:
        return False, f"{total} ocorrências de mojibake (threshold={THRESHOLD_MOJIBAKE})"
    return True, ""


def _confirmar_com_operador(
    caminho: Path, linhas: list[str], resultado: ResultadoEncoding
) -> None:
    """Exibe amostra e pede confirmação explícita quando confiança = suspeito."""
    amostra = linhas[:3]
    print(f"\n[ATENÇÃO] Encoding suspeito em {caminho.name}")
    print(f"Motivo: {resultado.motivo}")
    print("Amostra das 3 primeiras linhas:")
    for i, l in enumerate(amostra, 1):
        print(f"  {i}: {l[:120]}")
    resposta = input("Confirmar leitura com encoding Latin1? [s/n]: ").strip().lower()
    if resposta != "s":
        raise ValueError(
            f"Importação cancelada pelo operador para {caminho.name}. "
            "Use --encoding utf8 se o arquivo for UTF-8."
        )


def _registrar_log(caminho: Path, resultado: ResultadoEncoding, inicio: float) -> None:
    ms = int((time.monotonic() - inicio) * 1000)
    logger.info(
        "Arquivo %s detectado como encoding %s com confiança %s. Tempo de detecção: %d ms.",
        caminho.name,
        resultado.encoding,
        resultado.confianca,
        ms,
    )
    if resultado.confianca == "suspeito":
        logger.warning(
            "Encoding suspeito em %s: %s. Verifique na aba 'Qualidade da Análise' do relatório.",
            caminho.name,
            resultado.motivo,
        )
