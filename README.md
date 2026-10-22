# Conversor de Bases

Aplicativo desktop local para preparar bases para importação em ERP. Windows e Linux, com conversão determinística, revisão dos resultados, relatórios e IA opcional. O dashboard inicial reúne atalhos, últimas importações, indicadores e fontes configuradas. A área Importações mantém trabalhos nomeados, com categorias, arquivos, andamento e resultados próprios. Biblioteca e aparência ficam em áreas separadas.

Pasta atual do projeto: `/home/yanscholze/Documentos/Company/Conversor` (renomeada de `Importações` em 22/10/2026). As referências da biblioteca local e os scripts do ambiente virtual foram ajustados ao novo caminho. O documento original de regras mantém sua descrição histórica, sem alteração. Backups da configuração anterior ficam em `.local/relocation-backup-*`; logs e artefatos antigos conservam os caminhos de quando foram gerados.

## Abrir

No pacote Linux, extraia o ZIP em uma pasta gravável e execute `ConversorDeBases`. O pacote inclui Python e as bibliotecas; não exige instalação de Python. No Windows, o mesmo processo usa `ConversorDeBases.exe`, gerado pelo build nativo Windows.

A distribuição 1.2 também tem instalador Windows (`Transmute-1.2.0-Windows-x64-Setup.exe`) e RPM Fedora (`transmute-1.2.0-1.fc44.x86_64.rpm`). Windows é compilado/testado em runner Windows nativo, sem Wine. No Fedora instale com `sudo dnf install ./NOME_DO_PACOTE.rpm` e abra Transmute no menu. Os instaladores mantêm estado por usuário fora da pasta do programa; detalhes e receitas estão em [docs/EMPACOTAMENTO.md](docs/EMPACOTAMENTO.md).

Para desenvolvimento, dentro desta pasta:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python run.py
```

No PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python run.py
```

Use sempre o mesmo ambiente virtual para instalar, testar e executar. O desenvolvimento local foi realizado com Python 3.14; o código exige Python 3.12 ou superior. `requirements.lock` registra o ambiente Linux usado, sem credenciais. Em outra plataforma, instale as dependências do `pyproject.toml`, pois bibliotecas de cofre são específicas do sistema.

## Navegação e white label

**Dashboard** é a tela inicial, com identidade Soft UI: fundo neutro, painéis arredondados, sombras suaves e destaque personalizável. Mostra quatro importações recentes, total/prontas/pendências, taxa de sucesso local, atalhos para todas as áreas e os caminhos das regras/planilhas de base. Caminhos podem ser copiados ou abertos no gerenciador de arquivos; o atalho das regras abre o editor existente. Sem trabalhos, exibe instruções para começar e nenhum percentual fictício.

A **sidebar** alterna entre ícones e ícones com rótulos pelo botão de menu; sua escolha é lembrada localmente. Ícones possuem nomes acessíveis e tooltips. A busca do cabeçalho abre os resultados em Importações ao pressionar Enter. O botão de tema alterna claro/escuro sem interromper sessões.

**Importações** lista nome, categorias, quantidade de arquivos, andamento e atualização de cada trabalho. Possui pesquisa por nome, filtro por andamento e o botão **Nova importação**. Clique duas vezes em uma linha para abrir seu resumo. O histórico técnico anterior continua disponível em **Diagnóstico**.

Em **Biblioteca**, configure os modelos de destino e as regras. As planilhas recebidas de um cliente são anexadas à importação; modelos são a estrutura da saída. A biblioteca aceita uma pasta externa ou cópias locais dos modelos selecionados:

- **Apontar pasta de modelos:** lê recursivamente arquivos XLSX de uma pasta escolhida, sem alterá-los. Não exige nomes específicos de arquivo.
- **Importar planilhas:** copia os modelos escolhidos para a biblioteca local. Não é upload para internet.
- **Regras aplicáveis:** escolha Genérico para layouts personalizados ou associe explicitamente uma família conhecida. A associação define regras de domínio, portanto precisa corresponder à documentação da biblioteca.
- **Selecionar arquivo .md / Abrir e editar regras:** documentação e perfil executável lado a lado. Uma revisão aprovada cria novas cópias locais. Os arquivos de referência escolhidos permanecem intactos.

