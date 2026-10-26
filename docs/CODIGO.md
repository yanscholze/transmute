# Índice do código

Gerado por `scripts/document_code.py`. A árvore e os contratos são explicados em DESENVOLVIMENTO.md. Números de linha ajudam a localizar os pontos de extensão.

## app/__init__.py

Conversor de Bases.


## app/ai/__init__.py

Sugestões opcionais; sem ferramentas e sem transformação de registros.


## app/ai/cli.py

Detecção conservadora de CLI e execução só com controles confirmados.

Comandos são listas fixas, sem shell. Claude roda sem ferramentas/MCP e em
diretório vazio; Codex/Gemini permanecem detectáveis sem execução habilitada.

- `detect_clis` (linha 21)
- `CLIProvider` (linha 45)
  Métodos: `generate`:51.

## app/ai/configuration.py

Provider configuration independent of widgets; models and keys stay separate.

- `model_for` (linha 13)
- `configured_providers` (linha 17)
- `readiness` (linha 33): Presence is reported separately from an actual successful network test.

## app/ai/credentials.py

Credenciais no cofre seguro do SO ou apenas memória; nunca configuração textual.

- `Credentials` (linha 7): OS credential vault, otherwise process memory only. No plaintext fallback.
  Métodos: `__init__`:11, `get`:14, `secure`:30, `set`:34, `delete`:47.

## app/ai/environment.py

Read a developer-owned .env.local without executing it or writing secrets.

The packaged app uses OS environment/keyring. This source-only convenience
connects the secure key provisioning destination to run.py. Only known API/model
variables are accepted; PYTHONPATH, commands and unrelated settings are ignored.

- `read_environment_file` (linha 15): Pure local parser used by development startup and explicit UI import.
- `load_development_env` (linha 38)

## app/ai/providers.py

Adapters HTTP independentes, canceláveis e sem ferramentas executáveis.

Somente payload sanitizado e schema chegam aqui. Não há acesso a arquivos de
clientes; mensagens externas de erro não são registradas em log.

- `ProviderFailure` (linha 17): Safe diagnostic code; never retains a response body or secret header.
  Métodos: `__init__`:19.
- `Provider` (linha 33)
  Métodos: `generate`:34.
- `APIProvider` (linha 38)
  Métodos: `request`:45, `extract`:63, `generate`:79.

## app/ai/sanitization.py

Única fronteira de envio externo: conteúdo de célula vira estatística, nunca amostra literal.

- `shape` (linha 7): No literal cell content leaves this boundary.
- `payload` (linha 15)

## app/ai/schema.py

Schema fechado e validação local independente do fornecedor de IA.

- `schema` (linha 6)
- `parse` (linha 12)

## app/ai/service.py

Fallback somente entre provedores já consentidos; nenhuma tentativa altera dados.

- `suggestions` (linha 6)

## app/ai/studio.py

Structured planning/auditing for all API providers, with explicit payloads.

No provider can execute a recipe, read files on its own, or approve its answer.
Only this local boundary constructs the content shown in the consent dialog.

- `planning_payload` (linha 40)
- `request_plan` (linha 62)
- `audit_schema` (linha 66)
- `audit_payload` (linha 71)
- `request_audit` (linha 89)
- `structured` (linha 100)

## app/core/batch.py

Orquestra arquivos de uma importação sem misturar tabelas de famílias distintas.

Todas as abas/tabelas detectadas são representadas. Falha de arquivo não apaga
os demais e fica explícita no manifesto. Exportação valida todos os grupos
antes de publicar um diretório único, com rollback em cancelamento/erro.

- `options_from` (linha 25)
- `groups` (linha 30)
- `process_import` (linha 49)
- `export_import` (linha 121)

## app/core/catalog.py

Estrutura vem dos modelos; comportamento vem de um perfil revisado.

Uma biblioteca pode apontar a fontes externas ou a cópias importadas. Exemplos
de dados não são retornados pelo catálogo e nunca viram valores padrão.

- `digest` (linha 15): Hash incremental usado para provar que as fontes não mudaram.
- `discover` (linha 24): Leia todas as abas/modelos e preserve cabeçalhos literais e sua ordem.
- `verify_rules` (linha 54): Recuse prosa alterada sem uma revisão correspondente do perfil.
- `workspace_config` (linha 69)
- `rules_path` (linha 74)

