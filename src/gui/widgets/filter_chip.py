"""
FilterChip — chip toggleável para filtros multi-valor (Bloco 5 §C12).

Usado em T3 para filtrar matriz de cruzamentos por severidade
(`[✓ Alto] [✓ Médio] [□ Baixo]`). Múltipla seleção combina (AND).

Estados:
  - Inativo: border default, bg surface.primary, text text.primary.
  - Ativo: border primary, bg primary.subtle, text primary.active,
           ícone check à esquerda.
  - Badge count opcional à direita (ex: "Alto (34)").
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton, QWidget


_COR_PRIMARY = "#008C95"
_COR_PRIMARY_ACTIVE = "#006F76"
_COR_PRIMARY_SUBTLE = "#E6F3F4"
_COR_BORDER = "#D1D3D6"
_COR_TEXT = "#53565A"
_COR_TEXT_SEC = "#787A80"


class FilterChip(QPushButton):
    """Chip checkable. Emite `toggled_with_id(chip_id, novo_estado)`."""

    toggled_with_id = Signal(str, bool)

    def __init__(
        self,
        label: str,
        chip_id: str,
        icon: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._chip_id = chip_id
        self._label = label
        self._icon = icon  # ex: "🚨" ou similar; SVG Lucide depois
        self._count: int | None = None

        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setFixedHeight(28)

        self._render()
        self._apply_qss()
        self.toggled.connect(self._on_toggled)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def chip_id(self) -> str:
        return self._chip_id

    def set_count(self, count: int | None) -> None:
        self._count = count
        self._render()

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _on_toggled(self, checked: bool) -> None:
        self._render()
        self._apply_qss()
        self.toggled_with_id.emit(self._chip_id, checked)

    def _render(self) -> None:
        prefix = ""
        if self.isChecked():
            prefix = "✓ "
        elif self._icon:
            prefix = f"{self._icon} "

        suffix = f" ({self._count})" if self._count is not None else ""
        self.setText(f"{prefix}{self._label}{suffix}")

    def _apply_qss(self) -> None:
        if self.isChecked():
            self.setStyleSheet(self._qss_ativo())
        else:
            self.setStyleSheet(self._qss_inativo())

    @staticmethod
    def _qss_inativo() -> str:
        return f"""
        QPushButton {{
            color: {_COR_TEXT};
            background: #FFFFFF;
            border: 1px solid {_COR_BORDER};
            border-radius: 2px;
            padding: 4px 10px;
            font-size: 9pt;
            font-weight: 500;
        }}
        QPushButton:hover {{
            border-color: {_COR_PRIMARY};
            color: {_COR_PRIMARY};
        }}
        """

    @staticmethod
    def _qss_ativo() -> str:
        return f"""
        QPushButton {{
            color: {_COR_PRIMARY_ACTIVE};
            background: {_COR_PRIMARY_SUBTLE};
            border: 1px solid {_COR_PRIMARY};
            border-radius: 2px;
            padding: 4px 10px;
            font-size: 9pt;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: #D1EAEC;
        }}
        """
