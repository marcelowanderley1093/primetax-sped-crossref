"""
EmptyState — placeholder para zero-data (Bloco 5 §C13).

Aparece quando uma view não tem nada a exibir: tabela sem registros,
filtro com zero resultados, lista vazia. Texto técnico, não infantilizado
(constraint 2 do CLAUDE.md — auditor é sênior, não consumer).

Composição:
  - Ícone Lucide (placeholder Unicode até substituirmos por SVG)
  - Título — uma linha curta
  - Descrição — opcional, max 400px
  - Botão primário (opcional)
  - Botão secundário (opcional)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


_COR_TITULO = "#53565A"
_COR_DESCR = "#787A80"
_COR_ICON = "#787A80"
_COR_PRIMARY = "#008C95"


class EmptyState(QWidget):
    primary_action = Signal()
    secondary_action = Signal()

    def __init__(
        self,
        title: str,
        description: str = "",
        icon: str = "📭",
        primary_action_label: str | None = None,
        secondary_action_label: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._has_primary = primary_action_label is not None

        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(12)
        v.setContentsMargins(48, 48, 48, 48)

        # Ícone
        self._icon_label = QLabel(icon)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet(
            f"font-size: 36pt; color: {_COR_ICON}; background: transparent;"
        )
        v.addWidget(self._icon_label)

        # Título
        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet(
            f"font-size: 14pt; font-weight: 600; color: {_COR_TITULO}; "
            "background: transparent;"
        )
        v.addWidget(self._title_label)

        # Descrição
        if description:
            self._description_label = QLabel(description)
            self._description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._description_label.setWordWrap(True)
            self._description_label.setMaximumWidth(420)
            self._description_label.setStyleSheet(
                f"font-size: 11pt; color: {_COR_DESCR}; background: transparent;"
            )
            v.addWidget(self._description_label, 0, Qt.AlignmentFlag.AlignCenter)
        else:
            self._description_label = None

        # Botões
        if primary_action_label or secondary_action_label:
            buttons = QHBoxLayout()
            buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)
            buttons.setSpacing(10)

            if primary_action_label:
                btn_primary = QPushButton(primary_action_label)
                btn_primary.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_primary.setStyleSheet(self._qss_primary())
                btn_primary.clicked.connect(self.primary_action)
                buttons.addWidget(btn_primary)
                self._btn_primary = btn_primary
            else:
                self._btn_primary = None

            if secondary_action_label:
                btn_secondary = QPushButton(secondary_action_label)
                btn_secondary.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_secondary.setStyleSheet(self._qss_secondary())
                btn_secondary.clicked.connect(self.secondary_action)
                buttons.addWidget(btn_secondary)
                self._btn_secondary = btn_secondary
            else:
                self._btn_secondary = None

            wrap = QWidget()
            wrap.setLayout(buttons)
            v.addWidget(wrap)
        else:
            self._btn_primary = None
            self._btn_secondary = None

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def set_title(self, title: str) -> None:
        self._title_label.setText(title)

    def set_description(self, description: str) -> None:
        if self._description_label is not None:
            self._description_label.setText(description)

    @staticmethod
    def _qss_primary() -> str:
        return f"""
        QPushButton {{
            background: {_COR_PRIMARY};
            color: #FFFFFF;
            border: none;
            border-radius: 2px;
            padding: 6px 16px;
            font-size: 10pt;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background: #00A4AE;
        }}
        QPushButton:pressed {{
            background: #006F76;
        }}
        """

    @staticmethod
    def _qss_secondary() -> str:
        return f"""
        QPushButton {{
            background: #FFFFFF;
            color: {_COR_PRIMARY};
            border: 1px solid {_COR_PRIMARY};
            border-radius: 2px;
            padding: 6px 16px;
            font-size: 10pt;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background: #E6F3F4;
        }}
        QPushButton:pressed {{
            background: #B3D7DA;
        }}
        """
