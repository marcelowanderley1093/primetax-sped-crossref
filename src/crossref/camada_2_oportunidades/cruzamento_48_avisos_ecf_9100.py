"""CR-48 — Avisos da escrituração emitidos pelo PGE da ECF (registro 9100).

Base legal:
  ADE Cofis 02/2026 §22.1 — registro 9100 preserva avisos não-bloqueantes
  gerados pelo Programa Gerador da Escrituração (PGE) da RFB durante a
  validação do arquivo submetido. Diferentemente dos erros, avisos não
  impedem a transmissão mas sinalizam inconsistências estruturais (ex:
  REGRA_LINHA_DESPREZADA, REGRA_COMPATIBILIDADE_K155_E155) que afetam a
  qualidade fiscal do cliente.

Lógica:
  Cada 9100 importado gera uma Divergencia informativa com severidade
  'medio'. A mensagem reproduz cod_aviso + descr_aviso + registro/campo
  referenciado para que o auditor possa contextualizar o diagnóstico.

Uso esperado pela Primetax (CLAUDE.md §8.6):
  Volume alto de 9100 → qualidade fiscal baixa → maior probabilidade de
  créditos não aproveitados. Este cruzamento é informativo, não detecta
  tese específica — serve para priorizar análise manual dos clientes.

Dependência: ecf apenas (CLAUDE.md §18).
modo_degradado_suportado: N/A — cruzamento natureza-informativa.
"""

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-48"
DEPENDENCIAS_SPED = ["ecf"]


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Divergencia

    disp = verificar_dependencias(repo, conn, ["ecf"])
    if disp["ecf"] != "importada":
        return [], []

    avisos = repo.consultar_ecf_9100(conn, cnpj, ano_calendario)
    if not avisos:
        return [], []

    divergencias = []
    for aviso in avisos:
        cod = (aviso.get("cod_aviso") or "").strip()
        descr = (aviso.get("descr_aviso") or "").strip()
        reg_ref = (aviso.get("reg_ref") or "").strip()
        campo_ref = (aviso.get("campo_ref") or "").strip()

        ref_txt = reg_ref + ("." + campo_ref if campo_ref else "") if reg_ref else "—"
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=(
                    f"Aviso do PGE na transmissão da ECF: {cod or '(sem código)'} — "
                    f"{descr or '(sem descrição)'}. Referência: {ref_txt}. "
                    f"AC {ano_calendario}. Aviso não bloqueia transmissão, mas sinaliza "
                    f"inconsistência estrutural reconhecida pelo validador oficial."
                ),
                severidade="medio",
                evidencia=[{
                    "registro": "9100",
                    "arquivo": aviso.get("arquivo_origem", ""),
                    "linha": aviso.get("linha_arquivo", 0),
                    "campos_chave": {
                        "cod_aviso": cod,
                        "descr_aviso": descr,
                        "reg_ref": reg_ref,
                        "campo_ref": campo_ref,
                        "ano_calendario": ano_calendario,
                    },
                }],
            )
        )

    return [], divergencias
