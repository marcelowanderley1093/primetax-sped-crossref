"""
DiagnosticoController — fachada de leitura + execução do diagnóstico.

Duas responsabilidades:
  1. Leitura síncrona (rápida) de dados já existentes no banco —
     oportunidades, divergências, sped_contexto. Usado para popular T3
     sem rodar o motor.
  2. Disparar o motor em thread (DiagnosticoWorker) para diagnosticar/
     rerodar; a view escuta signals para atualizar o ProgressIndicator.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import (
    Q_ARG,
    QMetaObject,
    QObject,
    Qt,
    QThread,
    Signal,
)

from src.db.repo import Repositorio
from src.gui.threading.diagnostico_worker import (
    DiagnosticoWorker,
    ResultadoDiagnostico,
)

logger = logging.getLogger(__name__)


@dataclass
class CruzamentoRow:
    """Linha agregada por código de regra para a matriz de T3."""
    codigo_regra: str
    descricao: str
    severidade: str            # "alto" | "medio" | "baixo" | "ok" | "pendente"
    achados: int               # quantidade de oportunidades/divergências
    impacto_conservador: Decimal


@dataclass
class DiagnosticoView:
    """Snapshot dos dados de diagnóstico para uma tela T3."""
    total_oportunidades: int
    total_divergencias: int
    impacto_conservador_total: Decimal
    impacto_maximo_total: Decimal
    pendencias_recuperaveis: int
    limitacoes_estruturais: int
    cruzamentos: list[CruzamentoRow] = field(default_factory=list)
    # Sinaliza se o motor encontra o que cruzar. False quando o cliente
    # × AC tem só SPEDs auxiliares (ex: EFD ICMS/IPI sem EFD-Contribuições)
    # ou nada importado. Permite que T3 explique o porquê de "0 achados".
    tem_dados_para_diagnostico: bool = False
    speds_importados: list[str] = field(default_factory=list)
    # Caso filial: se o CNPJ atual aparenta ser uma filial (não termina
    # em 0001-XX) e existe uma matriz com EFD-Contrib importada para o
    # mesmo AC em data/db/, este campo carrega o CNPJ da matriz. T3
    # usa para mostrar mensagem informativa em vez de "nada importado".
    matriz_cnpj_sugerida: str | None = None


class DiagnosticoController(QObject):
    """Fachada de leitura + execução do motor de cruzamentos."""

    diagnostico_iniciado = Signal(str, int)    # cnpj, ano
    diagnostico_log = Signal(str, str)         # level, mensagem
    diagnostico_concluido = Signal(object)     # ResultadoDiagnostico

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread = QThread()
        self._thread.setObjectName("DiagnosticoWorkerThread")
        self._worker = DiagnosticoWorker()
        self._worker.moveToThread(self._thread)

        self._worker.iniciado.connect(self.diagnostico_iniciado)
        self._worker.log_event.connect(self.diagnostico_log)
        self._worker.concluido.connect(self.diagnostico_concluido)

        self._thread.start()

    # ------------------------------------------------------------
    # Leitura síncrona — para popular T3 sem rodar motor
    # ------------------------------------------------------------

    def carregar_diagnostico(
        self, cnpj: str, ano_calendario: int
    ) -> DiagnosticoView:
        """Lê do banco SQLite existente. Não roda o motor."""
        repo = Repositorio(cnpj, ano_calendario)
        if not repo.caminho.exists():
            return DiagnosticoView(
                total_oportunidades=0, total_divergencias=0,
                impacto_conservador_total=Decimal("0"),
                impacto_maximo_total=Decimal("0"),
                pendencias_recuperaveis=0, limitacoes_estruturais=0,
                cruzamentos=[],
                tem_dados_para_diagnostico=False,
                speds_importados=[],
            )

        conn = repo.conexao()
        try:
            ops = repo.consultar_oportunidades(conn, cnpj, ano_calendario)
            divs = repo.consultar_divergencias(conn, cnpj, ano_calendario)
            ctx = repo.consultar_sped_contexto(conn) or {}
            # Detecta o que foi importado pra ajudar o T3 a explicar
            # quando "0 achados" significa "faltando EFD-Contribuições".
            tipos_importados = self._tipos_importados(conn)
        finally:
            conn.close()

        view = self._montar_view(ops, divs, ctx)
        view.speds_importados = tipos_importados
        view.tem_dados_para_diagnostico = (
            "efd_contribuicoes" in tipos_importados
            or "ecd" in tipos_importados
            or "ecf" in tipos_importados
        )
        # Filial sem EFD-Contrib + matriz com EFD-Contrib disponível?
        # T3 usa pra orientar o auditor em vez de mostrar alarme falso.
        if not view.tem_dados_para_diagnostico:
            view.matriz_cnpj_sugerida = self._localizar_matriz_com_contrib(
                cnpj, ano_calendario, repo.caminho.parent.parent,
            )
        return view

    @staticmethod
    def _tipos_importados(conn) -> list[str]:
        """Lista distinct de sped_tipo registrados em _importacoes."""
        try:
            cur = conn.execute(
                "SELECT DISTINCT sped_tipo FROM _importacoes ORDER BY sped_tipo"
            )
            return [r[0] for r in cur]
        except Exception:
            return []

    @staticmethod
    def _localizar_matriz_com_contrib(
        cnpj_atual: str, ano_calendario: int, base_dir,
    ) -> str | None:
        """Para um CNPJ filial, localiza um CNPJ matriz (mesmos 8 primeiros
        dígitos, terminação 0001-XX) com EFD-Contribuições importada para o
        mesmo AC. Retorna None quando não há filial ou não há matriz.

        Heurística por CNPJ raiz: primeiros 8 dígitos. Estabelecimento
        matriz tem ordem '0001'. Filiais têm '0002', '0003', etc.
        Não usa Receita — apenas o cadastro local de bancos importados.
        """
        if len(cnpj_atual) != 14 or not cnpj_atual.isdigit():
            return None
        ordem = cnpj_atual[8:12]
        if ordem == "0001":
            return None  # já é matriz; nada a sugerir

        cnpj_raiz = cnpj_atual[:8]
        try:
            from pathlib import Path
            import sqlite3
            base = Path(base_dir)
            for sub in sorted(base.iterdir()):
                nome = sub.name
                if (
                    not sub.is_dir()
                    or len(nome) != 14
                    or not nome.isdigit()
                    or not nome.startswith(cnpj_raiz)
                    or nome[8:12] != "0001"
                ):
                    continue
                banco = sub / f"{ano_calendario}.sqlite"
                if not banco.exists():
                    continue
                # Verifica se tem EFD-Contrib importada
                try:
                    conn = sqlite3.connect(banco)
                    try:
                        n = conn.execute(
                            "SELECT COUNT(*) FROM efd_contrib_0000"
                        ).fetchone()[0]
                    finally:
                        conn.close()
                    if n > 0:
                        return nome
                except Exception:
                    continue
        except Exception:
            return None
        return None

    # ------------------------------------------------------------
    # Disparo do motor em thread
    # ------------------------------------------------------------

    def diagnosticar(self, cnpj: str, ano_calendario: int) -> None:
        QMetaObject.invokeMethod(
            self._worker,
            "diagnosticar",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, cnpj),
            Q_ARG(int, ano_calendario),
        )

    def shutdown(self) -> None:
        self._thread.quit()
        self._thread.wait(3000)

    # ------------------------------------------------------------
    # Internos — montagem da view
    # ------------------------------------------------------------

    def _montar_view(
        self,
        oportunidades: list[dict],
        divergencias: list[dict],
        ctx: dict,
    ) -> DiagnosticoView:
        # Agregação por codigo_regra
        agg: dict[str, dict] = {}

        for o in oportunidades:
            cod = o.get("codigo_regra", "?")
            entry = agg.setdefault(cod, {
                "achados": 0,
                "impacto_cons": Decimal("0"),
                "impacto_max": Decimal("0"),
                "severidades": [],
            })
            entry["achados"] += 1
            entry["impacto_cons"] += Decimal(
                str(o.get("valor_impacto_conservador") or 0)
            )
            entry["impacto_max"] += Decimal(
                str(o.get("valor_impacto_maximo") or 0)
            )
            entry["severidades"].append(o.get("severidade", "baixo"))

        for d in divergencias:
            cod = d.get("codigo_regra", "?")
            entry = agg.setdefault(cod, {
                "achados": 0,
                "impacto_cons": Decimal("0"),
                "impacto_max": Decimal("0"),
                "severidades": [],
            })
            entry["achados"] += 1
            entry["severidades"].append(d.get("severidade", "baixo"))

        # Importa _METADATA_REGRAS para conhecer todas as 49 regras + descrições
        from src.reports.excel_diagnostico import _METADATA_REGRAS

        # Determina pendentes e estruturais a partir do _sped_contexto
        from src.reports.excel_diagnostico import _CAMPO_POR_SPED

        def estado_dep(sped_id: str) -> str:
            campo = _CAMPO_POR_SPED.get(sped_id, "")
            return ctx.get(campo) or "pendente"

        pendencias = 0
        limitacoes = 0

        cruzamentos: list[CruzamentoRow] = []
        for codigo, deps, descricao in _METADATA_REGRAS:
            estados = [estado_dep(d) for d in deps]
            if "estruturalmente_ausente" in estados:
                limitacoes += 1
                cruzamentos.append(CruzamentoRow(
                    codigo_regra=codigo,
                    descricao=descricao,
                    severidade="na",
                    achados=0,
                    impacto_conservador=Decimal("0"),
                ))
                continue
            if "pendente" in estados:
                pendencias += 1
                cruzamentos.append(CruzamentoRow(
                    codigo_regra=codigo,
                    descricao=descricao,
                    severidade="pendente",
                    achados=0,
                    impacto_conservador=Decimal("0"),
                ))
                continue
            entry = agg.get(codigo)
            if entry is None:
                cruzamentos.append(CruzamentoRow(
                    codigo_regra=codigo,
                    descricao=descricao,
                    severidade="ok",
                    achados=0,
                    impacto_conservador=Decimal("0"),
                ))
                continue
            severidade = self._severidade_dominante(entry["severidades"])
            cruzamentos.append(CruzamentoRow(
                codigo_regra=codigo,
                descricao=descricao,
                severidade=severidade,
                achados=entry["achados"],
                impacto_conservador=entry["impacto_cons"],
            ))

        total_imp_cons = sum(
            (e["impacto_cons"] for e in agg.values()), Decimal("0")
        )
        total_imp_max = sum(
            (e["impacto_max"] for e in agg.values()), Decimal("0")
        )

        return DiagnosticoView(
            total_oportunidades=len(oportunidades),
            total_divergencias=len(divergencias),
            impacto_conservador_total=total_imp_cons,
            impacto_maximo_total=total_imp_max,
            pendencias_recuperaveis=pendencias,
            limitacoes_estruturais=limitacoes,
            cruzamentos=cruzamentos,
        )

    @staticmethod
    def _severidade_dominante(severidades: list[str]) -> str:
        prioridade = {"alto": 0, "medio": 1, "baixo": 2}
        if not severidades:
            return "ok"
        return min(severidades, key=lambda s: prioridade.get(s, 3))