## app/core/exporters/writer.py

Exportação textual e transacional: planejar antes, publicar só ao terminar.

Partes vinculadas compartilham grupos; quando preservar ordem e vínculo é
impossível, bloquear é mais seguro do que reorganizar silenciosamente.

- `selected_lines` (linha 26)
- `plan_parts` (linha 55): Planeje partes por grupo e prove monotonicidade em cada fonte.
- `write_workbook` (linha 94): Derive cabeçalhos/estilos do modelo e escreva dados como texto literal.
- `report_data` (linha 127)
- `save_reports` (linha 161)
- `export` (linha 183): Nunca sobrescreva fontes/saídas; em erro ou cancelamento retire o staging.

## app/core/importers/__init__.py

Leitores iteráveis; nunca alteram a origem.


## app/core/importers/pdf.py

Tabelas PDF por página e geometria; texto corrido nunca vira linha de cadastro.

Cada tabela é uma fonte distinta. A confirmação visual é exigida pelo motor
antes da exportação. PDFs sem grade reconhecível ficam pendentes, sem OCR ou
inferência de campos por proximidade de texto.

- `tables` (linha 14)
- `rows` (linha 31)

## app/core/importers/reader.py

Detecção por conteúdo e leitores que expõem posição física e tipo de origem.

CSV e XLSX são iterados; HTML tem limite explícito de tamanho. Nenhum leitor
executa fórmula ou tenta recuperar zeros que já desapareceram da fonte.

- `excel_cell` (linha 21): Converta representação sem float arithmetic, mantendo evidência de risco.
- `detect` (linha 47)
- `csv_settings` (linha 64)
- `HTMLTables` (linha 91)
  Métodos: `__init__`:92, `handle_starttag`:96, `handle_data`:110, `handle_endtag`:114.
- `html_tables` (linha 126)
- `sheets` (linha 135)
- `raw_rows` (linha 158)
- `inspect` (linha 199): Sugira estrutura a partir de amostra limitada; a UI permite corrigir a escolha.
- `records` (linha 237): Inclua linhas vazias e células excedentes para contagem e auditoria explícitas.

## app/core/mapping/__init__.py

Mapeamento determinístico: igualdade, aliases revisados e semelhança incerta.

Confiança é metadado de sugestão, não permissão para resolver conflitos.
Diferença de caixa entre os campos de natureza/código do item é significativa.

- `norm` (linha 14)
- `targets` (linha 37)
- `suggest` (linha 46)
- `validate_mapping` (linha 76): Garanta colunas existentes, destino único e confirmação de sugestões.

## app/core/rules/declarative.py

Interpretador fechado de regras: nenhum eval, Python ou comando do usuário.

Markdown é documentação; o perfil JSON explicita o comportamento determinístico.
Acrescentar uma operação exige implementá-la aqui e testar sua semântica.

- `validate_profile` (linha 17)
- `apply` (linha 47)

## app/core/session.py

Sessão de conversão em disco, com snapshots e revisão paginada.

SQLite evita uma cópia integral da base em RAM. O chamador possui a sessão e
deve fechá-la; processamento malsucedido remove o arquivo automaticamente.

- `Session` (linha 21)
  Métodos: `__init__`:22, `connect`:44, `close`:47, `rows`:50, `stats`:70, `verify`:75, `lineage`:86, `audit_counts`:93.
- `process` (linha 105)
- `validate_links` (linha 170): Cheque integridade referencial sem excluir/deduplicar nenhum registro.

## app/core/transformation/engine.py

Regras de domínio confirmadas no Markdown e trilha antes/depois.

O motor recebe apenas dados/opções, sem UI, rede ou escrita na origem. Toda
mutação de saída passa por put() para carregar uma regra identificável.

- `transform` (linha 13)

## app/core/validation/values.py

Validações objetivas, sem inventar obrigatoriedade a partir de exemplos.

Família genérica aplica apenas integridade técnica; suas regras de negócio
precisam ser declaradas. Documentos inválidos são preservados para correção.

- `identifier` (linha 17)
- `money_field` (linha 22)
- `decimal_value` (linha 27)
- `document_valid` (linha 43)
- `validate_values` (linha 54)

## app/main.py

Módulo da camada app.

- `main` (linha 18)

## app/models.py

