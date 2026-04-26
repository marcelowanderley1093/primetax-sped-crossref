"""
T1 — Tela de Clientes & Competências (Bloco 3 §3.1).

Lista clientes existentes em data/db/{cnpj}/{ano}.sqlite, com filtro,
ordenação e contadores. Sinal `cliente_aberto` é emitido em duplo-clique
ou Enter — consumidor (AppShell) decide o que fazer (abrir T3, etc.).

Esta primeira iteração é READ-ONLY: lista clientes existentes. Criação
manual e exclusão (com confirmação) ficam para iteração seguinte.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from src.gui.controllers.clientes_controller import ClienteRow, ClientesController
from src.gui.widgets import (
    ColumnSpec,
    DataTable,
    EmptyState,
)

logger = logging.getLogger(__name__)


class T1Clientes(QWidget):
    """Tela inicial — listagem de clientes existentes."""

    cliente_aberto = Signal(ClienteRow)
    importacao_solicitada = Signal()  # botão "Importar SPED..." clicado

    def __init__(
        self,
        controller: ClientesController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller or ClientesController()
        self._rows: list[ClienteRow] = []

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        titulo = QLabel("Clientes & Competências")
        titulo.setStyleSheet(
            "color: #008C95; font-size: 18pt; font-weight: 600; "
            "background: transparent;"
        )
        header_row.addWidget(titulo)
        header_row.addStretch()

        self._btn_atualizar = QPushButton("↻ Atualizar")
        self._btn_atualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_atualizar.setStyleSheet(self._qss_btn_secundario())
        self._btn_atualizar.clicked.connect(self.recarregar)
        header_row.addWidget(self._btn_atualizar)

        self._btn_importar = QPushButton("+ Importar SPED")
        self._btn_importar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_importar.setStyleSheet(self._qss_btn_primario())
        self._btn_importar.clicked.connect(self.importacao_solicitada)
        header_row.addWidget(self._btn_importar)

        wrap_header = QWidget()
        wrap_header.setLayout(header_row)
        v.addWidget(wrap_header)

        # Stacked: tabela ou empty state conforme houver dados
        self._stack = QStackedWidget()

        # Tabela
        self._tabela = DataTable(
            columns=self._construir_colunas(),
            rows=[],
            with_search=True,
            with_export=True,
            empty_message="Nenhum cliente corresponde ao filtro.",
        )
        self._tabela.row_activated.connect(self._on_row_activated)
        self._stack.addWidget(self._tabela)

        # Empty state
        self._empty = EmptyState(
            title="Nenhum cliente importado ainda",
            description=(
                "Para começar, importe um arquivo SPED (EFD-Contribuições, "
                "EFD ICMS/IPI, ECD ou ECF). O tipo é detectado automaticamente "
                "pelo registro 0000 e o banco é criado em data/db/."
            ),
            primary_action_label="Importar agora",
            secondary_action_label="Abrir documentação",
        )
        self._empty.primary_action.connect(self.importacao_solicitada)
        self._stack.addWidget(self._empty)

        v.addWidget(self._stack, 1)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def recarregar(self) -> None:
        """Re-varre o filesystem e atualiza a tabela."""
        self._rows = self._controller.listar_clientes()

        if not self._rows:
            self._stack.setCurrentWidget(self._empty)
            return

        self._stack.setCurrentWidget(self._tabela)
        self._tabela.set_rows([
            self._row_to_dict((i, r)) for i, r in enumerate(self._rows)
        ])

    def cliente_selecionado(self) -> ClienteRow | None:
        """Retorna o cliente da linha atualmente selecionada."""
        row_dict = self._tabela.selected_row()
        if row_dict is None:
            return None
        idx = row_dict.get("_idx")
        if idx is None or idx >= len(self._rows):
            return None
        return self._rows[idx]

    def localizar_cliente_por_cnpj(
        self, cnpj: str, ano_calendario: int | None = None,
    ) -> ClienteRow | None:
        """Procura cliente carregado pelo CNPJ (e AC opcional). Útil
        para navegação sugerida (ex: T3 sugere abrir matriz quando
        filial não tem EFD-Contrib).
        """
        for r in self._rows:
            if r.cnpj != cnpj:
                continue
            if ano_calendario is None or r.ano_calendario == ano_calendario:
                return r
        return None

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _on_row_activated(self, row_dict: dict) -> None:
        idx = row_dict.get("_idx")
        if idx is None or idx >= len(self._rows):
            return
        self.cliente_aberto.emit(self._rows[idx])

    def _row_to_dict(self, idx_row: tuple[int, ClienteRow] | ClienteRow) -> dict:
        # `set_rows` chama _row_to_dict para cada item na lista; o índice é
        # mantido em '_idx' para mapear de volta.
        if isinstance(idx_row, tuple):
            idx, r = idx_row
        else:
            r = idx_row
            idx = self._rows.index(r)

        speds_str = " ".join(self._sigla(s) for s in r.speds_importados) or "—"
        ultima = r.ultima_atividade.strftime("%d/%m/%Y %H:%M") if r.ultima_atividade else "—"
        return {
            "_idx": idx,
            "cnpj": r.cnpj_formatado(),
            "razao_social": r.razao_social,
            "ano_calendario": r.ano_calendario,
            "speds": speds_str,
            "impacto": r.impacto_total,
            "ultima_atividade": ultima,
        }

    def _construir_colunas(self) -> list[ColumnSpec]:
        return [
            ColumnSpec(id="cnpj", header="CNPJ", kind="text", width=160),
            ColumnSpec(id="razao_social", header="Razão Social", kind="text", width=280),
            ColumnSpec(id="ano_calendario", header="AC", kind="int", width=70),
            ColumnSpec(id="speds", header="SPEDs", kind="text", width=130),
            ColumnSpec(id="impacto", header="Impacto Conservador", kind="money", width=170),
            ColumnSpec(id="ultima_atividade", header="Última atividade", kind="text", width=160),
        ]

    @staticmethod
    def _sigla(sped: str) -> str:
        mapa = {
            "EFD-Contrib": "E",
            "EFD-ICMS/IPI": "C",
            "ECD": "D",
            "ECF": "F",
        }
        return mapa.get(sped, sped[:1])

    # Sobrescreve set_rows para preservar índice
    def set_rows_with_index(self, rows: list[ClienteRow]) -> None:
        self._rows = rows
        self._tabela.set_rows([
            self._row_to_dict((i, r)) for i, r in enumerate(rows)
        ])

    @staticmethod
    def _qss_btn_primario() -> str:
        return """
        QPushButton {
            background: #008C95; color: #FFFFFF; border: none;
            border-radius: 2px; padding: 6px 14px;
            font-size: 10pt; font-weight: 500;
        }
        QPushButton:hover { background: #00A4AE; }
        QPushButton:pressed { background: #006F76; }
        """

    @staticmethod
    def _qss_btn_secundario() -> str:
        return """
        QPushButton {
            background: #FFFFFF; color: #008C95; border: 1px solid #008C95;
            border-radius: 2px; padding: 6px 14px;
            font-size: 10pt; font-weight: 500;
        }
        QPushButton:hover { background: #E6F3F4; }
        """
