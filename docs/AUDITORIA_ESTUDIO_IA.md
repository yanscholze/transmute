# Auditoria e evolução para Estúdio de Conversão — 26/10/2026

## Evidências antes da alteração

`storage/workspace.initialize` persistia o perfil padrão usando `__file__`. No
PyInstaller onefile esse arquivo mora em `_MEI...`, diretório temporário removido
ao sair. A próxima abertura podia conservar um profile_path inválido. A biblioteca
de desenvolvimento desta máquina tem regras/perfil existentes; não reproduz o
estado de uma instalação do usuário. A reprodução usa estado sintético com perfil
temporário removido, sem tocar nas regras originais.

O assistente exigia um modelo de saída por arquivo e uma fonte por categoria.
`batch.process_import` tratava fontes independentemente e só reconhecia um par
de cabeçalho/itens. Não havia particionamento CTP/CTR, união de peças/serviços ou
enriquecimento de produtos com estoque separado. Apontar pasta existia apenas para
modelos de destino. Selecionar abas de fontes por pasta não existia.

`ai_actions` consultava exclusivamente sugestões de mapeamento; o contrato do
provider proibia outros resultados. Isso não implementava um agente de conversão.
OpenAI/Gemini/Claude já tinham adapters básicos, mas a configuração não mostrava
prontidão individual nem consumia variáveis de ambiente. Chaves de API não foram
encontradas na checagem OpenAI. O usuário autorizou criação segura; a seleção da
conta/projeto na janela segura continua necessária. Não há prova de chamadas reais.

## Contrato da evolução

Um projeto de conversão reúne fontes/abas selecionadas, modelos de destino,
instruções em linguagem natural, conversa persistente, revisões de plano e
execuções auditáveis. A IA pode propor divisões, uniões e junções por chave,
explicar dúvidas e auditar resultados. O operador aprova uma revisão exata antes
de executá-la. Alterar fontes, regras, modelos ou instruções invalida a aprovação.

O plano é declarativo: rotas para destinos, filtros explícitos, mapeamentos,
constantes documentadas e consultas exatas a outras tabelas. Não executa Python,
SQL, shell ou comandos retornados por modelos. Ambiguidades, chaves duplicadas,
linhas sem classificação e vínculos órfãos permanecem visíveis. Nunca se decide
CTP/CTR pelo sinal do valor nem se inventa a chave de uma OS/produto.

Separar CTP/CTR usa duas rotas com filtros declarados. OS pode unir peças e
serviços no destino de itens, mantendo ligação com cabeçalhos. Produtos podem
receber estoque por chave exata; serviços podem seguir rota própria ou aprovada
para o mesmo modelo. Contagens e origens de cada linha ficam auditáveis.

O motor existente continua responsável pela validação e exportação textual após
a composição. Isso permite repetir um plano aprovado com os mesmos dados sem
pedir que um modelo reescreva cada célula. IA planeja e audita; as alterações
efetivas permanecem reproduzíveis e verificáveis. O fluxo clássico é preservado
para trabalhos antigos. Sem API, o plano pode ser editado e validado localmente.

## Privacidade e estado

Fontes não são alteradas. Antes de cada consulta, a tela mostra o payload exato,
os provedores e o nível de amostragem. Histórico de conversa, regras e planos pode
conter informações sensíveis; permanece no estado local. Não enviar arquivos
completos ou incluir valores reais automaticamente. API/chaves não acompanham
pacotes ou histórico. Recursos preparados e testes com mocks não equivalem a
autenticação ou conectividade real de uma conta.