Contratos compartilhados: não dependem de Qt, HTTP ou armazenamento.

- `Cancelled` (linha 7)
- `Control` (linha 12)
  Métodos: `check`:16.
- `Cell` (linha 22)
- `Source` (linha 29)
  Métodos: `ids`:40.
- `Layout` (linha 45)
  Métodos: `label`:54.
- `Decision` (linha 63)
- `Issue` (linha 73)
- `Change` (linha 81)
- `Options` (linha 89)

## app/paths.py

Resolve diretório portátil e estado gravável, com override explícito do operador.

- `project_root` (linha 8)
- `state_root` (linha 14)

## app/selftest.py

Teste sintético disponível também no executável distribuído, sem pytest.

- `synthetic_pdf` (linha 15): PDF mínimo com grade, sem gerador externo nem dados reais no binário.
- `run` (linha 39)

## app/storage/dashboard.py

Indicadores derivados do último estado salvo de cada trabalho.

Não contamos eventos técnicos como novas importações nem medimos aceite no ERP.
Trabalhos aguardando/interrompidos não possuem resultado concluído e ficam fora
do denominador. A ausência de resultados produz None, nunca sucesso fictício.

- `summarize` (linha 11)

## app/storage/database.py

Transação com fechamento determinístico, inclusive em erro e no Windows.

O context manager de sqlite3.Connection faz commit/rollback, mas não fecha a
conexão. closing externo evita deixar handles dependentes do coletor de lixo.

- `database` (linha 11)

## app/storage/imports.py

Importações nomeadas: referências persistentes sem duplicar bases completas.

As referências a arquivos são necessárias para reabrir uma importação. Dados
de revisão completos continuam em sessões temporárias. Correções manuais
necessárias à retomada podem conter dados pessoais e ficam no manifesto local.
A tabela nova preserva histórico,
perfis e configurações existentes na mesma base SQLite.

- `now` (linha 19)
- `ImportStore` (linha 24)
  Métodos: `__init__`:25, `create`:35, `save`:55, `get`:60, `list`:67.

## app/storage/local.py

Persistência mínima: histórico sem células, perfis estruturais e opções sem secrets.

- `LocalStore` (linha 8)
  Métodos: `__init__`:9, `connect`:19, `save_profile`:22, `profiles`:26, `delete_profile`:31, `record`:35, `history`:39, `clear_history`:43, `setting`:49, `set_setting`:54.

## app/storage/studio.py

Append-only local conversation/revision/run history; no credential storage.

- `StudioHistory` (linha 6)
  Métodos: `__init__`:7, `append`:13, `list`:19.

## app/storage/workspace.py

Biblioteca configurável. Referências externas são somente leitura.

Uploads e edições são copiados para o estado local. Cada revisão de regras é
um novo par Markdown/JSON; o ponteiro só muda depois que ambos são gravados.

- `save_config` (linha 15)
- `initialize` (linha 22)
- `import_model` (linha 63)
- `save_rule_revision` (linha 88)
- `set_brand` (linha 106)

## app/studio/__init__.py

Conversion workspace: source inventory, reviewed recipes and traceable runs.


## app/studio/catalog.py

Local source inventory. Never uploads files or confuses inputs with templates.

- `fingerprint` (linha 14)
- `folder_tables` (linha 18): List individual sheets/tables, including readable failures for the picker.
- `source_attachments` (linha 41)
- `inventory` (linha 45): Snapshot IDs bind a recipe to exact input bytes, headers and target models.

## app/studio/engine.py

Execute an approved composition locally, retaining Cell types and row lineage.

SQLite staging/indexes avoid keeping client tables in RAM. Joins are exact and
many-to-one: duplicate lookup keys fail instead of multiplying/deleting rows.
Every selected source row must be consumed or explicitly excluded with a reason.

- `cells` (linha 23)
- `reliable_key` (linha 27)
- `row_identity` (linha 33): Bind a correction to original lineage and mapped cells, not output position.
- `execute` (linha 39)
- `verify_export` (linha 205)

## app/studio/plan.py

Closed recipe language: split, concatenate and exact many-to-one lookup.

Models never provide code. Local validation checks the JSON contract AND every
source, field, alias and target reference independently of the provider.

