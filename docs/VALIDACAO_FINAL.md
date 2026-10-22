# Validação final — 22/10/2026

## Versão 1.1 — fluxo por importação e aparência

Em 22/10/2026, **68 testes passaram** na fonte Linux, incluindo os 56 anteriores e 12 novos casos de trabalhos/PDF/UI (última suíte: 18,61 s). O lint passou e o índice de código foi regenerado. O self-test da fonte passou com CSV, PDF sintético posicional, zeros textuais, exportação, relatórios e carregamento QtPdf. Nenhum dado real ou chamada externa foi usado. Os 38 hashes das referências originais foram conferidos novamente, sem alterações.

Foram exercitados: trabalho com duas categorias, classificação/títulos por arquivo, processamento em segundo plano, revisão individual, correção pendente salva e retomada, reprocessamento e retorno à lista; todas as abas e tabelas de PDF representadas; falha de arquivo preservada; mudança de cabeçalhos impede reutilizar mapeamento; PDF sem grade rejeitado; exportação de PDF bloqueada sem conferência; relatórios detalhados disponíveis nas pendências; saída Tratadas/Parciais e rollback de cancelamento.

Aparência foi testada em widgets Qt reais offscreen: cor aplicada à paleta completa, importação de logo sintética, tamanho/intensidade persistidos e reabertura. Capturas de início, categorias, arquivos, resumo e aparência estão em `docs/interface-*-v1.1.png`, com dados sintéticos; foram inspecionadas visualmente. A marca/cor local existente (Transmute/laranja) foi preservada. O preset portátil também foi testado com caminho relativo e parâmetros de logo.

A versão 1.1 acrescenta `imports_v1` ao banco existente, preservando histórico/perfis. Manifestos persistem caminhos e correções esparsas potencialmente sensíveis; fontes não são copiadas e resultados completos são temporários. Fechar/reabrir exige reprocessamento. Veja PRIVACIDADE.md.

PDF limita-se a tabelas posicionais reconhecidas pelo pdfplumber, até 500 páginas, com visualizador local e conferência obrigatória. Não há OCR, extração universal, testes com PDFs reais ou prova de completude em documentos externos. Windows/ERP/APIs continuam sem validação real nesta máquina.

O pacote `Conversor-de-Bases-Linux-x86_64-20261022-123824.zip` foi construído com a biblioteca local Transmute. O smoke test do binário passou; a validação independente do ZIP extraído passou com **179 hashes**, **36 modelos vazios**, self-test CSV/PDF/QtPdf e smoke test. Estado local, trabalhos e credenciais não foram distribuídos. Logs ficam em `.local/build-linux-v1.1.log` e `.local/release-validation-v1.1.log`, fora da distribuição. Documentação foi sincronizada ao pacote e o manifesto/ZIP foram recalculados após a última suíte, sem alteração do binário.

## Registro preservado da versão 1.0 — Linux

- Python 3.14.8 em um único `.venv`; PySide6 6.12.0, openpyxl 3.1.5, xlrd 2.0.2, httpx 0.28.1, PyInstaller 6.22.3. Lock do ambiente em requirements.lock.
- **56 testes passaram**, cobrindo parsing, regras, preservação, documentos, contatos, CSV UTF-8/UTF-16/Windows-1252, XLSX, BIFF XLS real, HTML em XLS, mapeamento, providers mockados, JSON inválido, biblioteca configurável, revisão de regras, branding portátil, histórico, exportação e UI.
- Base sintética de **20.005 registros** exportada em **9.999 + 9.999 + 7** registros, cada parte com cabeçalho adicional. Contagens reconciliadas.
- Exportação sintética dos **12 layouts**, incluindo cabeçalhos/itens vinculados; órfãos, duplicidades, grupos grandes/intercalados e cancelamento cobertos por testes específicos.
- Fluxo Qt real offscreen: arquivo → prévia → mapeamento/regras → processamento → correção → nova validação. Editor inicial de Markdown/JSON salvo como revisão local, sem modificar o documento original. Biblioteca inválida não impede recuperar a configuração.
- Interface inicial e revisão capturadas e inspecionadas visualmente. Lint `ruff check app scripts tests` passou. Índice do código regenerado.
- Self-test da fonte passou. Build Linux nativo gera executável com runtime próprio; o pipeline executa self-test e smoke test do binário e valida CRC do ZIP. Não usa Python do usuário final.
- O pacote distribui modelos derivados vazios. Hashes das referências originais são verificados por teste; todos os originais e as regras fornecidas permanecem intactos.

Comandos e saídas do build estão em `.local/build-linux-final.log` na máquina de desenvolvimento. Esse log não é necessário para executar o aplicativo e não é incluído na distribuição. Pacotes e manifestos SHA-256 ficam em `dist/`.

## Recursos implementados

Biblioteca apontada/importada, modelos genéricos ou associados a famílias, editor de regras e perfil declarativo, identidade visual configurável, fluxo desktop completo, drag and drop, escolha de aba/cabeçalho/encoding/delimitador, mapeamento editável e perfis reutilizáveis, prévia original/transformado, validação por severidade, correções/revalidação, pesquisa/filtros/paginação, threads/progresso/cancelamento, divisão preservando vínculos e ordem, relatórios MD/TXT/JSON, auditoria sensível opt-in, histórico mínimo, cofre/memória, adapters OpenAI/Gemini/Claude, fallback consentido e CLI restrita com flags confirmados.

O script de build também aceita biblioteca white label aprovada e gera preset portátil sem estado sensível. A inicialização do preset e seus caminhos são independentes de nomes absolutos da máquina de desenvolvimento.

## Não verificado ou fora do escopo inicial

- **Windows:** código e receita/workflow preparados; nenhum binário ou runtime Windows foi executado aqui. Gerar e testar em runner/máquina Windows.
- **Outras distribuições Linux:** build local Fedora não prova compatibilidade universal de glibc, drivers e dependências gráficas. Há receita de runner Ubuntu para builds adicionais.
- **ERP:** nenhuma importação real foi realizada. Campos obrigatórios, enumerações e detalhes não declarados no material de origem precisam de confirmação e teste parcial no ERP.
- **APIs/CLI:** nenhum dado real, chave ou chamada paga foi utilizado. Protocolos HTTP e isolamento de argumentos foram testados com mocks; --help das CLIs foi inspecionado. Login, modelos disponíveis, cotas e respostas reais dependem das contas do usuário.
- **Geografia/tributação:** sem pesquisa automática de UF ou classificação fiscal externa. Operador registra conferência/fonte; pendências bloqueiam exportação. Código não transforma decisões históricas da Riske em defaults para outras empresas.
- **PDF na versão 1.0:** não implementado naquela entrega. Na versão 1.1 há extração posicional limitada a tabelas reconhecíveis, descrita abaixo; não há OCR nem validação de documentos reais.
- **Distribuição:** pacote portátil, sem assinatura de código, instalador nativo ou atualização automática. Revisões/local storage não são sincronizados entre computadores.
- **Disco:** sessões temporárias/relatórios não são criptografados pelo app. Crash pode deixar temporários; remoção normal não é apagamento forense.

## Antes de usar uma base real

Revise o perfil executável e os conflitos aplicáveis, confira UF/documentos a partir da fonte autorizada, faça uma parcial representativa e valide no ERP. Preserve diagnósticos e originais. Amplie regras/testes quando o ERP revelar requisito ainda não documentado.
