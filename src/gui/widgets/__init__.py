"""Componentes reutilizáveis da GUI Primetax (Nível 0+).

Ver planejamento Bloco 5 — 19 componentes em 5 níveis de dependência.
Este pacote começa pelo Nível 0 (primitivos sem dependências entre si).
"""

from src.gui.widgets.codigo_link_button import CodigoLinkButton
from src.gui.widgets.status_badge import BadgeStatus, StatusBadge
from src.gui.widgets.version_label import SpedType, VersionLabel

__all__ = [
    "BadgeStatus",
    "CodigoLinkButton",
    "SpedType",
    "StatusBadge",
    "VersionLabel",
]
