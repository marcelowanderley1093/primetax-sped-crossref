"""Parsers para Bloco 9 da ECF — Controle e Encerramento (9100).

Base legal: ADE Cofis 02/2026 §22.1.
9100: avisos emitidos pelo PGE da RFB na validação — cada aviso identifica
uma inconsistência reconhecida pelo próprio validador oficial.
CR-48: cada 9100 presente vira uma Divergência informativa no diagnóstico.
"""

from src.models.registros import RegEcf9100


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_9100(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcf9100:
    return RegEcf9100(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="9100",
        cod_aviso=_g(campos, 2),
        descr_aviso=_g(campos, 3),
        reg_ref=_g(campos, 4),
        campo_ref=_g(campos, 5),
    )
