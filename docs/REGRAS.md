# Regras: documentação, perfil e execução

## Por que existem duas representações

O Markdown é a fonte de negócio para a pessoa que revisa a biblioteca. JSON torna a interpretação explícita e determinística. Não há execução de instruções em prosa, Python, shell ou fórmulas. O editor inicial cria um par novo de arquivos por revisão e atualiza o ponteiro somente ao terminar a gravação.

O perfil original é `app/core/rules/profile.json`. Um perfil portátil personalizado pode ser distribuído como `regras_perfil.json` junto do executável. A biblioteca configurada aponta para seus arquivos em `workspace.json`. Hash de Markdown e perfil são associados à sessão e ao relatório. Mudança posterior exige novo processamento.

## Estrutura do perfil

```json
{
  "version": 1,
  "source_sha256": "calculado pelo editor após aprovação",
  "max_total_rows": 10000,
  "enabled_modules": [],
  "rules": [
    {"id":"NOME_OBRIGATORIO","family":"generic","field":"Nome","operation":"required","severity":"ERRO"},
    {"id":"STATUS_PADRAO","field":"Status","operation":"default","value":"Ativo"},
    {"id":"CODIGO_LIMPEZA","field":"Código","operation":"digits"},
    {"id":"UF_ENUM","field":"UF","operation":"enum","values":["SC","PR","RS"]},
    {"id":"CODIGO_TAMANHO","field":"Código","operation":"length","min":1,"max":20},
    {"id":"DATA_ISO","field":"Data","operation":"date","input_format":"%Y-%m-%d"}
  ]
}
```

IDs são únicos. Cabeçalhos são literais e sensíveis a maiúsculas. Regra de campo ausente no modelo é ignorada, permitindo um perfil para vários modelos; revise essa condição quando criar obrigatórios. `family` omitido equivale a `*`. Severidades: `ERRO`, `AVISO`, `INFORMAÇÃO`. Limite de linhas pode ser menor, nunca maior que 10.000.

| Operação | Semântica | Tratamento de ausência |
|---|---|---|
| required | Exige valor | Erro ou severidade configurada |
| digits | Remove apenas pontuação conhecida, preservando todos os dígitos | Conserva vazio |
| default | Aplica valor textual declarado | Preenche somente vazio; proibido para identificadores críticos |
| uppercase | Maiúsculas | Conserva vazio |
| enum | Exige um dos textos declarados | Conserva vazio; combine com required se necessário |
| length | Comprimento entre min/max | Conserva vazio |
| decimal | Decimal sem arredondar, saída com vírgula | Conserva vazio; separador ambíguo gera erro |
| date | Lê input_format e escreve DD/MM/AAAA | Conserva vazio |

Não use defaults para fabricar informação desconhecida. A lista fechada de operações evita execução de código vindo de regras ou planilhas. Para criar outra operação, altere o interpretador e os testes.

## Módulos de domínio existentes

`contacts`: limpeza e exclusão auditada de contatos evidentemente inválidos em famílias conhecidas.

`clients`: ATIVO apenas após decisão por conversão e Normal para regime vazio em clientes.

`products`: códigos e regras de serviços/mercadorias, sem adivinhar categoria genérica ou tributação de óleos. Conflito da origem com regra fica em aviso/erro e trilha de transformação.

`geography`: UF obrigatória e evidência humana de compatibilidade geográfica em clientes/fornecedores.

O perfil original habilita esses módulos implicitamente; perfis novos devem listar explicitamente os desejados. Modo genérico não aplica os módulos, mesmo que estejam habilitados. Vínculos de OS/vendas, CPF sem IE em cadastros conhecidos e integridade dos identificadores são invariantes de segurança das respectivas famílias.

## Ordem de execução

Leitura textual e metadados → mapeamento confirmado → correções locais rastreáveis → limpeza documentada → regras de domínio → operações declarativas, em ordem → validações finais → revisão → exportação textual.

Uma regra declarativa posterior pode tornar obsoleto o resultado de uma validação declarativa anterior. Organize transformações antes de validadores e revise o relatório; o motor não reordena regras por conta própria. Validações finais de integridade sempre ocorrem após as operações.

## Adicionar modelo/família

Importe o XLSX em Biblioteca ou aponte sua pasta; cabeçalhos são lidos do arquivo. Use Genérico para começar. Depois declare regras com os cabeçalhos exatos. Só associe uma família conhecida quando sua semântica corresponder ao perfil.

Uma família nova com lógica específica exige: registrar nome em `Layout.label`/UI, adicionar regras ao módulo de domínio, testar com dados sintéticos e documentar conflitos. Não basta renomear um arquivo para simular compatibilidade.

## PDF e decisões por trabalho

`Options.pdf_confirmed` registra a conferência humana do documento/tabelas. Sem ela, o core adiciona `PDF_CONFERENCIA` como erro global: permite processar/revisar e exportar diagnósticos, mas impede planilha final. Não é default de domínio nem uma regra que o perfil possa desativar. A UI oferece visualizador do original e opção contextual; a responsabilidade de conferir todas as tabelas permanece do operador. Não há OCR ou preenchimento de colunas ausentes por inferência.

Opções gerais do trabalho valem para os arquivos sem uma revisão específica. Revisão individual pode salvar opções próprias, mapeamentos e correções; alterar Regras deste trabalho descarta as opções individuais e exige reprocessamento de todos. Alterar Markdown/perfil/modelos invalida os snapshots usados na exportação. Um arquivo marcado como apoio não passa pela conversão e fica identificado assim no resumo.


## Regras de projeto no Estúdio 1.3

Instruções em linguagem natural podem ser traduzidas pela IA em regras declarativas de uma saída do plano. As operações são as mesmas da biblioteca. O operador revisa e aprova a revisão exata; o plano não executa prosa ou código. Regras locais não podem definir paralelamente um campo já regulado pela biblioteca, nem usar defaults para fabricar identificadores. As operações do projeto são aplicadas antes das regras declarativas originais, sem desativar módulos/invariantes da biblioteca. Cada mudança mantém rule/before/after e contagens completas.

Separações CTP/CTR, união de fontes e consultas produtos/estoque pertencem à linguagem de composição (studio/plan.py), não a uma regra escondida de widget ou heurística de nome/sinal. Perguntas pendentes bloqueiam aprovação; valores desconhecidos ficam pendentes. A confirmação antiga não é exigida para criar um projeto em planejamento, mas executar exige um plano aprovado e decisões obrigatórias do perfil.
