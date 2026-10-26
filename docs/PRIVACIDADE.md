# Privacidade, auditoria e dados locais

## Onde os dados ficam

Fonte/ZIP usam `.local/` ao lado do projeto/executável. Instaladores usam `%LOCALAPPDATA%\Transmute` no Windows e `${XDG_DATA_HOME:-~/.local/share}/transmute` no Linux. `CONVERSOR_STATE_DIR` permite escolher outro diretório gravável de forma explícita. A UI não inicia servidor HTTP nem exige porta local.

- `history.sqlite3`: perfis cabeçalho/destino, histórico técnico data/layout/contagens, resultado e opções de IA sem chave. A nova tabela `imports_v1` também contém nome do trabalho, títulos, caminhos completos das fontes/saídas, categorias, opções, mapeamentos, hashes, estatísticas e correções manuais esparsas. As correções e textos livres podem conter dados pessoais; não há cópia integral das bases nessa tabela.
- `workspace/workspace.json`: referências a modelos/regras e identidade visual, incluindo caminho e parâmetros da logo.
- `workspace/assets/`: cópias das logos adicionadas. Remover a logo da tela desassocia a imagem; não promete eliminação de cópias/backups anteriores.
- `workspace/models/`: cópias dos modelos importados.
- `workspace/rule-revisions/`: versões aprovadas do Markdown e perfil.
- `sessions/review-*.sqlite3`: dados sensíveis temporários de revisão. Removidos ao encerrar conversão/janela normalmente.
- `diagnostico.log`: eventos mínimos com rotação, sem linhas de planilha, payloads, caminhos completos ou texto de exceções.

O dashboard usa os manifestos e configurações já persistidos; não cria telemetria, não consulta provedores e não lê amostras de bases para calcular indicadores. A setting `ui_sidebar_expanded` guarda apenas um booleano; `theme_mode` em workspace.json guarda claro/escuro. A taxa representa resultado local, não confirmação do ERP. Os caminhos configurados ficam visíveis na tela: copiar coloca o caminho no clipboard do sistema; abrir pasta usa o gerenciador local. As capturas de documentação do dashboard são geradas com estado e nomes sintéticos, separados dos trabalhos reais.

Permissões de diretórios novos restringem acesso quando suportado. Não há criptografia de toda a sessão/relatórios no disco. Use volume/conta de sistema com proteção adequada. Encerramento abrupto pode deixar dados de sessão. Não apague sessões enquanto outra instância estiver aberta. Remoção de arquivo não comprova apagamento físico em SSD/backups.

## Credenciais

`credentials.py` aceita apenas backends reconhecidos de cofre seguro do sistema; backend desconhecido/inseguro mantém somente memória. O app não grava chaves em `.env` ou JSON. Pode ler variáveis do ambiente e importar um arquivo local explicitamente escolhido. Em desenvolvimento, run.py lê .env.local do projeto, que fica ignorado pelo Git e não acompanha pacotes; eventual escrita por uma ferramenta de criação de chave requer confirmação específica do usuário. Troca de provedor preserva rascunhos mascarados, sem revelar chaves salvas. Remoção de chave atua no cofre e na memória.

## Fronteira de IA

Sanitização central substitui células por tipo, tamanho e quantidade de dígitos. No mapeamento clássico não há amostra literal enviada. O Estúdio 1.3 permite incluir até três valores reais por coluna/saída somente após opção e confirmação do conteúdo exato. Cabeçalhos canônicos conhecidos podem aparecer; desconhecidos ficam ocultos. Usuário pode autorizar cabeçalhos originais após revisar o payload. O diálogo lista provedor e fallbacks; envio pode consumir cota e está sujeito às políticas de retenção de cada serviço.

OpenAI usa `store=false`, sem prometer retenção zero na infraestrutura do fornecedor. Gemini/Claude seguem o contrato de suas APIs. A aplicação não oferece garantia sobre retenção externa além dos parâmetros da requisição.

Nenhum adapter tem acesso a caminho de arquivo ou ferramenta de sistema. O retorno produz correspondências, propostas de plano ou auditorias validadas por schema; não há executor de comandos, código livre ou URLs retornadas. Um plano usa apenas as operações registradas no motor local e exige aprovação independente. Fonte maliciosa continua conteúdo. JSON é dado mesmo quando contém texto parecido com uma instrução.

CLI tem risco adicional de configurações pessoais. Execução habilitada somente quando flags necessários de isolamento são confirmados no --help. Claude é chamado sem ferramentas/MCP/personalizações/persistência, em diretório temporário vazio, com args em lista e shell=False. Não se promete isolamento equivalente a contêiner; políticas gerenciadas pela instalação/empresa podem ainda existir. A autenticação da CLI é responsabilidade de sua instalação, não é lida pela aplicação.

## Relatórios

Padrão: contagens, nomes de arquivos, cabeçalhos, decisões, códigos e linhas problemáticas. Não inclui valores de todas as células. Texto digitado em evidências ou justificativas pode conter dado sensível, portanto relatórios também exigem cuidado.

`auditoria_sensivel.jsonl`, quando explicitamente escolhido, inclui raw/output/changes/issues por linha. Guarde junto da importação com controle de acesso. O histórico mínimo não é substituto dessa auditoria.


## Histórico e composição do Estúdio (1.3)

A tabela aditiva studio_events registra conversas, instruções, planos, contextos de aprovação, falhas e execuções. Pode conter regras do cliente, cabeçalhos, caminhos, constantes e correções manuais com valores sensíveis. Não contém credenciais. A lista de fontes permanece no manifesto studio.sources; attachments passa a representar as saídas após executar. O cache de catálogo é somente visual: execução e exportação relêem hashes e referências.

`composition-*/sources.sqlite3` contém dados temporários para cruzamentos/concatenação, removidos normalmente ao terminar. Sessões de revisão guardam linhas compostas e sua linhagem. Encerrar abruptamente pode deixar temporários. Não há criptografia/eliminação forense ou sincronização de histórico. Eventos são append-only pela API da aplicação, não um livro-razão imune à edição externa do SQLite.

Cada consulta exibe o payload completo e provedores consentidos. O histórico conserva hashes de consentimento/disclosure, não uma cópia automática dos payloads de amostras. Aprovações conservam instruções, perfil e catálogo de metadados usados; não copiam todas as bases. Uma nova execução não transforma a auditoria anterior da IA em auditoria atual. Descartar correções ativas mantém seus eventos históricos e exige confirmação do operador.

Exportações podem conter plano, regras do projeto, auditorias e linhagem (IDs/linhas/referências), além dos relatórios anteriores. Planos e textos livres também podem conter dados pessoais. O arquivo de auditoria sensível continua separado e opt-in. Consulte ESTUDIO_IA.md para o escopo amostral da auditoria IA e os controles locais.
