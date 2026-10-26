# Estúdio de Conversão — Transmute 1.3

O projeto passa a reunir fontes, instruções, conversa, plano de conversão,
revisões e auditoria. O objetivo é trabalhar como um ambiente especializado de
conversão assistida por IA, sem exigir que cada planilha recebida já corresponda
a uma única tabela do ERP. O fluxo clássico continua disponível para trabalhos
antigos e conversões manuais simples.

## Começar um projeto

1. No dashboard, use **Nova importação**, informe o nome e as categorias de saída.
   **Planejar no Estúdio IA** vem marcado. Criar o projeto não exige a antiga
   confirmação de regras nem inicia uma transformação sem plano.
2. Use **Escolher tabelas de uma pasta**. O app lista abas/tabelas individualmente;
   marque as que pertencem ao trabalho. Arquivos que falham continuam visíveis
   com seu motivo. Também é possível selecionar arquivos diretamente; nesse caso
   suas abas são inventariadas ao abrir o projeto.
3. Em **Biblioteca**, mantenha os modelos do ERP. Eles definem os destinos; não são
   as planilhas recebidas. Modelos genéricos/customizados continuam disponíveis.
4. Em **Regras**, descreva as decisões do cliente. Na lateral, informe o papel de
   cada fonte quando souber: CTP/CTR juntos, estoque, OS peças, OS serviços etc.
   Documento de apoio permanece associado, sem gerar registros.

O primeiro inventário é feito em segundo plano. **Atualizar leitura** relê as
estruturas. Fontes não são movidas, editadas ou enviadas automaticamente.

## Configurar OpenAI, Gemini e Claude

Em **IA e perfis**, escolha qual provedor está configurando, seu modelo e sua
credencial. Essa seleção é independente de **Usar como provedor principal**.
É possível preparar os três provedores e manter um principal fixo. As chaves
digitadas permanecem mascaradas e não aparecem nas configurações ou histórico.

**Salvar configurações** conserva os rascunhos de credenciais dos provedores
editados. O cofre seguro é opcional; sem ele, chaves digitadas ficam somente na
memória do processo. **Testar este provedor** consulta exclusivamente o provedor
em edição, após confirmação, com estrutura sintética e sem bases de cliente.
Presença de chave/modelo não significa autenticação ou conexão comprovada.

São aceitas variáveis de ambiente:

| API | Chave | Modelo |
| --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| Gemini | `GEMINI_API_KEY` (ou `GOOGLE_API_KEY`) | `GEMINI_MODEL` |
| Claude/Anthropic | `ANTHROPIC_API_KEY` (ou `CLAUDE_API_KEY`) | `ANTHROPIC_MODEL` |

Não existe modelo pago selecionado automaticamente. Use um ID disponível na sua
conta. `.env.example` contém apenas nomes de variáveis, sem credenciais.
No desenvolvimento, `run.py` pode ler `.env.local` do projeto, sem executar seu
conteúdo e sem sobrescrever variáveis não vazias do ambiente. O executável
empacotado não carrega esse arquivo automaticamente. **Importar credenciais de
arquivo local** permite importar explicitamente as variáveis reconhecidas para
memória/cofre, inclusive uma chave criada pelo fluxo seguro, sem colá-la no chat.
Nenhum teste externo é iniciado pela importação.

O timeout é configurável entre 5 e 300 segundos e a operação pode ser cancelada.
Fallback usa somente a lista configurada, apresentada no consentimento. Falhas
mostram códigos seguros, como HTTP_401 ou CONFIGURACAO; corpos de erro e chaves
não entram em logs. Login, saldo, disponibilidade e limites dependem da conta.

## Conversar e revisar o plano

Na aba **Conversa e histórico**, peça uma análise ou responda às perguntas da IA.
Antes do envio, confira o payload completo e os provedores. Nomes de colunas e
títulos podem ser compartilhados conforme o controle visível; por padrão, células
viram estatísticas. Incluir até três valores reais por coluna é uma opção separada
e sensível. O diálogo exige autorização explícita para o conteúdo daquela consulta.

A IA recebe as instruções do projeto, regras aprovadas da biblioteca, metadados
das tabelas e o plano anterior. Ela não recebe acesso ao disco, shell ou banco.
Uma resposta incompleta ou fora do contrato é rejeitada; uma proposta válida
continua sendo rascunho. Perguntas essenciais impedem aprovação/execução.

**Plano** mostra destinos, fontes, filtros, cruzamentos, constantes e regras com
nomes legíveis. Confirme a revisão e use **Aprovar esta revisão**. Alterar fontes,
modelos, instruções, decisões ou correções invalida a aprovação. Uma proposta com
contexto antigo exige nova análise ou validação manual com as fontes atuais.
O histórico conserva propostas, instruções, aprovações, falhas, execuções e
auditorias. **Abrir revisão** reabre um rascunho, sem executar nem aprovar sozinho.

## Composições disponíveis

