"""
Dataclasses dos registros SPED para Sprint 1.
Mapeamento 1:1 com a estrutura dos registros da EFD-Contribuições.

Convenção de campos monetários: Decimal (nunca float).
Convenção de datas no banco: TEXT "YYYY-MM-DD".
Convenção de ano_mes: int YYYYMM.
"""

from dataclasses import dataclass, field
from decimal import Decimal


# ---------------------------------------------------------------------------
# Tipos de output do motor de cruzamentos
# ---------------------------------------------------------------------------

@dataclass
class Evidencia:
    arquivo_origem: str
    linha_arquivo: int
    bloco: str
    registro: str
    cnpj_declarante: str
    ano_mes: int
    campos_chave: dict = field(default_factory=dict)


@dataclass
class Oportunidade:
    codigo_regra: str
    descricao: str
    severidade: str          # "alto", "medio", "baixo"
    valor_impacto_conservador: Decimal
    valor_impacto_maximo: Decimal
    evidencia: list[dict]    # lista de dicts serializáveis para JSON


@dataclass
class Divergencia:
    codigo_regra: str
    descricao: str
    severidade: str
    evidencia: list[dict]


# ---------------------------------------------------------------------------
# Registros do Bloco 0
# ---------------------------------------------------------------------------

@dataclass
class Reg0000:
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    dt_ini: str          # DDMMAAAA no arquivo; "YYYY-MM-DD" no banco
    dt_fin: str
    nome: str
    cnpj: str
    cpf: str
    uf: str
    ie: str
    cod_mun: str
    im: str
    suframa: str
    ind_perfil: str      # "A", "B" ou "C"
    ind_ativ: str        # "0" ou "1"
    cod_ver: str


@dataclass
class Reg0110:
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_inc_trib: str    # "1" não-cumulativo, "2" cumulativo, "3" ambos
    ind_apro_cred: str   # "1" apropriação direta, "2" rateio proporcional
    cod_tipo_cont: str
    ind_reg_cum: str


@dataclass
class Reg0111:
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    rec_brt_ncum_trib_mi: Decimal
    rec_brt_ncum_nt_mi: Decimal
    rec_brt_ncum_exp: Decimal
    rec_brt_cum: Decimal
    rec_brt_total: Decimal


# ---------------------------------------------------------------------------
# Registros do Bloco C
# ---------------------------------------------------------------------------

@dataclass
class RegC100:
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    ind_oper: str        # "0" entrada, "1" saída
    ind_emit: str
    cod_part: str
    cod_mod: str
    cod_sit: str
    ser: str
    num_doc: str
    chave_nfe: str
    dt_doc: str
    vl_doc: Decimal


@dataclass
class RegC170:
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    # Chave de vínculo ao C100 pai — populada pelo parser
    c100_linha_arquivo: int
    num_item: str
    cod_item: str
    vl_item: Decimal
    vl_desc: Decimal
    cfop: str
    vl_icms: Decimal         # campo 15 — ICMS próprio
    vl_icms_st: Decimal      # campo 18 — ICMS substituição tributária
    cst_pis: str             # campo 25
    vl_bc_pis: Decimal       # campo 26
    aliq_pis: Decimal        # campo 27 (%)
    quant_bc_pis: Decimal    # campo 28
    aliq_pis_quant: Decimal  # campo 29 (R$/unidade)
    vl_pis: Decimal          # campo 30
    cst_cofins: str          # campo 31
    vl_bc_cofins: Decimal    # campo 32
    aliq_cofins: Decimal     # campo 33 (%)
    quant_bc_cofins: Decimal # campo 34
    aliq_cofins_quant: Decimal  # campo 35
    vl_cofins: Decimal       # campo 36
    cod_cta: str             # campo 37


# ---------------------------------------------------------------------------
# Registros do Bloco C — Sprint 2 (NFC-e consolidada)
# ---------------------------------------------------------------------------

@dataclass
class RegC181:
    """PIS — detalhe por CST/alíquota da NFC-e consolidada (filho de C180)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    c180_linha_arquivo: int   # FK de rastreabilidade ao C180 pai
    ind_oper: str             # herdado do C180 pai ("0"=entrada, "1"=saída)
    cst_pis: str              # campo 2
    cfop: str                 # campo 3
    vl_item: Decimal          # campo 4
    vl_desc: Decimal          # campo 5 — inclui exclusão de ICMS se feita corretamente
    vl_bc_pis: Decimal        # campo 6
    aliq_pis: Decimal         # campo 7 (%)
    quant_bc_pis: Decimal     # campo 8
    aliq_pis_quant: Decimal   # campo 9
    vl_pis: Decimal           # campo 10
    cod_cta: str              # campo 11


@dataclass
class RegC185:
    """COFINS — detalhe por CST/alíquota da NFC-e consolidada (filho de C180)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    c180_linha_arquivo: int
    ind_oper: str
    cst_cofins: str
    cfop: str
    vl_item: Decimal
    vl_desc: Decimal
    vl_bc_cofins: Decimal
    aliq_cofins: Decimal
    quant_bc_cofins: Decimal
    aliq_cofins_quant: Decimal
    vl_cofins: Decimal
    cod_cta: str


# ---------------------------------------------------------------------------
# Registros do Bloco D — Sprint 2 (serviços de transporte)
# ---------------------------------------------------------------------------

@dataclass
class RegD201:
    """PIS — detalhe por CST/alíquota das NFS de transporte consolidadas (filho de D200)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    d200_linha_arquivo: int   # FK de rastreabilidade ao D200 pai
    ind_oper: str             # herdado do D200 pai
    cst_pis: str              # campo 2
    vl_item: Decimal          # campo 3
    vl_bc_pis: Decimal        # campo 4 — se == VL_ITEM, ICMS foi incluído na base
    aliq_pis: Decimal         # campo 5 (%)
    quant_bc_pis: Decimal     # campo 6
    aliq_pis_quant: Decimal   # campo 7
    vl_pis: Decimal           # campo 8
    cod_cta: str              # campo 9


@dataclass
class RegD205:
    """COFINS — detalhe por CST/alíquota das NFS de transporte consolidadas (filho de D200)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    d200_linha_arquivo: int
    ind_oper: str
    cst_cofins: str
    vl_item: Decimal
    vl_bc_cofins: Decimal
    aliq_cofins: Decimal
    quant_bc_cofins: Decimal
    aliq_cofins_quant: Decimal
    vl_cofins: Decimal
    cod_cta: str


