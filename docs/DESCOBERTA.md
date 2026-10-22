# Descoberta e especificação — 22/10/2026

Fontes lidas integralmente: `INSTRUCOES_CONVERSOES.md` e `#PLANILHAS DE BASE/VERSOES.md`. Todos os 36 XLSX foram abertos e inspecionados: abas, células preenchidas, tipos, formatos, comentários, mesclagens e validações. SHA-256 inicial em `originais.sha256.json`. Não há código anterior, bases de clientes ou outros formatos na pasta inicial.

## Catálogo

São 12 layouts por versão (V1, V2 e V3), com conteúdo byte a byte idêntico entre versões. As versões representam grupos parciais da Riske, não evoluções de schema. Todos possuem uma aba `Sheet0`, sem validações de célula ou mesclagens. Há exemplos preenchidos: a leitura do layout considera apenas o cabeçalho, jamais copia os exemplos. `catalogo_modelos.json` contém a ordem literal das colunas, tipos observados e formatos, sem reproduzir dados pessoais dos exemplos.

| Layout | Colunas | Particularidades |
|---|---:|---|
| Clientes | 41 | Pessoa, documento, IE, contatos, endereços principal/entrega/cobrança |
| Fornecedores | 29 | Cadastro separado, dados bancários textuais |
| Produtos | 35 | Natureza, preços, estoque, tributação, CFOP, CST |
| Veículos | 13 | Nomes em snake_case, id, proprietário, placa/chassi/renavam |
| Contas a pagar | 16 | Fornecedor, documento, parcelas, datas, valores |
| Contas a receber | 17 | Cliente, documento, parcelas, representante, recebimento |
| OS cabeçalhos | 13 | Número externo, cliente, veículo, abertura, observação |
| OS itens | 7 | Número externo, produto/serviço, quantidade, valores, descrição livre |
| OS juntos | 19 | Cabeçalho e itens repetidos por linha |
| Vendas cabeçalhos | 7 | Número externo, cliente, data, vendedor |
| Vendas itens | 7 | Número externo, produto, unidade, quantidade, valores |
| Vendas juntos | 13 | Cabeçalho e itens repetidos por linha |

## Contrato das regras

- Originais e modelos imutáveis. Saídas nunca sobrescrevem arquivos. Nenhuma linha inválida é descartada; exportação final bloqueia erros. Relatórios podem ser exportados com erros, sem mascarar rejeições.
- Máximo de 10.000 linhas incluindo cabeçalho. Partes relacionadas têm os mesmos grupos de OS/vendas, mantêm a ordem e nunca dividem um grupo. Se um único grupo ultrapassar o limite, bloquear e explicar. Itens separados exigem base de cabeçalhos para validar vínculos e exportar em conjunto.
- Identificadores são texto, sem completar dígitos, sem notação científica e sem arredondamento. Valores numéricos de origem potencialmente danificados exigem revisão. Formatação explícita com zeros no Excel pode ser preservada, com rastreabilidade.
- CPF não recebe IE. IE/RG composto é separado por pessoa apenas quando a identificação é inequívoca. RG pode ser acrescentado à saída por regra explícita, mantendo o modelo intacto. IE de pessoa física sem origem identificada como RG gera erro para revisão.
- Contatos evidentemente inválidos ficam vazios, com aviso e rastreio. CEP/documento malformado permanece para revisão, bloqueando exportação; não inventar valores.
- UF principal obrigatória em clientes/fornecedores. Sigla válida não prova compatibilidade geográfica. Usuário registra fonte e confirmação de localidade/endereço; falta ou dúvida bloqueia saída, sem pesquisar/enviar endereço automaticamente.
- Clientes: decisão obrigatória por conversão sobre aplicar `ATIVO`; se não, conservar origem. Regime vazio recebe `Normal`.
- Produtos: natureza deve vir da origem ou decisão explícita. Serviços recebem `09`, `SERVIÇOS`, `5933/6933`. Produto genérico não prova categoria `00`. Categoria do sistema só é exportada quando confirmada. Mercadoria com situação vazia recebe `VENDA NORMAL`, CFOP `5.102/6.102`. Óleo inequívoco requer revisão de classificação e fonte dos CFOP ST; não usar palavra óleo em peças como classificador automático. Não mapear CSOSN para CST.
- KM alfanumérico não é convertido por remoção de letras. Revisão permite movê-lo para modelo apenas após confirmação explícita. Não inserir diagnósticos em observações do cliente.
- Relatórios Markdown, TXT e JSON contêm contagens, problemas, regras, decisões e colunas omitidas. Auditoria detalhada local inclui valores de antes/depois; é dado sensível, exportado somente por opção explícita. Histórico SQLite guarda metadados e contagens, sem registros, caminhos completos ou amostras.

## Conflitos e ambiguidades tratados explicitamente

1. **Layout fixo × omissão de colunas vazias:** documentação de negócio manda omitir. Tela exige escolher política, mostra colunas omitidas e registra decisão. Ordem relativa e grafia das remanescentes vêm do modelo. Modo completo também está disponível por escolha explícita, registrado como exceção.
2. **`Ativo = Sim` nos exemplos × `ATIVO` na regra:** regra prevalece somente após escolha do usuário. Nunca generalizar a confirmação histórica da Riske.
3. **`Tipo do item` descritivo × `Tipo do Item` codificado:** campo do modelo é preservado como natureza, código documentado é acrescentado à saída como coluna distinta. Não normalizar os dois cabeçalhos para o mesmo campo. Tela e relatório exibem essa extensão e exigem ciência do conflito.
4. **Modelos não vazios:** exemplos não são defaults. Não tratá-los como dados sintéticos de teste, nem copiar seus dados para testes.
5. **Obrigatórios, enumerações, escalas e limites não especificados:** não inferir obrigatoriedade por exemplo preenchido. Validar somente regras expressas e integridade técnica. Campos de vínculo são exigidos para divisão/vinculação segura. O ERP precisa validar requisitos não documentados antes de produção.
6. **UF on-line × funcionamento off-line:** bloquear UF não resolvida e permitir correção com fonte. Nenhum preenchimento por inferência; revisão da compatibilidade é humana e auditada.
7. **Parciais:** seleção assistida diversificada de cinco registros/cabeçalhos distintos, com cenários sem cobertura no relatório; itens associados são preservados. Não criar V4 ou copiar modelos sem uma conversão solicitada.
8. **PDF e HTML disfarçado de XLS:** PDF é extensão futura, fora dos formatos iniciais; HTML em `.xls` é detectado por assinatura e lido como tabela, nunca como BIFF. Sem extração automática de PDF não se pode declarar reconciliação das OS históricas.
9. **Fiscal:** regras são as instruções fornecidas, não aconselhamento tributário ou catálogo fiscal atualizado. Óleos, natureza e diferenças com fonte permanecem visíveis, sem substituição silenciosa.
10. **Evolução do Markdown:** aplicação compara hash com a versão auditada. Se mudar, bloqueia processamento até atualizar o perfil declarativo e o hash mediante nova revisão. Não interpretar prosa livre automaticamente como código.

## Escopo de comprovação

Testes usam exclusivamente dados sintéticos e cabeçalhos dos modelos. Testes locais provam o comportamento do conversor, não aceitação em ERP, autenticação externa ou funcionamento no Windows sem execução naquele sistema.
