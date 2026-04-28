"""
Ícones desenhados via QPainter — substitui glifos unicode no SideRailItem.

Por que QPainter em vez de SVG/QSvgWidget: não exige asset externo nem
configuração extra do PyInstaller. Cada ícone é uma função pura que
recebe (painter, rect, color) e desenha primitivas (linhas, polígonos,
arcos). Estilo aproximado dos Lucide/Feather: traço fino (2px), borda
arredondada, currentColor.

Uso:
    from src.gui.widgets.icons import paint_icon, IconName
    paint_icon(painter, rect, IconName.HOME, QColor("#008C95"))

Ícones disponíveis (correspondência com telas):
    HOME           → T1 Clientes
    DOWNLOAD       → T2 Importação
    BAR_CHART      → T3 Diagnóstico
    FLAG           → T4 Oportunidade
    FILE_TEXT      → T5 Visualizador SPED
    GIT_MERGE      → T6 Reconciliação
    PEN            → T7 Parecer
    SHIELD_CHECK   → T8 Auditoria
    SETTINGS       → T9 Configurações
    LIST_CHECK     → T0 Regras (visualizador)
"""

from __future__ import annotations

from enum import Enum
from math import cos, pi, sin

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen


class IconName(Enum):
    HOME = "home"
    DOWNLOAD = "download"
    BAR_CHART = "bar_chart"
    FLAG = "flag"
    FILE_TEXT = "file_text"
    GIT_MERGE = "git_merge"
    PEN = "pen"
    SHIELD_CHECK = "shield_check"
    SETTINGS = "settings"
    LIST_CHECK = "list_check"
    LEDGER = "ledger"