# ---------------------------------------------------------------------------
# Registros do Bloco M (mínimo Sprint 1)
# ---------------------------------------------------------------------------

@dataclass
class RegM200:
    """Resumo da apuração do PIS/Pasep. Campos completos em Sprint 3+."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    vl_tot_cont_nc_per: Decimal   # campo 2 — total contribuições não-cumulativo do período
    vl_tot_cred_desc: Decimal = Decimal("0")   # campo 3 — Σ M100.VL_CRED_DESC (Sprint 4+)
    vl_rec_brt_total: Decimal = Decimal("0")   # campo 12 — receita bruta total


@dataclass
class RegM600:
    """Resumo da apuração da COFINS. Campos completos em Sprint 3+."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    vl_tot_cont_nc_per: Decimal   # campo 2
    vl_tot_cred_desc: Decimal = Decimal("0")   # campo 3 — Σ M500.VL_CRED_DESC (Sprint 4+)
    vl_rec_brt_total: Decimal = Decimal("0")   # campo 12


# ---------------------------------------------------------------------------
# Registros do Bloco F — Sprint 4 (ativo imobilizado e estoque de abertura)
# ---------------------------------------------------------------------------

@dataclass
class RegF120:
    """Bens Incorporados ao Ativo Imobilizado – Crédito sobre Encargos de Depreciação.
    Art. 3º, VI da Lei 10.637/2002 e Lei 10.833/2003. NAT_BC_CRED=09.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    nat_bc_cred: str           # campo 2 — fixo "09"
    ident_bem_imob: str        # campo 3 — 01=Edif; 03=Instal; 04=Máq; 05=Equip; 06=Veic; 99=Outros
    ind_orig_cred: str         # campo 4 — 0=MI; 1=Importação
    ind_util_bem_imob: str     # campo 5 — 1=Prod; 2=Serv; 3=Loc; 9=Vedado
    vl_oper_dep: Decimal       # campo 6 — encargos de depreciação/amortização do período
    parc_oper_nao_bc_cred: Decimal  # campo 7 — parcela excluída da base
    cst_pis: str               # campo 8
    vl_bc_pis: Decimal         # campo 9
    aliq_pis: Decimal          # campo 10 (%)
    vl_pis: Decimal            # campo 11 — crédito PIS do período
    cst_cofins: str            # campo 12
    vl_bc_cofins: Decimal      # campo 13
    aliq_cofins: Decimal       # campo 14 (%)
    vl_cofins: Decimal         # campo 15 — crédito COFINS do período
    cod_cta: str               # campo 16
    cod_ccus: str              # campo 17
    desc_bem_imob: str         # campo 18 — descrição complementar


@dataclass
class RegF130:
    """Bens Incorporados ao Ativo Imobilizado – Crédito sobre Valor de Aquisição.
    Art. 3º, VI da Lei 10.637/2002 e Lei 10.833/2003. NAT_BC_CRED=10.
    Lei 12.546/2011 — crédito integral para máquinas/equipamentos adquiridos após ago/2011.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    nat_bc_cred: str           # campo 2 — fixo "10"
    ident_bem_imob: str        # campo 3 — 01=Edif; 03=Instal; 04=Máq; 05=Equip; 06=Veic; 99=Outros
    ind_orig_cred: str         # campo 4 — 0=MI; 1=Importação
    ind_util_bem_imob: str     # campo 5 — 1=Prod; 2=Serv; 3=Loc; 9=Vedado
    mes_oper_aquis: str        # campo 6 — mmaaaa — mês de aquisição
    vl_oper_aquis: Decimal     # campo 7 — valor de aquisição
    parc_oper_nao_bc_cred: Decimal  # campo 8 — parcela excluída
    vl_bc_cred: Decimal        # campo 9 — base total = campo 7 − campo 8
    ind_nr_parc: str           # campo 10 — 1=Integral; 2=12m; 3=24m; 4=48m; 5=6m; 9=Outra
    cst_pis: str               # campo 11
    vl_bc_pis: Decimal         # campo 12 — base mensal = vl_bc_cred / nº meses
    aliq_pis: Decimal          # campo 13 (%)
    vl_pis: Decimal            # campo 14 — crédito PIS do mês
    cst_cofins: str            # campo 15
    vl_bc_cofins: Decimal      # campo 16
    aliq_cofins: Decimal       # campo 17 (%)
    vl_cofins: Decimal         # campo 18 — crédito COFINS do mês
    cod_cta: str               # campo 19
    cod_ccus: str              # campo 20
    desc_bem_imob: str         # campo 21


@dataclass
class RegF150:
    """Crédito Presumido sobre Estoque de Abertura.
    Art. 11 da Lei 10.637/2002 e art. 12 da Lei 10.833/2003. NAT_BC_CRED=18.
    Alíquotas fixas: PIS=0,65%, COFINS=3,0%. Apurado em 12 parcelas mensais.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    nat_bc_cred: str           # campo 2 — fixo "18"
    vl_tot_est: Decimal        # campo 3 — valor total do estoque de abertura
    est_imp: Decimal           # campo 4 — parcela sem direito a crédito
    vl_bc_est: Decimal         # campo 5 — base total = campo 3 − campo 4
    vl_bc_men_est: Decimal     # campo 6 — base mensal = campo 5 / 12
    cst_pis: str               # campo 7
    aliq_pis: Decimal          # campo 8 — fixo 0,65
    vl_cred_pis: Decimal       # campo 9 — crédito PIS mensal
    cst_cofins: str            # campo 10
    aliq_cofins: Decimal       # campo 11 — fixo 3,0
    vl_cred_cofins: Decimal    # campo 12 — crédito COFINS mensal
    desc_est: str              # campo 13 — descrição
    cod_cta: str               # campo 14


# ---------------------------------------------------------------------------
# Registros do Bloco F — Sprint 3 (retenções na fonte)
# ---------------------------------------------------------------------------

@dataclass
class RegF600:
    """Retenção na Fonte do PIS/Pasep (Art. 30/33/34 Lei 10.833/2003)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    ind_nat_ret: str      # natureza da retenção
    dt_ret: str           # DDMMAAAA → YYYY-MM-DD — data da retenção
    vl_bc_ret: Decimal    # base de cálculo
    aliq_ret: Decimal     # alíquota (%)
    vl_ret_apu: Decimal   # valor retido total
    cod_rec: str          # código de receita SRF
    ind_nat_rec: str      # natureza da receita
    pr_rec_ret: str       # previsão de recuperação (YYYY-MM-DD) — CR-19
    cnpj_fonte_pag: str   # CNPJ do pagador/fonte retentora
    vl_ret_per: Decimal   # recuperado neste período
    vl_ret_dcomp: Decimal # compensado via DCOMP


