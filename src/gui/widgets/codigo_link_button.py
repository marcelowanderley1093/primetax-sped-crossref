"""
CodigoLinkButton — link clicável para uma linha específica de um SPED.

Componente primitivo de Nível 0 (Bloco 5 §C10). É a peça física que
implementa o princípio 1 do CLAUDE.md — rastreabilidade em 3 cliques:
toda evidência em T4 expõe um destes links para abrir T5 na linha exata.

Renderização: QLabel com rich text (hyperlink teal, underline). Estado
"visitado" persiste por sessão em QSettings (cap 1000 entradas, rolling).
Emite signal `open_sped` com payload completo.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QWidget


_PRIMARY = "#008C95"
_PRIMARY_HOVER = "#00A4AE"
_VISITED = "#787A80"

_QSETTINGS_KEY = "visited_sped_links"
_MAX_VISITED = 1000


class CodigoLinkButton(QLabel):
    """Link para `(arquivo, linha, bloco, registro)`.

    API:
      - signal `open_sped(dict)` — emitido em click/Enter; payload tem
        arquivo, linha, bloco, registro.
      - `mark_visited(True)` — marca como visitado (cor drift para cinza).
      - cache de visitados em QSettings; consulta automática na construção.
    """

    open_sped = Signal(dict)

    def __init__(
        self,
        arquivo: str,
        linha: int,
        bloco: str,
        registro: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._arquivo = arquivo
        self._linha = linha
        self._bloco = bloco
        self._registro = registro
        self._visited = self._is_visited_cached()
        self._hovering = False

        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._renderizar()
        self._atualizar_tooltip()

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def payload(self) -> dict:
        return {
            "arquivo": self._arquivo,
            "linha": self._linha,
            "bloco": self._bloco,
            "registro": self._registro,
        }

    def mark_visited(self, visited: bool = True) -> None:
        self._visited = visited
        if visited:
            self._persistir_visitado()
        self._renderizar()

    def is_visited(self) -> bool:
        return self._visited

    # ------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------

    def mousePressEvent(self, ev: QMouseEvent) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self._acionar()
        super().mousePressEvent(ev)

    def keyPressEvent(self, ev) -> None:  # noqa: N802
        if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._acionar()
            ev.accept()
            return
        super().keyPressEvent(ev)

    def enterEvent(self, ev) -> None:  # noqa: N802
        self._hovering = True
        self._renderizar()
        super().enterEvent(ev)

    def leaveEvent(self, ev) -> None:  # noqa: N802
        self._hovering = False
        self._renderizar()
        super().leaveEvent(ev)

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _acionar(self) -> None:
        self.mark_visited(True)
        self.open_sped.emit(self.payload())

    def _renderizar(self) -> None:
        if self._visited:
            cor = _VISITED
        elif self._hovering:
            cor = _PRIMARY_HOVER
        else:
            cor = _PRIMARY
        texto = f'<a style="color:{cor}; text-decoration:underline;">L{self._linha}</a>'
        self.setText(texto)

    def _atualizar_tooltip(self) -> None:
        nome = Path(self._arquivo).name if self._arquivo else "—"
        self.setToolTip(
            f"{nome}\nBloco {self._bloco} · Registro {self._registro} · Linha {self._linha}"
        )

    def _chave(self) -> str:
        return f"{self._arquivo}:{self._linha}"

    def _is_visited_cached(self) -> bool:
        settings = QSettings("Primetax Solutions", "SpedCrossref")
        visited = settings.value(_QSETTINGS_KEY, [], type=list) or []
        return self._chave() in visited

    def _persistir_visitado(self) -> None:
        settings = QSettings("Primetax Solutions", "SpedCrossref")
        visited = settings.value(_QSETTINGS_KEY, [], type=list) or []
        chave = self._chave()
        if chave in visited:
            return
        visited.append(chave)
        # Rolling cap — mantém apenas últimas N entradas.
        if len(visited) > _MAX_VISITED:
            visited = visited[-_MAX_VISITED:]
        settings.setValue(_QSETTINGS_KEY, visited)
