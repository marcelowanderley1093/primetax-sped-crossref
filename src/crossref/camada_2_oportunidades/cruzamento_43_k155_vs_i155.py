"""CR-43 — K155/K355 (ECF) × I155 (ECD): consistência de saldos contábeis.

Base legal:
  Lei 12.973/2014 (art. 8º e seguintes) — convergência ECF-ECD: os saldos contábeis
  que alimentam a ECF (Bloco K) devem ser idênticos aos saldos da ECD (I155) para
  o mesmo período e conta. Divergência não justificada por K915/K935 é erro estrutural.
  REGRA_COMPATIBILIDADE_K155_E155 do PGE RFB valida essa consistência internamente;
  o cruzamento Primetax a detecta preventivamente antes da transmissão.
  ADE Cofis 02/2026 §10: K155 (patrimonial, COD_NAT 01/02/03 pós-encerramento),
  K355 (resultado, COD_NAT 04 antes do encerramento).
  Vigência: desde AC 2014 (criação da ECF pela Lei 12.973/2014).

Lógica:
  Modo integral (reconciliacao='integra'):
    1. Carrega K155+K355 da ECF (saldos finais por COD_CTA).
    2. Carrega I155 da ECD (saldos finais por COD_CTA, sinalizados D/C).
    3. Para cada conta presente em ambos, compara VL_SLD_FIN.
    4. Divergência proporcional > 1% → Divergencia por conta.

  Modo degradado (reconciliacao='suspeita' ou 'ausente', §16.3):
    1. Agrega saldos ECF por COD_NAT (usando plano combinado I050 ∪ C050).
    2. Agrega saldos ECD por COD_NAT (idem).
    3. Compara totais por natureza. Divergência > 1% → Divergencia por natureza.

Dependência: ecd, ecf (CLAUDE.md §18).
modo_degradado_suportado: True (CLAUDE.md §16.3).
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias
from src.crossref.common.reconciliacao_plano_contas import (
    agregar_por_natureza,
    classificar_reconciliacao,
    consultar_plano_contas_combinado,
)

CODIGO_REGRA = "CR-43"
MODO_DEGRADADO_SUPORTADO = True
_THRESHOLD_DIVERGENCIA = Decimal("0.01")  # 1%


def _saldos_ecf_por_conta(registros: list[dict]) -> dict[str, Decimal]:
    """Converte K155/K355 em `{cod_cta: saldo_sinalizado}` (D negativo, C positivo)."""
    saldos: dict[str, Decimal] = {}
    for r in registros:
        cta = r.get("cod_cta", "")
        if not cta:
            continue
        vl = Decimal(str(r.get("vl_sld_fin") or 0))
        ind = r.get("ind_vl_sld_fin", "C")
        saldo = -vl if ind == "D" else vl
        saldos[cta] = saldos.get(cta, Decimal("0")) + saldo
    return saldos


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Divergencia

    disp = verificar_dependencias(repo, conn, ["ecf", "ecd"])
    if disp["ecf"] != "importada" or disp["ecd"] != "importada":
        return [], []

    k155 = repo.consultar_ecf_k155(conn, cnpj, ano_calendario)
    k355 = repo.consultar_ecf_k355(conn, cnpj, ano_calendario)
    saldos_ecf = _saldos_ecf_por_conta(k155 + k355)
    if not saldos_ecf:
        return [], []

    saldos_ecd = repo.consultar_ecd_i155_fin_por_conta(conn, cnpj, ano_calendario)
    if not saldos_ecd:
        return [], []

    reconc = classificar_reconciliacao(repo, conn, cnpj, ano_calendario)
    modo_degradado = reconc in ("suspeita", "ausente")

    if modo_degradado:
        return _executar_degradado(
            cnpj, ano_calendario, saldos_ecf, saldos_ecd, reconc, repo, conn
        )
    return _executar_integral(
        cnpj, ano_calendario, saldos_ecf, saldos_ecd, reconc
    )


def _executar_integral(
    cnpj: str,
    ano_calendario: int,
    saldos_ecf: dict[str, Decimal],
    saldos_ecd: dict[str, Decimal],
    reconc: str,
):
    from src.models.registros import Divergencia

    divergencias = []
    for cta, saldo_ecf in saldos_ecf.items():
        if cta not in saldos_ecd:
            continue
        saldo_ecd = Decimal(str(saldos_ecd[cta]))
        diferenca = abs(saldo_ecf - saldo_ecd)
        denominador = max(abs(saldo_ecd), abs(saldo_ecf), Decimal("1"))
        if diferenca / denominador > _THRESHOLD_DIVERGENCIA:
            divergencias.append(
                Divergencia(
                    codigo_regra=CODIGO_REGRA,
                    descricao=(
                        f"Conta {cta}: saldo ECF K155/K355 = R$ {float(saldo_ecf):,.2f} "
                        f"diverge do saldo ECD I155 = R$ {float(saldo_ecd):,.2f} "
                        f"({float(diferenca / denominador) * 100:.1f}% de diferença). "
                        f"AC {ano_calendario}. Verificar se existe K915/K935 justificando."
                    ),
                    severidade="alto",
                    evidencia=[{
                        "registro": "K155/K355 × I155",
                        "campos_chave": {
                            "cod_cta": cta,
                            "saldo_ecf": float(saldo_ecf),
                            "saldo_ecd": float(saldo_ecd),
                            "diferenca": float(diferenca),
                            "ano_calendario": ano_calendario,
                            "modo_execucao": "integra",
                            "reconciliacao_plano_contas": reconc,
                        },
                    }],
                )
            )
    return [], divergencias


def _executar_degradado(
    cnpj: str,
    ano_calendario: int,
    saldos_ecf: dict[str, Decimal],
    saldos_ecd: dict[str, Decimal],
    reconc: str,
    repo,
    conn,
):
    """Agrega ambos os lados por COD_NAT e compara totais.

    Contas que não se mapeiam em nenhum plano vão para COD_NAT='99' e são
    ignoradas na comparação — preservam-se no campo `valor_nao_classificado`
    da evidência para rastreabilidade.
    """
    from src.models.registros import Divergencia

    plano = consultar_plano_contas_combinado(repo, conn, cnpj, ano_calendario)
    saldos_ecf_nat = agregar_por_natureza(saldos_ecf, plano)
    saldos_ecd_nat = agregar_por_natureza(saldos_ecd, plano)

    nao_classif_ecf = saldos_ecf_nat.pop("99", Decimal("0"))
    nao_classif_ecd = saldos_ecd_nat.pop("99", Decimal("0"))

    naturezas = set(saldos_ecf_nat) | set(saldos_ecd_nat)
    divergencias = []

    for nat in sorted(naturezas):
        saldo_ecf = saldos_ecf_nat.get(nat, Decimal("0"))
        saldo_ecd = saldos_ecd_nat.get(nat, Decimal("0"))
        diferenca = abs(saldo_ecf - saldo_ecd)
        denominador = max(abs(saldo_ecd), abs(saldo_ecf), Decimal("1"))
        if diferenca / denominador <= _THRESHOLD_DIVERGENCIA:
            continue
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=(
                    f"[modo degradado — reconciliação '{reconc}'] "
                    f"Natureza {nat}: saldo agregado ECF = R$ {float(saldo_ecf):,.2f} "
                    f"diverge do saldo agregado ECD = R$ {float(saldo_ecd):,.2f} "
                    f"({float(diferenca / denominador) * 100:.1f}% de diferença). "
                    f"AC {ano_calendario}. Reconcilie o plano de contas para análise por conta."
                ),
                severidade="alto",
                evidencia=[{
                    "registro": "K155/K355 × I155 (agregado por COD_NAT)",
                    "campos_chave": {
                        "cod_nat": nat,
                        "saldo_ecf_agregado": float(saldo_ecf),
                        "saldo_ecd_agregado": float(saldo_ecd),
                        "diferenca": float(diferenca),
                        "valor_nao_classificado_ecf": float(nao_classif_ecf),
                        "valor_nao_classificado_ecd": float(nao_classif_ecd),
                        "ano_calendario": ano_calendario,
                        "modo_execucao": "degradado",
                        "reconciliacao_plano_contas": reconc,
                    },
                }],
            )
        )
    return [], divergencias
