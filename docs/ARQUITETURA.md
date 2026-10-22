# Decisão arquitetural

## Alternativas e escolha

Python + PySide6 foi escolhido para interface nativa Windows/Linux, tabelas virtualizadas, threads e drag and drop, junto de leitores confiáveis para Excel. Tkinter reduz dependências, mas exige mais trabalho em tabelas e interação. Electron/React adiciona runtime e ponte com parser. Tauri reduz o shell, mas aumenta complexidade de build Rust e parsing/empacotamento. Não há servidor ou serviço remoto obrigatório.

Python 3.12+; openpyxl (XLSX), xlrd (BIFF XLS), charset-normalizer (CSV), parser HTML restrito para XLS HTML, Decimal para quantidades/valores; SQLite para perfis e histórico; keyring para credenciais; httpx para APIs opcionais; PyInstaller para distribuição. Não usar DataFrame intermediário. Registros são iterados e convertidos para SQLite temporário local para revisão/paginação, removido ao fechar sessão. Interface usa modelos Qt e trabalho em threads canceláveis.

Fontes: [Qt for Python](https://doc.qt.io/qtforpython-6/), [PyInstaller: distribuição por sistema](https://pyinstaller.org/en/stable/operating-mode.html). Build nativo separado em Windows e Linux, pois PyInstaller não gera binário Windows a partir do Linux. Pacote inclui runtime e bibliotecas; modelos/regras são externos ao lado do aplicativo, substituíveis sem instalar Python. Licenças de dependências acompanham a distribuição.

## Módulos

`app/core/importers`: detecção por conteúdo, cabeçalhos, metadados, iteradores e posição física.

`app/core/rules`: perfil declarativo versionado com hash de regras e decisões explícitas de conflitos.

`app/core/mapping`: sugestões determinísticas, ambiguidades e memória de mapeamentos por fingerprint do layout.

`app/core/transformation` e `validation`: regras rastreáveis e problemas tipados. Nenhuma regra de negócio na UI.

`app/core/exporters`: partes, vínculos, planilhas derivadas do cabeçalho, escrita textual segura e relatórios, transação de diretório sem sobrescrita.

`app/storage`: histórico mínimo persistente e sessão de revisão local temporária. Configuração/estado na pasta do aplicativo por padrão; override explícito para diretório gravável. Não escrever em outros projetos.

`app/ui`: assistente arquivo/modelo/mapeamento/revisão/exportação, modelos Qt de tabela, threads canceláveis, configurações, histórico e modelos.

`app/ai`: providers independentes para OpenAI, Gemini, Claude e CLI restrita quando comprovada; schema JSON fechado, sanitização central e confirmação antes de envio. Nunca converter registro via modelo. Apenas sugestões com IDs opacos de coluna, sem nomes/células brutas enviados por padrão. Retorno só sugere mapeamentos. Chaves em keyring ou somente memória, nunca config. Fallback explícito por usuário e somente entre provedores consentidos.

## Ordem de implementação

1. Descoberta e contrato, inventário e hashes.
2. Core de importação/catálogo/mapeamento/regras/sessão/exportação.
3. Testes de integridade, separação, limites, preservação e cancelamento.
4. Interface completa, tarefas fora da thread principal, correção e nova validação.
5. IA opt-in com mocks antes de qualquer teste externo; não provisionar chave por conta própria.
6. Histórico, perfis, auditoria e relatórios integrados.
7. Build Linux local, receita e workflow Windows; validação sintética da aplicação e do pacote.

## Evolução para biblioteca configurável e white label

Conforme refinamento do pedido em 22/10/2026, referências padrão são apenas um preset inicial. `storage/workspace.py` mantém ponteiros para qualquer pasta de modelos e arquivo de regras, cópias de uploads, revisões aprovadas de Markdown/JSON e branding. `ui/library.py` expõe essas ações na tela inicial. Nenhum caminho absoluto da máquina de desenvolvimento é embutido no executável.

Modelos desconhecidos são genéricos e usam somente regras declarativas explícitas. Associação a famílias conhecidas é escolhida na biblioteca, sem adivinhar a natureza de uma base. Mudança da biblioteca reinicia a conversão em curso, preservando fontes.

O build aceita `--library` para criar distribuição configurada com marca, modelos vazios e perfil aprovado. O preset distribuído usa caminhos relativos; a instalação resolve os caminhos no primeiro uso. Estado, credenciais e histórico não são exportados.
