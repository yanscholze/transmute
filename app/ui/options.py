"""Coleta escolhas e evidências por conversão; o core é quem aplica as regras."""
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from app.models import Options
from app.ui.common import text_label


class OptionsPane(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        inner = QWidget()
        box = QVBoxLayout(inner)
        box.addWidget(text_label("Regras desta importação", "section"))
        box.addWidget(text_label("A documentação e os exemplos têm diferenças. As escolhas abaixo ficam registradas no relatório.", "muted"))
        form = QFormLayout()
        self.form = form
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.columns = QComboBox()
        self.columns.addItem("Escolha a política de colunas…", "")
        self.columns.addItem("Omitir colunas totalmente vazias — regra documentada", "omit")
        self.columns.addItem("Manter todas as colunas — exceção explícita ao Markdown", "full")
        form.addRow("Colunas de saída", self.columns)
        self.active = QComboBox()
        self.active.addItem("Para clientes: aplicar ATIVO a todos nesta conversão?", "")
        self.active.addItem("Sim, aplicar ATIVO a todos os clientes", "yes")
        self.active.addItem("Não, preservar os valores da origem", "no")
        form.addRow("Classificação dos clientes", self.active)
        self.geography = QCheckBox("Conferi UF e compatibilidade com endereço/localidade")
        form.addRow("Verificação geográfica", self.geography)
        self.geo_evidence = QLineEdit()
        self.geo_evidence.setPlaceholderText("Fonte/URL e critério da conferência; corrija cada UF pendente na revisão")
        form.addRow("Evidência de UF", self.geo_evidence)
        self.oil = QLineEdit()
        self.oil.setPlaceholderText("Fonte dos CFOP ST confirmados, se houver óleos/lubrificantes")
        form.addRow("Tributação de óleos", self.oil)
        self.numeric = QCheckBox("Conferi identificadores numéricos de até 15 dígitos no original")
        form.addRow("Identificadores", self.numeric)
        self.partial = QCheckBox("Exportar parcial com até cinco registros/grupos distintos e todos os itens vinculados")
        form.addRow("Seleção de teste", self.partial)
        self.pdf_confirmed = QCheckBox("Conferi a tabela extraída com a página do PDF original")
        form.addRow("Quando houver PDF", self.pdf_confirmed)
        box.addLayout(form)
        self.conflicts = text_label("Colunas vazias podem ser omitidas conforme a regra documentada. Clientes usam ATIVO somente após sua escolha. Produtos preservam a natureza e acrescentam o código Tipo do Item. RG pode ser acrescentado sem editar os modelos. Confira essas diferenças antes de exportar.", "notice")
        box.addWidget(self.conflicts)
        self.ack = QCheckBox("Revisei as regras e confirmo as escolhas desta importação")
        box.addWidget(self.ack)
        box.addStretch()
        self.setWidget(inner)
        self.overrides = [{}, {}]

    def get(self, index=0):
        return Options(active=self.active.currentData(), columns=self.columns.currentData(), acknowledge_conflicts=self.ack.isChecked(), geography_confirmed=self.geography.isChecked(), geography_evidence=self.geo_evidence.text(), oil_cfop_evidence=self.oil.text(), numeric_identifiers_confirmed=self.numeric.isChecked(), partial=self.partial.isChecked(), pdf_confirmed=self.pdf_confirmed.isChecked(), overrides=dict(self.overrides[index]))

    def set_options(self, options):
        """Reabra decisões salvas sem marcar confirmações que não existiam."""
        for field in ["columns", "active"]:
            widget = getattr(self, field)
            widget.setCurrentIndex(max(0, widget.findData(getattr(options, field))))
        self.ack.setChecked(options.acknowledge_conflicts)
        self.geography.setChecked(options.geography_confirmed)
        self.geo_evidence.setText(options.geography_evidence)
        self.oil.setText(options.oil_cfop_evidence)
        self.numeric.setChecked(options.numeric_identifiers_confirmed)
        self.partial.setChecked(options.partial)
        self.pdf_confirmed.setChecked(options.pdf_confirmed)

    def configure_categories(self, categories, has_pdf=False):
        """Mostre apenas decisões relacionadas às tabelas escolhidas no assistente."""
        for widget, visible in [(self.active, "clientes" in categories),
                                (self.geography, bool(set(categories) & {"clientes", "fornecedores"})),
                                (self.geo_evidence, bool(set(categories) & {"clientes", "fornecedores"})),
                                (self.oil, "produtos" in categories), (self.pdf_confirmed, has_pdf)]:
            self.form.setRowVisible(widget, visible)
        messages = ["A ordem das colunas é preservada. A omissão de colunas totalmente vazias segue a política escolhida acima."]
        if "clientes" in categories:
            messages.append("ATIVO depende da sua escolha nesta importação; os exemplos usam Sim. RG será separado de IE quando identificado na origem.")
        if "produtos" in categories:
            messages.append("Produtos mantêm Tipo do item (natureza) e acrescentam Tipo do Item (código). A categoria não será inventada.")
        if has_pdf:
            messages.append("PDFs precisam de conferência visual antes da exportação; você pode fazê-la na revisão de cada arquivo.")
        self.conflicts.setText("\n\n".join(messages))