@dataclass
class RegF700:
    """Retenção na Fonte da COFINS (Art. 30/33/34 Lei 10.833/2003)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    ind_nat_ret: str
    dt_ret: str
    vl_bc_ret: Decimal
    aliq_ret: Decimal
    vl_ret_apu: Decimal
    cod_rec: str
    ind_nat_rec: str
    pr_rec_ret: str
    cnpj_fonte_pag: str
    vl_ret_per: Decimal
    vl_ret_dcomp: Decimal


# ---------------------------------------------------------------------------
# Registros do Bloco M — Sprint 2 (ajustes de base)
# ---------------------------------------------------------------------------

@dataclass
class RegM215:
    """Ajuste à base de cálculo do PIS/Pasep (filho de M210). Leiaute 3.1.0+."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    m210_linha_arquivo: int   # FK de rastreabilidade ao M210 pai
    ind_aj_bc: str            # "0"=redução, "1"=acréscimo
    vl_aj_bc: Decimal         # valor do ajuste
    cod_aj_bc: str            # código tabela SRF
    num_doc: str
    descr_aj_bc: str
    dt_ref: str
    cod_cta: str
    cnpj_ref: str


@dataclass
class RegM615:
    """Ajuste à base de cálculo da COFINS (filho de M610). Leiaute 3.1.0+."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    m610_linha_arquivo: int
    ind_aj_bc: str
    vl_aj_bc: Decimal
    cod_aj_bc: str
    num_doc: str
    descr_aj_bc: str
    dt_ref: str
    cod_cta: str
    cnpj_ref: str


# ---------------------------------------------------------------------------
# Registros do Bloco M — Sprint 4 (créditos PIS/COFINS por tipo)
# ---------------------------------------------------------------------------

@dataclass
class RegM100:
    """Crédito de PIS/Pasep Relativo ao Período de Apuração (filho de M001).
    Cada ocorrência representa um tipo/código de crédito. A soma de VL_CRED_DESC
    de todos os M100 deve igualar M200.VL_TOT_CRED_DESC (CR-29).
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_cred: str              # campo 2 — código do crédito (ex: 101, 201, 301...)
    ind_cred_ori: str          # campo 3 — 0=Próprio; 1=Transferência de crédito
    vl_bc_pis: Decimal         # campo 4 — base de cálculo
    aliq_pis: Decimal          # campo 5 — alíquota (%)
    quant_bc_pis: Decimal      # campo 6 — quantidade base (alíquota por unidade)
    aliq_pis_quant: Decimal    # campo 7 — alíquota por unidade
    vl_cred_disp: Decimal      # campo 8 — crédito disponível (apurado + ajustes)
    vl_ajus_acres: Decimal     # campo 9 — ajuste de acréscimo
    vl_ajus_reduc: Decimal     # campo 10 — ajuste de redução
    vl_cred_difer: Decimal     # campo 11 — crédito diferido neste período
    vl_cred_difer_ant: Decimal # campo 12 — crédito diferido de períodos anteriores
    ind_apro: str              # campo 13 — "0"=total; "1"=parcial
    vl_cred_desc: Decimal      # campo 14 — crédito DESCONTADO neste período → Σ = M200.VL_TOT_CRED_DESC
    sld_cred: Decimal          # campo 15 — saldo a transportar


@dataclass
class RegM500:
    """Crédito de COFINS Relativo ao Período de Apuração (filho de M001).
    Estrutura idêntica ao M100. Σ VL_CRED_DESC = M600.VL_TOT_CRED_DESC (CR-30).
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_cred: str
    ind_cred_ori: str
    vl_bc_cofins: Decimal      # campo 4
    aliq_cofins: Decimal       # campo 5 (%)
    quant_bc_cofins: Decimal   # campo 6
    aliq_cofins_quant: Decimal # campo 7
    vl_cred_disp: Decimal      # campo 8
    vl_ajus_acres: Decimal     # campo 9
    vl_ajus_reduc: Decimal     # campo 10
    vl_cred_difer: Decimal     # campo 11
    vl_cred_difer_ant: Decimal # campo 12
    ind_apro: str              # campo 13
    vl_cred_desc: Decimal      # campo 14 → Σ = M600.VL_TOT_CRED_DESC
    sld_cred: Decimal          # campo 15


# ---------------------------------------------------------------------------
# Registros do Bloco 0 — Sprint 5 (catálogo de itens)
# ---------------------------------------------------------------------------

@dataclass
class Reg0200:
    """Item (produto/serviço) — Tabela de Identificação do Item.
    Base legal: IN RFB 1.252/2012 — Bloco 0, registro 0200.
    TIPO_ITEM='07' (uso e consumo) com CFOP de insumo → candidato a CR-11.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_item: str           # campo 2
    descr_item: str         # campo 3
    cod_barra: str          # campo 4
    cod_ant_item: str       # campo 5
    unid_inv: str           # campo 6
    tipo_item: str          # campo 7 — 00=Merc revenda; 01=MP; 02=Emb; 03=PI; 04=Ativo; 05=Consumo; 06=Serv; 07=Outros
    cod_ncm: str            # campo 8
    ex_ipi: str             # campo 9
    cod_gen: str            # campo 10
    cod_lst: str            # campo 11
    aliq_icms: Decimal      # campo 12


# ---------------------------------------------------------------------------
# Registros do Bloco F — Sprint 5 (F100, F800)
# ---------------------------------------------------------------------------

