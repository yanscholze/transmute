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

- `selected_lines` (linha 25)
- `plan_parts` (linha 54): Planeje partes por grupo e prove monotonicidade em cada fonte.
- `write_workbook` (linha 93): Derive cabeçalhos/estilos do modelo e escreva dados como texto literal.
- `report_data` (linha 126)
- `save_reports` (linha 159)
- `export` (linha 181): Nunca sobrescreva fontes/saídas; em erro ou cancelamento retire o staging.

## app/core/importers/__init__.py

Leitores iteráveis; nunca alteram a origem.


## app/core/importers/reader.py

Detecção por conteúdo e leitores que expõem posição física e tipo de origem.

CSV e XLSX são iterados; HTML tem limite explícito de tamanho. Nenhum leitor
executa fórmula ou tenta recuperar zeros que já desapareceram da fonte.

- `excel_cell` (linha 21): Converta representação sem float arithmetic, mantendo evidência de risco.
- `detect` (linha 47)
- `csv_settings` (linha 62)
- `HTMLTables` (linha 89)
  Métodos: `__init__`:90, `handle_starttag`:94, `handle_data`:108, `handle_endtag`:112.
- `html_tables` (linha 124)
- `sheets` (linha 133)
- `raw_rows` (linha 153)
- `inspect` (linha 191): Sugira estrutura a partir de amostra limitada; a UI permite corrigir a escolha.
- `records` (linha 227): Inclua linhas vazias e células excedentes para contagem e auditoria explícitas.

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
- `validate_links` (linha 125): Cheque integridade referencial sem excluir/deduplicar nenhum registro.

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

- `main` (linha 16)

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

- `project_root` (linha 7)
- `state_root` (linha 13)

## app/selftest.py

Teste sintético disponível também no executável distribuído, sem pytest.

- `run` (linha 15)

## app/storage/local.py

Persistência mínima: histórico sem células, perfis estruturais e opções sem secrets.

- `LocalStore` (linha 7)
  Métodos: `__init__`:8, `connect`:18, `save_profile`:21, `profiles`:25, `delete_profile`:30, `record`:34, `history`:38, `clear_history`:42, `setting`:48, `set_setting`:53.

## app/storage/workspace.py

Biblioteca configurável. Referências externas são somente leitura.

Uploads e edições são copiados para o estado local. Cada revisão de regras é
um novo par Markdown/JSON; o ponteiro só muda depois que ambos são gravados.

- `save_config` (linha 15)
- `initialize` (linha 22)
- `import_model` (linha 37)
- `save_rule_revision` (linha 62)
- `set_brand` (linha 80)

## app/ui/ai_actions.py

Diálogo de consentimento com payload exato e aplicação de sugestões não confirmadas.

- `suggest_mapping` (linha 15)

## app/ui/common.py

Tarefas em thread e tabelas de apresentação sem regras de negócio.

Erro é mostrado ao operador, mas o log contém só o tipo da exceção. O modelo
de tabela recebe apenas a página atual, sem duplicar uma base inteira.

- `Worker` (linha 16)
  Métodos: `__init__`:21, `run`:26.
- `GridModel` (linha 37)
  Métodos: `__init__`:38, `rowCount`:44, `columnCount`:47, `data`:50, `headerData`:59.
- `table` (linha 64)
- `button` (linha 76)
- `text_label` (linha 86)

## app/ui/conversion.py

Coordena o assistente e o ciclo de vida das sessões principal/vinculada.

UI coleta decisões e despacha operações ao core. Correção pendente bloqueia
exportação até revalidar; uma chamada de IA nunca escreve uma célula.

- `ConversionPane` (linha 20)
  Métodos: `__init__`:21, `panes`:73, `previous`:76, `advance`:80, `prepare_mapping`:102, `process`:114, `processed`:128, `correct`:145, `do_export`:152, `exported`:167, `update_step`:172, `ai_suggest`:182, `close_sessions`:187.