def paint_icon(
    painter: QPainter,
    rect: QRect,
    name: IconName,
    color: QColor,
    stroke_width: float = 2.0,
) -> None:
    """Desenha o ícone `name` centralizado no `rect` com a `color` dada."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(color, stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Sistema de coordenadas: caixa 24×24 centralizada no rect.
    box = 24
    side = min(rect.width(), rect.height())
    scale = side / box
    offset_x = rect.x() + (rect.width() - side) / 2
    offset_y = rect.y() + (rect.height() - side) / 2
    painter.translate(offset_x, offset_y)
    painter.scale(scale, scale)

    drawer = _DRAWERS.get(name)
    if drawer is not None:
        drawer(painter)

    painter.restore()


# ----------------------------------------------------------------
# Cada drawer assume canvas 24×24, viewBox (0,0)-(24,24)
# ----------------------------------------------------------------

def _draw_home(p: QPainter) -> None:
    # Telhado: M3,12 L12,3 L21,12
    path = QPainterPath()
    path.moveTo(3, 12)
    path.lineTo(12, 3)
    path.lineTo(21, 12)
    p.drawPath(path)
    # Casa: retângulo 5,12 → 19,21 (com beirais visíveis)
    p.drawLine(5, 12, 5, 21)
    p.drawLine(19, 12, 19, 21)
    p.drawLine(5, 21, 19, 21)
    # Porta: 10,21 → 10,15 → 14,15 → 14,21
    p.drawLine(10, 21, 10, 15)
    p.drawLine(10, 15, 14, 15)
    p.drawLine(14, 15, 14, 21)


def _draw_download(p: QPainter) -> None:
    # Bandeja inferior
    path = QPainterPath()
    path.moveTo(4, 16)
    path.lineTo(4, 20)
    path.lineTo(20, 20)
    path.lineTo(20, 16)
    p.drawPath(path)
    # Seta para baixo
    p.drawLine(12, 4, 12, 15)
    # Cabeça da seta
    arrow = QPainterPath()
    arrow.moveTo(7, 10)
    arrow.lineTo(12, 16)
    arrow.lineTo(17, 10)
    p.drawPath(arrow)


def _draw_bar_chart(p: QPainter) -> None:
    # Eixo
    p.drawLine(4, 4, 4, 20)
    p.drawLine(4, 20, 20, 20)
    # 3 barras de alturas diferentes
    p.drawLine(8, 14, 8, 20)
    p.drawLine(13, 9, 13, 20)
    p.drawLine(18, 12, 18, 20)
    # Espessura visual: traçar barras paralelas para simular largura
    pen2 = QPen(p.pen())
    pen2.setWidthF(p.pen().widthF())
    p.setPen(pen2)
    p.drawLine(9, 14, 9, 20)
    p.drawLine(14, 9, 14, 20)
    p.drawLine(19, 12, 19, 20)


def _draw_flag(p: QPainter) -> None:
    # Mastro
    p.drawLine(5, 3, 5, 22)
    # Bandeira (triângulo)
    flag = QPainterPath()
    flag.moveTo(5, 4)
    flag.lineTo(20, 8)
    flag.lineTo(5, 12)
    p.drawPath(flag)


def _draw_file_text(p: QPainter) -> None:
    # Folha com canto dobrado
    folha = QPainterPath()
    folha.moveTo(6, 3)
    folha.lineTo(15, 3)
    folha.lineTo(20, 8)
    folha.lineTo(20, 21)
    folha.lineTo(6, 21)
    folha.closeSubpath()
    p.drawPath(folha)
    # Canto dobrado
    dobra = QPainterPath()
    dobra.moveTo(15, 3)
    dobra.lineTo(15, 8)
    dobra.lineTo(20, 8)
    p.drawPath(dobra)
    # Linhas de texto
    p.drawLine(9, 12, 17, 12)
    p.drawLine(9, 15, 17, 15)
    p.drawLine(9, 18, 14, 18)


def _draw_git_merge(p: QPainter) -> None:
    # Lucide-style git-merge: 2 círculos + linha + arco merge
    # Círculo esquerdo (origem)
    p.drawEllipse(QPointF(6, 6), 2, 2)
    # Círculo direito (destino)
    p.drawEllipse(QPointF(18, 18), 2, 2)
    # Linha vertical da origem
    p.drawLine(6, 8, 6, 18)
    # Curva de merge: do círculo esquerdo até o direito
    arc = QPainterPath()
    arc.moveTo(6, 12)
    arc.cubicTo(6, 16, 12, 18, 16, 18)
    p.drawPath(arc)


def _draw_pen(p: QPainter) -> None:
    # Caneta inclinada — corpo
    corpo = QPainterPath()
    corpo.moveTo(15, 4)
    corpo.lineTo(20, 9)
    corpo.lineTo(9, 20)
    corpo.lineTo(4, 20)
    corpo.lineTo(4, 15)
    corpo.closeSubpath()
    p.drawPath(corpo)
    # Linha divisória da ponta
    p.drawLine(13, 6, 18, 11)


def _draw_shield_check(p: QPainter) -> None:
    # Escudo
    escudo = QPainterPath()
    escudo.moveTo(12, 3)
    escudo.lineTo(20, 6)
    escudo.lineTo(20, 12)
    escudo.cubicTo(20, 17, 16, 20, 12, 21)
    escudo.cubicTo(8, 20, 4, 17, 4, 12)
    escudo.lineTo(4, 6)
    escudo.closeSubpath()
    p.drawPath(escudo)
    # Check interno
    check = QPainterPath()
    check.moveTo(8, 12)
    check.lineTo(11, 15)
    check.lineTo(16, 9)
    p.drawPath(check)


def _draw_settings(p: QPainter) -> None:
    # Engrenagem: círculo central + 8 dentes
    cx, cy, r_in, r_out = 12, 12, 3, 5
    # 8 dentes distribuídos
    for i in range(8):
        ang = i * pi / 4
        x1 = cx + r_in * cos(ang)
        y1 = cy + r_in * sin(ang)
        x2 = cx + (r_out + 2) * cos(ang)
        y2 = cy + (r_out + 2) * sin(ang)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    # Círculo do hub
    p.drawEllipse(QPointF(cx, cy), r_in, r_in)
    # Aro externo (parcial entre dentes — fica como 8 arcos curtos)
    # Simplificação: círculo médio
    p.drawEllipse(QPointF(cx, cy), r_out, r_out)


def _draw_list_check(p: QPainter) -> None:
    # Lista com checks à esquerda
    # Linha 1
    check1 = QPainterPath()
    check1.moveTo(4, 7)
    check1.lineTo(6, 9)
    check1.lineTo(9, 5)
    p.drawPath(check1)
    p.drawLine(12, 7, 21, 7)
    # Linha 2
    check2 = QPainterPath()
    check2.moveTo(4, 13)
    check2.lineTo(6, 15)
    check2.lineTo(9, 11)
    p.drawPath(check2)
    p.drawLine(12, 13, 21, 13)
    # Linha 3
    check3 = QPainterPath()
    check3.moveTo(4, 19)
    check3.lineTo(6, 21)
    check3.lineTo(9, 17)
    p.drawPath(check3)
    p.drawLine(12, 19, 21, 19)


def _draw_ledger(p: QPainter) -> None:
    # Livro aberto com espinha central — análise contábil
    # Capa esquerda
    p.drawLine(4, 5, 4, 19)
    p.drawLine(4, 5, 12, 5)
    p.drawLine(4, 19, 12, 19)
    # Espinha
    p.drawLine(12, 4, 12, 20)
    # Capa direita
    p.drawLine(20, 5, 20, 19)
    p.drawLine(12, 5, 20, 5)
    p.drawLine(12, 19, 20, 19)
    # Linhas internas (texto da página)
    p.drawLine(6, 9, 10, 9)
    p.drawLine(6, 12, 10, 12)
    p.drawLine(6, 15, 10, 15)
    p.drawLine(14, 9, 18, 9)
    p.drawLine(14, 12, 18, 12)
    p.drawLine(14, 15, 18, 15)


_DRAWERS = {
    IconName.HOME: _draw_home,
    IconName.DOWNLOAD: _draw_download,
    IconName.BAR_CHART: _draw_bar_chart,
    IconName.FLAG: _draw_flag,
    IconName.FILE_TEXT: _draw_file_text,
    IconName.GIT_MERGE: _draw_git_merge,
    IconName.PEN: _draw_pen,
    IconName.SHIELD_CHECK: _draw_shield_check,
    IconName.SETTINGS: _draw_settings,
    IconName.LIST_CHECK: _draw_list_check,
    IconName.LEDGER: _draw_ledger,
}