@dataclass
class RegF100:
    """Demais Documentos e Operações (não NF-e nem serviços de transporte).
    Base legal: Art. 3º Lei 10.637/2002 — créditos de aluguel, frete, armazenagem etc.
    CR-13: ausência de F100 quando empresa é não-cumulativa.
    CR-32/CR-34: Σ VL_BC_PIS/VL_BC_COFINS (CST 50-67) vs M105/M505.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    ind_oper: str           # campo 2 — 0=Entrada; 1=Saída
    cod_part: str           # campo 3
    cod_item: str           # campo 4
    dt_oper: str            # campo 5 — DDMMAAAA → YYYY-MM-DD
    vl_oper: Decimal        # campo 6
    cst_pis: str            # campo 7
    vl_bc_pis: Decimal      # campo 8
    aliq_pis: Decimal       # campo 9 (%)
    vl_pis: Decimal         # campo 10
    cst_cofins: str         # campo 11
    vl_bc_cofins: Decimal   # campo 12
    aliq_cofins: Decimal    # campo 13 (%)
    vl_cofins: Decimal      # campo 14
    nat_bc_cred: str        # campo 15
    ind_orig_cred: str      # campo 16
    cod_cta: str            # campo 17
    cod_ccus: str           # campo 18
    desc_doc_oper: str      # campo 19


@dataclass
class RegF800:
    """Crédito de PIS/COFINS em Operações de Incorporação, Fusão e Cisão.
    Base legal: Art. 3º, §4º Lei 10.637/2002 e Lei 10.833/2003;
    IN RFB 900/2008 (créditos transferidos em eventos corporativos).
    CR-18: crédito recebido em evento corporativo — verificar aproveitamento.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    ind_transf: str              # campo 2 — 1=crédito apurado; 2=saldo credor
    ind_nat_transf: str          # campo 3 — 01=Incorporação; 02=Fusão; 03=Cisão; 04=Extinção
    cnpj_transf: str             # campo 4 — CNPJ da empresa transmissora/sucedida
    dt_transf: str               # campo 5 — DDMMAAAA → YYYY-MM-DD
    vl_transf_pis: Decimal       # campo 6 — crédito PIS repassado
    vl_transf_cofins: Decimal    # campo 7 — crédito COFINS repassado
    vl_cred_pis_trans: Decimal   # campo 8 — crédito PIS efetivamente transferido
    vl_cred_cofins_trans: Decimal  # campo 9 — crédito COFINS efetivamente transferido


# ---------------------------------------------------------------------------
# Registros do Bloco M — Sprint 5 (base de crédito por NAT_BC_CRED)
# ---------------------------------------------------------------------------

@dataclass
class RegM105:
    """Detalhamento da Base de Cálculo do Crédito de PIS/Pasep por Natureza.
    Filho de M100. Σ VL_BC_PIS_TOT ↔ créditos analíticos de C170/F100/F120/F130 (CR-32).
    Base legal: IN RFB 1.252/2012.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    nat_bc_cred: str           # campo 2
    vl_bc_pis_tot: Decimal     # campo 3 — total da base por nat_bc_cred
    vl_bc_minut: Decimal       # campo 4
    vl_bc_mindt: Decimal       # campo 5
    vl_bc_mexp: Decimal        # campo 6
    vl_amt_parc_forn: Decimal  # campo 7
    vl_bc_isenta: Decimal      # campo 8
    vl_bc_outras: Decimal      # campo 9
    desc_compl: str            # campo 10


@dataclass
class RegM505:
    """Detalhamento da Base de Cálculo do Crédito de COFINS por Natureza.
    Filho de M500. Estrutura idêntica ao M105 (campo 3 = VL_BC_COFINS_TOT). CR-34.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    nat_bc_cred: str
    vl_bc_cofins_tot: Decimal  # campo 3
    vl_bc_minut: Decimal
    vl_bc_mindt: Decimal
    vl_bc_mexp: Decimal
    vl_amt_parc_forn: Decimal
    vl_bc_isenta: Decimal
    vl_bc_outras: Decimal
    desc_compl: str


# ---------------------------------------------------------------------------
# Registros do Bloco 1 — Sprint 5 (carry-forward de créditos)
# ---------------------------------------------------------------------------

@dataclass
class Reg1100:
    """Controle de Créditos PIS/Pasep — saldo mensal a transportar.
    Base legal: Art. 3º Lei 10.637/2002; Lei 9.430/1996 (compensação);
    IN RFB 1.252/2012.
    SLD_CRED_FIM > 0 → crédito disponível não utilizado → CR-25.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    per_apu_cred: str              # campo 2 — MMAAAA: período de apuração do crédito
    orig_cred: str                 # campo 3
    cnpj_suc: str                  # campo 4 — CNPJ da sucedida (evento corporativo)
    cod_cred: str                  # campo 5 — código do crédito
    vl_cred_apu: Decimal           # campo 6
    vl_cred_ext_apu: Decimal       # campo 7
    vl_tot_cred_apu: Decimal       # campo 8
    vl_cred_desc_pa_ant: Decimal   # campo 9
    vl_cred_per_pa_ant: Decimal    # campo 10
    vl_cred_dcomp_pa_ant: Decimal  # campo 11
    sd_cred_disp_efd: Decimal      # campo 12
    vl_cred_desc_efd: Decimal      # campo 13
    vl_cred_per_efd: Decimal       # campo 14
    vl_cred_dcomp_efd: Decimal     # campo 15
    vl_cred_trans: Decimal         # campo 16
    vl_cred_out: Decimal           # campo 17
    sld_cred_fim: Decimal          # campo 18 — saldo a transportar para mês seguinte


@dataclass
class Reg1500:
    """Controle de Créditos COFINS — estrutura idêntica ao Reg1100.
    SLD_CRED_FIM > 0 → crédito disponível não utilizado → CR-25.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    per_apu_cred: str
    orig_cred: str
    cnpj_suc: str
    cod_cred: str
    vl_cred_apu: Decimal
    vl_cred_ext_apu: Decimal
    vl_tot_cred_apu: Decimal
    vl_cred_desc_pa_ant: Decimal
    vl_cred_per_pa_ant: Decimal
    vl_cred_dcomp_pa_ant: Decimal
    sd_cred_disp_efd: Decimal
    vl_cred_desc_efd: Decimal
    vl_cred_per_efd: Decimal
    vl_cred_dcomp_efd: Decimal
    vl_cred_trans: Decimal
    vl_cred_out: Decimal
    sld_cred_fim: Decimal