## app/ui/input.py

Escolha/drag and drop, opções de leitura e amostra local limitada.

Alterar leitura invalida a estrutura anterior; nada é processado com uma
prévia que corresponda a outro arquivo, aba ou encoding.

- `InputPane` (linha 16)
  Métodos: `__init__`:19, `layout`:79, `invalidate`:82, `browse`:86, `set_path`:91, `load`:100, `loaded`:113, `dragEnterEvent`:131, `dropEvent`:135.

## app/ui/library.py

Tela inicial: biblioteca, branding e revisão das regras sem editar fontes.

- `LibraryPane` (linha 15)
  Métodos: `__init__`:18, `refresh`:65, `reload`:92, `choose_folder`:99, `upload`:107, `family_changed`:117, `choose_rules`:123, `branding`:132, `edit_rules`:139.

## app/ui/mapping.py

Editor de correspondências e perfis, sem transformar células.

Decisões incertas precisam de confirmação; perfis só armazenam estrutura e
ficam restritos ao fingerprint do destino para evitar reaplicação absoluta.

- `fingerprint` (linha 17)
- `MappingPane` (linha 21)
  Métodos: `__init__`:22, `render`:43, `manual`:72, `get_decisions`:80, `update_summary`:83, `save_profile`:88, `load_profile`:98.

## app/ui/options.py

Coleta escolhas e evidências por conversão; o core é quem aplica as regras.

- `OptionsPane` (linha 8)
  Métodos: `__init__`:9, `get`:48.

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

Módulo da camada app/ui.


## app/ui/window.py

Shell desktop: navegação, biblioteca ativa e execução/cancelamento de tarefas.

Fechamento aguarda o worker terminar antes de remover sessões. Mudanças de
biblioteca recriam o assistente para não reaproveitar decisões de outra base.

- `Window` (linha 16)
  Métodos: `__init__`:17, `notify`:94, `navigate`:98, `apply_brand`:106, `reload_library`:113, `run_job`:133, `job_error`:148, `job_finished`:153, `cancel_job`:164, `make_history`:169, `refresh_history`:179, `clear_history`:187, `make_models`:193, `closeEvent`:206.

## scripts/audit_models.py

Inventário estrutural sem reproduzir amostras pessoais.


## scripts/build.py

Build nativo e pacote portátil, sem copiar estado, secrets ou exemplos.

Execute com o Python do .venv no SO alvo. PyInstaller não faz cross-compilation.
Cada release ganha diretório novo; versões anteriores não são apagadas.

- `build` (linha 24)

## scripts/document_code.py

Gera índice auditável de todos os símbolos Python sem importar o aplicativo.


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

## tests/test_edges.py

Módulo da camada tests.

- `test_real_biff_xls_format_zeros` (linha 16)
- `test_formula_like_csv_exported_as_literal` (linha 25)
- `test_cancel_export_publishes_nothing` (linha 42)
- `test_orphan_items_block` (linha 50)
- `test_all_twelve_layouts_export_synthetic` (linha 58)
- `test_numeric_excel_decimal_not_ambiguous` (linha 69)
- `test_cli_restricted_arguments_and_json` (linha 75)

## tests/test_ui.py

Módulo da camada tests.

- `test_desktop_full_flow_and_review` (linha 9)
- `test_initial_rule_editor_saves_revision_without_touching_original` (linha 53)
- `test_bad_model_folder_is_recoverable` (linha 79)

## tests/test_workspace.py

Módulo da camada tests.

- `test_whitelabel_folder_upload_custom_rules` (linha 15)
- `test_declarative_validation_and_no_default_identifiers` (linha 45)
- `test_local_store_only_minimal_history_and_profiles` (linha 62)
- `test_report_copy_to_selected_partial_directory` (linha 76)
- `test_portable_branded_library_uses_relative_sources` (linha 84)
