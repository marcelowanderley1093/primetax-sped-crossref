"""Parser do Bloco F da EFD-Contribuições.

Sprint 3: F600/F700 (retenções na fonte). CR-16, CR-17, CR-19.
Sprint 4: F120/F130 (ativo imobilizado). CR-14, CR-15, CR-27. F150 (estoque). CR-22.
Sprint 5: F100 (demais documentos). CR-13, CR-32, CR-34.
          F800 (eventos corporativos). CR-18.
Base legal: Art. 3º Lei 10.637/2002 e 10.833/2003; Art. 30/33/34 Lei 10.833/2003.
"""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import RegF100, RegF120, RegF130, RegF150, RegF600, RegF700, RegF800

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
    """DDMMAAAA → YYYY-MM-DD. Retorna '' se inválido."""
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[4:8]}-{s[2:4]}-{s[0:2]}"
    return s


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_f100(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegF100:
    """
    Layout F100 (Demais Documentos e Operações, 19 campos):
    [1]=REG [2]=IND_OPER [3]=COD_PART [4]=COD_ITEM [5]=DT_OPER [6]=VL_OPER
    [7]=CST_PIS [8]=VL_BC_PIS [9]=ALIQ_PIS [10]=VL_PIS
    [11]=CST_COFINS [12]=VL_BC_COFINS [13]=ALIQ_COFINS [14]=VL_COFINS
    [15]=NAT_BC_CRED [16]=IND_ORIG_CRED [17]=COD_CTA [18]=COD_CCUS [19]=DESC_DOC_OPER

    CR-13: ausência de F100 no período com empresa não-cumulativa → gap de créditos.
    CR-32: Σ VL_BC_PIS (CST 50-67) → deve constar no M105.
    CR-34: Σ VL_BC_COFINS (CST 50-67) → deve constar no M505.
    """
    return RegF100(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        ind_oper=_g(campos, 2),
        cod_part=_g(campos, 3),
        cod_item=_g(campos, 4),
        dt_oper=_data(_g(campos, 5)),
        vl_oper=_dec(_g(campos, 6)),
        cst_pis=_g(campos, 7),
        vl_bc_pis=_dec(_g(campos, 8)),
        aliq_pis=_dec(_g(campos, 9)),
        vl_pis=_dec(_g(campos, 10)),
        cst_cofins=_g(campos, 11),
        vl_bc_cofins=_dec(_g(campos, 12)),
        aliq_cofins=_dec(_g(campos, 13)),
        vl_cofins=_dec(_g(campos, 14)),
        nat_bc_cred=_g(campos, 15),
        ind_orig_cred=_g(campos, 16),
        cod_cta=_g(campos, 17),
        cod_ccus=_g(campos, 18),
        desc_doc_oper=_g(campos, 19),
    )


def parsear_f800(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegF800:
    """
    Layout F800 (Crédito em Incorporação/Fusão/Cisão, 9 campos):
    [1]=REG [2]=IND_TRANSF [3]=IND_NAT_TRANSF [4]=CNPJ_TRANSF [5]=DT_TRANSF
    [6]=VL_TRANSF_PIS [7]=VL_TRANSF_COFINS [8]=VL_CRED_PIS_TRANS [9]=VL_CRED_COFINS_TRANS

    IND_NAT_TRANSF: 01=Incorporação; 02=Fusão; 03=Cisão; 04=Extinção.
    CR-18: VL_CRED_PIS_TRANS > 0 → crédito recebido em evento corporativo.
    """
    return RegF800(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        ind_transf=_g(campos, 2),
        ind_nat_transf=_g(campos, 3),
        cnpj_transf=_g(campos, 4),
        dt_transf=_data(_g(campos, 5)),
        vl_transf_pis=_dec(_g(campos, 6)),
        vl_transf_cofins=_dec(_g(campos, 7)),
        vl_cred_pis_trans=_dec(_g(campos, 8)),
        vl_cred_cofins_trans=_dec(_g(campos, 9)),
    )


def parsear_f120(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegF120:
    """
    Layout F120 (Crédito sobre Encargos de Depreciação/Amortização):
    [1]=REG [2]=NAT_BC_CRED [3]=IDENT_BEM_IMOB [4]=IND_ORIG_CRED [5]=IND_UTIL_BEM_IMOB
    [6]=VL_OPER_DEP [7]=PARC_OPER_NAO_BC_CRED [8]=CST_PIS [9]=VL_BC_PIS
    [10]=ALIQ_PIS [11]=VL_PIS [12]=CST_COFINS [13]=VL_BC_COFINS
    [14]=ALIQ_COFINS [15]=VL_COFINS [16]=COD_CTA [17]=COD_CCUS [18]=DESC_BEM_IMOB
    IND_UTIL_BEM_IMOB=9 com VL_PIS>0 → divergência CR-27.
    VL_PIS=0 com VL_BC_PIS>0 e IND_UTIL in {1,2,3} → oportunidade CR-14.
    """
    return RegF120(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        nat_bc_cred=_g(campos, 2),
        ident_bem_imob=_g(campos, 3),
        ind_orig_cred=_g(campos, 4),
        ind_util_bem_imob=_g(campos, 5),
        vl_oper_dep=_dec(_g(campos, 6)),
        parc_oper_nao_bc_cred=_dec(_g(campos, 7)),
        cst_pis=_g(campos, 8),
        vl_bc_pis=_dec(_g(campos, 9)),
        aliq_pis=_dec(_g(campos, 10)),
        vl_pis=_dec(_g(campos, 11)),
        cst_cofins=_g(campos, 12),
        vl_bc_cofins=_dec(_g(campos, 13)),
        aliq_cofins=_dec(_g(campos, 14)),
        vl_cofins=_dec(_g(campos, 15)),
        cod_cta=_g(campos, 16),
        cod_ccus=_g(campos, 17),
        desc_bem_imob=_g(campos, 18),
    )


def parsear_f130(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegF130:
    """
    Layout F130 (Crédito sobre Valor de Aquisição do Imobilizado):
    [1]=REG [2]=NAT_BC_CRED [3]=IDENT_BEM_IMOB [4]=IND_ORIG_CRED [5]=IND_UTIL_BEM_IMOB
    [6]=MES_OPER_AQUIS [7]=VL_OPER_AQUIS [8]=PARC_OPER_NAO_BC_CRED [9]=VL_BC_CRED
    [10]=IND_NR_PARC [11]=CST_PIS [12]=VL_BC_PIS [13]=ALIQ_PIS [14]=VL_PIS
    [15]=CST_COFINS [16]=VL_BC_COFINS [17]=ALIQ_COFINS [18]=VL_COFINS
    [19]=COD_CTA [20]=COD_CCUS [21]=DESC_BEM_IMOB
    IND_UTIL_BEM_IMOB=9 com VL_PIS>0 → divergência CR-27.
    VL_PIS=0 com VL_BC_PIS>0 e IND_UTIL in {1,2,3} → oportunidade CR-15.
    """
    return RegF130(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        nat_bc_cred=_g(campos, 2),
        ident_bem_imob=_g(campos, 3),
        ind_orig_cred=_g(campos, 4),
        ind_util_bem_imob=_g(campos, 5),
        mes_oper_aquis=_g(campos, 6),
        vl_oper_aquis=_dec(_g(campos, 7)),
        parc_oper_nao_bc_cred=_dec(_g(campos, 8)),
        vl_bc_cred=_dec(_g(campos, 9)),
        ind_nr_parc=_g(campos, 10),
        cst_pis=_g(campos, 11),
        vl_bc_pis=_dec(_g(campos, 12)),
        aliq_pis=_dec(_g(campos, 13)),
        vl_pis=_dec(_g(campos, 14)),
        cst_cofins=_g(campos, 15),
        vl_bc_cofins=_dec(_g(campos, 16)),
        aliq_cofins=_dec(_g(campos, 17)),
        vl_cofins=_dec(_g(campos, 18)),
        cod_cta=_g(campos, 19),
        cod_ccus=_g(campos, 20),
        desc_bem_imob=_g(campos, 21),
    )


def parsear_f150(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegF150:
    """
    Layout F150 (Crédito Presumido sobre Estoque de Abertura):
    [1]=REG [2]=NAT_BC_CRED [3]=VL_TOT_EST [4]=EST_IMP [5]=VL_BC_EST
    [6]=VL_BC_MEN_EST [7]=CST_PIS [8]=ALIQ_PIS [9]=VL_CRED_PIS
    [10]=CST_COFINS [11]=ALIQ_COFINS [12]=VL_CRED_COFINS [13]=DESC_EST [14]=COD_CTA
    Alíquotas fixas: PIS=0,65%, COFINS=3,0%. 12 parcelas mensais.
    VL_CRED_PIS=0 com VL_BC_MEN_EST>0 → oportunidade CR-22.
    """
    return RegF150(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        nat_bc_cred=_g(campos, 2),
        vl_tot_est=_dec(_g(campos, 3)),
        est_imp=_dec(_g(campos, 4)),
        vl_bc_est=_dec(_g(campos, 5)),
        vl_bc_men_est=_dec(_g(campos, 6)),
        cst_pis=_g(campos, 7),
        aliq_pis=_dec(_g(campos, 8)),
        vl_cred_pis=_dec(_g(campos, 9)),
        cst_cofins=_g(campos, 10),
        aliq_cofins=_dec(_g(campos, 11)),
        vl_cred_cofins=_dec(_g(campos, 12)),
        desc_est=_g(campos, 13),
        cod_cta=_g(campos, 14),
    )


def parsear_f600(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegF600:
    """
    Layout F600 (Retenção na Fonte do PIS/Pasep):
    [1]=REG [2]=IND_NAT_RET [3]=DT_RET [4]=VL_BC_RET [5]=ALIQ_RET
    [6]=VL_RET_APU [7]=COD_REC [8]=IND_NAT_REC [9]=PR_REC_RET
    [10]=DT_INI_REC [11]=DT_FIN_REC [12]=CNPJ_FONTE_PAG
    [13]=VL_RET_PER [14]=VL_RET_DCOMP [15]=QTDE_DOC_DPREV [16]=VL_DPREV

    Saldo não-compensado = VL_RET_APU - VL_RET_PER - VL_RET_DCOMP → CR-16.
    PR_REC_RET com DT_RET > 5 anos atrás → CR-19 (prescrição quinquenal CTN 168).
    """
    return RegF600(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        ind_nat_ret=_g(campos, 2),
        dt_ret=_data(_g(campos, 3)),
        vl_bc_ret=_dec(_g(campos, 4)),
        aliq_ret=_dec(_g(campos, 5)),
        vl_ret_apu=_dec(_g(campos, 6)),
        cod_rec=_g(campos, 7),
        ind_nat_rec=_g(campos, 8),
        pr_rec_ret=_data(_g(campos, 9)),
        cnpj_fonte_pag=_g(campos, 12),
        vl_ret_per=_dec(_g(campos, 13)),
        vl_ret_dcomp=_dec(_g(campos, 14)),
    )


def parsear_f700(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegF700:
    """
    Layout F700 (Retenção na Fonte da COFINS): estrutura idêntica ao F600.
    [1]=REG [2]=IND_NAT_RET [3]=DT_RET [4]=VL_BC_RET [5]=ALIQ_RET
    [6]=VL_RET_APU [7]=COD_REC [8]=IND_NAT_REC [9]=PR_REC_RET
    [10]=DT_INI_REC [11]=DT_FIN_REC [12]=CNPJ_FONTE_PAG
    [13]=VL_RET_PER [14]=VL_RET_DCOMP
    """
    return RegF700(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        ind_nat_ret=_g(campos, 2),
        dt_ret=_data(_g(campos, 3)),
        vl_bc_ret=_dec(_g(campos, 4)),
        aliq_ret=_dec(_g(campos, 5)),
        vl_ret_apu=_dec(_g(campos, 6)),
        cod_rec=_g(campos, 7),
        ind_nat_rec=_g(campos, 8),
        pr_rec_ret=_data(_g(campos, 9)),
        cnpj_fonte_pag=_g(campos, 12),
        vl_ret_per=_dec(_g(campos, 13)),
        vl_ret_dcomp=_dec(_g(campos, 14)),
    )