- `obj` (linha 15)
- `arr` (linha 19)
- `text` (linha 23)
- `schema` (linha 27)
- `_check` (linha 42)
- `decode` (linha 64): Strict JSON at the trust boundary; duplicate keys cannot hide decisions.
- `parse` (linha 78)
- `_filters` (linha 135)
- `matches` (linha 143): Exact text comparison: never infer CTP/CTR from sign, case or a filename.
- `approve` (linha 155)
- `review_fingerprint` (linha 160): The review checkbox itself must not invalidate the proposal it confirms.
- `verify_approval` (linha 167)

## app/ui/ai_actions.py

Diálogo de consentimento com payload exato e aplicação de sugestões não confirmadas.

- `suggest_mapping` (linha 15)

## app/ui/appearance.py

Aparência isolada do fluxo de importação, com prévia local e logo copiada.

- `AppearancePane` (linha 16)
  Métodos: `__init__`:19, `draft`:105, `refresh`:109, `choose_color`:117, `choose_logo`:122, `load_logo`:127, `remove_logo`:140, `save`:144.

## app/ui/common.py

Tarefas em thread e tabelas de apresentação sem regras de negócio.

Erro é mostrado ao operador, mas o log contém só o tipo da exceção. O modelo
de tabela recebe apenas a página atual, sem duplicar uma base inteira.

- `Worker` (linha 17)
  Métodos: `__init__`:22, `run`:27.
- `GridModel` (linha 38)
  Métodos: `__init__`:39, `rowCount`:45, `columnCount`:48, `data`:51, `headerData`:65.
- `table` (linha 70)
- `button` (linha 82)
- `text_label` (linha 92)

## app/ui/conversion.py

Coordena o assistente e o ciclo de vida das sessões principal/vinculada.

UI coleta decisões e despacha operações ao core. Correção pendente bloqueia
exportação até revalidar; uma chamada de IA nunca escreve uma célula.

- `ConversionPane` (linha 22)
  Métodos: `__init__`:26, `release_sessions`:78, `panes`:82, `previous`:85, `advance`:89, `prepare_mapping`:111, `process`:123, `processed`:137, `correct`:155, `do_export`:162, `exported`:177, `update_step`:183, `ai_suggest`:193, `close_sessions`:198.

## app/ui/dashboard.py

Visão geral operacional: metadados reais, atalhos e fontes configuradas.

O dashboard não lê células, não processa bases e não guarda cópias do histórico.
Usa o catálogo já carregado pelo shell e o manifesto dos trabalhos. Caminhos
podem ser copiados ou abertos localmente; o editor continua na Biblioteca.

- `date_label` (linha 23)
- `decorative` (linha 30): Filhos visuais não interceptam o clique/teclado do botão que os contém.
- `PathAccess` (linha 36)
  Métodos: `__init__`:37, `configure`:59, `copy_path`:69, `open_folder`:74.
- `Dashboard` (linha 83)
  Métodos: `__init__`:84, `panel_box`:113, `link`:119, `make_recent`:124, `make_launch`:142, `make_shortcuts`:187, `row`:202, `make_models`:226, `make_rules`:241, `refresh`:256.

## app/ui/file_settings.py

Classificação de arquivo e visualizador PDF local, sem abrir navegador externo.

- `FileSettings` (linha 10)
  Métodos: `__init__`:11, `populate`:50, `browse`:58, `save`:65.
- `open_pdf` (linha 80)

## app/ui/icons.py

Ícones vetoriais locais, com traço uniforme e cores do tema.

Primitivas SVG evitam dependência de fontes, emojis ou downloads. O texto
acessível pertence ao controle que usa o ícone, nunca ao desenho decorativo.

- `icon` (linha 30): Renderize em dobro para manter linhas nítidas também em escala alta.

## app/ui/import_detail.py

Detalhes de um trabalho e ponte para o conversor existente por arquivo/lote.

O trabalho possui as sessões; editores apenas as usam enquanto estão abertos.
Revalidação substitui sessões e mantém correções manuais necessárias à retomada.

- `ImportDetail` (linha 25)
  Métodos: `__init__`:29, `set_job`:78, `refresh`:89, `selection_changed`:111, `selected`:116, `save`:120, `process_all`:125, `processing_failed`:147, `processed`:154, `recalculate_status`:163, `edit_options`:177, `rename`:203, `edit_selected`:210, `add_file`:215, `edit_item`:222, `view_pdf`:239, `review_selected`:246, `open_editor`:285, `review_processed`:323, `leave_editor`:338, `do_export`:357, `exported`:369, `close_sessions`:376.

