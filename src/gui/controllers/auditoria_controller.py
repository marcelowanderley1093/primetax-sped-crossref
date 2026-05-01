"""
AuditoriaController — leitura forense da tabela _importacoes.

Expõe ao T8 a trilha completa de importações de SPED para um cliente
× ano-calendário, com detecção automática de REIMPORT (mesmo
sped_tipo + dt_ini + dt_fin, mas hash diferente do anterior).

Operações são síncronas — `_importacoes` raramente passa de algumas
dezenas de linhas por cliente×AC. Não justifica QThread.

Decisão #21 (CLAUDE.md GUI Bloco 6): export CSV + .sha256 companheiro
para integridade. Esta iteração entrega o CSV e o SHA — assinatura
digital com certificado A1 fica fora do escopo.
"""

from __future__ import annotations

import csv
import hashlib
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


_LABELS_TIPO = {
    "efd_contribuicoes": "EFD-Contribuições",
    "efd_icms": "EFD ICMS/IPI",
    "efd_icms_ipi": "EFD ICMS/IPI",
    "ecd": "ECD",
    "ecf": "ECF",
}


@dataclass
class ImportacaoRow:
    """Linha exibida em T8 — uma importação registrada."""
    id: int
    sped_tipo: str
    sped_label: str               # rótulo amigável (ex: "EFD-Contrib")
    dt_ini: str                   # YYYY-MM-DD
    dt_fin: str
    ano_mes: int
    arquivo_origem: str           # path absoluto
    arquivo_nome: str             # só nome
    arquivo_hash: str             # SHA-256
    importado_em: datetime | None
    cod_ver: str
    encoding_origem: str
    encoding_confianca: str
    status: str                   # "ok", "rejeitado", "parcial"
    is_reimport: bool             # True se hash diferente de import anterior
    hash_anterior: str | None     # se REIMPORT: hash que estava antes


class AuditoriaController:
    """Leitura síncrona de _importacoes para um cliente × AC.

    Não recebe Repositorio diretamente para evitar dependência circular —
    abre conexão SQLite no caminho conhecido (data/db/{cnpj}/{ano}.sqlite)
    via mesmo padrão dos outros controllers.
    """

    def __init__(
        self,
        cnpj: str,
        ano_calendario: int,
        base_dir: Path = Path("data/db"),
    ) -> None:
        self._cnpj = cnpj
        self._ano = ano_calendario
        self._caminho = base_dir / cnpj / f"{ano_calendario}.sqlite"

    # ------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------

    def listar_importacoes(self) -> list[ImportacaoRow]:
        """Retorna todas as importações ordenadas por timestamp DESC.

        Para cada linha, calcula `is_reimport`: True quando há entrada
        anterior (mais antiga) com mesmo (sped_tipo, dt_ini, dt_fin, ano_mes)
        cujo arquivo_hash é diferente do atual.
        """
        if not self._caminho.exists():
            return []

        conn = sqlite3.connect(self._caminho)
        conn.row_factory = sqlite3.Row
        try:
            try:
                cur = conn.execute(
                    "SELECT * FROM _importacoes ORDER BY importado_em DESC, id DESC"
                )
                raw = [dict(r) for r in cur]
            except sqlite3.OperationalError:
                # Tabela ainda não existe — banco antes da decisão #16/#21
                return []
        finally:
            conn.close()

        # Pré-mapa dos hashes mais antigos por chave para detecção de REIMPORT
        chave_para_hashes: dict[tuple, list[tuple[str, str]]] = {}
        for r in sorted(raw, key=lambda x: x.get("importado_em") or ""):
            chave = (r["sped_tipo"], r["dt_ini"], r["dt_fin"], r["ano_mes"])
            chave_para_hashes.setdefault(chave, []).append(
                (r["arquivo_hash"], r.get("importado_em") or "")
            )

        linhas: list[ImportacaoRow] = []
        for r in raw:
            chave = (r["sped_tipo"], r["dt_ini"], r["dt_fin"], r["ano_mes"])
            historico = chave_para_hashes.get(chave, [])
            # Encontra o hash anterior (entrada mais antiga com hash diferente)
            hash_atual = r["arquivo_hash"]
            ts_atual = r.get("importado_em") or ""
            hash_anterior: str | None = None
            for h, ts in historico:
                if ts < ts_atual and h != hash_atual:
                    hash_anterior = h
            is_reimport = hash_anterior is not None

            linhas.append(ImportacaoRow(
                id=int(r["id"]),
                sped_tipo=r["sped_tipo"],
                sped_label=_LABELS_TIPO.get(r["sped_tipo"], r["sped_tipo"]),
                dt_ini=r["dt_ini"],
                dt_fin=r["dt_fin"],
                ano_mes=int(r["ano_mes"]),
                arquivo_origem=r["arquivo_origem"],
                arquivo_nome=Path(r["arquivo_origem"]).name,
                arquivo_hash=hash_atual,
                importado_em=self._parse_iso(r.get("importado_em")),
                cod_ver=r.get("cod_ver", ""),
                encoding_origem=r.get("encoding_origem", ""),
                encoding_confianca=r.get("encoding_confianca", ""),
                status=r.get("status", ""),
                is_reimport=is_reimport,
                hash_anterior=hash_anterior,
            ))
        return linhas

    # ------------------------------------------------------------
    # Export CSV + SHA256 companheiro (decisão #21)
    # ------------------------------------------------------------

    def exportar_csv(self, destino_csv: Path) -> Path:
        """Grava CSV da trilha + arquivo .sha256 companheiro com hash do CSV.

        Retorna o caminho do CSV.
        """
        linhas = self.listar_importacoes()

        destino_csv.parent.mkdir(parents=True, exist_ok=True)
        with destino_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id", "sped_tipo", "dt_ini", "dt_fin", "ano_mes",
                "arquivo_origem", "arquivo_hash", "importado_em",
                "cod_ver", "encoding_origem", "encoding_confianca",
                "status", "is_reimport", "hash_anterior",
            ])
            for l in linhas:
                writer.writerow([
                    l.id, l.sped_tipo, l.dt_ini, l.dt_fin, l.ano_mes,
                    l.arquivo_origem, l.arquivo_hash,
                    l.importado_em.isoformat() if l.importado_em else "",
                    l.cod_ver, l.encoding_origem, l.encoding_confianca,
                    l.status,
                    "true" if l.is_reimport else "false",
                    l.hash_anterior or "",
                ])

        # SHA-256 do CSV recém-gerado
        sha = hashlib.sha256(destino_csv.read_bytes()).hexdigest()
        destino_sha = destino_csv.with_suffix(destino_csv.suffix + ".sha256")
        destino_sha.write_text(
            f"{sha}  {destino_csv.name}\n", encoding="utf-8",
        )
        return destino_csv

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    @staticmethod
    def _parse_iso(s: str | None) -> datetime | None:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
