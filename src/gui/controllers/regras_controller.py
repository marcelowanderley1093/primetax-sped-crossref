"""
RegrasController — introspecção das 49 regras de cruzamento.

Lê os módulos importados em `src.crossref.engine` e expõe metadados
(código, camada, descrição, base legal, dependências SPED, sprint)
para a view T0. Read-only — adicionar regra ainda é fluxo de código,
via slash command `/novo-cruzamento` (CLAUDE.md §11).

Por que ler de `engine` e não escanear o filesystem: a fonte da verdade
do "que está ativo" é o engine. Se um módulo está em `src/crossref/`
mas não foi adicionado às listas `_CRUZAMENTOS_CAMADA*`, ele não roda.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.crossref import engine as _engine


@dataclass
class RegraInfo:
    """Metadados de uma regra de cruzamento, derivados via introspecção."""
    codigo: str            # "CR-07", "CI-01", etc.
    camada: int            # 1, 2 ou 3
    descricao: str         # primeira linha após o título do docstring
    base_legal: str        # bloco "Base legal:" do docstring
    dependencias_sped: list[str]  # ex: ["efd_contribuicoes"]
    sprint: str            # "Sprint 1", "Sprint 6", etc., ou ""
    severidade: str        # "alto", "medio", "baixo", "ok", "n/a"
    modulo_path: str       # ex: "src.crossref.camada_2_oportunidades.cruzamento_07_tese69_c170"


_RE_BASE_LEGAL = re.compile(
    r"Base legal:?\s*\n?(.+?)(?:\n\s*\n|$)",
    re.DOTALL | re.IGNORECASE,
)
_RE_SPRINT = re.compile(r"Sprint\s+(\d+)", re.IGNORECASE)
_RE_PRIMEIRA_LINHA = re.compile(r"Cruzamento\s+\d+\s*[—\-:]\s*(.+)")
_RE_CODIGO_NA_DESCRICAO = re.compile(r"^(C[RI]-\d+)\s*[—\-:]\s*", re.IGNORECASE)
_RE_CODIGO_DOCSTRING = re.compile(
    r"Cruzamento\s+(\d+)", re.IGNORECASE
)


class RegrasController:
    """Read-only — introspecciona os módulos do engine."""

    def listar_regras(self) -> list[RegraInfo]:
        regras: list[RegraInfo] = []
        for modulo in _engine._CRUZAMENTOS_CAMADA1:
            regras.append(self._extrair_info(modulo, camada=1))
        for modulo in _engine._CRUZAMENTOS_CAMADA2:
            regras.append(self._extrair_info(modulo, camada=2))
        for modulo in _engine._CRUZAMENTOS_CAMADA3:
            regras.append(self._extrair_info(modulo, camada=3))
        # Ordena por código (CI-01, CR-01, CR-02, ...)
        regras.sort(key=lambda r: (r.codigo[:2], self._numero_ordenacao(r.codigo)))
        return regras

    @staticmethod
    def _numero_ordenacao(codigo: str) -> int:
        """Extrai o número final do código pra ordenação (CR-07 → 7)."""
        m = re.search(r"(\d+)\s*$", codigo)
        return int(m.group(1)) if m else 999

    @staticmethod
    def _extrair_info(modulo, *, camada: int) -> RegraInfo:
        codigo = getattr(modulo, "CODIGO_REGRA", None) or ""
        deps = getattr(modulo, "DEPENDENCIAS_SPED", []) or ["efd_contribuicoes"]
        severidade = ""
        # Tenta puxar SEVERIDADE do módulo de regra correlato (ex: tese_69_icms)
        # Fallback: parsing do docstring
        for nome in ("SEVERIDADE", "_SEVERIDADE"):
            if hasattr(modulo, nome):
                severidade = getattr(modulo, nome) or ""
                break

        doc = (modulo.__doc__ or "").strip()
        descricao = ""
        primeira = doc.split("\n", 1)[0].strip() if doc else ""
        m = _RE_PRIMEIRA_LINHA.match(primeira)
        if m:
            descricao = m.group(1).strip().rstrip(".")
        elif primeira:
            descricao = primeira.rstrip(".")

        # Fallbacks para o código quando o módulo não exporta CODIGO_REGRA:
        # 1. código embutido no início da descrição ("CR-14 — ...")
        # 2. número do docstring "Cruzamento NN" → CR-NN
        m_desc = _RE_CODIGO_NA_DESCRICAO.match(descricao)
        if m_desc:
            if not codigo:
                codigo = m_desc.group(1).upper()
            # Sempre remove prefixo "CR-NN —" da descrição — é redundante
            # quando o código é exibido em coluna separada na T0.
            descricao = _RE_CODIGO_NA_DESCRICAO.sub("", descricao, count=1)
        if not codigo:
            m_doc = _RE_CODIGO_DOCSTRING.search(doc)
            if m_doc:
                num = int(m_doc.group(1))
                # Camada 1 historicamente usa "CI-NN" (Integridade);
                # Camadas 2/3 usam "CR-NN".
                prefixo = "CI" if camada == 1 else "CR"
                codigo = f"{prefixo}-{num:02d}"
        if not codigo:
            codigo = "?"

        base_legal = ""
        m = _RE_BASE_LEGAL.search(doc)
        if m:
            base_legal = re.sub(r"\s+", " ", m.group(1).strip())

        sprint = ""
        m = _RE_SPRINT.search(doc)
        if m:
            sprint = f"Sprint {m.group(1)}"

        return RegraInfo(
            codigo=codigo,
            camada=camada,
            descricao=descricao or "(sem descrição)",
            base_legal=base_legal or "(base legal não encontrada na docstring)",
            dependencias_sped=list(deps),
            sprint=sprint,
            severidade=severidade or "—",
            modulo_path=modulo.__name__,
        )
