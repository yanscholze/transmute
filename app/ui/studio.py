"""Per-project AI conversion workspace: sources, rules, revisions and audits.

This widget orchestrates reviewed actions only. Business composition/validation
lives in studio/; secrets and HTTP construction remain in ai/.
"""
import copy
import json
import uuid
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QInputDialog, QMessageBox, QPlainTextEdit, QSplitter, QTabWidget, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from app.ai.configuration import configured_providers
from app.ai.studio import audit_payload, planning_payload, request_audit, request_plan
from app.core.catalog import rules_path
from app.storage.studio import StudioHistory
from app.studio.catalog import fingerprint, folder_tables, inventory, source_attachments
from app.studio.plan import approve, parse, review_fingerprint
from app.ui.common import GridModel, button, table, text_label
from app.ui.source_picker import SourcePicker

ROLES = ["auto", "CTP/CTR juntos", "CTP", "CTR", "OS cabeçalhos", "OS peças", "OS serviços", "produtos", "estoque", "serviços", "Documento de apoio"]


class StudioPane(QWidget):
    settings_requested = Signal()
    library_requested = Signal()

    def __init__(self, detail):
        super().__init__()
        self.detail = detail
        self.history = StudioHistory(detail.store)
        self.context, self.bound_job, self.page_offset = None, "", 0
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        self.state_label = text_label("Fontes → regras e conversa → plano aprovado → execução → auditoria.", "notice")
        box.addWidget(self.state_label)
        split = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        sources_box = QVBoxLayout(left)
        sources_box.setContentsMargins(0, 0, 6, 0)
        actions = QHBoxLayout()
        actions.addWidget(button("Pasta…", self.add_folder))
        actions.addWidget(button("Arquivos…", self.add_files))
        sources_box.addLayout(actions)
        self.sources = QTreeWidget()
        self.sources.setHeaderLabels(["Fontes e colunas"])
        self.sources.setMinimumWidth(180)
        sources_box.addWidget(self.sources, 1)
        actions = QHBoxLayout()
        actions.addWidget(button("Papel…", self.change_role))
        actions.addWidget(button("Remover", self.remove_source))
        sources_box.addLayout(actions)
        sources_box.addWidget(button("Atualizar leitura", self.scan))
        sources_box.addWidget(button("Modelos e regras da biblioteca", self.library_requested.emit))
        split.addWidget(left)
        self.tabs = QTabWidget()
        self.instructions = QPlainTextEdit()
        self.instructions.setAccessibleName("Regras em linguagem natural deste projeto")
        self.instructions.setPlaceholderText("Descreva as regras deste cliente: como distinguir CTP/CTR, quais chaves ligam OS/peças/serviços, como juntar produtos/estoque e quais saídas o ERP exige. Não é preciso escrever código ou JSON.")
        rules = QWidget()
        rules_box = QVBoxLayout(rules)
        rules_box.addWidget(text_label("Regras deste projeto", "section"))
        rules_box.addWidget(self.instructions, 1)
        rules_box.addWidget(button("Salvar instruções", self.save_instructions, True))
        self.tabs.addTab(rules, "Regras")
        chat = QWidget()
        chat_box = QVBoxLayout(chat)
        self.conversation = QTextBrowser()
        self.conversation.setOpenExternalLinks(False)
        chat_box.addWidget(self.conversation, 1)
        self.prompt = QPlainTextEdit()
        self.prompt.setAccessibleName("Mensagem para a IA sobre a conversão")
        self.prompt.setPlaceholderText("Peça uma análise ou explique uma dúvida da IA. Ex.: use Tipo=P para CTP e Tipo=R para CTR; não use o sinal do valor.")
        self.prompt.setMaximumHeight(100)
        chat_box.addWidget(self.prompt)
        self.headers = QCheckBox("Compartilhar nomes das colunas e títulos das tabelas")
        self.headers.setChecked(True)
        self.samples = QCheckBox("Incluir até 3 valores reais por coluna / saída (dados sensíveis)")
        chat_box.addWidget(self.headers)
        chat_box.addWidget(self.samples)
        chat_actions = QHBoxLayout()
        chat_actions.addWidget(button("Enviar / revisar plano", self.ask_plan, True))
        chat_actions.addWidget(button("Configurar APIs", self.settings_requested.emit))
        chat_box.addLayout(chat_actions)
        self.tabs.addTab(chat, "Conversa e histórico")
        plan_page = QWidget()
        plan_box = QVBoxLayout(plan_page)
        revisions = QHBoxLayout()
        self.revisions = QComboBox()
        revisions.addWidget(self.revisions, 1)
        revisions.addWidget(button("Abrir revisão", self.restore_revision))
        plan_box.addLayout(revisions)
        self.plan_view = QTreeWidget()
        self.plan_view.setHeaderLabels(["Plano de conversão", "Detalhe"])
        self.plan_view.setColumnWidth(0, 240)
        plan_box.addWidget(self.plan_view, 1)
        self.plan_ack = QCheckBox("Revisei destinos, filtros, junções e constantes desta revisão")
        plan_box.addWidget(self.plan_ack)
        plan_box.addWidget(button("Aprovar esta revisão", self.approve_current, True))
        self.tabs.addTab(plan_page, "Plano")
        advanced = QWidget()
        advanced_box = QVBoxLayout(advanced)
        advanced_box.addWidget(text_label("Editor opcional do plano declarativo. A IA pode preencher o plano pela conversa; nenhum código é executado.", "muted"))
        self.plan_json = QPlainTextEdit()
        self.plan_json.setAccessibleName("Plano declarativo JSON opcional")
        self.plan_json.textChanged.connect(lambda: self.plan_ack.setChecked(False))
        self.plan_json.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        advanced_box.addWidget(self.plan_json, 1)
        advanced_box.addWidget(button("Validar e salvar rascunho", self.validate_draft))
        advanced_box.addWidget(button("Copiar referências de origem e destino", self.copy_catalog))
        self.tabs.addTab(advanced, "JSON avançado")
        audit_page = QWidget()
        audit_box = QVBoxLayout(audit_page)
        self.audit = QPlainTextEdit()
        self.audit.setReadOnly(True)
        audit_box.addWidget(self.audit, 1)
        audit_actions = QHBoxLayout()
        audit_actions.addWidget(button("Auditar com IA…", self.ask_audit, True))
        audit_actions.addWidget(button("Registrar revisão", self.review_audit))
        audit_box.addLayout(audit_actions)
        self.tabs.addTab(audit_page, "Auditoria")
        results = QWidget()
        results_box = QVBoxLayout(results)
        self.result_route = QComboBox()
        self.result_route.currentIndexChanged.connect(self.load_results)
        results_box.addWidget(self.result_route)
        self.result_grid = table()
        results_box.addWidget(self.result_grid, 1)
        self.result_detail = QPlainTextEdit()
        self.result_detail.setReadOnly(True)
        self.result_detail.setMaximumHeight(95)
        self.result_detail.setAccessibleName("Origem, alterações e problemas da célula selecionada")
        results_box.addWidget(self.result_detail)
        pages = QHBoxLayout()
        pages.addWidget(button("Anterior", lambda: self.move_page(-200)))
        pages.addWidget(button("Próxima", lambda: self.move_page(200)))
        pages.addWidget(button("Corrigir célula…", self.correct_cell))
        pages.addWidget(button("Descartar correções…", self.clear_corrections))
        results_box.addLayout(pages)
        self.tabs.addTab(results, "Resultados")
        split.addWidget(self.tabs)
        split.setSizes([260, 700])
        split.setStretchFactor(1, 1)
        box.addWidget(split, 1)

    @property
    def job(self):
        return self.detail.job

    def studio(self):
        if self.job.get("mode") != "studio":
            self.detail.close_sessions()
            self.job["mode"] = "studio"
        return self.job.setdefault("studio", {"instructions": "", "sources": copy.deepcopy(self.job["attachments"]), "plan": None, "approval": None})

    def bind(self):
        if not self.job:
            return
        changed = self.bound_job != self.job["id"]
        if changed:
            self.context = self.job.get("studio", {}).get("catalog_snapshot")
            self.bound_job = self.job["id"]
            self.instructions.setPlainText(self.job.get("studio", {}).get("instructions", ""))
            self.prompt.clear()
            self.plan_ack.setChecked(False)
            self.set_plan_text(self.job.get("studio", {}).get("plan"))
        self.render_sources()
        self.render_history()
        studio = self.job.get("studio", {})
        self.render_audit()
        previous = self.result_route.currentData()
        self.result_route.blockSignals(True)
        self.result_route.clear()
        for item in self.job["attachments"]:
            if item["id"] in self.detail.sessions:
                self.result_route.addItem(item["title"], item["id"])
        self.result_route.setCurrentIndex(max(0, self.result_route.findData(previous)))
        self.result_route.blockSignals(False)
        self.load_results()
        self.state_label.setText("Plano aprovado. Execute para gerar resultados auditáveis." if studio.get("approval") else "Defina suas regras e converse com a IA. Revise o plano antes de aprovar; nenhuma sugestão executa sozinha.")
        if self.detail.sessions and studio.get("last_run"):
            total = sum(s.stats()["read"] for s in self.detail.sessions.values())
            self.state_label.setText(f"Execução concluída: {len(self.detail.sessions)} saídas · {total} registros. Confira Resultados e Auditoria antes de exportar.")

    def dispatch(self, task, callback, label):
        # Result callbacks can chain another job before QThread.finished arrives.
        # Wait for the existing controller instead of silently dropping the call.
        job_id = self.job["id"]
        def start():
            if not self.job or self.job["id"] != job_id:
                return
            controller = getattr(self.detail.run_job, "__self__", None)
            if getattr(controller, "worker", None) is not None:
                QTimer.singleShot(30, start)
            else:
                def failed(message):
                    self.history.append(job_id, "operation_failed", {"text": message})
                    if self.job and self.job["id"] == job_id:
                        self.render_history()
                self.detail.run_job(task, callback, label, failed)
        start()

    def invalidate(self):
        self.studio()["approval"] = None
        self.plan_ack.setChecked(False)
        self.job["status"] = "Aguardando processamento"
        self.detail.close_sessions()
        self.detail.save()

    def save_instructions(self):
        studio = self.studio()
        value = self.instructions.toPlainText()
        if value != studio.get("instructions", ""):
            studio["instructions"] = value
            self.history.append(self.job["id"], "instructions", {"text": value})
            self.invalidate()

    def scan(self):
        self.dispatch(lambda control: inventory(self.detail.root, self.job, control), self.scanned, "Lendo estruturas e verificando regras…")

    def scanned(self, context):
        self.context = context
        if self.job.get("mode") == "studio":
            studio = self.studio()
            if studio.get("approval") and studio["approval"]["context_hash"] != fingerprint(context):
                studio["approval"] = None
                self.detail.close_sessions()
            self.remember_catalog(context)
            self.detail.save()
        self.render_sources()
        self.state_label.setText(f"{len(context['sources'])} tabelas de origem · {len(context['targets'])} modelos de destino · regras disponíveis.")

    def remember_catalog(self, context):
        # Display cache only. Approval/execution always re-read and hash inputs.
        self.studio()["catalog_snapshot"] = {"sources": [{k: s[k] for k in ("id", "attachment", "title", "sheet", "columns")} for s in context["sources"]],
                                             "targets": [{k: t[k] for k in ("id", "path", "title", "columns")} for t in context["targets"]]}

    def render_sources(self):
        self.sources.clear()
        entries = source_attachments(self.job)
        for entry in entries:
            role = entry.get("semantic_role", "auto")
            top = QTreeWidgetItem([entry["title"] + " · " + ("não classificada" if role == "auto" else role)])
            top.setData(0, Qt.ItemDataRole.UserRole, entry["id"])
            top.setToolTip(0, entry["path"])
            self.sources.addTopLevelItem(top)
            for source in (self.context or {}).get("sources", []):
                if source["attachment"] == entry["id"]:
                    child = QTreeWidgetItem([source["sheet"]])
                    child.setToolTip(0, source["id"])
                    top.addChild(child)
                    for column in source["columns"]:
                        field = QTreeWidgetItem([column["header"]])
                        field.setToolTip(0, column["id"])
                        child.addChild(field)
        self.sources.expandToDepth(1)

    def selected_source(self):
        node = self.sources.currentItem()
        while node and not node.data(0, Qt.ItemDataRole.UserRole):
            node = node.parent()
        return node.data(0, Qt.ItemDataRole.UserRole) if node else None

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pasta das fontes recebidas")
        if folder:
            self.dispatch(lambda control: folder_tables(folder, control), self.pick_sources, "Lendo tabelas da pasta…")

    def pick_sources(self, entries):
        dialog = SourcePicker(entries, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.add_entries(dialog.selected)

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Adicionar fontes", "", "Planilhas e PDFs (*.xlsx *.xls *.csv *.tsv *.pdf)")
        if paths:
            self.add_entries([{"path": p, "title": Path(p).stem} for p in paths])

    def add_entries(self, entries):
        studio = self.studio()
        known = {(e["path"], e.get("source_sheet", "")) for e in studio["sources"]}
        for entry in entries:
            if (entry["path"], entry.get("source_sheet", "")) not in known:
                studio["sources"].append({"id": uuid.uuid4().hex, "path": entry["path"], "title": entry["title"],
                                          "source_sheet": entry.get("source_sheet", ""), "role": "source", "family": self.job["categories"][0], "group": "principal"})
                known.add((entry["path"], entry.get("source_sheet", "")))
        self.context = None
        self.invalidate()
        self.scan()

    def remove_source(self):
        selected = self.selected_source()
        if selected:
            studio = self.studio()
            studio["sources"] = [s for s in studio["sources"] if s["id"] != selected]
            self.context = None
            self.invalidate()

    def change_role(self):
        selected = self.selected_source()
        if not selected:
            return
        role, ok = QInputDialog.getItem(self, "Papel desta fonte", "A IA recebe este papel como contexto; o plano define o destino efetivo.", ROLES, editable=False)
        if ok:
            for entry in self.studio()["sources"]:
                if entry["id"] == selected:
                    entry["semantic_role"] = role
                    entry["role"] = "reference" if role == "Documento de apoio" else "source"
            self.context = None
            self.invalidate()

    def providers(self):
        config = self.detail.store.setting("ai", {})
        if not config.get("enabled"):
            self.settings_requested.emit()
            raise ValueError("Habilite a IA e configure chave e modelo em IA e perfis. O projeto e o plano manual continuam disponíveis.")
        providers = configured_providers(config, self.detail.state)
        if not any(p.model and (getattr(p, "secret", "") or p.name == "Claude CLI") for p in providers):
            raise ValueError("Faltam modelo e credencial para os provedores selecionados. Configure-os em IA e perfis.")
        return providers

    def consent(self, data, providers):
        dialog = QDialog(self)
        dialog.setWindowTitle("Conferir envio à IA")
        dialog.resize(850, 650)
        box = QVBoxLayout(dialog)
        box.addWidget(text_label("Provedores consentidos, nesta ordem: " + ", ".join(p.name for p in providers) + ". A consulta pode consumir cota. Confira todo o conteúdo abaixo.", "notice"))
        preview = QPlainTextEdit(json.dumps(data, ensure_ascii=False, indent=2))
        preview.setReadOnly(True)
        box.addWidget(preview, 1)
        ack = QCheckBox("Autorizo o envio deste conteúdo aos provedores listados")
        box.addWidget(ack)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Enviar consulta")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        ack.toggled.connect(buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        box.addWidget(buttons)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def ask_plan(self):
        try:
            providers = self.providers()
            self.save_instructions()
            studio = self.studio()
            message = self.prompt.toPlainText().strip() or "Analise as fontes e proponha o plano. Pergunte o que faltar."
            self.history.append(self.job["id"], "user", {"text": message})
            self.detail.save()
            self.prompt.clear()
            conversation = [{"role": event["kind"], "text": event["payload"].get("text", "")} for event in self.history.list(self.job["id"])[-20:] if event["kind"] in {"user", "assistant"}]
            include_headers, samples = self.headers.isChecked(), self.samples.isChecked()
            def prepare(control):
                context = inventory(self.detail.root, self.job, control)
                data = planning_payload(context, rules_path(self.detail.root).read_text(encoding="utf-8"), headers=include_headers, samples=samples, conversation=conversation, previous_plan=studio.get("plan"))
                return context, data
            self.dispatch(prepare, lambda prepared: self.send_plan(prepared, providers), "Preparando contexto para revisão de envio…")
            self.render_history()
        except (ValueError, OSError) as error:
            self.detail.notify(str(error))

    def send_plan(self, prepared, providers):
        context, data = prepared
        self.scanned(context)
        if not self.consent(data, providers):
            return
        self.history.append(self.job["id"], "consent", {"purpose": "plan", "providers": [p.name for p in providers], "payload_sha256": fingerprint(data), "disclosure": data["disclosure"]})
        self.dispatch(lambda control: request_plan(providers, data, context, control), lambda answer: self.proposed(answer, context), "IA analisando fontes e regras…")

    def proposed(self, answer, context):
        plan, event = answer
        studio = self.studio()
        studio.update(plan=plan, approval=None, proposal_context_hash=review_fingerprint(context))
        self.remember_catalog(context)
        self.history.append(self.job["id"], "plan_revision", {"plan": plan, "context_sha256": fingerprint(context), "context": context, **event})
        self.history.append(self.job["id"], "assistant", {"text": plan["summary"] + "\n" + "\n".join("• " + q for q in plan["questions"]), **event})
        self.context = context
        self.set_plan_text(plan)
        self.invalidate()
        self.tabs.setCurrentIndex(1 if plan["questions"] else 2)

    def set_plan_text(self, plan):
        self.plan_json.setPlainText(json.dumps(plan, ensure_ascii=False, indent=2) if plan else "")
        self.plan_view.clear()
        if not plan:
            return
        sources = {s["id"]: s for s in (self.context or {}).get("sources", [])}
        targets = {t["id"]: t for t in (self.context or {}).get("targets", [])}
        def column(source_id, field):
            source = sources.get(source_id, {})
            return next((c["header"] for c in source.get("columns", []) if c["id"] == field), field)
        for output in plan["outputs"]:
            target = targets.get(output["target"], {})
            route = QTreeWidgetItem([output["title"], Path(target["path"]).name if target else "Modelo: " + output["target"]])
            self.plan_view.addTopLevelItem(route)
            for rule in output["rules"]:
                label = {"required": "Obrigatório", "digits": "Remover pontuação", "default": "Valor padrão", "uppercase": "Maiúsculas", "enum": "Valores permitidos", "length": "Comprimento", "decimal": "Formato decimal", "date": "Formato de data"}[rule["operation"]]
                detail = rule["input_format"] or rule["value"] or ", ".join(rule["values"])
                if rule["operation"] == "length":
                    detail = f"{rule['min']} a {rule['max']} caracteres"
                route.addChild(QTreeWidgetItem(["Regra: " + rule["field"], label + (" · " + detail if detail else "") + " · " + rule["severity"].lower()]))
            for entry in output["inputs"]:
                origin = sources.get(entry["source"], {})
                source = QTreeWidgetItem(["Origem", origin.get("title", entry["source"])])
                route.addChild(source)
                for condition in entry["filters"]:
                    op = {"equals": "igual a", "in": "um de", "not_in": "diferente de", "empty": "vazio", "nonempty": "preenchido"}[condition["operator"]]
                    source.addChild(QTreeWidgetItem(["Filtrar " + column(entry["source"], condition["column"]), op + " " + ", ".join(condition["values"])]))
                for join in entry["joins"]:
                    other = sources.get(join["source"], {})
                    source.addChild(QTreeWidgetItem(["Cruzar com " + other.get("title", join["alias"]), column(entry["source"], join["left"]) + " = " + column(join["source"], join["right"]) + (" · obrigatório" if join["required"] else " · opcional")]))
                for field in entry["fields"]:
                    ref = field["source"]
                    if "." in ref:
                        alias, name = ref.split(".", 1)
                        linked = next(j for j in entry["joins"] if j["alias"] == alias)
                        name = alias + " · " + column(linked["source"], name)
                    else:
                        name = column(entry["source"], ref)
                    source.addChild(QTreeWidgetItem([field["target"], "← " + name]))
                for constant in entry["constants"]:
                    source.addChild(QTreeWidgetItem(["Valor fixo: " + constant["target"], constant["value"]]))
        for question in plan["questions"]:
            self.plan_view.addTopLevelItem(QTreeWidgetItem(["Pergunta pendente", question]))
        for exclusion in plan["exclusions"]:
            node = QTreeWidgetItem(["Excluir de " + sources.get(exclusion["source"], {}).get("title", "uma fonte"), exclusion["reason"]])
            for condition in exclusion["filters"]:
                node.addChild(QTreeWidgetItem([column(exclusion["source"], condition["column"]), condition["operator"] + " " + ", ".join(condition["values"])]))
            self.plan_view.addTopLevelItem(node)
        self.plan_view.expandToDepth(1)

    def validate_draft(self):
        try:
            self.save_instructions()
            context = inventory(self.detail.root, self.job)
            plan = parse(self.plan_json.toPlainText(), context)
            self.studio().update(plan=plan, proposal_context_hash=review_fingerprint(context))
            self.remember_catalog(context)
            self.context = context
            self.history.append(self.job["id"], "plan_revision", {"plan": plan, "context_sha256": fingerprint(context), "provider": "revisão manual"})
            self.set_plan_text(plan)
            self.invalidate()
            self.state_label.setText("Rascunho válido. Confira a visão do plano e aprove esta revisão.")
            self.tabs.setCurrentIndex(2)
        except (ValueError, OSError) as error:
            self.detail.notify(str(error))

    def copy_catalog(self):
        if not self.context:
            self.state_label.setText("Use Atualizar leitura para obter as referências das tabelas.")
            return
        data = {"sources": [{k: s[k] for k in ("id", "title", "columns")} for s in self.context["sources"]],
                "targets": [{k: t[k] for k in ("id", "title", "columns")} for t in self.context["targets"]]}
        QApplication.clipboard().setText(json.dumps(data, ensure_ascii=False, indent=2))
        self.state_label.setText("Referências copiadas. O clipboard contém títulos e colunas, sem células ou caminhos.")

    def approve_current(self):
        try:
            if not self.plan_ack.isChecked():
                raise ValueError("Confirme a revisão dos destinos, filtros, junções e constantes antes de aprovar.")
            self.save_instructions()
            self.job["options"]["acknowledge_conflicts"] = True
            self.job["options"]["columns"] = self.job["options"].get("columns") or "full"
            context = inventory(self.detail.root, self.job)
            self.context = context
            plan = parse(self.plan_json.toPlainText(), context, executable=True)
            studio = self.studio()
            if studio.get("proposal_context_hash") != review_fingerprint(context):
                raise ValueError("Fontes, regras ou decisões mudaram desde a proposta. Peça uma revisão à IA ou valide o rascunho com o contexto atual antes de aprovar.")
            studio.update(plan=plan, approval=approve(plan, context))
            self.remember_catalog(context)
            self.history.append(self.job["id"], "approval", {"approval": studio["approval"], "plan": plan, "context": context, "library_rules": rules_path(self.detail.root).read_text(encoding="utf-8")})
            self.detail.save()
            self.state_label.setText("Plano aprovado. Clique em Executar plano aprovado para transformar as bases.")
        except (ValueError, OSError) as error:
            self.detail.notify(str(error))

    def render_history(self):
        self.revisions.clear()
        lines = []
        for event in self.history.list(self.job["id"]):
            data = event["payload"]
            if event["kind"] == "plan_revision":
                self.revisions.addItem(f"Revisão {event['id']} · {data.get('provider', 'local')}", data["plan"])
            if event["kind"] in {"user", "assistant", "instructions", "run", "run_failed", "audit", "approval", "audit_review", "operation_failed"}:
                content = data.get("text", data.get("summary", event["kind"]))
                lines.extend([f"{event['created']} · {event['kind']}", str(content), ""])
        self.conversation.setPlainText("\n".join(lines[-600:]))

    def render_audit(self):
        studio = self.job.get("studio", {})
        run = studio.get("last_run")
        if not run:
            self.audit.setPlainText("Execute um plano aprovado para conferir as contagens, a cobertura e os vínculos. Depois, solicite a auditoria da IA se desejar.")
            return
        lines = ["AUDITORIA DA EXECUÇÃO", "", "Fontes:"]
        for source in run["sources"].values():
            lines.append(f"• {source['file']} · {source['sheet']}: {source['rows']} registros")
        lines.extend(["", "Saídas:"])
        titles = {o["id"]: o["title"] for o in studio.get("plan", {}).get("outputs", [])}
        for oid, stats in run["outputs"].items():
            lines.append(f"• {titles.get(oid, oid)}: {stats['read']} registros · {stats['errors']} com erro · {stats['warnings']} com aviso")
            lines.extend(f"  Regra {rule}: {count} alterações" for rule, count in stats.get("transformations", {}).items())
            lines.extend(f"  Problema {code}: {count} ocorrências" for code, count in stats.get("problems", {}).items())
        lines.extend(["", f"Linhas sem destino: {run['unassigned_rows']} (qualquer linha pendente bloqueia a exportação)."])
        for item in run["exclusions"]:
            lines.append(f"Exclusão justificada: {item['rows']} linhas · {item['reason']}")
        audit = studio.get("ai_audit")
        if audit:
            lines.extend(["", "AUDITORIA IA · " + audit["provider"], audit["summary"]])
            lines.extend(f"{f['severity']} · {f['message']}" for f in audit["findings"])
            lines.extend("Pergunta: " + q for q in audit["questions"])
            lines.append("Revisão registrada: " + audit.get("review_reason", "pendente"))
        lines.extend(["", "A IA recebe contagens completas e até três amostras por saída, conforme o conteúdo autorizado. Isso não comprova conferência de cada linha pelo modelo nem aceitação do ERP."])
        self.audit.setPlainText("\n".join(lines))

    def restore_revision(self):
        plan = self.revisions.currentData()
        if plan:
            self.studio().update(plan=copy.deepcopy(plan), approval=None, proposal_context_hash=None)
            self.set_plan_text(plan)
            self.invalidate()
            self.state_label.setText("Revisão aberta como rascunho. Valide com as fontes atuais antes de aprovar.")

    def ask_audit(self):
        try:
            studio = self.studio()
            if not studio.get("last_run") or not self.detail.sessions:
                raise ValueError("Execute o plano antes de solicitar auditoria dos resultados.")
            providers = self.providers()
            data = audit_payload(studio["plan"], studio["last_run"], self.detail.sessions, samples=self.samples.isChecked())
            if self.consent(data, providers):
                self.history.append(self.job["id"], "consent", {"purpose": "audit", "providers": [p.name for p in providers], "payload_sha256": fingerprint(data), "disclosure": data["disclosure"]})
                self.dispatch(lambda control: request_audit(providers, data, control), self.audited, "IA auditando contagens e alterações…")
        except (ValueError, OSError) as error:
            self.detail.notify(str(error))

    def audited(self, answer):
        audit, event = answer
        self.studio()["ai_audit"] = {**audit, **event, "context_sha256": self.studio()["last_run"]["context_hash"], "reviewed": False}
        self.history.append(self.job["id"], "audit", {**self.studio()["ai_audit"], "text": audit["summary"]})
        self.detail.save()
        self.tabs.setCurrentIndex(4)

    def review_audit(self):
        audit = self.studio().get("ai_audit")
        if not audit:
            return
        reason, ok = QInputDialog.getText(self, "Registrar revisão da auditoria", "Como os apontamentos foram conferidos? Não altera dados nem dispensa os erros do motor.")
        if ok and reason.strip():
            audit.update(reviewed=True, review_reason=reason.strip())
            self.history.append(self.job["id"], "audit_review", {"text": reason.strip()})
            self.detail.save()

    def load_results(self):
        session = self.detail.sessions.get(self.result_route.currentData())
        self.result_rows = list(session.rows(offset=self.page_offset, limit=200)) if session else []
        self.result_fields = list(self.result_rows[0]["values"]) if self.result_rows else []
        rows = [[row["line"], row["severity"], *[row["values"].get(field, "") for field in self.result_fields]] for row in self.result_rows]
        self.result_grid.setModel(GridModel(["Linha", "Situação", *self.result_fields], rows, [r["severity"] for r in self.result_rows], parent=self.result_grid))
        self.result_grid.selectionModel().currentChanged.connect(self.describe_cell)
        self.result_detail.clear()

    def describe_cell(self, index, previous=None):
        if not index.isValid() or index.row() >= len(self.result_rows):
            return
        row = self.result_rows[index.row()]
        session = self.detail.sessions.get(self.result_route.currentData())
        origin = next(session.lineage(row["line"]), None) if session else None
        lines = []
        if origin:
            source = self.job["studio"]["last_run"]["sources"].get(origin["source_id"], {})
            lines.append(f"Origem: {source.get('file', '')} · {source.get('sheet', '')} · linha {origin['source_line']}")
        if index.column() > 1:
            field = self.result_fields[index.column() - 2]
            mapping = next((d.source for d in session.decisions if d.target == field), "") if session else ""
            lines.append("Original mapeado: " + row["raw"].get(mapping, {}).get("text", "") + " → resultado: " + row["values"].get(field, ""))
            lines.extend(c["rule"] + ": " + c["before"] + " → " + c["after"] for c in row["changes"] if c["field"] == field)
        lines.extend(i["severity"] + ": " + i["message"] for i in row["issues"])
        self.result_detail.setPlainText("\n".join(lines))

    def move_page(self, amount):
        self.page_offset = max(0, self.page_offset + amount)
        self.load_results()

    def correct_cell(self):
        index = self.result_grid.currentIndex()
        if not index.isValid() or index.column() < 2 or index.row() >= len(self.result_rows):
            return
        row = self.result_rows[index.row()]
        field = self.result_fields[index.column() - 2]
        value, ok = QInputDialog.getText(self, "Correção local", field, text=row["values"].get(field, ""))
        if ok:
            from app.studio.engine import row_identity
            session = self.detail.sessions[self.result_route.currentData()]
            origin = next(session.lineage(row["line"]))
            identity = row_identity(origin["source_id"], origin["source_line"], origin["joins"], row["raw"])
            corrections = self.studio().setdefault("corrections", {}).setdefault(self.result_route.currentData(), [])
            corrections[:] = [c for c in corrections if (c["line"], c["field"]) != (row["line"], field)]
            corrections.append({"line": row["line"], "field": field, "value": value, "origin_hash": identity})
            self.history.append(self.job["id"], "correction", {"output": self.result_route.currentData(), "line": row["line"], "field": field, "value": value})
            self.invalidate()
            self.state_label.setText("Correção salva. Aprove e execute novamente para revalidar os resultados.")

    def clear_corrections(self):
        current = self.studio().get("corrections", {})
        if not current:
            return
        if QMessageBox.question(self, "Descartar correções locais", "Retirar as correções manuais deste projeto e voltar a usar as fontes? As correções anteriores continuam registradas no histórico. As fontes não serão alteradas.", defaultButton=QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.history.append(self.job["id"], "corrections_cleared", {"corrections": copy.deepcopy(current)})
        self.studio()["corrections"] = {}
        self.invalidate()
