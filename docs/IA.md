# Integrações opcionais de IA

## Contratos

OpenAI: POST `/v1/responses`, instructions estáticas, input delimitado como dados, text.format JSON Schema e store=false. Fonte: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Gemini: POST `v1beta/models/{model}:generateContent`, systemInstruction, contents, generationConfig com responseMimeType/responseJsonSchema. Fonte: [generateContent](https://ai.google.dev/api/generate-content) e [saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output).

Claude: POST `/v1/messages`, tool schema fechado `suggest_mapping` forçado para representação estruturada. A ferramenta não é executada; apenas seu input é lido como objeto de sugestões. Fonte: [Messages](https://platform.claude.com/docs/en/api/messages).

Modelo é texto configurado pelo usuário. Capacidades dependem do modelo/conta. Testes por mocks verificam construção e validação do protocolo; não comprovam credenciais, disponibilidade ou cobrança real.

## Schema de resposta

Raiz contém somente `suggestions`. Cada entrada contém source_column, target_column, confidence e reason. IDs de origem e nomes de destino precisam existir; confiança finita entre 0 e 1, sem booleanos. Chaves duplicadas, colunas repetidas, atributos extras, texto livre e JSON inválido são rejeitados. Limites de tamanho evitam aceitar saídas desnecessariamente grandes.

Provider não recebe inteiro do arquivo, linhas completas, senha em prompt, ferramentas ou caminho. Fonte chega em `untrusted_data`; regras do sistema são constantes. Razão retornada fica como justificativa de sugestão, nunca como observação do cliente.

## CLI

Inspeção local realizada em 22/10/2026 via --help, sem executar geração ou ler autenticação:

- Codex exec: existem stdin, read-only sandbox, ephemeral e output-schema. Não foi confirmado neste trabalho um modo que remova todas as ferramentas/hooks e acesso a arquivos; apenas detecção.
- Gemini: existem headless, JSON e plan/read-only. Sem contrato confirmado de desativação completa de ferramentas/hooks; apenas detecção.
- Claude: foram confirmados --safe-mode, --tools "", --strict-mcp-config, --mcp-config, --no-session-persistence, --disable-slash-commands, --json-schema e --output-format. O provider verifica os flags novamente antes de executar. Ausência bloqueia a integração.

Não usar shell=True, flags de bypass, modo YOLO ou comandos montados a partir de célula. Prompts passam por stdin; modelo é configuração confiável validada. Timeout/cancelamento encerram o processo/grupo criado. Stderr não entra nos logs, pois pode conter dados ou secrets.

Autenticação real e respostas CLI não foram verificadas nesta sessão. Adicione teste de contrato com sua versão em ambiente próprio antes de usar dados reais. O aplicativo funciona integralmente sem essa integração.
