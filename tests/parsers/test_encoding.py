"""
Testes da política de detecção de encoding.

Foco: Passo 0 (truncamento em |9999|) introduzido após bench
Norte Geradores que descobriu rejeição indevida de arquivos PVA-signed.

Não cobre os 5 cenários canônicos (UTF-8 alto, Latin1 validado,
suspeito, CNPJ corrompido, token corrompido) — esses ficam como
débito separado, fora do escopo deste porte.
"""

from __future__ import annotations

from pathlib import Path

from src.parsers.common.encoding import truncar_em_9999, detectar_encoding


class TestTruncamentoEm9999:
    """Passo 0 da §7.2.1: descarte do blob pós-9999 (assinatura PVA)."""

    def test_arquivo_sem_assinatura_passa_intocado(self) -> None:
        # SPED limpo sem nada após 9999 - retorna idêntico (com newline final).
        conteudo = "|0000|006|0|...|\r\n|9999|2|\r\n"
        truncado = truncar_em_9999(conteudo)
        assert truncado == conteudo

    def test_arquivo_sem_9999_retorna_intocado(self) -> None:
        # Verificações reportarão separadamente a ausência do 9999.
        conteudo = "|0000|006|0|...|\r\n|0001|0|\r\n"
        truncado = truncar_em_9999(conteudo)
        assert truncado == conteudo

    def test_arquivo_com_blob_apos_9999_e_truncado(self) -> None:
        # Bytes binários após 9999 são removidos.
        sped = "|0000|006|0|...|\r\n|9999|2|\r\n"
        blob = "BLOB\x0b|fake|register|\x0c\x00\x00"
        truncado = truncar_em_9999(sped + blob)
        assert truncado == sped
        assert "BLOB" not in truncado
        assert "fake" not in truncado

    def test_arquivo_com_assinatura_pva_detecta_latin1_validado(
        self, caminho_sped_com_assinatura_pva: Path
    ) -> None:
        # Cenário integrado: arquivo + blob sintético — detector deve passar
        # como latin1/validado (não suspeito) graças ao truncamento.
        resultado = detectar_encoding(caminho_sped_com_assinatura_pva)
        assert resultado.encoding == "latin1"
        assert resultado.confianca == "validado"

    def test_truncamento_preserva_lf_apenas(self) -> None:
        # Arquivos podem ter \n sozinho (sem CR) — terminador deve ser preservado.
        conteudo = "|0000|...|\n|9999|1|\nBLOB"
        truncado = truncar_em_9999(conteudo)
        assert truncado == "|0000|...|\n|9999|1|\n"

    def test_truncamento_em_eof_sem_newline(self) -> None:
        # Arquivo termina exatamente em |9999|N| sem \r\n — permitido.
        conteudo = "|0000|...|\r\n|9999|1|"
        truncado = truncar_em_9999(conteudo)
        assert truncado == conteudo
