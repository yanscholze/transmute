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

## app/ai/credentials.py

Credenciais no cofre seguro do SO ou apenas memória; nunca configuração textual.

- `Credentials` (linha 4): OS credential vault, otherwise process memory only. No plaintext fallback.
  Métodos: `__init__`:8, `get`:11, `secure`:24, `set`:28, `delete`:41.

## app/ai/providers.py

Adapters HTTP independentes, canceláveis e sem ferramentas executáveis.

Somente payload sanitizado e schema chegam aqui. Não há acesso a arquivos de
clientes; mensagens externas de erro não são registradas em log.

- `Provider` (linha 22)
  Métodos: `generate`:23.
- `APIProvider` (linha 27)
  Métodos: `request`:34, `extract`:52, `generate`:63.

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
- `workspace_config` (linha 66)
- `rules_path` (linha 71)

## app/core/exporters/writer.py

Exportação textual e transacional: planejar antes, publicar só ao terminar.

Partes vinculadas compartilham grupos; quando preservar ordem e vínculo é
impossível, bloquear é mais seguro do que reorganizar silenciosamente.

- `selected_lines` (linha 26)
- `plan_parts` (linha 55): Planeje partes por grupo e prove monotonicidade em cada fonte.
- `write_workbook` (linha 94): Derive cabeçalhos/estilos do modelo e escreva dados como texto literal.
- `report_data` (linha 127)
- `save_reports` (linha 160)
- `export` (linha 182): Nunca sobrescreva fontes/saídas; em erro ou cancelamento retire o staging.

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

- `Session` (linha 20)
  Métodos: `__init__`:21, `connect`:40, `close`:43, `rows`:46, `stats`:66, `verify`:71.
- `process` (linha 81)
- `validate_links` (linha 127): Cheque integridade referencial sem excluir/deduplicar nenhum registro.

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

- `now` (linha 18)
- `ImportStore` (linha 23)
  Métodos: `__init__`:24, `create`:34, `save`:49, `get`:54, `list`:61.

## app/storage/local.py

Persistência mínima: histórico sem células, perfis estruturais e opções sem secrets.

- `LocalStore` (linha 8)
  Métodos: `__init__`:9, `connect`:19, `save_profile`:22, `profiles`:26, `delete_profile`:31, `record`:35, `history`:39, `clear_history`:43, `setting`:49, `set_setting`:54.

## app/storage/workspace.py

Biblioteca configurável. Referências externas são somente leitura.

Uploads e edições são copiados para o estado local. Cada revisão de regras é
um novo par Markdown/JSON; o ponteiro só muda depois que ambos são gravados.

- `save_config` (linha 15)
- `initialize` (linha 22)
- `import_model` (linha 41)
- `save_rule_revision` (linha 66)
- `set_brand` (linha 84)

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
  Métodos: `__init__`:29, `set_job`:71, `refresh`:77, `selection_changed`:95, `selected`:100, `save`:104, `process_all`:109, `processing_failed`:122, `processed`:126, `recalculate_status`:131, `edit_options`:145, `rename`:169, `edit_selected`:176, `add_file`:181, `edit_item`:185, `view_pdf`:202, `review_selected`:209, `open_editor`:241, `review_processed`:279, `leave_editor`:294, `do_export`:313, `exported`:325, `close_sessions`:332.

## app/ui/import_wizard.py

Assistente: nome/categorias → arquivos classificados → regras e início.

Cada arquivo tem título, categoria e destino visíveis. Os originais são
referenciados, não movidos nem enviados a serviços externos.

- `ImportWizard` (linha 18)
  Métodos: `__init__`:22, `identification`:49, `selected_categories`:74, `file_page`:77, `browse`:95, `add_files`:99, `snapshot`:111, `render_files`:120, `populate_models`:146, `remove`:162, `previous`:169, `advance`:179, `update_step`:213, `dragEnterEvent`:220, `dropEvent`:224.

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

- `configured_providers` (linha 15)
- `SettingsPane` (linha 29)
  Métodos: `__init__`:30, `provider_changed`:86, `save`:92, `test_connection`:110, `delete_key`:124, `detect`:129, `refresh_profiles`:132, `view_profile`:138, `remove_profile`:142.

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

- `Window` (linha 21)
  Métodos: `__init__`:22, `make_header`:96, `search_imports`:145, `toggle_theme`:150, `edit_rules_from_dashboard`:157, `refresh_overview`:161, `notify`:165, `navigate`:169, `configure_backdrop`:185, `new_import`:193, `cancel_wizard`:207, `import_created`:214, `open_import`:219, `apply_brand`:227, `reload_library`:251, `run_job`:271, `job_error`:287, `job_finished`:294, `cancel_job`:305, `make_history`:310, `refresh_history`:319, `closeEvent`:327.

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
- `test_global_color_logo_size_and_reopen` (linha 89)
- `test_light_and_dark_colors_have_distinct_surfaces` (linha 128)

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