# ---------------------------------------------------------------------------
# Registros do Bloco M — Sprint 3 (contribuição por CST/alíquota)
# ---------------------------------------------------------------------------

@dataclass
class RegM210:
    """Contribuição do Período — PIS/Pasep (detalhe por COD_CONT / CST×alíquota)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_cont: str         # campo 2 — código da contribuição (mapa: CST+alíquota)
    vl_rec_brt: Decimal   # campo 3 — receita bruta
    vl_bc_cont: Decimal   # campo 4 — base de cálculo
    aliq_pis: Decimal     # campo 5 — alíquota (%)
    vl_cont_apu: Decimal  # campo 8 — contribuição apurada
    vl_ajus_reduc: Decimal  # campo 10 — reduções (inclui exclusão ICMS base M215)
    vl_cont_per: Decimal  # campo 13 — contribuição do período


@dataclass
class RegM610:
    """Contribuição do Período — COFINS (detalhe por COD_CONT / CST×alíquota)."""
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_cont: str
    vl_rec_brt: Decimal
    vl_bc_cont: Decimal
    aliq_cofins: Decimal
    vl_cont_apu: Decimal
    vl_ajus_reduc: Decimal
    vl_cont_per: Decimal


# ---------------------------------------------------------------------------
# Registros do Bloco 9
# ---------------------------------------------------------------------------

@dataclass
class Reg9900:
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    reg_blc: str     # tipo de registro contado
    qtd_reg_blc: int # quantidade declarada


@dataclass
class Reg9999:
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    qtd_lin: int     # total de linhas declarado


# ---------------------------------------------------------------------------
# Resultado de importação
# ---------------------------------------------------------------------------

@dataclass
class ResultadoImportacao:
    arquivo: str
    cnpj: str
    ano_calendario: int
    ano_mes: int
    dt_ini: str
    dt_fin: str
    cod_ver: str
    encoding_origem: str
    encoding_confianca: str
    total_linhas_lidas: int
    contagens_reais: dict[str, int]  # reg -> count
    contagens_declaradas: dict[str, int]
    divergencias_bloco9: list[str]
    sucesso: bool
    mensagem: str = ""


# ---------------------------------------------------------------------------
# EFD ICMS/IPI — Sprint 6 (cruzamentos 35, 36, 37)
# ---------------------------------------------------------------------------

@dataclass
class RegIcms0000:
    """Header do EFD ICMS/IPI (Leiaute 3.2.2).
    Base legal: Ato COTEPE/ICMS 44/2018; Ajuste SINIEF 02/2009.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_ver: str    # campo 2
    cod_fin: str    # campo 3
    dt_ini: str     # campo 4 — YYYY-MM-DD
    dt_fin: str     # campo 5 — YYYY-MM-DD
    nome: str       # campo 6
    cnpj: str       # campo 7
    cpf: str        # campo 8
    uf: str         # campo 9
    ie: str         # campo 10
    cod_mun: str    # campo 11
    im: str         # campo 12
    suframa: str    # campo 13
    ind_perfil: str # campo 14
    ind_ativ: str   # campo 15


@dataclass
class RegIcmsC100:
    """C100 do EFD ICMS/IPI — cabeçalho do documento fiscal.
    Rastreia hierarquia pai → C170. IND_OPER usado no CR-37.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    ind_oper: str   # campo 2 — 0=Entrada; 1=Saída


@dataclass
class RegIcmsC170:
    """Item do documento fiscal EFD ICMS/IPI — 38 campos (vs 37 da EFD-Contrib).
    Base legal: Ato COTEPE/ICMS 44/2018, Bloco C.
    Campo extra [38]=VL_ABAT_NT versus EFD-Contribuições.
    CR-37: CFOP início '7' → exportação → verificar CST_PIS/COFINS na EFD-Contrib.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    c100_linha_arquivo: int
    num_item: str         # campo 2
    cod_item: str         # campo 3
    cfop: str             # campo 11 — chave para CR-37
    cst_icms: str         # campo 10
    vl_item: Decimal      # campo 7
    vl_bc_icms: Decimal   # campo 13
    aliq_icms: Decimal    # campo 14
    vl_icms: Decimal      # campo 15
    cst_pis: str          # campo 25
    vl_bc_pis: Decimal    # campo 26
    aliq_pis: Decimal     # campo 27
    vl_pis: Decimal       # campo 30
    cst_cofins: str       # campo 31
    vl_bc_cofins: Decimal # campo 32
    aliq_cofins: Decimal  # campo 33
    vl_cofins: Decimal    # campo 36
    cod_cta: str          # campo 37


@dataclass
class RegIcmsG110:
    """CIAP — Apuração do ICMS a Apropriar por Período (G110).
    Base legal: Ajuste SINIEF 8/1997; art. 20 §§5º-7º ADCT.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    dt_ini: str             # campo 2 — YYYY-MM-DD
    dt_fin: str             # campo 3 — YYYY-MM-DD
    saldo_in_icms: Decimal  # campo 4
    som_parc: Decimal       # campo 5
    vl_trib_exp: Decimal    # campo 6
    vl_total: Decimal       # campo 7
    ind_per_sai: Decimal    # campo 8
    icms_aprop: Decimal     # campo 9
    som_icms_oc: Decimal    # campo 10


@dataclass
class RegIcmsG125:
    """CIAP — Movimentação de Bem do Ativo Imobilizado (G125).
    Base legal: Ajuste SINIEF 8/1997; art. 20 §§5º-7º ADCT.
    VL_PARC_PASS > 0 → ICMS sendo apropriado → CR-35: verificar F120/F130.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    cod_ind_bem: str           # campo 2
    ident_bem: str             # campo 3
    dt_mov: str                # campo 4 — YYYY-MM-DD
    tipo_mov: str              # campo 5
    vl_imob_icms_op: Decimal   # campo 6
    vl_imob_icms_st: Decimal   # campo 7
    vl_imob_icms_frt: Decimal  # campo 8
    vl_imob_icms_dif: Decimal  # campo 9
    num_parc: str              # campo 10
    vl_parc_pass: Decimal      # campo 11 — parcela passível de apropriação


