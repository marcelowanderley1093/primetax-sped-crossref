"""Fixtures compartilhadas do pytest para o projeto Primetax SPED Cross-Reference."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def fixture_tese69_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_tese69_positivo.txt"


@pytest.fixture()
def fixture_tese69_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_tese69_negativo.txt"


@pytest.fixture()
def fixture_minimo() -> Path:
    return FIXTURES_DIR / "efd_contrib_minimo.txt"


@pytest.fixture()
def fixture_bloco9_divergencia() -> Path:
    return FIXTURES_DIR / "efd_contrib_bloco9_divergencia.txt"


@pytest.fixture()
def fixture_ecd_bloco9_divergencia() -> Path:
    return FIXTURES_DIR / "ecd_bloco9_divergencia.txt"


@pytest.fixture()
def fixture_efd_icms_bloco9_divergencia() -> Path:
    return FIXTURES_DIR / "efd_icms_bloco9_divergencia.txt"


@pytest.fixture()
def fixture_ecf_bloco9_divergencia() -> Path:
    return FIXTURES_DIR / "ecf_bloco9_divergencia.txt"


@pytest.fixture()
def fixture_apro_rateio() -> Path:
    return FIXTURES_DIR / "efd_contrib_apro_rateio.txt"


# Sprint 2 — CR-08 (C181/NFC-e)
@pytest.fixture()
def fixture_sprint2_c181_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint2_c181_positivo.txt"


@pytest.fixture()
def fixture_sprint2_c181_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint2_c181_negativo.txt"


# Sprint 2 — CR-09 (D201/transporte)
@pytest.fixture()
def fixture_sprint2_d201_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint2_d201_positivo.txt"


@pytest.fixture()
def fixture_sprint2_d201_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint2_d201_negativo.txt"


# Sprint 2 — CR-26 (M215/ajuste de base)
# positivo reutiliza fixture_tese69_positivo (sem M215, logo gap total)
@pytest.fixture()
def fixture_sprint2_m215_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint2_m215_negativo.txt"


# Sprint 3 — CR-16/17 (F600/F700 retenções)
@pytest.fixture()
def fixture_sprint3_f600_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint3_f600_positivo.txt"


@pytest.fixture()
def fixture_sprint3_f600_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint3_f600_negativo.txt"


# Sprint 3 — CR-19 (prescrição)
@pytest.fixture()
def fixture_sprint3_f600_prescrito() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint3_f600_prescrito.txt"


# Sprint 3 — CR-31 (consistência base M210)
@pytest.fixture()
def fixture_sprint3_m210_consistente() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint3_m210_consistente.txt"


@pytest.fixture()
def fixture_sprint3_m210_divergente() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint3_m210_divergente.txt"


# Sprint 4 — CR-14 (F120 depreciação)
@pytest.fixture()
def fixture_sprint4_f120_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_f120_positivo.txt"


@pytest.fixture()
def fixture_sprint4_f120_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_f120_negativo.txt"


# Sprint 4 — CR-15 (F130 aquisição imobilizado)
@pytest.fixture()
def fixture_sprint4_f130_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_f130_positivo.txt"


@pytest.fixture()
def fixture_sprint4_f130_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_f130_negativo.txt"


# Sprint 4 — CR-22 (F150 estoque de abertura)
@pytest.fixture()
def fixture_sprint4_f150_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_f150_positivo.txt"


@pytest.fixture()
def fixture_sprint4_f150_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_f150_negativo.txt"


# Sprint 4 — CR-27 (imobilizado uso vedado)
@pytest.fixture()
def fixture_sprint4_imob_vedado() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_imob_vedado.txt"


# Sprint 4 — CR-28 (rateio proporcional)
@pytest.fixture()
def fixture_sprint4_rateio_proporcional() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_rateio_proporcional.txt"


# Sprint 4 — CR-29/CR-30 (consistência M100/M200 e M500/M600)
@pytest.fixture()
def fixture_sprint4_m100_consistente() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_m100_consistente.txt"


@pytest.fixture()
def fixture_sprint4_m100_divergente() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint4_m100_divergente.txt"


# Sprint 5 — CR-10 (CST × alíquota × valor C170)
@pytest.fixture()
def fixture_sprint5_cr10_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr10_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr10_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr10_negativo.txt"


# Sprint 5 — CR-11 (TIPO_ITEM 07 com CFOP de insumo)
@pytest.fixture()
def fixture_sprint5_cr11_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr11_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr11_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr11_negativo.txt"


# Sprint 5 — CR-12 (CST 70-75 auditoria)
@pytest.fixture()
def fixture_sprint5_cr12_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr12_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr12_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr12_negativo.txt"


# Sprint 5 — CR-13 (ausência de F100)
@pytest.fixture()
def fixture_sprint5_cr13_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr13_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr13_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr13_negativo.txt"


# Sprint 5 — CR-18 (F800 evento corporativo)
@pytest.fixture()
def fixture_sprint5_cr18_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr18_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr18_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr18_negativo.txt"


# Sprint 5 — CR-20 (crédito presumido setorial)
@pytest.fixture()
def fixture_sprint5_cr20_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr20_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr20_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr20_negativo.txt"


# Sprint 5 — CR-21 (frete subcontratado)
@pytest.fixture()
def fixture_sprint5_cr21_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr21_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr21_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr21_negativo.txt"


# Sprint 5 — CR-23 (CST 98/99 imobilizado)
@pytest.fixture()
def fixture_sprint5_cr23_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr23_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr23_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr23_negativo.txt"


# Sprint 5 — CR-25 (saldo crédito 1100/1500)
@pytest.fixture()
def fixture_sprint5_cr25_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr25_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr25_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr25_negativo.txt"


# Sprint 5 — CR-32 (BC PIS crédito vs M105)
@pytest.fixture()
def fixture_sprint5_cr32_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr32_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr32_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr32_negativo.txt"


# Sprint 5 — CR-33 (BC COFINS débito vs M610)
@pytest.fixture()
def fixture_sprint5_cr33_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr33_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr33_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr33_negativo.txt"


# Sprint 5 — CR-34 (BC COFINS crédito vs M505)
@pytest.fixture()
def fixture_sprint5_cr34_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr34_positivo.txt"


@pytest.fixture()
def fixture_sprint5_cr34_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint5_cr34_negativo.txt"


# Sprint 6 — EFD ICMS/IPI (registros G125, H010, C170)
@pytest.fixture()
def fixture_sprint6_icms_cr35_202601() -> Path:
    return FIXTURES_DIR / "efd_icms_sprint6_cr35_202601.txt"


@pytest.fixture()
def fixture_sprint6_icms_cr35_202602() -> Path:
    return FIXTURES_DIR / "efd_icms_sprint6_cr35_202602.txt"


@pytest.fixture()
def fixture_sprint6_icms_cr36_202601() -> Path:
    return FIXTURES_DIR / "efd_icms_sprint6_cr36_202601.txt"


@pytest.fixture()
def fixture_sprint6_icms_cr36_202602() -> Path:
    return FIXTURES_DIR / "efd_icms_sprint6_cr36_202602.txt"


@pytest.fixture()
def fixture_sprint6_icms_cr37_202601() -> Path:
    return FIXTURES_DIR / "efd_icms_sprint6_cr37_202601.txt"


@pytest.fixture()
def fixture_sprint6_icms_cr37_202602() -> Path:
    return FIXTURES_DIR / "efd_icms_sprint6_cr37_202602.txt"


# Sprint 6 — EFD-Contribuições complementares para cruzamentos inter-SPED
@pytest.fixture()
def fixture_sprint6_contrib_minimal_202601() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint6_minimal_202601.txt"


@pytest.fixture()
def fixture_sprint6_contrib_com_f120_202602() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint6_com_f120_202602.txt"


@pytest.fixture()
def fixture_sprint6_contrib_com_f150_202602() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint6_com_f150_202602.txt"


@pytest.fixture()
def fixture_sprint6_contrib_cr37_positivo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint6_cr37_positivo.txt"


@pytest.fixture()
def fixture_sprint6_contrib_cr37_negativo() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint6_cr37_negativo.txt"


# Sprint 7 — ECD parser + cruzamentos 38-42

# CR-38: I155 (ECD) × M200 (EFD-Contrib)
@pytest.fixture()
def fixture_sprint7_ecd_cr38_positivo() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr38_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint7_ecd_cr38_negativo() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr38_negativo_2025.txt"


@pytest.fixture()
def fixture_sprint7_contrib_m200_alto() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint7_202501_m200_alto.txt"


@pytest.fixture()
def fixture_sprint7_contrib_m200_match() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint7_202501_m200_match.txt"


# CR-39: J150 (DRE-ECD) × M210 (EFD-Contrib)
@pytest.fixture()
def fixture_sprint7_ecd_cr39() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr39_2025.txt"


@pytest.fixture()
def fixture_sprint7_contrib_minimal() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint7_202501_minimal.txt"


@pytest.fixture()
def fixture_sprint7_contrib_m210_cst73() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint7_202501_m210_cst73.txt"


# CR-40: COD_CTA em C170 × I050 (ECD)
@pytest.fixture()
def fixture_sprint7_ecd_cr40_positivo() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr40_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint7_ecd_cr40_negativo() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr40_negativo_2025.txt"


@pytest.fixture()
def fixture_sprint7_contrib_c170_cta3001() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint7_202501_c170_cta3001.txt"


# CR-41: I200 extemporâneos (ECD) × 1100/1500 (EFD-Contrib)
@pytest.fixture()
def fixture_sprint7_ecd_cr41() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr41_2025.txt"


@pytest.fixture()
def fixture_sprint7_contrib_com_1100_ant() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint7_202501_com_1100_ant.txt"


# CR-42: TIPO_ITEM × COD_NAT I050 (ECD)
@pytest.fixture()
def fixture_sprint7_ecd_cr42_positivo() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr42_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint7_ecd_cr42_negativo() -> Path:
    return FIXTURES_DIR / "ecd_sprint7_cr42_negativo_2025.txt"


@pytest.fixture()
def fixture_sprint7_contrib_0200_c170() -> Path:
    return FIXTURES_DIR / "efd_contrib_sprint7_202501_0200_c170.txt"


# Sprint 8 — ECF parser + cruzamentos 43-47

# CR-43: K155/K355 (ECF) × I155 (ECD)
@pytest.fixture()
def fixture_sprint8_ecf_cr43() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr43_2025.txt"


@pytest.fixture()
def fixture_sprint8_ecd_cr43_positivo() -> Path:
    return FIXTURES_DIR / "ecd_sprint8_cr43_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint8_ecd_cr43_negativo() -> Path:
    return FIXTURES_DIR / "ecd_sprint8_cr43_negativo_2025.txt"


# CR-44: M300/M312 (ECF) × I200 (ECD)
@pytest.fixture()
def fixture_sprint8_ecf_cr44() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr44_2025.txt"


@pytest.fixture()
def fixture_sprint8_ecd_cr44_positivo() -> Path:
    return FIXTURES_DIR / "ecd_sprint8_cr44_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint8_ecd_cr44_negativo() -> Path:
    return FIXTURES_DIR / "ecd_sprint8_cr44_negativo_2025.txt"


# CR-45: M500 Parte B estagnada
@pytest.fixture()
def fixture_sprint8_ecf_cr45_positivo() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr45_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint8_ecf_cr45_negativo() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr45_negativo_2025.txt"


# CR-46: X480 × M300
@pytest.fixture()
def fixture_sprint8_ecf_cr46_positivo() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr46_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint8_ecf_cr46_negativo() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr46_negativo_2025.txt"


# CR-47: Y570 IRRF/CSRF retidos
@pytest.fixture()
def fixture_sprint8_ecf_cr47_positivo() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr47_positivo_2025.txt"


@pytest.fixture()
def fixture_sprint8_ecf_cr47_negativo() -> Path:
    return FIXTURES_DIR / "ecf_sprint8_cr47_negativo_2025.txt"


# §8.6 — Cruzamentos adicionais
@pytest.fixture()
def fixture_ecf_cr48_avisos_positivo() -> Path:
    """ECF com 2 registros 9100 → CR-48 deve emitir 2 divergências."""
    return FIXTURES_DIR / "ecf_cr48_avisos_positivo_2025.txt"


@pytest.fixture()
def fixture_ecf_cr48_avisos_negativo() -> Path:
    """ECF sem avisos → CR-48 silencioso."""
    return FIXTURES_DIR / "ecf_cr48_avisos_negativo_2025.txt"


@pytest.fixture()
def fixture_ecf_cr49_x460_positivo() -> Path:
    """ECF com X460 80K + M300 sem exclusão Lei do Bem → CR-49 dispara."""
    return FIXTURES_DIR / "ecf_cr49_x460_positivo_2025.txt"


@pytest.fixture()
def fixture_ecf_cr49_x460_negativo() -> Path:
    """ECF com X460 80K + M300 exclusão 50K (>48K estimado) → CR-49 silencioso."""
    return FIXTURES_DIR / "ecf_cr49_x460_negativo_2025.txt"


# Reconciliação de plano de contas (§16) — três estados
@pytest.fixture()
def fixture_ecd_reconciliacao_mudanc_pc() -> Path:
    """ECD com IND_MUDANC_PC=1 e Bloco C vazio → classificação 'ausente'."""
    return FIXTURES_DIR / "ecd_reconciliacao_mudanc_pc_2025.txt"


@pytest.fixture()
def fixture_ecd_reconciliacao_blococ_completo() -> Path:
    """ECD com IND_MUDANC_PC=1 e Bloco C completo (≥50% C050 + C155) → 'integra'."""
    return FIXTURES_DIR / "ecd_reconciliacao_blococ_completo_2025.txt"


@pytest.fixture()
def fixture_ecd_reconciliacao_blococ_parcial() -> Path:
    """ECD com IND_MUDANC_PC=1 e Bloco C parcial (<50% C050) → 'suspeita'."""
    return FIXTURES_DIR / "ecd_reconciliacao_blococ_parcial_2025.txt"


# Modo degradado (§16.3) — ECDs com IND_MUDANC_PC=1 sem Bloco C
@pytest.fixture()
def fixture_ecd_cr38_degradado_positivo() -> Path:
    """ECD degradada: IND_MUDANC_PC=1 + sem Bloco C + I155 receita 100K."""
    return FIXTURES_DIR / "ecd_cr38_degradado_positivo_2025.txt"


@pytest.fixture()
def fixture_ecd_cr38_degradado_negativo() -> Path:
    """ECD degradada: receita 120K (bate com M200)."""
    return FIXTURES_DIR / "ecd_cr38_degradado_negativo_2025.txt"


@pytest.fixture()
def fixture_ecd_cr39_degradado() -> Path:
    """ECD degradada para CR-39 (J150 + IND_MUDANC_PC=1)."""
    return FIXTURES_DIR / "ecd_cr39_degradado_2025.txt"


@pytest.fixture()
def fixture_ecd_cr43_degradado_positivo() -> Path:
    """ECD degradada: IND_MUDANC_PC=1 + I050 Ativo + I155 saldo 100K (ECF terá 150K)."""
    return FIXTURES_DIR / "ecd_cr43_degradado_positivo_2025.txt"


@pytest.fixture()
def fixture_ecd_cr43_degradado_negativo() -> Path:
    """ECD degradada com saldo batendo (150K × 150K) — não dispara."""
    return FIXTURES_DIR / "ecd_cr43_degradado_negativo_2025.txt"


# Encoding — assinatura PVA (Passo 0 / truncamento em |9999|)
# ASSINATURA_PVA_SINTETICA: bytes que simulam o blob PKCS#7 anexado pelo
# PVA da RFB ao final de SPEDs transmitidos. Marcador `SBRCAAEPDR` +
# ASN.1 SEQUENCE indefinido + OID signedData (1.2.840.113549.1.7.2) +
# bytes que viram strings começando com '|' quando decodificadas como
# Latin1 (caso real: bytes UTF-16LE de strings técnicas embutidas no
# envelope) + caracteres \x0b/\x0c que `splitlines()` trata como quebra.
ASSINATURA_PVA_SINTETICA: bytes = (
    b"SBRCAAEPDR"
    b"\x30\x80"  # SEQUENCE, indefinite length
    b"\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x07\x02"  # OID signedData
    b"\xa0\x80\x30\x80\x02\x01\x01"  # context [0], SET de digestAlgorithms
    b"|\x001\x00|\x005\x00.\x001\x00.\x000\x00|"
    b"\x0b" + b"|9900|FAKE|999|\x0c"
    b"\x00\x00\x00\x00"  # zeros que terminam o ASN.1 indefinite
)


@pytest.fixture()
def caminho_sped_com_assinatura_pva(tmp_path: Path, fixture_minimo: Path) -> Path:
    """SPED válido (reusa fixture_minimo) + blob simulando assinatura PVA.

    Reproduz o cenário real do bench Norte Geradores: arquivos PVA-signed
    têm ~7-8 KB de PKCS#7 SignedData anexados após o registro 9999.
    O detector deve truncar em |9999| antes das Verificações A/B/C,
    assegurando classificação como 'latin1/validado' (não 'suspeito').
    """
    arquivo = tmp_path / "efd_contribuicoes_com_assinatura_pva.txt"
    sped_bytes = fixture_minimo.read_bytes()
    arquivo.write_bytes(sped_bytes + ASSINATURA_PVA_SINTETICA)
    return arquivo
