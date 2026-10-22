# Conversor de Bases

Aplicativo desktop local para preparar bases para importação em ERP. Windows e Linux, com conversão determinística, revisão dos resultados, relatórios e IA opcional. A tela inicial permite configurar a biblioteca e a identidade da aplicação.

## Abrir

No pacote Linux, extraia o ZIP em uma pasta gravável e execute `ConversorDeBases`. O pacote inclui Python e as bibliotecas; não exige instalação de Python. No Windows, o mesmo processo usa `ConversorDeBases.exe`, gerado pelo build nativo Windows.

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

## Tela inicial e white label

- **Apontar pasta de modelos:** lê recursivamente arquivos XLSX de uma pasta escolhida, sem alterá-los. Não exige nomes específicos de arquivo.
- **Importar planilhas:** copia os modelos escolhidos para a biblioteca local. Não é upload para internet.
- **Regras aplicáveis:** escolha Genérico para layouts personalizados ou associe explicitamente uma família conhecida. A associação define regras de domínio, portanto precisa corresponder à documentação da biblioteca.
- **Selecionar arquivo .md / Abrir e editar regras:** documentação e perfil executável lado a lado. Uma revisão aprovada cria novas cópias locais. Os arquivos de referência escolhidos permanecem intactos.
- **Nome e cor:** altera o nome da janela, marca da navegação e cor principal. Escolha uma cor que mantenha texto branco legível. Nome técnico do executável, serviço de cofre e formato de relatórios são estáveis para preservar compatibilidade e não mudam com o branding.

Modelos novos começam em modo genérico. Esse modo preserva valores, aplica integridade técnica e executa apenas regras declaradas no perfil. Não adivinha regras tributárias, campos obrigatórios ou defaults a partir dos exemplos.

O editor não interpreta prosa arbitrária como código. Quando mudar o Markdown, revise também as operações executáveis. A aplicação compara hashes e bloqueia exportações processadas com regras anteriores. Consulte [docs/REGRAS.md](docs/REGRAS.md).

## Converter uma base

1. Na tela inicial, confira modelos e regras; clique em **Nova conversão**.
2. Arraste ou selecione XLSX, XLS ou CSV. Escolha o modelo de destino, aba e linha do cabeçalho. A prévia mostra até vinte linhas.
3. Confirme encoding e delimitador do CSV. A detecção sugere UTF-8, UTF-16 ou Windows-1252 conforme conteúdo; outros encodings podem ser informados. Confira acentos visualmente.
4. Confira o mapeamento. Correspondências exatas e aliases conhecidos são confirmados automaticamente; semelhanças, histórico e IA exigem confirmação. Duplicidades são identificadas por IDs físicos C1, C2 etc.
5. Em **Regras e conflitos**, escolha omitir colunas vazias ou manter o layout completo; confirme os conflitos. Para clientes, escolha expressamente se aplica ATIVO nesta conversão. Registre conferência geográfica e fontes quando a família a exigir.
6. Clique em **Processar e validar**. Erros não descartam registros. A prévia oferece paginação, busca, filtro por severidade e comparação original → transformado.
7. Selecione linha/campo e clique **Corrigir campo**. A alteração fica pendente até **Revalidar correções**. Correções jamais alteram o arquivo original.
8. Exporte a planilha e escolha também a pasta de diagnósticos usada pela empresa, por exemplo `Parciais/Vn`. Arquivos vão para um diretório novo com nome único. Relatórios acompanham a saída e são copiados para a pasta de diagnósticos escolhida.

Com erros, somente o relatório pode ser exportado. A aceitação no ERP deve ser comprovada em importação de teste; validação local não conhece regras que o ERP não documentou.

## OS e vendas vinculadas

Para modelos separados, habilite a base vinculada e selecione cabeçalhos e itens da mesma família/versão. Mapeie e confira as duas bases. Itens órfãos e cabeçalhos duplicados bloqueiam a saída. Cabeçalhos sem itens geram aviso. Não há deduplicação silenciosa.

Arquivos têm até 10.000 linhas incluindo cabeçalho. A divisão usa os mesmos grupos em cabeçalhos/itens e mantém todos os itens de um grupo juntos. Grupo acima do limite ou grupos intercalados que tornem impossível preservar ordem e vínculos bloqueiam a exportação. O relatório explica o problema.

**Parcial de teste** seleciona até cinco registros/grupos distintos, priorizando cenários diferentes. Todos os itens vinculados aos grupos selecionados são mantidos. A seleção aparece no relatório; não garante cobertura de todos os cenários. A revisão e a validação abrangem a base completa antes da exportação da parcial.

## Integridade e privacidade

- Originais e modelos não são editados. Identificadores permanecem texto na saída.
- Identificador já numérico no Excel gera problema, pois zeros/precisão podem ter sido perdidos antes da leitura. Formato explícito de zeros é preservado e auditado. Acima de quinze dígitos, corrija a partir de fonte confiável.
- Fórmulas recebidas não são executadas. Fórmula em campo mapeado exige valor revisado. Textos iniciados por `=`, `+` ou `@` vindos de CSV são exportados como texto XLSX.
- Vazio não vira zero. CPF/CNPJ inválido não é completado. Validação atual de documento cobre CPF/CNPJ numéricos com dígitos verificadores; outros formatos permanecem para revisão, sem alteração de caracteres.
- Histórico guarda data, layout, contagens e resultado. Não guarda células, amostras ou caminhos completos.
- Prévia e auditoria usam SQLite temporário em `.local/sessions`, removido ao fechar a conversão. Interrupção abrupta pode deixar arquivos temporários: feche todas as instâncias antes de removê-los. Não há promessa de apagamento forense de disco/SSD.
- Auditoria detalhada é opcional e contém dados sensíveis originais e transformados. Relatórios podem conter nomes de arquivos, cabeçalhos, fontes e justificativas inseridas pelo usuário; trate-os de acordo com a política da empresa.

Consulte [docs/PRIVACIDADE.md](docs/PRIVACIDADE.md).

## IA opcional

OpenAI, Gemini e Claude têm adapters separados; modelo é configurado pelo usuário de acordo com sua conta. Não há modelo pago selecionado automaticamente. Configure provedor, modelo, chave e timeout em **Configurações**. Chaves são mantidas em memória ou no cofre seguro do sistema; não existe fallback para arquivo de texto.

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
    exporters/         Divisão, XLSX textual e relatórios
  ai/                  Providers, schema, sanitização, cofre e fallback
  storage/             Biblioteca, revisões, perfis e histórico mínimo
  ui/                  Telas separadas por responsabilidade
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

## Arquivos fornecidos preservados

`INSTRUCOES_CONVERSOES.md` e `#PLANILHAS DE BASE/` continuam sendo referências originais. [docs/DESCOBERTA.md](docs/DESCOBERTA.md) descreve as regras e conflitos encontrados, e `docs/originais.sha256.json` registra os hashes anteriores à implementação. Nenhum dado dos exemplos foi incorporado aos testes.
