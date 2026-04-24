"""
Regras para retenções de PIS/COFINS na fonte (F600/F700).

Base legal:
  Art. 30 da Lei 10.833/2003 — retenção na fonte sobre pagamentos de PJ a PJ
    por prestação de serviços profissionais, limpeza, vigilância etc.
  Art. 33 da Lei 10.833/2003 — compensação de retenções com débitos próprios
  Art. 34 da Lei 10.833/2003 — ressarcimento de retenções não-compensáveis
  Art. 168, I do CTN (Lei 5.172/1966) — prazo decadencial de 5 anos para
    pedido de restituição/compensação (contado da data do fato gerador)

Vigência: F600/F700 existem a partir de ago/2013 (leiaute EFD-Contribuições 1.2+).
  CLAUDE.md §5.2 — não gerar alertas de retenção para fatos anteriores a ago/2013.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass
class ResultadoRetencao:
    """Resultado da análise de um registro F600 ou F700."""
    saldo_nao_compensado: Decimal
    dt_ret: str
    cnpj_fonte_pag: str
    cod_rec: str
    ind_nat_ret: str
    linha_arquivo: int
    arquivo_origem: str
    prescrito: bool
    data_prescricao: str  # YYYY-MM-DD — data em que prescreve (DT_RET + 5 anos)


_VIGENCIA_F600_F700 = date(2013, 8, 1)  # §5.2 CLAUDE.md


def _parse_date(s: str) -> date | None:
    """'YYYY-MM-DD' → date. Retorna None se inválido."""
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _data_prescricao(dt_ret: date) -> date:
    """Retorna o dia exato em que a retenção prescreve (DT_RET + 5 anos)."""
    return dt_ret.replace(year=dt_ret.year + 5)


def verificar_saldo_retencao(
    ind_nat_ret: str,
    dt_ret_str: str,
    vl_ret_apu: Decimal,
    vl_ret_per: Decimal,
    vl_ret_dcomp: Decimal,
    cod_rec: str,
    ind_nat_rec: str,
    cnpj_fonte_pag: str,
    linha_arquivo: int,
    arquivo_origem: str,
    data_diagnostico: date | None = None,
) -> ResultadoRetencao | None:
    """
    Calcula o saldo não-compensado de uma retenção (F600 ou F700).

    Saldo = VL_RET_APU - VL_RET_PER - VL_RET_DCOMP

    Retorna None quando:
      - saldo <= 0 (retenção já compensada/ressarcida integralmente)
      - DT_RET anterior à vigência do registro (ago/2013)
      - DT_RET inválida

    Retorna ResultadoRetencao quando há saldo positivo (oportunidade CR-16/17).
    O campo `prescrito` indica se a retenção já ultrapassou o prazo quinquenal
    do art. 168 I do CTN (base para CR-19).
    """
    dt_ret = _parse_date(dt_ret_str)
    if dt_ret is None:
        return None
    if dt_ret < _VIGENCIA_F600_F700:
        return None

    saldo = vl_ret_apu - vl_ret_per - vl_ret_dcomp
    if saldo <= Decimal("0"):
        return None

    hoje = data_diagnostico or date.today()
    dt_presc = _data_prescricao(dt_ret)
    prescrito = hoje >= dt_presc

    return ResultadoRetencao(
        saldo_nao_compensado=saldo,
        dt_ret=dt_ret_str,
        cnpj_fonte_pag=cnpj_fonte_pag,
        cod_rec=cod_rec,
        ind_nat_ret=ind_nat_ret,
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        prescrito=prescrito,
        data_prescricao=dt_presc.strftime("%Y-%m-%d"),
    )