## app/ui/import_wizard.py

Assistente: nome/categorias → arquivos classificados → regras e início.

Cada arquivo tem título, categoria e destino visíveis. Os originais são
referenciados, não movidos nem enviados a serviços externos.

- `ImportWizard` (linha 18)
  Métodos: `__init__`:22, `identification`:50, `selected_categories`:79, `file_page`:82, `browse_folder`:101, `pick_tables`:116, `browse`:127, `add_files`:131, `snapshot`:143, `render_files`:152, `populate_models`:178, `remove`:194, `previous`:201, `advance`:211, `update_step`:245, `dragEnterEvent`:254, `dropEvent`:258.

## app/ui/imports_home.py

Início centrado em trabalhos nomeados; configurações ficam em outras telas.

- `ImportsHome` (linha 8)
  Métodos: `__init__`:9, `refresh`:50, `open_selected`:65.

## app/ui/input.py

Escolha/drag and drop, opções de leitura e amostra local limitada.

Alterar leitura invalida a estrutura anterior; nada é processado com uma
prévia que corresponda a outro arquivo, aba ou encoding.

- `InputPane` (linha 16)
  Métodos: `__init__`:19, `layout`:79, `invalidate`:82, `browse`:86, `set_path`:91, `load`:100, `loaded`:113, `dragEnterEvent`:131, `dropEvent`:135.

## app/ui/library.py

Biblioteca técnica separada dos trabalhos e da aparência, sem editar fontes.

- `LibraryPane` (linha 15)
  Métodos: `__init__`:18, `refresh`:52, `reload`:77, `choose_folder`:84, `upload`:92, `family_changed`:102, `choose_rules`:108, `edit_rules`:117.

## app/ui/mapping.py

Editor de correspondências e perfis, sem transformar células.

Decisões incertas precisam de confirmação; perfis só armazenam estrutura e
ficam restritos ao fingerprint do destino para evitar reaplicação absoluta.

- `fingerprint` (linha 17)
- `MappingPane` (linha 21)
  Métodos: `__init__`:22, `render`:43, `manual`:72, `get_decisions`:80, `update_summary`:83, `save_profile`:88, `load_profile`:98.

## app/ui/navigation.py

Sidebar recolhível com navegação por teclado e preferência local persistida.

- `NavigationRail` (linha 14)
  Métodos: `__init__`:19, `toggle_expanded`:62, `set_current`:67, `apply_theme`:71, `render`:75.

## app/ui/options.py

Coleta escolhas e evidências por conversão; o core é quem aplica as regras.

- `OptionsPane` (linha 8)
  Métodos: `__init__`:9, `get`:52, `set_options`:55, `configure_categories`:68.

## app/ui/review.py

Revisão paginada: correção vira pendência até novo processamento determinístico.

- `ReviewPane` (linha 9)
  Métodos: `__init__`:10, `set_sessions`:56, `reset`:65, `turn`:69, `refresh`:75, `show_details`:93, `correct`:111.

## app/ui/settings.py

Configura provedores/cofre, testa com estrutura sintética e administra perfis locais.

- `SettingsPane` (linha 15)
  Métodos: `__init__`:16, `provider_changed`:91, `import_credentials`:99, `refresh_readiness`:122, `save`:125, `test_connection`:149, `delete_key`:163, `detect`:170, `refresh_profiles`:173, `view_profile`:179, `remove_profile`:183.

## app/ui/source_picker.py

Pick individual source tables from a directory; failures remain visible.

- `SourcePicker` (linha 8)
  Métodos: `__init__`:9, `mark`:46, `accept_selection`:51.

## app/ui/studio.py

Per-project AI conversion workspace: sources, rules, revisions and audits.

This widget orchestrates reviewed actions only. Business composition/validation
lives in studio/; secrets and HTTP construction remain in ai/.

