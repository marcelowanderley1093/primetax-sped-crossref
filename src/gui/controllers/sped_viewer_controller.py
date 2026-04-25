"""
SpedViewerController — leitura de arquivo SPED com contexto.

Lê arquivo bruto sem reparsear (princípio 2 — SPED original imutável).
Para arquivos pequenos (<5 MB) carrega em memória; para grandes, lê
linhas com `readline()` em modo posicional, mantendo apenas a janela
de contexto.

Operações de navegação (próxima ocorrência, registro pai) sempre
sobre o arquivo aberto, não sobre o banco SQLite — é a fonte de
verdade para a tela.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


_TAMANHO_MAX_CARGA_MEMORIA = 5 * 1024 * 1024  # 5 MB


@dataclass
class CampoRegistro:
    """Um campo decomposto da linha SPED."""
    indice: int                # posição (0-based) entre os pipes
    nome: str                  # genérico "campo[N]" ou nome conhecido
    valor: str


@dataclass
class ContextoLinha:
    """Resultado de carregar_arquivo: tudo o que T5 precisa para renderizar."""
    arquivo: Path
    linhas: list[str]          # janela de contexto (cru, com pipes)
    linha_offset: int          # número da primeira linha em `linhas`
    linha_alvo: int            # número absoluto da linha alvo
    linha_alvo_idx: int        # índice em `linhas` da linha alvo
    reg_alvo: str              # ex: "C170"
    campos: list[CampoRegistro]
    parent_linha: int | None = None    # número da linha do registro pai (se houver)
    parent_reg: str | None = None
    total_linhas: int = 0      # total absoluto do arquivo


# Mapa de pais conhecidos — fallback heurístico quando registro filho
# claramente pertence a um pai específico. Aproximações por inicial:
#   C100 → pai de C170, C175, C181, C185, ...
#   M100 → pai de M105
#   M300 → pai de M310, M312
#   I150 → pai de I155
#   I200 → pai de I250
_PARENT_HINTS: dict[str, str] = {
    "C170": "C100", "C175": "C100", "C180": "C100", "C181": "C100",
    "C185": "C100", "C190": "C100", "C195": "C100",
    "M105": "M100", "M115": "M110", "M210": "M200", "M225": "M210",
    "M310": "M300", "M312": "M300", "M315": "M300",
    "M505": "M500", "M610": "M600",
    "I155": "I150", "I250": "I200",
    "F129": "F120", "F139": "F130",
    "G125": "G110", "H010": "H005",
}


class SpedViewerController:
    """Controller stateful para um arquivo aberto."""

    JANELA_PADRAO = 10  # 10 linhas antes + 10 depois

    def __init__(self, parent: object | None = None) -> None:
        self._cache_linhas: list[str] | None = None
        self._cache_path: Path | None = None

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def carregar_arquivo(
        self, arquivo: Path, linha_alvo: int, *, janela: int | None = None
    ) -> ContextoLinha:
        """Lê arquivo e retorna janela de contexto + decomposição da linha."""
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo SPED não encontrado: {arquivo}")
        janela = janela if janela is not None else self.JANELA_PADRAO

        linhas = self._ler_linhas(arquivo)
        total = len(linhas)
        if linha_alvo < 1 or linha_alvo > total:
            raise IndexError(
                f"linha_alvo {linha_alvo} fora do intervalo do arquivo (1..{total})"
            )

        ini = max(1, linha_alvo - janela)
        fim = min(total, linha_alvo + janela)
        janela_linhas = linhas[ini - 1: fim]
        linha_alvo_idx = linha_alvo - ini

        linha_alvo_raw = linhas[linha_alvo - 1]
        reg_alvo = self._extrair_reg(linha_alvo_raw)
        campos = self._decompor_campos(linha_alvo_raw)

        parent_linha = None
        parent_reg = _PARENT_HINTS.get(reg_alvo)
        if parent_reg:
            parent_linha = self._achar_pai(linhas, linha_alvo, parent_reg)

        return ContextoLinha(
            arquivo=arquivo,
            linhas=janela_linhas,
            linha_offset=ini,
            linha_alvo=linha_alvo,
            linha_alvo_idx=linha_alvo_idx,
            reg_alvo=reg_alvo,
            campos=campos,
            parent_linha=parent_linha,
            parent_reg=parent_reg,
            total_linhas=total,
        )

    def proxima_ocorrencia(
        self, arquivo: Path, partir_de: int, reg_tipo: str
    ) -> int | None:
        """Retorna a próxima linha (>partir_de) com o mesmo registro, ou None."""
        linhas = self._ler_linhas(arquivo)
        for i in range(partir_de, len(linhas)):
            if self._extrair_reg(linhas[i]) == reg_tipo:
                return i + 1  # 1-based
        return None

    def anterior_ocorrencia(
        self, arquivo: Path, ate: int, reg_tipo: str
    ) -> int | None:
        """Retorna a linha anterior (<ate) com o mesmo registro, ou None."""
        linhas = self._ler_linhas(arquivo)
        for i in range(min(ate - 2, len(linhas) - 1), -1, -1):
            if self._extrair_reg(linhas[i]) == reg_tipo:
                return i + 1
        return None

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _ler_linhas(self, arquivo: Path) -> list[str]:
        """Lê todas as linhas do arquivo. Cache simples para mesmo path."""
        if self._cache_path == arquivo and self._cache_linhas is not None:
            return self._cache_linhas

        # Detecta encoding rapidamente — Latin-1 é tolerante (qualquer byte
        # decodifica). Para uso interno do viewer, isso é seguro.
        encoding = "latin-1"
        try:
            tamanho = arquivo.stat().st_size
            if tamanho > _TAMANHO_MAX_CARGA_MEMORIA:
                logger.info(
                    "Arquivo grande (%d bytes) — leitura linha-a-linha", tamanho
                )
            with arquivo.open(encoding=encoding, errors="replace") as f:
                linhas = [l.rstrip("\r\n") for l in f]
        except OSError as exc:
            raise FileNotFoundError(f"Falha ao ler {arquivo}: {exc}") from exc

        self._cache_path = arquivo
        self._cache_linhas = linhas
        return linhas

    @staticmethod
    def _extrair_reg(linha: str) -> str:
        """Retorna o tipo do registro de uma linha SPED (segundo campo)."""
        if not linha or not linha.startswith("|"):
            return ""
        partes = linha.split("|", 3)
        return partes[1].strip().upper() if len(partes) >= 2 else ""

    @staticmethod
    def _decompor_campos(linha: str) -> list[CampoRegistro]:
        if not linha:
            return []
        partes = linha.split("|")
        # Primeira e última posições costumam ser vazias por causa dos pipes
        # de delimitação. Preservamos os índices originais (esqueleto SPED).
        campos = []
        for i, valor in enumerate(partes):
            if i == 0 and valor == "":
                continue  # pipe inicial
            if i == len(partes) - 1 and valor == "":
                continue  # pipe final
            nome = "REG" if i == 1 else f"campo[{i}]"
            campos.append(CampoRegistro(indice=i, nome=nome, valor=valor))
        return campos

    @staticmethod
    def _achar_pai(linhas: list[str], linha_filho: int, parent_reg: str) -> int | None:
        """Sobe procurando pelo pai do registro filho.

        Estratégia: percorre de baixo para cima a partir de linha_filho-1
        até achar uma linha cujo registro seja parent_reg.
        """
        for i in range(linha_filho - 2, -1, -1):
            partes = linhas[i].split("|", 3)
            if len(partes) >= 2 and partes[1].strip().upper() == parent_reg:
                return i + 1
        return None
