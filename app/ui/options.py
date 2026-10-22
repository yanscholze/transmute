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
        box.addWidget(text_label("Decisões desta conversão", "section"))
        box.addWidget(text_label("A documentação e os exemplos têm diferenças. As escolhas abaixo ficam registradas no relatório.", "muted"))
        form = QFormLayout()
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
        box.addLayout(form)
        box.addWidget(text_label("Conflitos registrados\n\n• Omissão de colunas vazias altera o conjunto de cabeçalhos; a ordem das restantes será preservada.\n• Para clientes, a regra ATIVO só será aplicada após sua escolha; exemplos usam Sim.\n• Produtos preservam Tipo do item (natureza) e acrescentam Tipo do Item (código), conforme a regra. Categoria 00 precisa de origem confirmada.\n• RG pode ser acrescentado à saída, sem editar o modelo.\n• Campos obrigatórios não declarados não podem ser inferidos dos exemplos. A importação precisa ser testada no ERP.", "notice"))
        self.ack = QCheckBox("Li os conflitos e confirmo as decisões desta conversão")
        box.addWidget(self.ack)
        box.addStretch()
        self.setWidget(inner)
        self.overrides = [{}, {}]

    def get(self, index=0):
        return Options(active=self.active.currentData(), columns=self.columns.currentData(), acknowledge_conflicts=self.ack.isChecked(), geography_confirmed=self.geography.isChecked(), geography_evidence=self.geo_evidence.text(), oil_cfop_evidence=self.oil.text(), numeric_identifiers_confirmed=self.numeric.isChecked(), partial=self.partial.isChecked(), overrides=dict(self.overrides[index]))