Em **Aparência**, configure nome, **tema claro ou escuro**, **cor de destaque** e logo de fundo. O laranja da referência é um exemplo; nenhuma cor é obrigatória. Os temas usam superfícies neutras próprias, enquanto a cor escolhida aparece nas ações, marca, realces e indicadores nos dois modos. Texto e foco usam contraste adequado, inclusive com destaques claros/escuros. Campos, tabelas, abas, popups e barras de rolagem acompanham o tema. A prévia também mostra o modo escolhido antes de salvar.

A logo aceita PNG, JPG e WebP, até 10 MB e 16 milhões de pixels. É copiada para a biblioteca local, sem alterar a imagem recebida. Ajuste **tamanho (10–100% da área disponível)**, **intensidade (0–25%)** e posição central ou inferior direita, conferindo a prévia antes de salvar. A imagem mantém sua proporção e fica atrás do conteúdo. Há opção para removê-la. Alterar aparência preserva o processamento em curso.

Nome técnico do executável, serviço de cofre e formato de relatórios são estáveis para preservar compatibilidade. A identidade configurada também pode ser incluída em um pacote white label.

A taxa do dashboard é **(prontas + exportadas) / trabalhos com resultado**. Entram no denominador os estados Pronta para exportar, Exportada e Revisar pendências; aguardando e interrompidos ficam fora. Cada trabalho conta uma vez, pelo último estado salvo. A taxa não mede aceitação no ERP. Detalhes, estados e manutenção em [docs/DASHBOARD.md](docs/DASHBOARD.md).

Modelos novos começam em modo genérico. Esse modo preserva valores, aplica integridade técnica e executa apenas regras declaradas no perfil. Não adivinha regras tributárias, campos obrigatórios ou defaults a partir dos exemplos.

O editor não interpreta prosa arbitrária como código. Quando mudar o Markdown, revise também as operações executáveis. A aplicação compara hashes e bloqueia exportações processadas com regras anteriores. Consulte [docs/REGRAS.md](docs/REGRAS.md).

## Iniciar e acompanhar uma importação

