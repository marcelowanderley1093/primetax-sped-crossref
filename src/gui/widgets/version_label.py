"""
VersionLabel — pill compacto com versão de leiaute SPED.

Componente primitivo de Nível 0 (Bloco 5 §C6). Usado em T4 ao lado de
cada evidência e em T5 no cabeçalho da linha, para que o auditor veja
imediatamente a qual leiaute a lógica foi aplicada (CLAUDE.md §5).

Renderização simples: QLabel com fonte mono pequena e cor text.secondary.
Tooltip informa vigência do leiaute; quando versão diverge da mais recente
conhecida, ganha ícone de alerta (ainda sem SVG — por ora só cor).
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QWidget


class SpedType(Enum):
    EFD_CONTRIB = "efd_contrib"
    EFD_ICMS = "efd_icms"
    ECD = "ecd"
    ECF = "ecf"


_ROTULOS: dict[SpedType, str] = {
    SpedType.EFD_CONTRIB: "EFD-Contrib",
    SpedType.EFD_ICMS: "EFD-ICMS/IPI",
    SpedType.ECD: "ECD",
    SpedType.ECF: "ECF",
}

# Versões mais recentes conhecidas pelo projeto (CLAUDE.md §5).
# Versão diferente desta → destacar como "desatualizada".
_VERSAO_CORRENTE: dict[SpedType, str] = {
    SpedType.EFD_CONTRIB: "3.1.0",
    SpedType.EFD_ICMS: "3.2.2",
    SpedType.ECD: "9.00",
    SpedType.ECF: "0012",
}

# Vigência legal para tooltip (base em CLAUDE.md §5).
_VIGENCIA: dict[SpedType, str] = {
    SpedType.EFD_CONTRIB: "Desde jan/2019 (Leiaute 3.x). Manual IN RFB 1.252/2012.",
    SpedType.EFD_ICMS: "Desde jan/2023 (Leiaute 017). Ato COTEPE/ICMS 44/2018.",
    SpedType.ECD: "Desde AC 2020 (Leiaute 9). ADE Cofis 01/2026.",
    SpedType.ECF: "Desde AC 2025 (Leiaute 12). ADE Cofis 02/2026.",
}

_COR_NORMAL = "#787A80"   # text.secondary
_COR_DESATUAL = "#C28B2F"  # warning


class VersionLabel(QLabel):
    """Pill compacto de versão de leiaute SPED."""

    def __init__(
        self,
        sped_type: SpedType,
        version: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._sped_type = sped_type
        self._version = version

        font = QFont("JetBrains Mono, Consolas, Courier New")
        font.setPointSize(9)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._renderizar()

    def set_version(self, version: str) -> None:
        self._version = version
        self._renderizar()

    def sped_type(self) -> SpedType:
        return self._sped_type

    def version(self) -> str:
        return self._version

    def is_desatualizada(self) -> bool:
        return self._version != _VERSAO_CORRENTE[self._sped_type]

    def _renderizar(self) -> None:
        rotulo = f"{_ROTULOS[self._sped_type]} v{self._version}"
        self.setText(rotulo)

        cor = _COR_DESATUAL if self.is_desatualizada() else _COR_NORMAL
        self.setStyleSheet(
            f"color: {cor}; padding: 0px 4px; background: transparent;"
        )

        tip = _VIGENCIA[self._sped_type]
        if self.is_desatualizada():
            tip += (
                f"\n\nVersão reconhecida pelo sistema: {_VERSAO_CORRENTE[self._sped_type]}."
                f"\nVersão lida no arquivo: {self._version}."
                f"\nRegras podem divergir do leiaute atual — verificar manualmente."
            )
        self.setToolTip(tip)
