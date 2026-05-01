"""
MoneyCellDelegate + Money helper — formatação monetária BRL.

Componente C2 do Bloco 5. Renderiza valores Decimal/float como
"R$ 1.234.567,89" com font-feature `tnum` ativa (largura tabular),
alinhamento à direita, suporte a estilos para zero e negativos.

Money.format() é a função pura — usável em labels avulsos sem delegate.
MoneyCellDelegate é a versão para QTableView, garantindo alinhamento
e cor consistentes em colunas de valor.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)


_COR_NORMAL = QColor(0x53, 0x56, 0x5A)
_COR_FADED = QColor(0xA0, 0xA2, 0xA6)
_COR_ERROR = QColor(0xB2, 0x3A, 0x3A)


@dataclass
class MoneyOptions:
    currency: str = "R$"
    show_zero: bool = True
    zero_style: Literal["faded", "dash", "blank"] = "faded"
    negative_style: Literal["minus", "parens", "red"] = "parens"
    decimal_places: int = 2
    thousands_sep: str = "."
    decimal_sep: str = ","


class Money:
    """Formatação pura — sem dependência de Qt."""

    @staticmethod
    def format(value, options: MoneyOptions | None = None) -> str:
        opts = options or MoneyOptions()

        try:
            d = Decimal(str(value)) if value is not None else Decimal("0")
        except (InvalidOperation, ValueError, TypeError):
            return "—"

        if d == 0 and not opts.show_zero:
            if opts.zero_style == "dash":
                return "—"
            if opts.zero_style == "blank":
                return ""
            # faded → ainda mostra mas em cinza claro (gerido pelo delegate)

        negativo = d < 0
        abs_str = f"{abs(d):,.{opts.decimal_places}f}"
        # Locale BR: , decimal e . milhar — padrão Python é o inverso.
        abs_str = abs_str.replace(",", "TMP").replace(".", opts.decimal_sep).replace(
            "TMP", opts.thousands_sep
        )
        formatado = f"{opts.currency} {abs_str}"

        if negativo:
            if opts.negative_style == "parens":
                formatado = f"({formatado})"
            elif opts.negative_style == "minus":
                formatado = f"-{formatado}"
            # red é tratado pela cor no delegate

        return formatado

    @staticmethod
    def format_accessible(value) -> str:
        """Formata para screen reader (sem cifrão visual)."""
        try:
            d = Decimal(str(value)) if value is not None else Decimal("0")
        except (InvalidOperation, ValueError, TypeError):
            return "valor inválido"
        sinal = "menos " if d < 0 else ""
        return f"{sinal}{abs(d):.2f} reais".replace(".", " vírgula ")


class MoneyCellDelegate(QStyledItemDelegate):
    """Delegate que renderiza coluna de valor monetário em QTableView.

    Lê o valor cru de `Qt.UserRole` (Decimal preservado) e o texto
    formatado de `Qt.DisplayRole`. Aplica alinhamento direito + tnum.
    Cor é decidida em runtime: faded para zero, red para negativo
    (se options.negative_style == 'red').
    """

    def __init__(self, options: MoneyOptions | None = None, parent=None):
        super().__init__(parent)
        self._options = options or MoneyOptions()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        raw = index.data(Qt.ItemDataRole.UserRole)

        # Pinta apenas o fundo (seleção, hover, alternate-row) — sem o texto
        # do DisplayRole. Usa CE_ItemViewItem com opt zerado em texto e ícone.
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        opt.icon = QIcon()
        opt.features &= ~QStyleOptionViewItem.ViewItemFeature.HasDecoration
        widget = option.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)

        painter.save()

        # Cor conforme valor cru
        try:
            d = Decimal(str(raw)) if raw is not None else Decimal(str(text or "0"))
        except (InvalidOperation, ValueError, TypeError):
            d = Decimal("0")

        if d == 0 and self._options.zero_style == "faded":
            painter.setPen(_COR_FADED)
        elif d < 0 and self._options.negative_style == "red":
            painter.setPen(_COR_ERROR)
        else:
            painter.setPen(_COR_NORMAL)

        # Font tabular: ativa OpenType `tnum` quando a API estiver disponível.
        # Em PySide6 6.7+ existe QFont.setFeature(QFont.Tag, int); em versões
        # anteriores (ou onde a Tag não existe), simplesmente usa a fonte
        # padrão — as fontes Inter/System já têm dígitos de largura razoável.
        f = QFont(option.font)
        try:
            tag_cls = getattr(QFont, "Tag", None)
            if tag_cls is not None and hasattr(tag_cls, "fromString"):
                f.setFeature(tag_cls.fromString("tnum"), 1)
        except (AttributeError, ValueError, TypeError):
            pass
        painter.setFont(f)

        rect = option.rect.adjusted(8, 0, -8, 0)
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            text,
        )
        painter.restore()