1. Clique em **Nova importação** no dashboard ou na lista, dê um nome ao trabalho e selecione suas categorias: veículos, clientes, fornecedores, produtos/serviços, OS, vendas, contas ou outra tabela.
2. Arraste ou selecione todos os arquivos recebidos: XLSX, XLS, CSV/TSV e PDF. Cada arquivo possui **título**, **categoria**, **modelo de saída** e **finalidade**. Há pelo menos um arquivo por categoria escolhida. Um documento de apoio permanece listado, mas não gera registros; essa decisão é explícita.
3. Confira as regras aplicáveis no último passo. Colunas vazias começam omitidas; para clientes, decida expressamente sobre ATIVO. Registre conferências geográficas/fontes quando exigidas. O assistente mostra opções pertinentes às categorias selecionadas.
4. Inicie a importação. O sistema processa os arquivos em segundo plano e abre o resumo. Todas as abas de planilhas e tabelas detectadas em PDFs ganham entradas próprias. Uma falha fica visível no arquivo correspondente, preservando os demais.
5. Selecione **Revisar arquivo** para conferir a prévia, cabeçalho, encoding/delimitador e mapeamento. Correspondências exatas/aliases conhecidos são automáticos; sugestões incertas, histórico ou IA exigem confirmação. Duplicidades usam IDs físicos C1, C2 etc. CSV sugere UTF-8, UTF-16 ou Windows-1252; confira acentos.
6. Em revisão, compare original → transformado, pesquise e filtre problemas por severidade. Use **Corrigir campo** e **Revalidar correções**. Ajustes manuais pendentes são salvos no trabalho, mas exigem novo processamento antes da saída. Fontes originais nunca são alteradas.
7. Use **Exportar importação** quando todos os arquivos e vínculos estiverem válidos. Escolha uma pasta: o app cria um diretório exclusivo com **Tratadas/** (XLSX e relatórios), **Parciais/** (diagnósticos) e um resumo geral. Cada arquivo/modelo gera seu conjunto; não há fusão silenciosa de tabelas da mesma categoria.
8. Volte à tela inicial para acompanhar ou reabrir o trabalho pelo nome. É possível renomear, adicionar arquivo e editar título/categoria/vínculo. Depois de reiniciar o app, referências e decisões são retomadas; reprocessar recria os resultados temporários. Mantenha as fontes nos caminhos originais ou selecione o novo local na edição do arquivo.

Em **Regras deste trabalho**, alterações invalidam os resultados anteriores. Alterar fonte/modelo também exige reprocessar. A revisão avançada permite exportar um arquivo/lote individual e escolher uma pasta adicional de diagnósticos; a ação **Exportar importação** reúne o trabalho completo.

Com erros, somente o relatório pode ser exportado. A aceitação no ERP deve ser comprovada em importação de teste; validação local não conhece regras que o ERP não documentou.

## PDFs

O leitor usa extração posicional de tabelas com bordas reconhecíveis pelo pdfplumber, preservando página, tabela e coordenadas na origem. Todas as tabelas detectadas são listadas separadamente, até 500 páginas por PDF. Confira cada tabela em **Conferir PDF original**, com visualizador local multipágina, e confirme a conferência nas regras antes da exportação. A detecção de cabeçalho e o mapeamento também precisam corresponder ao documento.

PDF escaneado, texto corrido, protegido ou sem grade reconhecível não é convertido por tentativa: permanece pendente com explicação. Não há OCR nem associação por espaços do texto. Use uma fonte tabular adequada ou marque explicitamente como documento de apoio. Não há garantia de identificar todas as tabelas de qualquer PDF; a conferência humana verifica omissões, quebras de página e alinhamento.

## OS e vendas vinculadas

Anexe cabeçalhos e itens separados com os modelos da mesma família/versão. O trabalho associa apenas um par inequívoco no mesmo **Grupo de vínculo** (inicialmente `principal`) e conjunto de modelos. Para vários lotes, use grupos distintos em **Editar título / categoria / vínculo**. Não basta ter dois arquivos da categoria: escolha os modelos de cabeçalho e itens correspondentes. Pares ausentes ou ambíguos bloqueiam a exportação. A revisão avançada também permite habilitar uma base vinculada manualmente. Itens órfãos e cabeçalhos duplicados bloqueiam a saída; cabeçalhos sem itens geram aviso. Não há deduplicação silenciosa.

Arquivos têm até 10.000 linhas incluindo cabeçalho. A divisão usa os mesmos grupos em cabeçalhos/itens e mantém todos os itens de um grupo juntos. Grupo acima do limite ou grupos intercalados que tornem impossível preservar ordem e vínculos bloqueiam a exportação. O relatório explica o problema.

**Parcial de teste** seleciona até cinco registros/grupos distintos, priorizando cenários diferentes. Todos os itens vinculados aos grupos selecionados são mantidos. A seleção aparece no relatório; não garante cobertura de todos os cenários. A revisão e a validação abrangem a base completa antes da exportação da parcial.

## Integridade e privacidade

- Originais e modelos não são editados. Identificadores permanecem texto na saída.
- Identificador já numérico no Excel gera problema, pois zeros/precisão podem ter sido perdidos antes da leitura. Formato explícito de zeros é preservado e auditado. Acima de quinze dígitos, corrija a partir de fonte confiável.
- Fórmulas recebidas não são executadas. Fórmula em campo mapeado exige valor revisado. Textos iniciados por `=`, `+` ou `@` vindos de CSV são exportados como texto XLSX.
- Vazio não vira zero. CPF/CNPJ inválido não é completado. Validação atual de documento cobre CPF/CNPJ numéricos com dígitos verificadores; outros formatos permanecem para revisão, sem alteração de caracteres.
- O histórico técnico antigo guarda data, layout, contagens e resultado. Os trabalhos nomeados guardam também títulos, caminhos das fontes, opções, mapeamentos, hashes, resultados e correções manuais necessárias à retomada; essas correções podem conter dados pessoais. As bases completas não são copiadas para esse manifesto.
- Prévia e auditoria usam SQLite temporário em `.local/sessions`, removido ao fechar a conversão. Interrupção abrupta pode deixar arquivos temporários: feche todas as instâncias antes de removê-los. Não há promessa de apagamento forense de disco/SSD.
- Auditoria detalhada é opcional e contém dados sensíveis originais e transformados. Relatórios podem conter nomes de arquivos, cabeçalhos, fontes e justificativas inseridas pelo usuário; trate-os de acordo com a política da empresa.

Consulte [docs/PRIVACIDADE.md](docs/PRIVACIDADE.md).

## IA opcional

OpenAI, Gemini e Claude têm adapters separados; modelo é configurado pelo usuário de acordo com sua conta. Não há modelo pago selecionado automaticamente. Configure provedor, modelo, chave e timeout em **IA e perfis**. Chaves são mantidas em memória ou no cofre seguro do sistema; não existe fallback para arquivo de texto.

**Testar conexão** pede consentimento e envia apenas uma estrutura sintética. Em **Sugerir com IA**, a aplicação mostra exatamente o payload a enviar. Por padrão, cabeçalhos desconhecidos são ocultos e células viram tipo/comprimento/quantidade de dígitos. Incluir cabeçalhos originais exige opção explícita.

IA apenas sugere mapeamentos JSON. Não recebe arquivos, ferramentas, caminhos ou acesso às bases. Respostas inválidas/conflitantes são rejeitadas. Sugestões nunca substituem decisões já confirmadas. Depois de confirmadas, passam pelo mesmo motor determinístico.

Fallback é opcional, em ordem, entre provedores configurados e consentidos no diálogo de envio. Falha externa mantém o mapeamento manual disponível.

**CLI:** detecção consulta `--help` das ferramentas instaladas. Somente Claude CLI fica executável quando a versão confirma todos os flags de isolamento, sem ferramentas, MCP, personalizações ou persistência. Codex/Gemini são apenas detectados até haver um contrato igualmente seguro confirmado. Não confundir executável encontrado com autenticação válida. Veja [docs/IA.md](docs/IA.md).

## Estrutura e manutenção

```text
app/
  main.py              Entrada, configuração Qt e logging mínimo
  paths.py             Diretório do aplicativo e estado local
  models.py            Contratos de dados, decisões e cancelamento
  core/
    catalog.py         Descoberta dinâmica de modelos e regras
    importers/         Detecção por conteúdo e leitores iteráveis
    mapping/           Sugestões determinísticas e confirmação
    transformation/    Regras de domínio rastreáveis
    validation/        Validações de valores e integridade
    rules/             Perfil e interpretador declarativo fechado
    session.py         Processamento para revisão em SQLite
    batch.py           Arquivos/categorias, vínculos e exportação do trabalho
    exporters/         Divisão, XLSX textual e relatórios
  ai/                  Providers, schema, sanitização, cofre e fallback
  storage/             Biblioteca, revisões, trabalhos nomeados e histórico
  ui/                  Dashboard, sidebar, assistente, revisão, aparência e biblioteca
tests/                 Dados sintéticos gerados durante os testes
scripts/               Inventário, documentação e build
docs/                  Descoberta, arquitetura e guias de manutenção
```

Cada camada tem contrato e finalidade documentados em [docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md). O índice [docs/CODIGO.md](docs/CODIGO.md) cataloga todos os módulos/classes/funções e pode ser regenerado. Regras específicas não devem ser colocadas em widgets ou providers.

## Verificar e empacotar

```bash
mkdir -p .local
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --basetemp=.local/test-tmp -q
.venv/bin/ruff check app scripts tests
.venv/bin/python run.py --self-test
QT_QPA_PLATFORM=offscreen .venv/bin/python run.py --smoke-test
.venv/bin/python scripts/build.py
```

O build gera executável, modelos derivados **sem exemplos**, regras e documentação em `dist/`. Os modelos originais permanecem intactos. A receita pode ser executada em Windows e Linux; há workflow de CI com matriz dos dois sistemas. Compilação é nativa: executar a receita no Linux não produz nem comprova um EXE Windows.

Veja [docs/EMPACOTAMENTO.md](docs/EMPACOTAMENTO.md), [docs/TESTES.md](docs/TESTES.md) e [docs/VALIDACAO_FINAL.md](docs/VALIDACAO_FINAL.md) para resultados efetivamente obtidos e limitações.

**Etapa atual:** interface aprovada pelo usuário em 22/10/2026; instaladores 1.2 em preparação e validação nos respectivos sistemas. Os ZIPs anteriores em dist são preservados. Resultado efetivamente obtido consta em VALIDACAO_FINAL.md; executar workflow não publica uma Release automaticamente.

## Arquivos fornecidos preservados

`INSTRUCOES_CONVERSOES.md` e `#PLANILHAS DE BASE/` continuam sendo referências originais. [docs/DESCOBERTA.md](docs/DESCOBERTA.md) descreve as regras e conflitos encontrados, e `docs/originais.sha256.json` registra os hashes anteriores à implementação. Nenhum dado dos exemplos foi incorporado aos testes.