- `StudioPane` (linha 26)
  Métodos: `__init__`:30, `job`:149, `studio`:152, `bind`:158, `dispatch`:187, `invalidate`:205, `save_instructions`:212, `scan`:220, `scanned`:223, `remember_catalog`:235, `render_sources`:240, `selected_source`:260, `add_folder`:266, `pick_sources`:271, `add_files`:276, `add_entries`:281, `remove_source`:293, `change_role`:301, `providers`:314, `consent`:324, `ask_plan`:344, `send_plan`:364, `proposed`:372, `set_plan_text`:384, `validate_draft`:434, `copy_catalog`:450, `approve_current`:459, `render_history`:480, `render_audit`:492, `restore_revision`:519, `ask_audit`:527, `audited`:540, `review_audit`:547, `load_results`:557, `describe_cell`:566, `move_page`:584, `correct_cell`:588, `clear_corrections`:607.

## app/ui/style.py

Default style for entrypoints; windows derive their palette from saved appearance.


## app/ui/surfaces.py

Superfícies suaves e texto truncável compartilhados pelo shell/dashboard.

Sombras são pintadas no próprio painel. Efeitos que cacheiam o subtree inteiro
podem recortar filhos após redimensionar/navegar; aqui somente a superfície é
desenhada, preservando a pintura normal e as hitboxes de cada controle filho.

- `SoftPanel` (linha 14)
  Métodos: `__init__`:15, `apply_theme`:23, `paintEvent`:27.
- `ElidedLabel` (linha 50): Rótulo de uma linha; mantém nome/caminho completo no tooltip e a11y.
  Métodos: `__init__`:52, `setText`:58, `render`:64, `resizeEvent`:67, `sizeHint`:71.

## app/ui/theme.py

Tema claro/escuro com acento independente e marca d'água atrás do conteúdo.

Superfícies neutras seguem a referência Soft UI. O acento colore ações, foco e
realces nos dois modos; contraste é calculado para qualquer cor configurada.

- `mix` (linha 13)
- `luminance` (linha 18)
- `contrast` (linha 24)
- `foreground` (linha 29)
- `palette` (linha 34)
- `native_palette` (linha 54): Cubra popups, indicadores e controles nativos que não usam somente QSS.
- `stylesheet` (linha 69)
- `Backdrop` (linha 153)
  Métodos: `__init__`:154, `configure`:158, `paintEvent`:164.

## app/ui/window.py

Shell Soft UI: dashboard, sidebar recolhível e páginas operacionais.

O worker único mantém cancelamento acessível. Aparência nunca reinicia uma
importação; mudanças da biblioteca exigem nova validação do trabalho.

- `Window` (linha 22)
  Métodos: `__init__`:23, `make_header`:99, `search_imports`:148, `toggle_theme`:153, `edit_rules_from_dashboard`:160, `refresh_overview`:164, `notify`:168, `navigate`:172, `configure_backdrop`:188, `new_import`:196, `cancel_wizard`:210, `import_created`:217, `open_import`:223, `apply_brand`:231, `reload_library`:255, `run_job`:278, `job_error`:302, `job_finished`:309, `cancel_job`:323, `make_history`:328, `refresh_history`:337, `closeEvent`:345.

## scripts/audit_models.py

Inventário estrutural sem reproduzir amostras pessoais.


## scripts/build.py

Build nativo e pacote portátil, sem copiar estado, secrets ou exemplos.

Execute com o Python do .venv no SO alvo. PyInstaller não faz cross-compilation.
Cada release ganha diretório novo; versões anteriores não são apagadas.

- `archive_path` (linha 26): Append extension: version dots are not a filesystem suffix to replace.
- `validate_binary` (linha 31): Surface frozen GUI tracebacks even when Windows has no console.
- `build` (linha 44)

## scripts/document_code.py

Gera índice auditável de todos os símbolos Python sem importar o aplicativo.


## scripts/package_installers.py

Cria instaladores a partir de ZIPs nativos já validados, sem estado pessoal.

Windows: execute no runner Windows com NSIS; Linux: execute com rpmbuild.
O conteúdo é extraído em staging novo e todos os hashes/modelos são conferidos.
Arquivos finais nunca substituem uma release existente silenciosamente.

- `write_manifest` (linha 26)
- `prepare_payload` (linha 31): Only native binaries and blank templates are admitted into an installer.
- `nsis_escape` (linha 79)
- `windows_installer` (linha 83)
- `rpm_installer` (linha 100)
- `main` (linha 120)

## scripts/validate_installer.py

Valida instalação, execução e remoção do EXE no Windows nativo do CI.