| Situação recebida | Plano explícito |
| --- | --- |
| CTP/CTR na mesma tabela | Duas saídas, cada uma com filtro em um discriminador confirmado |
| CTP e CTR separados | Uma entrada para cada destino, sem união implícita |
| OS, peças e serviços separados | Cabeçalho em uma saída; peças e serviços concatenados na saída de itens compatível, com o mesmo grupo de vínculo |
| Produtos e estoque separados | Consulta por código exato e único para enriquecer o produto com saldo/quantidade |
| Produtos e serviços separados | Rotas distintas ou concatenação explicitamente aprovada; natureza não é adivinhada |
| Tratamentos específicos | Regras declarativas do projeto, como maiúsculas, datas, decimais, listas permitidas e obrigatórios |

Não se infere CTP/CTR pelo sinal do valor, nome do arquivo ou semelhança textual.
Filtros usam igualdade textual exata, inclusão, exclusão, vazio ou preenchido.
Uma consulta por chave é muitos-para-um: duplicidade na tabela consultada bloqueia
a operação. Não há junção aproximada, multiplicação de linhas ou deduplicação
silenciosa. Chaves numéricas exigem conferência explícita e não podem ter mais de
15 dígitos; códigos textuais/zeros formatados preservam sua identidade.

Todas as linhas selecionadas precisam de destino, uso em consulta ou exclusão
filtrada e justificada. Uma linha sem cobertura bloqueia a saída. Classificação
financeira sobreposta também bloqueia. Destino sem registros fica explícito e
pode gerar uma planilha apenas com cabeçalhos; não desaparece do diagnóstico.
OS/vendas continuam sujeitas a cabeçalhos/itens compatíveis e conferência de
órfãos, duplicidades e divisão em partes do motor existente.

## Regras do projeto e linguagem do plano

A IA pode traduzir a instrução em operações fechadas: `required`, `digits`,
`default`, `uppercase`, `enum`, `length`, `decimal`, `date`. Datas usam formato de
entrada explícito e saem DD/MM/AAAA; decimal preserva precisão e usa vírgula.
IDs ausentes não podem ser fabricados por default ou constante. A natureza
Mercadoria/Serviço pode ser declarada explicitamente. Regras que sobrepõem um
campo já regulado na biblioteca precisam de revisão dessa biblioteca, evitando
dois motores contraditórios.

O JSON avançado é opcional. Seu contrato está em `studio/plan.py`: versão,
resumo, perguntas, saídas e exclusões. Cada saída declara modelo, grupo, entradas
e regras. Entradas possuem filtros, consultas por chave, campos e constantes.
Referências são IDs de tabela e colunas C1/C2...; não são caminhos ou comandos.
**Copiar referências de origem e destino** fornece o catálogo para manutenção
manual, sem células/caminhos. A aprovação liga o plano ao hash de seu contexto.
Não existe execução de Python, SQL, fórmulas ou comandos produzidos por IA.

## Executar, corrigir e auditar

Use **Executar plano aprovado**. O motor local compõe as tabelas e preserva o tipo
original das células, passa pelos tratamentos e validadores, e registra origem,
linha e consultas usadas em cada registro. Fórmulas, erros e identificadores
numéricos não são disfarçados como texto confiável durante uma junção.

Em **Resultados**, navegue em páginas de até 200 linhas. Selecione uma célula para
ver origem, valor mapeado, resultado, mudanças e problemas. **Corrigir célula**
salva uma correção local e exige nova aprovação/execução. A correção é ligada ao
conteúdo e à linhagem da linha; se um filtro reordenar a saída, o valor antigo não
é aplicado a outro registro. Correções sem correspondência ficam pendentes.
**Descartar correções** retira as correções ativas após confirmação, mantendo seu
registro histórico e sem modificar as fontes.

**Auditoria** mostra contagens completas, transformações por regra, problemas,
exclusões e cobertura. **Auditar com IA** consulta o provedor com essas contagens
e até três amostras de saída, conforme o payload autorizado. A IA não pode afirmar
que revisou linhas não enviadas. Apontamentos ERRO exigem revisão registrada; não
alteram dados nem dispensam erros do motor. Uma nova execução conserva a auditoria
anterior no histórico e solicita nova auditoria quando desejado.

**Exportar importação** revalida os snapshots. O diretório contém Tratadas,
Parciais, plano aprovado, instruções, auditoria de composição/IA e linhagem por
linha. Auditoria sensível com valores antes/depois continua sendo opt-in. Os
arquivos originais permanecem intactos e resultados anteriores não são apagados.

## Limites e validação

A integração é testada com fixtures sintéticas e contratos HTTP simulados. Esses
testes não comprovam autenticação de uma conta. PDFs continuam limitados às
tabelas posicionais reconhecidas, com conferência humana; não há OCR universal.
Agregações arbitrárias, fuzzy matching, geração de identificadores e código livre
não fazem parte desta linguagem. Requisitos ausentes viram perguntas/pendências.
Aceitação no ERP e bases reais continuam exigindo validação autorizada.

Implementação, motivo da mudança e reprodução do defeito estão em
AUDITORIA_ESTUDIO_IA.md e DESENVOLVIMENTO.md. Evidências atuais de fonte/builds em
VALIDACAO_FINAL.md; versões anteriores permanecem preservadas.
