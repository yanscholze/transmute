# Integrações de IA — OpenAI, Gemini e Claude

## Contratos

OpenAI: POST `/v1/responses`, instructions estáticas, input delimitado como dados, text.format JSON Schema e store=false. Fonte: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Gemini: POST `v1beta/models/{model}:generateContent`, systemInstruction, contents, generationConfig com responseMimeType/responseJsonSchema. Fonte: [generateContent](https://ai.google.dev/api/generate-content) e [saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output).

Claude: POST `/v1/messages`, tool schema fechado `conversion_result` forçado para representação estruturada. A ferramenta não é executada; apenas seu input é lido como resultado estruturado. Respostas antigas suggest_mapping continuam legíveis por compatibilidade. Fonte: [Messages](https://platform.claude.com/docs/en/api/messages).

Modelo é texto configurado pelo usuário. Capacidades dependem do modelo/conta. Testes por mocks verificam construção e validação do protocolo; não comprovam credenciais, disponibilidade ou cobrança real.

## Mapeamento clássico: schema de resposta

Raiz contém somente `suggestions`. Cada entrada contém source_column, target_column, confidence e reason. IDs de origem e nomes de destino precisam existir; confiança finita entre 0 e 1, sem booleanos. Chaves duplicadas, colunas repetidas, atributos extras, texto livre e JSON inválido são rejeitados. Limites de tamanho evitam aceitar saídas desnecessariamente grandes.

No mapeamento clássico, o provider não recebe o arquivo inteiro, linhas completas, senha em prompt, ferramentas ou caminho. Fonte chega em `untrusted_data`; regras do sistema são constantes. Razão retornada fica como justificativa de sugestão, nunca como observação do cliente.

## CLI

Inspeção local realizada em 22/10/2026 via --help, sem executar geração ou ler autenticação:

- Codex exec: existem stdin, read-only sandbox, ephemeral e output-schema. Não foi confirmado neste trabalho um modo que remova todas as ferramentas/hooks e acesso a arquivos; apenas detecção.
- Gemini: existem headless, JSON e plan/read-only. Sem contrato confirmado de desativação completa de ferramentas/hooks; apenas detecção.
- Claude: foram confirmados --safe-mode, --tools "", --strict-mcp-config, --mcp-config, --no-session-persistence, --disable-slash-commands, --json-schema e --output-format. O provider verifica os flags novamente antes de executar. Ausência bloqueia a integração.

Não usar shell=True, flags de bypass, modo YOLO ou comandos montados a partir de célula. Prompts passam por stdin; modelo é configuração confiável validada. Timeout/cancelamento encerram o processo/grupo criado. Stderr não entra nos logs, pois pode conter dados ou secrets.

Autenticação real e respostas CLI não foram verificadas nesta sessão. Adicione teste de contrato com sua versão em ambiente próprio antes de usar dados reais. O aplicativo funciona integralmente sem essa integração.


## Estúdio 1.3: planos e auditoria

`ai/studio.py` implementa planejamento e auditoria com os três providers. `studio/plan.schema` descreve fontes, destinos, filtros, junções por chave, concatenações, constantes e regras de campo; a validação local verifica referências, chaves JSON duplicadas, operações e invariantes. Não há dispatcher de ferramentas. Uma resposta jamais aprova ou executa o próprio plano. Perguntas pendentes impedem execução. Cada aprovação guarda o plano, o contexto e as regras da biblioteca usadas.

OpenAI mantém Responses + JSON Schema estrito/store=false; Gemini mantém generateContent/responseJsonSchema e rejeita respostas interrompidas; Claude usa resultado estruturado forçado e rejeita truncamento/recusa. Em Claude, a cota máxima de resposta foi ampliada para comportar planos, sem pré-selecionar modelo pago. ID/modelo e permissões devem existir na conta. Referências consultadas: [OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses), [Gemini](https://ai.google.dev/gemini-api/docs/structured-output), [Claude](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).

As chaves são independentes: OPENAI_API_KEY, GEMINI_API_KEY/GOOGLE_API_KEY e ANTHROPIC_API_KEY/CLAUDE_API_KEY. Modelos podem vir de OPENAI_MODEL, GEMINI_MODEL e ANTHROPIC_MODEL. A tela configura cada provedor sem trocar o principal e permite importar essas variáveis de arquivo local sem exibi-las no chat. Somente run.py em desenvolvimento carrega .env.local automaticamente; não há cópia desse arquivo para o pacote. O parser aceita uma lista fechada de variáveis, não executa shell e não modifica o arquivo.

O planejamento pode enviar nomes/títulos, regras, perfil e até três estatísticas por coluna; valores reais só mediante opção e confirmação do payload. Caminhos não são enviados. A auditoria recebe contagens/transformações completas e até três amostras de saída, nunca afirma conferir linhas não enviadas. Falha de autenticação, limite, conexão ou schema não altera os dados. Eventos incluem apenas códigos seguros do provider, nunca corpo de erro, credencial ou stderr.

Configuração presente e testes HTTP simulados não comprovam conexão de uma conta. O fluxo seguro de criação OpenAI depende da escolha de conta/projeto pelo usuário; não foi concluída nenhuma criação de chave nesta revisão. Não foram feitas chamadas pagas ou usadas planilhas reais. Guia do operador: ESTUDIO_IA.md.