Não aceita Wine nem executa em outro sistema. Diretórios/estado são isolados no
checkout do runner e nenhum perfil real é importado. Desinstalar deve conservar
o sentinela de dados fora da pasta da aplicação.

- `validate` (linha 22)

## scripts/validate_release.py

Verifica CRC, manifestos, modelos vazios e runtime extraído do pacote.

Toda extração/execução usa diretório temporário dentro do projeto. Não modifica
o pacote nem a instalação do usuário e não chama serviços externos.

- `validate` (linha 22)

## tests/conftest.py

Módulo da camada tests.

- `layouts` (linha 16)
- `layout` (linha 21)
- `make_xlsx` (linha 26)
- `options` (linha 42)
- `convert` (linha 47)
- `synthetic_cpf` (linha 64)

## tests/test_ai.py

Módulo da camada tests.

- `answer` (linha 15)
- `test_reject_invalid_ai` (linha 20)
- `test_privacy_injection_cells_and_headers` (linha 25)
- `test_provider_contracts_no_real_network` (linha 39)
- `test_fallback_only_configured_and_invalid_schema` (linha 60)
- `test_credentials_no_plaintext_backend` (linha 75)

## tests/test_core.py

Módulo da camada tests.

- `test_originals_unchanged` (linha 16)
- `test_layout_versions_and_headers` (linha 21)
- `test_rules_drift_blocks` (linha 27)
- `test_text_zeros_and_cpf` (linha 33)
- `test_csv_encodings` (linha 44)
- `test_csv_ragged_and_blank` (linha 54)
- `test_html_disguised_xls` (linha 64)
- `test_multiple_sheets_and_header` (linha 72)
- `test_duplicate_headers_not_auto_confirmed` (linha 83)
- `test_product_case_sensitive_mapping` (linha 92)
- `test_clients_preservation_defaults_and_invalid_contacts` (linha 99)
- `test_cpf_ie_not_guessed` (linha 110)
- `test_rg_composite_and_manual_correction` (linha 117)
- `test_missing_uf_and_confirmation` (linha 126)
- `test_active_requires_per_conversion_answer` (linha 134)
- `test_service_tax_and_not_generic_product_code` (linha 142)
- `test_oil_parts_not_classified` (linha 151)
- `test_km_letters_not_stripped` (linha 158)
- `test_numeric_identifier_and_formula_block` (linha 164)
- `test_export_zeros_order_omit_and_no_original_change` (linha 174)
- `test_large_csv_split_and_counts` (linha 189)
- `test_links_and_joint_partition` (linha 209)
- `test_oversized_group_and_interleaving_block` (linha 220)
- `test_cancel_processing_and_no_session_leak` (linha 229)
- `test_source_mutation_blocks_export` (linha 236)
- `test_decimal_no_rounding_or_ambiguous_guess` (linha 243)

## tests/test_dashboard.py

Dashboard usa metadados reais e não inventa taxa, atividade ou estado externo.

- `window_for` (linha 18)
- `create_job` (linha 31)
- `test_success_uses_latest_jobs_not_technical_events` (linha 40)
- `test_theme_contrast_and_independent_accent` (linha 51)
- `test_sidebar_expansion_navigation_search_and_paths` (linha 62)
- `test_light_dark_custom_accent_keeps_sessions_and_creates_previews` (linha 108)
- `test_appearance_draft_and_save_remain_accessible_in_small_window` (linha 158)

## tests/test_distribution.py

Contratos de instalação e encerramento SQLite, independentes do SO do teste.

- `test_archive_name_preserves_version_platform_and_build_id` (linha 15)
- `test_database_closes_on_success_and_rolls_back_on_error` (linha 20)
- `test_installed_state_is_outside_app_and_override_wins` (linha 37)
- `test_installer_rechecks_native_zip_and_blank_templates` (linha 54)

## tests/test_edges.py

Módulo da camada tests.

- `test_real_biff_xls_format_zeros` (linha 16)
- `test_formula_like_csv_exported_as_literal` (linha 25)
- `test_cancel_export_publishes_nothing` (linha 42)
- `test_orphan_items_block` (linha 50)
- `test_all_twelve_layouts_export_synthetic` (linha 58)
- `test_numeric_excel_decimal_not_ambiguous` (linha 69)
- `test_cli_restricted_arguments_and_json` (linha 75)

