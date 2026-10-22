# Privacidade, auditoria e dados locais

## Onde os dados ficam

Por padrão, `.local/` ao lado do projeto/executável. `CONVERSOR_STATE_DIR` permite escolher outro diretório gravável de forma explícita. A UI não inicia servidor HTTP nem exige porta local.

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

`credentials.py` aceita apenas backends reconhecidos de cofre seguro do sistema; backend desconhecido/inseguro mantém somente memória. Não há persistência em `.env` ou JSON. Troca de provedor limpa o campo visual, sem exibir a chave salva. Remoção de chave atua no cofre e na memória.

## Fronteira de IA

Sanitização central substitui células por tipo, tamanho e quantidade de dígitos. Não há amostra literal enviada. Cabeçalhos canônicos conhecidos podem aparecer; desconhecidos ficam ocultos. Usuário pode autorizar cabeçalhos originais após revisar o payload. O diálogo lista provedor e fallbacks; envio pode consumir cota e está sujeito às políticas de retenção de cada serviço.

OpenAI usa `store=false`, sem prometer retenção zero na infraestrutura do fornecedor. Gemini/Claude seguem o contrato de suas APIs. A aplicação não oferece garantia sobre retenção externa além dos parâmetros da requisição.

Nenhum adapter tem acesso a caminho de arquivo ou ferramenta de sistema. O retorno só produz correspondências validadas por schema; não há executor de comandos, código, URLs ou ações retornadas. Fonte maliciosa continua conteúdo. JSON é dado mesmo quando contém texto parecido com uma instrução.

CLI tem risco adicional de configurações pessoais. Execução habilitada somente quando flags necessários de isolamento são confirmados no --help. Claude é chamado sem ferramentas/MCP/personalizações/persistência, em diretório temporário vazio, com args em lista e shell=False. Não se promete isolamento equivalente a contêiner; políticas gerenciadas pela instalação/empresa podem ainda existir. A autenticação da CLI é responsabilidade de sua instalação, não é lida pela aplicação.

## Relatórios

Padrão: contagens, nomes de arquivos, cabeçalhos, decisões, códigos e linhas problemáticas. Não inclui valores de todas as células. Texto digitado em evidências ou justificativas pode conter dado sensível, portanto relatórios também exigem cuidado.

`auditoria_sensivel.jsonl`, quando explicitamente escolhido, inclui raw/output/changes/issues por linha. Guarde junto da importação com controle de acesso. O histórico mínimo não é substituto dessa auditoria.
