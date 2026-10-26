# Decisão arquitetural

## Alternativas e escolha

Python + PySide6 foi escolhido para interface nativa Windows/Linux, tabelas virtualizadas, threads e drag and drop, junto de leitores confiáveis para Excel. Tkinter reduz dependências, mas exige mais trabalho em tabelas e interação. Electron/React adiciona runtime e ponte com parser. Tauri reduz o shell, mas aumenta complexidade de build Rust e parsing/empacotamento. Não há servidor ou serviço remoto obrigatório.

Python 3.12+; openpyxl (XLSX), xlrd (BIFF XLS), charset-normalizer (CSV), parser HTML restrito para XLS HTML, pdfplumber para tabelas posicionais PDF, QtPdf para conferência local, Decimal para quantidades/valores; SQLite para perfis, trabalhos e histórico; keyring para credenciais; httpx para APIs opcionais; PyInstaller para distribuição. Não usar DataFrame intermediário. Registros são iterados e convertidos para SQLite temporário local para revisão/paginação, removido ao fechar sessão. Interface usa modelos Qt e trabalho em threads canceláveis.

Fontes: [Qt for Python](https://doc.qt.io/qtforpython-6/), [PyInstaller: distribuição por sistema](https://pyinstaller.org/en/stable/operating-mode.html). Build nativo separado em Windows e Linux, pois PyInstaller não gera binário Windows a partir do Linux. Pacote inclui runtime e bibliotecas; modelos/regras são externos ao lado do aplicativo, substituíveis sem instalar Python. Licenças de dependências acompanham a distribuição.

## Módulos

`app/core/importers`: detecção por conteúdo, cabeçalhos, metadados, iteradores e posição física.

`app/core/rules`: perfil declarativo versionado com hash de regras e decisões explícitas de conflitos.

`app/core/mapping`: sugestões determinísticas, ambiguidades e memória de mapeamentos por fingerprint do layout.

`app/core/transformation` e `validation`: regras rastreáveis e problemas tipados. Nenhuma regra de negócio na UI.

`app/core/exporters`: partes, vínculos, planilhas derivadas do cabeçalho, escrita textual segura e relatórios, transação de diretório sem sobrescrita.

`app/storage`: histórico técnico mínimo, trabalhos nomeados e sessão de revisão local temporária. `imports.py` acrescenta `imports_v1` ao SQLite existente sem apagar perfis/histórico. Guarda referências, decisões e correções manuais esparsas; dados completos permanecem temporários. Configuração/estado na pasta do aplicativo por padrão; override explícito para diretório gravável. Não escrever em outros projetos.

`app/core/batch.py`: expande abas/tabelas, processa cada fonte, conserva falhas no manifesto e valida grupos de OS/vendas. Exportação publica o trabalho completo por rename de staging, com Tratadas/Parciais; cancelamento remove a saída incompleta. Múltiplas fontes não são concatenadas implicitamente.

`app/ui`: `imports_home.py` lista trabalhos; `import_wizard.py` recolhe nome/categorias/arquivos/regras; `import_detail.py` possui sessões e integra a revisão avançada existente. `library.py` cuida dos modelos/regras; `appearance.py` cuida da marca; `theme.py` deriva tokens e desenha logo atrás do conteúdo. `window.py` navega e administra worker único/cancelamento. Há modelos Qt de tabela, perfis e diagnóstico separados do início.

Na revisão visual posterior à versão 1.1, `dashboard.py` passa a ser a entrada: compõe últimos trabalhos, indicadores e atalhos a partir de metadados existentes. `storage/dashboard.py` define a agregação sem Qt. `navigation.py` mantém a sidebar recolhível; `surfaces.py` e `icons.py` fornecem painéis e vetores locais. `theme.py` separa tema claro/escuro de cor de destaque, com QSS e QPalette. Aparência e navegação não recriam sessões de processamento. O contrato detalhado e a fórmula dos indicadores estão em DASHBOARD.md. A etapa visual foi aprovada; a distribuição 1.2 acrescenta instaladores .exe/.rpm.

Na versão 1.2, `app/ai` possuía providers independentes para OpenAI, Gemini, Claude e CLI restrita quando comprovada; schema JSON fechado, sanitização central e confirmação antes de envio. Nunca converter registro via modelo. Apenas sugestões com IDs opacos de coluna, sem nomes/células brutas enviados por padrão. Retorno só sugere mapeamentos. Chaves em keyring ou somente memória, nunca config. Fallback explícito por usuário e somente entre provedores consentidos.

## Ordem de implementação

1. Descoberta e contrato, inventário e hashes.
2. Core de importação/catálogo/mapeamento/regras/sessão/exportação.
3. Testes de integridade, separação, limites, preservação e cancelamento.
4. Interface completa, tarefas fora da thread principal, correção e nova validação.
5. IA opt-in com mocks antes de qualquer teste externo; não provisionar chave por conta própria.
6. Histórico, perfis, auditoria e relatórios integrados.
7. Build Linux local, receita e workflow Windows; validação sintética da aplicação e do pacote.

## Evolução para biblioteca configurável e white label

Conforme refinamento do pedido em 22/10/2026, referências padrão são apenas um preset inicial. `storage/workspace.py` mantém ponteiros para qualquer pasta de modelos e arquivo de regras, cópias de uploads, revisões aprovadas de Markdown/JSON e branding. Na versão 1.1, essas ações ficam em Biblioteca e Aparência, acessíveis pela navegação da tela inicial. Nenhum caminho absoluto da máquina de desenvolvimento é embutido no executável.

Modelos desconhecidos são genéricos e usam somente regras declarativas explícitas. Associação a famílias conhecidas é escolhida na biblioteca, sem adivinhar a natureza de uma base. Mudança da biblioteca invalida os resultados em curso, preservando fontes e trabalhos. Aparência não invalida processamento.

O build aceita `--library` para criar distribuição configurada com marca, modelos vazios e perfil aprovado. O preset distribuído usa caminhos relativos; a instalação resolve os caminhos no primeiro uso. Estado, credenciais e histórico não são exportados.

PDF não é convertido em texto corrido para simular linhas. O adapter localiza tabelas e coordenadas com pdfplumber; confirmação humana é uma condição do core (`PDF_CONFERENCIA`), inclusive fora da UI. PDFs sem tabela ficam pendentes ou são classificados explicitamente como apoio. Não há OCR. Fontes: [pdfplumber](https://github.com/jsvine/pdfplumber), [QPdfView](https://doc.qt.io/qtforpython-6/PySide6/QtPdfWidgets/QPdfView.html).


## Estúdio IA (1.3)

A mudança de direção foi auditada antes da implementação em AUDITORIA_ESTUDIO_IA.md. O projeto permanece desktop/PySide6, mas o fluxo novo começa pelo planejamento de múltiplas fontes, não pelo processamento automático de um arquivo para um modelo. A conversão clássica é preservada; novos manifestos usam mode=studio e conservam as fontes originais separadas das saídas geradas.

`studio/catalog.py` inventaria fontes/abas, modelos e hashes; `studio/plan.py` define schema fechado, referências, regras e aprovação de contexto; `studio/engine.py` executa filtros, concatenações, consultas por chave e regras aprovadas, com SQLite temporário e cobertura integral de linhas. `storage/studio.py` acrescenta uma tabela de eventos sem apagar dados antigos. `ai/studio.py` constrói os payloads consentidos e valida propostas/auditorias dos providers. `ai/configuration.py` separa configuração de widgets; `ai/environment.py` interpreta somente variáveis conhecidas, sem executar arquivos. `ui/studio.py` integra o espaço de trabalho por projeto e `ui/source_picker.py` permite selecionar tabelas por pasta.

Session recebe iteradores compostos sem perder Cell.kind, conferências ou hashes. Guarda linhagem, mudanças antes/depois e dependências de todas as fontes. Regras locais usam o interpretador existente, antes das operações declarativas da biblioteca; sobreposição de campos regulados é recusada, evitando duas políticas contraditórias. Exportação reconfere o contexto aprovado, modelos e fontes. Correções são vinculadas à origem e às células mapeadas, não somente à posição de saída.

A IA deixa de ser restrita ao mapeamento: planeja e audita, dentro de uma linguagem limitada de operações. Não recebe ferramentas de sistema nem autoridade para aprovar planos. IA sem credenciais continua desabilitada para consultas; o fluxo clássico e edição local de planos continuam utilizáveis. Nenhuma configuração de chave/modelo é tratada como prova de conexão. A política anterior de proibir qualquer plano além de mapeamentos descreve a versão 1.2, não o Estúdio 1.3.
