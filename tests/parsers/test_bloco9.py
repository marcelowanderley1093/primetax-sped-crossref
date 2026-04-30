"""Testes unitários de validar_bloco9() em src/parsers/common/bloco9.py.

Cobre paridade com efd_contribuicoes.py:418-434 (lógica original) +
casos limite (9999 ausente, divergência composta, vazio total).
"""

from __future__ import annotations

from src.models.registros import Reg9900, Reg9999
from src.parsers.common.bloco9 import validar_bloco9


def _r9900(reg_blc: str, qtd: int) -> Reg9900:
    return Reg9900(
        linha_arquivo=0, arquivo_origem="x", reg="9900",
        reg_blc=reg_blc, qtd_reg_blc=qtd,
    )


def _r9999(qtd: int) -> Reg9999:
    return Reg9999(linha_arquivo=0, arquivo_origem="x", reg="9999", qtd_lin=qtd)


class TestValidarBloco9:
    def test_caso_integro_sem_divergencia(self) -> None:
        """Declarações batem com contagens reais — divergencias vazia."""
        contagens_reais = {"0000": 1, "0110": 1, "M200": 1, "9900": 5, "9999": 1}
        regs_9900 = [
            _r9900("0000", 1),
            _r9900("0110", 1),
            _r9900("M200", 1),
            _r9900("9900", 5),
            _r9900("9999", 1),
        ]
        reg9999 = _r9999(11)  # 5 dados + 5 9900 + 1 9999 = 11
        contagens_declaradas, divergencias = validar_bloco9(
            contagens_reais, regs_9900, reg9999, total_linhas=11,
        )
        assert divergencias == []
        assert contagens_declaradas == {
            "0000": 1, "0110": 1, "M200": 1, "9900": 5, "9999": 1,
        }

    def test_divergencia_9900_declarado_diferente_de_real(self) -> None:
        """9900 declara M600=99 mas real é 1 — divergência detectada."""
        contagens_reais = {"0000": 1, "M600": 1}
        regs_9900 = [_r9900("0000", 1), _r9900("M600", 99)]
        reg9999 = None
        _, divergencias = validar_bloco9(
            contagens_reais, regs_9900, reg9999, total_linhas=10,
        )
        assert len(divergencias) == 1
        assert "M600" in divergencias[0]
        assert "declarado=99" in divergencias[0]
        assert "real=1" in divergencias[0]

    def test_divergencia_9999_qtd_lin_diferente_de_total(self) -> None:
        """9999.QTD_LIN declara 50 mas arquivo tem 11 linhas — divergência."""
        contagens_reais = {"0000": 1}
        regs_9900 = [_r9900("0000", 1)]
        reg9999 = _r9999(50)
        _, divergencias = validar_bloco9(
            contagens_reais, regs_9900, reg9999, total_linhas=11,
        )
        assert len(divergencias) == 1
        assert "9999.QTD_LIN=50" in divergencias[0]
        assert "linhas lidas=11" in divergencias[0]
        # Caractere especial preservado — paridade byte-a-byte
        assert "≠" in divergencias[0]

    def test_sem_9999_apenas_9900(self) -> None:
        """reg9999=None — só valida 9900, não emite divergência de 9999."""
        contagens_reais = {"0000": 1, "C100": 5}
        regs_9900 = [_r9900("0000", 1), _r9900("C100", 5)]
        reg9999 = None
        _, divergencias = validar_bloco9(
            contagens_reais, regs_9900, reg9999, total_linhas=10,
        )
        assert divergencias == []

    def test_caso_composto_multiplas_divergencias(self) -> None:
        """9900 declara M200=10 mas real=2 + 9999.QTD_LIN errado: 2 divergências."""
        contagens_reais = {"0000": 1, "M200": 2}
        regs_9900 = [_r9900("0000", 1), _r9900("M200", 10)]
        reg9999 = _r9999(99)
        _, divergencias = validar_bloco9(
            contagens_reais, regs_9900, reg9999, total_linhas=20,
        )
        assert len(divergencias) == 2
        # Uma de M200, uma de 9999
        assert any("M200" in d for d in divergencias)
        assert any("9999.QTD_LIN" in d for d in divergencias)