## tests/test_import_projects.py

Trabalhos, processamento em lote e PDF usam somente arquivos sintéticos.

- `attachment` (linha 18)
- `test_pdf_tables_and_zero_preservation` (linha 23)
- `test_pdf_without_table_is_explicitly_rejected` (linha 32)
- `test_named_job_multiple_categories_export` (linha 37)
- `test_every_pdf_table_represented_and_requires_review` (linha 59)
- `test_failed_file_stays_in_import` (linha 89)
- `test_multi_sheet_and_changed_header_does_not_reuse_mapping` (linha 104)
- `test_saved_corrections_and_cancel_do_not_publish` (linha 131)
- `test_batch_links_and_ambiguous_pairs_remain_pending` (linha 147): A lista de arquivos não autoriza adivinhar qual cabeçalho recebe itens.

## tests/test_import_ui.py

Fluxo amigável e aparência são verificados em widgets Qt reais, offscreen.

- `make_window` (linha 12)
- `test_home_shows_imports_and_wizard_validates` (linha 21)
- `test_named_multi_file_flow_and_saved_pending_correction` (linha 42)
- `test_global_color_logo_size_and_reopen` (linha 90)
- `test_light_and_dark_colors_have_distinct_surfaces` (linha 129)
- `test_worker_defers_qt_cycle_collection_to_gui_thread` (linha 137): Unreachable widgets must never be finalized by Python's worker GC.

## tests/test_studio.py

Synthetic compositions: financial splits, OS unions, stock joins and provenance.

- `library` (linha 23)
- `project` (linha 37)
- `recipe` (linha 45)
- `route` (linha 49)
- `ready` (linha 57)
- `close` (linha 62)
- `test_packaged_rules_survive_deleted_onefile_directory` (linha 67)
- `test_combined_ctp_ctr_splits_and_keeps_zero_codes` (linha 86)
- `test_unknown_financial_row_and_overlapping_routes_block_export` (linha 113)
- `test_product_stock_lookup_and_distinct_services_union` (linha 136)
- `test_duplicate_lookup_key_fails_without_multiplication` (linha 159)
- `test_os_headers_parts_and_services_become_linked_outputs` (linha 172)
- `test_recipe_is_data_not_code_and_approval_is_snapshot_bound` (linha 192)
- `test_folder_selection_and_append_only_history` (linha 212)
- `test_empty_destination_and_justified_exclusion_are_explicit` (linha 224)
- `test_constants_are_audited_and_missing_required_lookup_blocks` (linha 243)
- `test_unresolved_questions_and_duplicate_json_keys_cannot_be_approved` (linha 262)
- `test_correction_cannot_move_to_another_record_after_filter_change` (linha 274)
- `test_project_field_rules_are_executable_and_counted_in_the_audit` (linha 301)

## tests/test_studio_ai.py

Full planning/audit contracts over mocked HTTP; no paid calls or real data.

- `test_each_provider_can_plan_and_audit_through_http` (linha 16)
- `test_providers_use_independent_environment_credentials_and_models` (linha 50)
- `test_invalid_or_interrupted_provider_output_never_becomes_a_plan` (linha 70)
- `test_development_env_is_read_only_whitelisted_and_never_executed` (linha 88)

## tests/test_studio_ui.py

IDE-like workflow exercised with real Qt widgets and a synthetic AI provider.

- `test_new_project_ai_plan_execution_audit_history` (linha 12)
- `test_folder_picker_requires_explicit_tables` (linha 101)
- `test_provider_editor_preserves_primary_and_each_credential` (linha 112)
- `test_provider_controls_remain_accessible_in_small_window` (linha 139)

## tests/test_ui.py

Módulo da camada tests.

- `test_desktop_full_flow_and_review` (linha 9)
- `test_initial_rule_editor_saves_revision_without_touching_original` (linha 65)
- `test_bad_model_folder_is_recoverable` (linha 91)

## tests/test_workspace.py

Módulo da camada tests.

- `test_whitelabel_folder_upload_custom_rules` (linha 15)
- `test_declarative_validation_and_no_default_identifiers` (linha 45)
- `test_local_store_only_minimal_history_and_profiles` (linha 62)
- `test_report_copy_to_selected_partial_directory` (linha 76)
- `test_portable_branded_library_uses_relative_sources` (linha 84)