@dataclass
class RegIcmsH005:
    """Inventário — Totais por Período (H005).
    Base legal: Convênio ICMS 143/2006; Ajuste SINIEF 02/2009.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    dt_inv: str       # campo 2 — YYYY-MM-DD
    vl_inv: Decimal   # campo 3
    mot_inv: str      # campo 4


@dataclass
class RegIcmsH010:
    """Inventário — Item do Inventário (H010).
    Base legal: Convênio ICMS 143/2006; Ajuste SINIEF 02/2009.
    VL_ITEM_IR > 0 → valor com ICMS excluído para fins IR → CR-36: verificar F150.
    Manual EFD ICMS/IPI: 'O montante desse imposto, destacado em nota fiscal,
    deve ser excluído do valor dos estoques para efeito do imposto de renda.'
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    h005_linha_arquivo: int  # FK de rastreabilidade
    cod_item: str     # campo 2
    unid: str         # campo 3
    qtd: Decimal      # campo 4
    vl_unit: Decimal  # campo 5
    vl_item: Decimal  # campo 6
    ind_prop: str     # campo 7 — 0=próprio; 1=terceiros
    cod_part: str     # campo 8
    txt_compl: str    # campo 9
    cod_cta: str      # campo 10
    vl_item_ir: Decimal  # campo 11 — CHAVE para CR-36


# ---------------------------------------------------------------------------
# ECD — Sprint 7 (cruzamentos 38-42)
# ---------------------------------------------------------------------------

@dataclass
class RegEcd0000:
    """Header da ECD (Leiaute 9 — ADE Cofis 01/2026).
    Base legal: IN RFB 2.003/2021; Decreto 6.022/2007.
    IND_MUDANC_PC=[22] → política de reconciliação plano de contas (CLAUDE.md §16).
    CNPJ em campos[6] — diferente da EFD-Contrib (campos[9]) e EFD ICMS (campos[7]).
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "0000"
    dt_ini: str         # [3] DDMMAAAA → YYYY-MM-DD
    dt_fin: str         # [4]
    nome: str           # [5]
    cnpj: str           # [6] — 14 dígitos
    uf: str             # [7]
    cod_mun: str        # [9]
    ind_fin_esc: str    # [14] — 0=Original; 1=Substituta
    ind_grande_porte: str  # [16]
    tip_ecd: str        # [17] — 0=PJ; 1=ostensiva SCP; 2=SCP
    ident_mf: str       # [19] — S=moeda funcional; N=não
    ind_mudanc_pc: str  # [22] — 0=sem mudança; 1=houve mudança
    cod_plan_ref: str   # [23]
    cod_ver: str        # derivado do I010.COD_VER_LC após parsing


@dataclass
class RegEcdI010:
    """I010 — identificação da escrituração (tipo de livro + versão do leiaute).
    Base legal: ADE Cofis 01/2026, Bloco I.
    COD_VER_LC='9.00' → Leiaute 9, vigente AC 2020+.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "I010"
    ind_esc: str        # [2] — G/R/A/B/Z
    cod_ver_lc: str     # [3] — '9.00' para Leiaute 9


@dataclass
class RegEcdC050:
    """C050 — Plano de Contas Recuperado do ano anterior (Bloco C, CLAUDE.md §16).
    Base legal: ADE Cofis 01/2026; IN RFB 2.003/2021.
    Espelha I050 da ECD imediatamente anterior. Usado para reconciliação manual
    quando 0000.IND_MUDANC_PC='1'. Não é preenchido pelo declarante — é gerado
    pelo PGE ao recuperar o arquivo anterior.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "C050"
    dt_alt: str         # [2] — DDMMAAAA → YYYY-MM-DD
    cod_nat: str        # [3]
    ind_cta: str        # [4] — S/A
    nivel: str          # [5]
    cod_cta: str        # [6] — código no plano ANTIGO
    cod_cta_sup: str    # [7]
    cta: str            # [8] — nome no plano ANTIGO


@dataclass
class RegEcdC155:
    """C155 — Detalhe dos Saldos Recuperados do ano anterior (Bloco C, CLAUDE.md §16).
    Base legal: ADE Cofis 01/2026.
    Espelha I155 da ECD anterior — saldos finais do exercício anterior.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "C155"
    cod_cta: str        # [2] — código no plano antigo
    cod_ccus: str       # [3]
    vl_sld_ini: Decimal # [4]
    ind_dc_ini: str     # [5] — D/C
    vl_sld_fin: Decimal # [6]
    ind_dc_fin: str     # [7] — D/C


@dataclass
class RegEcdI050:
    """I050 — Plano de Contas (âncora do cruzamento ECD×EFD, CLAUDE.md §7.6).
    Base legal: CTG 2001 (R3) do CFC; ADE Cofis 01/2026.
    COD_NAT: 01=Ativo; 02=Passivo; 03=PL; 04=Resultado; 05=Compensação; 09=Outras.
    IND_CTA: 'S'=Sintética; 'A'=Analítica.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "I050"
    dt_alt: str         # [2] — DDMMAAAA → YYYY-MM-DD
    cod_nat: str        # [3] — natureza da conta
    ind_cta: str        # [4] — S/A
    nivel: str          # [5]
    cod_cta: str        # [6] — chave universal
    cod_cta_sup: str    # [7]
    cta: str            # [8] — nome


@dataclass
class RegEcdI150:
    """I150 — Identificação do Período para Saldos (pai do I155).
    Base legal: ADE Cofis 01/2026.
    Um I150 por mês (quando IND_ESC=G/R) ou por período de balancete.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "I150"
    dt_ini: str         # [2] — YYYY-MM-DD
    dt_fin: str         # [3] — YYYY-MM-DD


