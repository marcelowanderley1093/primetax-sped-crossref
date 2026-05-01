"""
ClientesController — orquestra leitura de clientes existentes em data/db/.

Para cada banco SQLite encontrado em `data/db/{cnpj}/{ano}.sqlite`:
  - abre conexão via Repositorio
  - lê _sped_contexto para detectar SPEDs disponíveis
  - lê razão social do primeiro 0000 disponível (efd_contrib → ecd → ecf)
  - calcula impacto total via crossref_oportunidades
  - lê última atividade via _importacoes

Não usa thread por enquanto — varredura é rápida o suficiente para
dezenas de clientes. Quando ficar lento, mover para QThread worker.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ClienteRow:
    """Uma linha da tabela de clientes em T1."""
    cnpj: str
    razao_social: str
    ano_calendario: int
    speds_importados: list[str]   # ["EFD-Contrib", "ECD", ...]
    impacto_total: Decimal        # somatório de oportunidades
    ultima_atividade: datetime | None
    banco_path: Path

    def cnpj_formatado(self) -> str:
        c = self.cnpj
        if len(c) != 14 or not c.isdigit():
            return c
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"


class ClientesController:
    """Orquestra a leitura da pasta data/db/."""

    def __init__(self, base_dir: Path = Path("data/db")) -> None:
        self._base_dir = base_dir

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def listar_clientes(self) -> list[ClienteRow]:
        """Varre a pasta base e retorna uma lista ordenada por última atividade."""
        if not self._base_dir.exists():
            return []

        rows: list[ClienteRow] = []
        for cnpj_dir in sorted(self._base_dir.iterdir()):
            if not cnpj_dir.is_dir():
                continue
            for sqlite_path in sorted(cnpj_dir.glob("*.sqlite")):
                try:
                    ano = int(sqlite_path.stem)
                except ValueError:
                    logger.warning("ignorando %s — nome não é ano-calendário", sqlite_path)
                    continue
                try:
                    rows.append(self._ler_cliente(cnpj_dir.name, ano, sqlite_path))
                except Exception as exc:  # noqa: BLE001
                    logger.error("erro ao ler %s: %s", sqlite_path, exc)

        # Ordena por última atividade desc; sem atividade vai para o fim.
        rows.sort(
            key=lambda r: (
                r.ultima_atividade or datetime.min,
                r.razao_social,
            ),
            reverse=True,
        )
        return rows

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _ler_cliente(self, cnpj: str, ano: int, banco: Path) -> ClienteRow:
        conn = sqlite3.connect(str(banco))
        conn.row_factory = sqlite3.Row
        try:
            return ClienteRow(
                cnpj=cnpj,
                razao_social=self._ler_razao_social(conn, cnpj, ano),
                ano_calendario=ano,
                speds_importados=self._ler_speds_disponiveis(conn, cnpj, ano),
                impacto_total=self._calcular_impacto(conn, cnpj, ano),
                ultima_atividade=self._ler_ultima_atividade(conn),
                banco_path=banco,
            )
        finally:
            conn.close()

    def _ler_razao_social(
        self, conn: sqlite3.Connection, cnpj: str, ano: int
    ) -> str:
        """Tenta ler nome da empresa de cada SPED, na ordem de prioridade."""
        for sql in (
            # EFD-Contribuições e EFD ICMS/IPI — campo 'nome'
            "SELECT nome FROM efd_contrib_0000 "
            "WHERE cnpj_declarante=? AND ano_calendario=? LIMIT 1",
            "SELECT nome FROM efd_icms_0000 "
            "WHERE cnpj_declarante=? AND ano_calendario=? LIMIT 1",
            "SELECT nome FROM ecd_0000 "
            "WHERE cnpj_declarante=? AND ano_calendario=? LIMIT 1",
            "SELECT nome FROM ecf_0000 "
            "WHERE cnpj_declarante=? AND ano_calendario=? LIMIT 1",
        ):
            try:
                row = conn.execute(sql, (cnpj, ano)).fetchone()
            except sqlite3.OperationalError:
                # Tabela não existe (banco mais antigo, schema parcial)
                continue
            if row and row[0]:
                return str(row[0]).strip()
        return "(razão social não importada)"

    def _ler_speds_disponiveis(
        self, conn: sqlite3.Connection, cnpj: str, ano: int
    ) -> list[str]:
        """Lê _sped_contexto e retorna lista de SPEDs com disponibilidade='importada'."""
        try:
            row = conn.execute(
                "SELECT * FROM _sped_contexto "
                "WHERE cnpj=? AND ano_calendario=? LIMIT 1",
                (cnpj, ano),
            ).fetchone()
        except sqlite3.OperationalError:
            return []
        if not row:
            return []

        importados = []
        mapa = {
            "disponibilidade_efd_contrib": "EFD-Contrib",
            "disponibilidade_efd_icms": "EFD-ICMS/IPI",
            "disponibilidade_ecd": "ECD",
            "disponibilidade_ecf": "ECF",
        }
        for campo, nome in mapa.items():
            try:
                if row[campo] == "importada":
                    importados.append(nome)
            except (KeyError, IndexError):
                continue
        return importados

    def _calcular_impacto(
        self, conn: sqlite3.Connection, cnpj: str, ano: int
    ) -> Decimal:
        """Soma valor_impacto_conservador das oportunidades já registradas."""
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(valor_impacto_conservador), 0) "
                "FROM crossref_oportunidades "
                "WHERE cnpj_declarante=? AND ano_calendario=?",
                (cnpj, ano),
            ).fetchone()
        except sqlite3.OperationalError:
            return Decimal("0")
        if not row or row[0] is None:
            return Decimal("0")
        return Decimal(str(row[0]))

    def _ler_ultima_atividade(
        self, conn: sqlite3.Connection
    ) -> datetime | None:
        try:
            row = conn.execute(
                "SELECT MAX(importado_em) FROM _importacoes"
            ).fetchone()
        except sqlite3.OperationalError:
            return None
        if not row or not row[0]:
            return None
        try:
            return datetime.fromisoformat(str(row[0]))
        except ValueError:
            return None
