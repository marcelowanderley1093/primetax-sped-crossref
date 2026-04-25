"""
OportunidadeController — carrega achados de uma regra específica + persiste revisão.

Operações são síncronas (consultas diretas ao banco): mostra evidências,
marca/desmarca revisada, salva nota. Não envolve thread separada.

A interface trabalha com `id` do achado (PK do banco). T4 itera os
achados de uma regra; cada linha conhece seu id e qual tabela
('oportunidades' ou 'divergencias').
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from src.db.repo import Repositorio

logger = logging.getLogger(__name__)


@dataclass
class EvidenciaRow:
    """Linha exibida em T4 — uma evidência de um achado."""
    achado_id: int
    tabela: str                # 'crossref_oportunidades' | 'crossref_divergencias'
    indice_evidencia: int      # qual posição na lista evidencia[N] do achado
    arquivo: str
    linha: int
    bloco: str
    registro: str
    campos_chave: dict
    revisada: bool
    nota: str = ""
    impacto_conservador: Decimal = Decimal("0")


@dataclass
class RegraDetalhe:
    """Resumo da regra (CR-XX) selecionada em T3."""
    codigo_regra: str
    descricao_curta: str
    severidade_predominante: str
    total_evidencias: int
    impacto_conservador_total: Decimal
    impacto_maximo_total: Decimal
    revisadas: int
    base_legal: str = ""        # extraído de docstring do módulo (best-effort)


class OportunidadeController(QObject):
    """Controller stateful: vinculado a um Cliente×AC."""

    achado_atualizado = Signal(int, str)   # achado_id, tabela

    def __init__(
        self,
        cnpj: str,
        ano_calendario: int,
        usuario: str = "auditor",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._cnpj = cnpj
        self._ano = ano_calendario
        self._usuario = usuario
        self._repo = Repositorio(cnpj, ano_calendario)

    # ------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------

    def carregar_regra(self, codigo_regra: str) -> tuple[RegraDetalhe, list[EvidenciaRow]]:
        """Retorna (detalhe da regra, lista de evidências expandidas)."""
        if not self._repo.caminho.exists():
            return self._detalhe_vazio(codigo_regra), []

        conn = self._repo.conexao()
        try:
            ops = self._consultar_filtrado(conn, codigo_regra, "crossref_oportunidades")
            divs = self._consultar_filtrado(conn, codigo_regra, "crossref_divergencias")
        finally:
            conn.close()

        # Agrega para o card de detalhe
        evidencias: list[EvidenciaRow] = []
        impacto_cons = Decimal("0")
        impacto_max = Decimal("0")
        revisadas = 0
        severidades: list[str] = []
        descricao_curta = self._descricao_de_metadata(codigo_regra)

        for tabela, achados in (
            ("crossref_oportunidades", ops),
            ("crossref_divergencias", divs),
        ):
            for r in achados:
                severidades.append(r.get("severidade", "baixo"))
                imp_c = Decimal(str(r.get("valor_impacto_conservador") or 0))
                imp_m = Decimal(str(r.get("valor_impacto_maximo") or 0))
                impacto_cons += imp_c
                impacto_max += imp_m
                if r.get("revisado_em"):
                    revisadas += 1
                evidencias.extend(
                    self._expandir_evidencias(r, tabela, imp_c)
                )

        detalhe = RegraDetalhe(
            codigo_regra=codigo_regra,
            descricao_curta=descricao_curta,
            severidade_predominante=self._severidade_dominante(severidades),
            total_evidencias=len(evidencias),
            impacto_conservador_total=impacto_cons,
            impacto_maximo_total=impacto_max,
            revisadas=revisadas,
            base_legal=self._base_legal_de_docstring(codigo_regra),
        )
        return detalhe, evidencias

    # ------------------------------------------------------------
    # Mutações de revisão (decisão #12)
    # ------------------------------------------------------------

    def marcar_revisada(self, achado_id: int, tabela: str) -> None:
        conn = self._repo.conexao()
        try:
            with conn:
                self._repo.marcar_revisada(
                    conn, achado_id, usuario=self._usuario, tabela=tabela,
                )
        finally:
            conn.close()
        self.achado_atualizado.emit(achado_id, tabela)

    def desmarcar_revisada(self, achado_id: int, tabela: str) -> None:
        conn = self._repo.conexao()
        try:
            with conn:
                self._repo.desmarcar_revisada(conn, achado_id, tabela=tabela)
        finally:
            conn.close()
        self.achado_atualizado.emit(achado_id, tabela)

    def salvar_nota(self, achado_id: int, tabela: str, nota: str) -> None:
        conn = self._repo.conexao()
        try:
            with conn:
                self._repo.atualizar_nota(conn, achado_id, nota, tabela=tabela)
        finally:
            conn.close()
        self.achado_atualizado.emit(achado_id, tabela)

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _consultar_filtrado(
        self, conn, codigo_regra: str, tabela: str
    ) -> list[dict]:
        cur = conn.execute(
            f"SELECT * FROM {tabela}"
            " WHERE cnpj_declarante=? AND ano_calendario=? AND codigo_regra=?"
            " ORDER BY valor_impacto_conservador DESC, id DESC"
            if "oportunidades" in tabela else
            f"SELECT * FROM {tabela}"
            " WHERE cnpj_declarante=? AND ano_calendario=? AND codigo_regra=?"
            " ORDER BY id DESC",
            (self._cnpj, self._ano, codigo_regra),
        )
        return [dict(r) for r in cur]

    def _expandir_evidencias(
        self, achado: dict, tabela: str, impacto: Decimal,
    ) -> list[EvidenciaRow]:
        """Cada `evidencia_json` é uma lista; expande em N linhas."""
        try:
            evs = json.loads(achado.get("evidencia_json") or "[]")
        except Exception:
            evs = []
        if not isinstance(evs, list):
            evs = [evs]

        achado_id = int(achado["id"])
        revisada = achado.get("revisado_em") is not None
        nota = achado.get("nota") or ""
        # Cada achado tem 1 ou mais evidências; impacto fica no nível do achado
        # (replicamos em cada linha para ordenação amigável)
        rows = []
        for i, ev in enumerate(evs):
            if not isinstance(ev, dict):
                ev = {}
            arquivo = (
                ev.get("arquivo") or ev.get("arquivo_origem") or ""
            )
            linha = ev.get("linha") or ev.get("linha_arquivo") or 0
            try:
                linha = int(linha)
            except (TypeError, ValueError):
                linha = 0
            campos = ev.get("campos_chave") or {}
            if not isinstance(campos, dict):
                campos = {}
            rows.append(EvidenciaRow(
                achado_id=achado_id,
                tabela=tabela,
                indice_evidencia=i,
                arquivo=str(arquivo),
                linha=linha,
                bloco=str(ev.get("bloco", "")),
                registro=str(ev.get("registro", "")),
                campos_chave=campos,
                revisada=revisada,
                nota=nota,
                impacto_conservador=impacto,
            ))
        return rows

    @staticmethod
    def _severidade_dominante(severidades: list[str]) -> str:
        prioridade = {"alto": 0, "medio": 1, "baixo": 2}
        if not severidades:
            return "ok"
        return min(severidades, key=lambda s: prioridade.get(s, 3))

    @staticmethod
    def _descricao_de_metadata(codigo_regra: str) -> str:
        from src.reports.excel_diagnostico import _METADATA_REGRAS
        for codigo, _deps, descricao in _METADATA_REGRAS:
            if codigo == codigo_regra:
                return descricao
        return ""

    @staticmethod
    def _base_legal_de_docstring(codigo_regra: str) -> str:
        """Extrai trecho de base legal do docstring do módulo da regra.

        Best-effort: importa o módulo correspondente e lê __doc__. Se não
        encontrar, retorna string vazia. Não falha — usado só para exibir.
        """
        try:
            from src.crossref import engine
            for grupo in (
                engine._CRUZAMENTOS_CAMADA1,
                engine._CRUZAMENTOS_CAMADA2,
                engine._CRUZAMENTOS_CAMADA3,
            ):
                for modulo in grupo:
                    cod = getattr(modulo, "CODIGO_REGRA", None)
                    if cod == codigo_regra:
                        return (modulo.__doc__ or "").strip()
        except Exception:
            return ""
        return ""

    @staticmethod
    def _detalhe_vazio(codigo_regra: str) -> RegraDetalhe:
        return RegraDetalhe(
            codigo_regra=codigo_regra,
            descricao_curta="",
            severidade_predominante="ok",
            total_evidencias=0,
            impacto_conservador_total=Decimal("0"),
            impacto_maximo_total=Decimal("0"),
            revisadas=0,
        )
