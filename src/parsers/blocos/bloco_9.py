"""Parser do Bloco 9: 9900 (totais por registro) e 9999 (encerramento)."""

from src.models.registros import Reg9900, Reg9999


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_9900(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg9900:
    """
    Layout: |9900|REG_BLC|QTD_REG_BLC|
    [2]=REG_BLC  [3]=QTD_REG_BLC
    """
    qtd_raw = _g(campos, 3)
    return Reg9900(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        reg_blc=_g(campos, 2),
        qtd_reg_blc=int(qtd_raw) if qtd_raw.isdigit() else 0,
    )


def parsear_9999(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg9999:
    """
    Layout: |9999|QTD_LIN|
    [2]=QTD_LIN (total de linhas do arquivo, incluindo esta)
    """
    qtd_raw = _g(campos, 2)
    return Reg9999(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        qtd_lin=int(qtd_raw) if qtd_raw.isdigit() else 0,
    )
