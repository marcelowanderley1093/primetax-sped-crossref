"""Componentes reutilizáveis da GUI Primetax (Nível 0+).

Ver planejamento Bloco 5 — 19 componentes em 5 níveis de dependência.
Este pacote começa pelo Nível 0 (primitivos sem dependências entre si).
"""

from src.gui.widgets.codigo_link_button import CodigoLinkButton
from src.gui.widgets.data_table import ColumnSpec, DataTable
from src.gui.widgets.empty_state import EmptyState
from src.gui.widgets.filter_chip import FilterChip
from src.gui.widgets.inline_message import InlineMessage, MessageLevel
from src.gui.widgets.money_cell import Money, MoneyCellDelegate, MoneyOptions
from src.gui.widgets.search_field import SearchField
from src.gui.widgets.stat_card import StatCard
from src.gui.widgets.status_badge import BadgeStatus, StatusBadge
from src.gui.widgets.toast import Toast, ToastAction, ToastLevel
from src.gui.widgets.traceability_breadcrumb import (
    BreadcrumbSegment,
    TraceabilityBreadcrumb,
)
from src.gui.widgets.version_label import SpedType, VersionLabel

__all__ = [
    "BadgeStatus",
    "BreadcrumbSegment",
    "CodigoLinkButton",
    "ColumnSpec",
    "DataTable",
    "EmptyState",
    "FilterChip",
    "InlineMessage",
    "MessageLevel",
    "Money",
    "MoneyCellDelegate",
    "MoneyOptions",
    "SearchField",
    "SpedType",
    "StatCard",
    "StatusBadge",
    "Toast",
    "ToastAction",
    "ToastLevel",
    "TraceabilityBreadcrumb",
    "VersionLabel",
]