@dataclass
class RegEcdI155:
    """I155 — Detalhe dos Saldos Periódicos (filho de I150).
    Base legal: ADE Cofis 01/2026.
    VL_SLD_FIN com IND_DC_FIN → saldo final do período para a conta.
    CR-38: soma de I155 para COD_NAT='04' (resultado) × M200.VL_REC_BRT_TOTAL.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "I155"
    i150_linha_arquivo: int   # FK rastreabilidade ao I150 pai
    cod_cta: str        # [2] — chave de join com I050 e EFD
    cod_ccus: str       # [3] — centro de custo (pode ser vazio)
    vl_sld_ini: Decimal # [4]
    ind_dc_ini: str     # [5] — D/C
    vl_deb: Decimal     # [6]
    vl_cred: Decimal    # [7]
    vl_sld_fin: Decimal # [8]
    ind_dc_fin: str     # [9] — D/C


@dataclass
class RegEcdI200:
    """I200 — Lançamento Contábil (pai de I250 partidas).
    Base legal: ADE Cofis 01/2026; ITG 2000 (R1) do CFC.
    IND_LCTO: 'N'=normal; 'E'=ajuste extemporâneo (Leiaute ≤8); 'X'=extemporâneo ITG 2000 R1 (Leiaute 9+).
    CR-41: IND_LCTO='X' → verificar contrapartida em 1100/1500 da EFD-Contrib.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "I200"
    num_lcto: str       # [2] — número do lançamento
    dt_lcto: str        # [3] — DDMMAAAA → YYYY-MM-DD
    vl_lcto: Decimal    # [4]
    ind_lcto: str       # [5] — N/E/X
    dt_lcto_ext: str    # [6] — data do fato original (se extemporâneo)


@dataclass
class RegEcdJ005:
    """J005 — Identificação da Demonstração Contábil (pai de J100/J150).
    Base legal: ADE Cofis 01/2026.
    ID_DEM: '01'=BP; '02'=DRE; '03'=DRE sem resultado do exercício; etc.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "J005"
    dt_ini: str         # [2] — YYYY-MM-DD
    dt_fin: str         # [3] — YYYY-MM-DD
    id_dem: str         # [4] — tipo de demonstração


@dataclass
class RegEcdJ150:
    """J150 — Detalhe da DRE / Demonstração de Resultado (filho de J005).
    Base legal: ADE Cofis 01/2026; Lei 6.404/1976 arts. 187-189.
    IND_GRP_DRE: agrupa linhas da DRE por natureza econômica.
    CR-39: linhas de receita financeira/aluguel/ganho de capital × M210/M610 EFD.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "J150"
    j005_linha_arquivo: int   # FK rastreabilidade ao J005 pai
    nu_ordem: str       # [2]
    cod_agl: str        # [3] — código de aglutinação
    ind_cod_agl: str    # [4]
    nivel_agl: str      # [5]
    cod_agl_sup: str    # [6]
    descr_cod_agl: str  # [7]
    vl_cta_ini: Decimal # [8] — valor início do período
    ind_dc_ini: str     # [9] — D/C
    vl_cta_fin: Decimal # [10] — valor fim do período
    ind_dc_fin: str     # [11] — D/C
    ind_grp_dre: str    # [12] — grupo DRE


# ============================================================
# Sprint 8 — ECF (Leiaute 12, AC 2025)
# ============================================================

@dataclass
class RegEcf0000:
    """0000 — Abertura do arquivo ECF.
    Base legal: ADE Cofis 02/2026 — Manual Leiaute 12 da ECF.
    Campos-chave: COD_VER (discriminador de versão), CNPJ, DT_INI/DT_FIN.
    TIP_ESC_PRE em 0010 indica se há ECD associada (C) ou Livro Caixa (L).
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "0000"
    cod_ver: str        # [3] — versão do leiaute (0012 para AC 2025)
    cnpj: str           # [4] — CNPJ do declarante
    nome: str           # [5] — nome empresarial
    ind_sit_ini_per: str  # [6]
    sit_especial: str   # [7]
    dt_ini: str         # [10] — YYYY-MM-DD
    dt_fin: str         # [11] — YYYY-MM-DD
    retificadora: str   # [12] — N/S/F
    tip_ecf: str        # [14] — 0=normal; 1=sócio ostensivo; 2=SCP


@dataclass
class RegEcf0010:
    """0010 — Parâmetros de Tributação (discriminador central da ECF).
    Base legal: ADE Cofis 02/2026; IN RFB 2.004/2021.
    FORMA_TRIB: 1=Lucro Real; 5=Presumido; 8=Imune; 9=Isenta.
    TIP_ESC_PRE: C=recupera ECD; L=Livro Caixa (sem ECD → disponibilidade_ecd=estruturalmente_ausente).
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "0010"
    forma_trib: str     # [4] — regime tributário
    forma_apur: str     # [5] — T=trimestral; A=anual
    cod_qualif_pj: str  # [6] — 01=Geral; 02=Financeira; 03=Seguradora
    tip_esc_pre: str    # [9] — C ou L


@dataclass
class RegEcfK155:
    """K155 — Saldos contábeis patrimoniais pós-encerramento.
    Base legal: ADE Cofis 02/2026 §10; REGRA_COMPATIBILIDADE_K155_E155.
    COD_NAT permitido: 01 (Ativo), 02 (Passivo), 03 (PL).
    CR-43: K155.VL_SLD_FIN × ECD I155.VL_SLD_FIN para COD_CTA coincidentes.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "K155"
    cod_cta: str        # [2] — conta analítica patrimonial
    cod_ccus: str       # [3] — centro de custos
    vl_sld_ini: Decimal # [4]
    ind_vl_sld_ini: str # [5] — D/C
    vl_deb: Decimal     # [6]
    vl_cred: Decimal    # [7]
    vl_sld_fin: Decimal # [8]
    ind_vl_sld_fin: str # [9] — D/C


@dataclass
class RegEcfK355:
    """K355 — Saldos finais das contas de resultado antes do encerramento.
    Base legal: ADE Cofis 02/2026 §10.3.
    COD_NAT permitido: 04 (Resultado).
    CR-43: K355 × ECD I155 para contas de resultado (COD_NAT=04).
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "K355"
    cod_cta: str        # [2]
    cod_ccus: str       # [3]
    vl_sld_ini: Decimal # [4]
    ind_vl_sld_ini: str # [5]
    vl_deb: Decimal     # [6]
    vl_cred: Decimal    # [7]
    vl_sld_fin: Decimal # [8]
    ind_vl_sld_fin: str # [9]


