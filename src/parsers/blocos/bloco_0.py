"""Parser do Bloco 0 da EFD-Contribuições: registros 0000, 0110, 0111, 0200."""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import Reg0000, Reg0110, Reg0111, Reg0200

logger = logging.getLogger(__name__)


def _dec(s: str) -> Decimal:
    s = s.strip()
    if not s:
        return Decimal("0")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def _data(s: str) -> str:
    """DDMMAAAA → YYYY-MM-DD. Retorna a string original se não reconhecível."""
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[4:8]}-{s[2:4]}-{s[0:2]}"
    return s


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_0000(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg0000:
    """
    Layout: |0000|COD_VER|TIPO_ESCRITURACAO|IND_SIT_ESP|NUM_REC_ANTERIOR|
             DT_INI|DT_FIN|NOME|CNPJ|CPF|UF|IE|COD_MUN|IM|SUFRAMA|IND_PERFIL|IND_ATIV|
    Posições: [1]=REG [2]=COD_VER [6]=DT_INI [7]=DT_FIN [8]=NOME [9]=CNPJ
              [10]=CPF [11]=UF [12]=IE [13]=COD_MUN [14]=IM [15]=SUFRAMA
              [16]=IND_PERFIL [17]=IND_ATIV
    """
    return Reg0000(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_ver=_g(campos, 2),
        dt_ini=_data(_g(campos, 6)),
        dt_fin=_data(_g(campos, 7)),
        nome=_g(campos, 8),
        cnpj=_g(campos, 9),
        cpf=_g(campos, 10),
        uf=_g(campos, 11),
        ie=_g(campos, 12),
        cod_mun=_g(campos, 13),
        im=_g(campos, 14),
        suframa=_g(campos, 15),
        ind_perfil=_g(campos, 16),
        ind_ativ=_g(campos, 17),
    )


def parsear_0110(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg0110:
    """
    Layout: |0110|COD_INC_TRIB|IND_APRO_CRED|COD_TIPO_CONT|IND_REG_CUM|
    Posições: [2]=COD_INC_TRIB [3]=IND_APRO_CRED [4]=COD_TIPO_CONT [5]=IND_REG_CUM
    """
    return Reg0110(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_inc_trib=_g(campos, 2),
        ind_apro_cred=_g(campos, 3),
        cod_tipo_cont=_g(campos, 4),
        ind_reg_cum=_g(campos, 5),
    )


def parsear_0111(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg0111:
    """
    Layout: |0111|REC_BRT_NCUM_TRIB_MI|REC_BRT_NCUM_NT_MI|REC_BRT_NCUM_EXP|
             REC_BRT_CUM|REC_BRT_TOTAL|
    Posições: [2..6]
    """
    return Reg0111(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        rec_brt_ncum_trib_mi=_dec(_g(campos, 2)),
        rec_brt_ncum_nt_mi=_dec(_g(campos, 3)),
        rec_brt_ncum_exp=_dec(_g(campos, 4)),
        rec_brt_cum=_dec(_g(campos, 5)),
        rec_brt_total=_dec(_g(campos, 6)),
    )


def parsear_0200(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg0200:
    """
    Layout 0200 (Item/Produto/Serviço):
    [1]=REG [2]=COD_ITEM [3]=DESCR_ITEM [4]=COD_BARRA [5]=COD_ANT_ITEM [6]=UNID_INV
    [7]=TIPO_ITEM [8]=COD_NCM [9]=EX_IPI [10]=COD_GEN [11]=COD_LST [12]=ALIQ_ICMS

    TIPO_ITEM: 00=Revenda; 01=MP; 02=Embalagem; 03=PI; 04=Ativo; 05=Consumo; 06=Serviço; 07=Outros.
    CR-11: TIPO_ITEM='07' com CFOP de insumo em C170 → candidato a REsp 1.221.170/PR.
    """
    return Reg0200(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_item=_g(campos, 2),
        descr_item=_g(campos, 3),
        cod_barra=_g(campos, 4),
        cod_ant_item=_g(campos, 5),
        unid_inv=_g(campos, 6),
        tipo_item=_g(campos, 7),
        cod_ncm=_g(campos, 8),
        ex_ipi=_g(campos, 9),
        cod_gen=_g(campos, 10),
        cod_lst=_g(campos, 11),
        aliq_icms=_dec(_g(campos, 12)),
    )
