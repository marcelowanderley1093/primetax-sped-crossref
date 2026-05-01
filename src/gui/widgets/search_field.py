"""
SearchField — campo de busca incremental com debounce e contador.

Componente de Nível 1 do design system (Bloco 5 §C8). Usado como filtro
em `DataTable` e como campo primário em `CommandPalette` (Ctrl+K).

Comportamento:
- Debounce 150ms — só emite `query_changed` após o usuário pausar.
- Queries < 2 chars não disparam filtro (evita trash).
- Botão `✕` à direita quando há texto; `Esc` limpa e desfoca.
- Badge "12 de 127" à direita quando filtro ativo; atualizado pelo
  consumidor via `set_match_count()`.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget


_MIN_QUERY_LEN = 2
_DEBOUNCE_MS_DEFAULT = 150


class SearchField(QWidget):
    """Campo de busca com debounce + limpar + contador opcional."""

    query_changed = Signal(str)
    cleared = Signal()

    def __init__(
        self,
        placeholder: str = "Filtrar...",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._debounce_ms = _DEBOUNCE_MS_DEFAULT
        self._last_emitted = ""

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText(placeholder)
        self._edit.setClearButtonEnabled(True)
        self._edit.setStyleSheet(
            """
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #D1D3D6;
                border-radius: 2px;
                background: #FFFFFF;
                color: #53565A;
                font-size: 10pt;
                selection-background-color: #008C95;
            }
            QLineEdit:focus {
                border: 1px solid #008C95;
            }
            """
        )
        self._edit.setFixedHeight(32)
        h.addWidget(self._edit, 1)

        self._count_label = QLabel("", self)
        self._count_label.setStyleSheet(
            "color: #787A80; font-size: 9pt; padding-right: 4px;"
        )
        self._count_label.setVisible(False)
        h.addWidget(self._count_label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_query)

        self._edit.textChanged.connect(self._on_text_changed)

        # Esc limpa e desfoca
        esc = QAction(self._edit)
        esc.setShortcut(Qt.Key.Key_Escape)
        esc.triggered.connect(self._on_escape)
        self._edit.addAction(esc)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def set_debounce_ms(self, ms: int) -> None:
        self._debounce_ms = max(0, int(ms))

    def set_match_count(self, visible: int, total: int) -> None:
        """Mostra `visible de total` no badge à direita."""
        if not self._edit.text().strip():
            self._count_label.setVisible(False)
            return
        self._count_label.setText(f"{visible} de {total}")
        self._count_label.setVisible(True)

    def text(self) -> str:
        return self._edit.text()

    def set_text(self, text: str) -> None:
        self._edit.setText(text)

    def setFocus(self) -> None:  # noqa: N802 (Qt API)
        self._edit.setFocus()

    def clear(self) -> None:
        self._edit.clear()
        self._count_label.setVisible(False)

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _on_text_changed(self, _new: str) -> None:
        self._timer.start(self._debounce_ms)

    def _emit_query(self) -> None:
        q = self._edit.text().strip()
        if 0 < len(q) < _MIN_QUERY_LEN:
            # Texto muito curto — não filtra, mas tampouco emite cleared.
            return
        if q == self._last_emitted:
            return
        self._last_emitted = q
        if q:
            self.query_changed.emit(q)
        else:
            self._count_label.setVisible(False)
            self.cleared.emit()

    def _on_escape(self) -> None:
        if self._edit.text():
            self.clear()
        self._edit.clearFocus()