@dataclass
class RegEcfM300:
    """M300 — Lançamentos da Parte A do e-Lalur (IRPJ).
    Base legal: Lei 12.973/2014; IN RFB 1.700/2017; ADE Cofis 02/2026 §12.2.
    TIPO_LANCAMENTO: A=Adição; E=Exclusão; P=Compensação; L=Lucro (rótulo).
    IND_RELACAO: 1=Parte B; 2=conta contábil; 3=ambos; 4=sem relação.
    CR-44: IND_RELACAO=2/3 → deve ter M310/M312 vinculando ao NUM_LCTO da ECD I200.
    CR-46: TIPO_LANCAMENTO='E' (exclusões) cruzadas com X480/X485.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str                # "M300"
    codigo: str             # [2] — código tabela dinâmica M300A/R/B/C
    descricao: str          # [3]
    tipo_lancamento: str    # [4] — A/E/P/L
    ind_relacao: str        # [5]
    valor: Decimal          # [6]
    hist_lan_lal: str       # [7]


@dataclass
class RegEcfM312:
    """M312 — Número de lançamento contábil (ECD) vinculado a M310.
    Base legal: ADE Cofis 02/2026 §12.5; ITG 2000 (R1) do CFC.
    NUM_LCTO deve corresponder a I200.NUM_LCTO da ECD do mesmo período.
    CR-44: rastreabilidade M300 → M310 → M312 → I200 (lançamento do Diário).
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "M312"
    m300_linha_arquivo: int  # FK rastreabilidade ao M300 avô
    num_lcto: str       # [2] — número do lançamento


@dataclass
class RegEcfM350:
    """M350 — Lançamentos da Parte A do e-Lacs (CSLL).
    Base legal: Lei 12.973/2014; IN RFB 1.700/2017; ADE Cofis 02/2026 §12.6.
    Espelho do M300 para CSLL — tabelas dinâmicas M350A/R/B/C são distintas.
    CR-44/CR-46: mesma lógica do M300 mas para CSLL.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    codigo: str
    descricao: str
    tipo_lancamento: str
    ind_relacao: str
    valor: Decimal
    hist_lan_lal: str


@dataclass
class RegEcfM362:
    """M362 — Número de lançamento contábil vinculado a M360 (e-Lacs/CSLL).
    Espelho do M312 para CSLL.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str
    m350_linha_arquivo: int
    num_lcto: str


@dataclass
class RegEcfM500:
    """M500 — Controle de saldos das contas da Parte B do e-Lalur/e-Lacs.
    Base legal: Lei 12.973/2014 art. 8º; IN RFB 1.700/2017; Lei 9.065/1995 art. 15.
    COD_TRIBUTO: I=IRPJ; C=CSLL.
    IND_SD_FIM_LAL: D=exclusão futura; C=adição futura.
    CR-45: SD_FIM_LAL > threshold + VL_LCTO_PARTE_A=0 + VL_LCTO_PARTE_B=0 → conta estagnada.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str                    # "M500"
    cod_cta_b: str              # [2] — conta Parte B (ref. M010.COD_CTA_B)
    cod_tributo: str            # [3] — I ou C
    sd_ini_lal: Decimal         # [4]
    ind_sd_ini_lal: str         # [5] — D/C
    vl_lcto_parte_a: Decimal    # [6]
    ind_vl_lcto_parte_a: str    # [7]
    vl_lcto_parte_b: Decimal    # [8]
    ind_vl_lcto_parte_b: str    # [9]
    sd_fim_lal: Decimal         # [10]
    ind_sd_fim_lal: str         # [11] — D/C


@dataclass
class RegEcfX460:
    """X460 — Inovação tecnológica (Lei do Bem).
    Base legal: Lei 11.196/2005 (Lei do Bem) — arts. 17 a 26 (incentivos à
    inovação tecnológica); Decreto 5.798/2006 regulamentador; ADE Cofis 02/2026 §20.
    Cada linha registra um dispêndio classificado por CODIGO da tabela dinâmica X460.
    CR-49: X460 com valor > 0 deve gerar exclusão correspondente no M300 (30%-60%
    dos dispêndios, conforme categoria). Ausência = crédito não aproveitado.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "X460"
    codigo: str         # [2] — tabela dinâmica X460 (categoria de dispêndio P&D)
    descricao: str      # [3] — descrição do dispêndio
    valor: Decimal      # [4] — valor do dispêndio declarado


@dataclass
class RegEcfX480:
    """X480 — Benefícios Fiscais Parte I (declarados pelo contribuinte).
    Base legal: ADE Cofis 02/2026 §20; Lei 11.196/2005 (Lei do Bem) e outras.
    CODIGO: tabela dinâmica X480 — cada código é um benefício específico.
    CR-46: X480 com valor > 0 deve ter contrapartida em M300 com TIPO_LANCAMENTO='E'.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "X480"
    codigo: str         # [2] — código tabela dinâmica X480
    descricao: str      # [3]
    valor: Decimal      # [4]
    ind_valor: str      # [5] — D/C


@dataclass
class RegEcfY570:
    """Y570 — Demonstrativo do IRRF e CSLL Retidos na Fonte.
    Base legal: Lei 9.430/1996; IN RFB 1.700/2017 — retenções na fonte.
    CR-47: somatório de retenções não compensadas → oportunidade de aproveitamento.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "Y570"
    per_apu: str        # [2] — período de apuração (MMAAAA ou AAAAMMDD)
    nat_rend: str       # [3] — natureza do rendimento
    vl_ir_ret: Decimal  # [4] — IRRF retido
    vl_csll_ret: Decimal  # [5] — CSLL retida na fonte (CSRF)


@dataclass
class RegEcf9100:
    """9100 — Avisos da escrituração emitidos pelo PGE (ECF layout §22.1).
    Cada aviso é uma inconsistência reconhecida pelo próprio PGE da RFB durante
    a validação do arquivo (REGRA_COMPATIBILIDADE_K155_E155, REGRA_LINHA_DESPREZADA etc.).
    Diferente dos erros, avisos não impedem a transmissão mas sinalizam baixa
    qualidade fiscal e maior probabilidade de créditos não aproveitados.
    CR-48: cada 9100 é emitido como Divergencia para contextualizar diagnóstico.
    """
    linha_arquivo: int
    arquivo_origem: str
    reg: str            # "9100"
    cod_aviso: str      # [2] — código do aviso (ex: "REGRA_LINHA_DESPREZADA")
    descr_aviso: str    # [3] — descrição humana do aviso
    reg_ref: str        # [4] — registro referenciado pelo aviso (ex: "M300")
    campo_ref: str      # [5] — campo específico impactado (pode ser vazio)
