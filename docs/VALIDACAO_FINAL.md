# Validação final — 22/10/2026

## Distribuição 1.2 — instaladores nativos validados

Interface aprovada e empacotamento autorizado pelo usuário em 22/10/2026. Fonte dos binários: commit `1a696c5` na branch `build/installers-1.2.0`. Entrega em `dist/releases/1.2.0/`: `Transmute-1.2.0-Windows-x64-Setup.exe`, `transmute-1.2.0-1.fc44.x86_64.rpm`, guia e SHA256SUMS.txt. Nenhuma GitHub Release foi publicada; os assets estão prontos para publicação pelo usuário.

- **Fonte Fedora 44:** 87 testes passaram em 27,32 s; lint passou. Os 38 hashes de regras/modelos originais continuam iguais. Fixtures e conversões são sintéticas, sem APIs ou dados de clientes.
- **Windows nativo:** [Actions 39830335195](https://github.com/yanscholze/transmute/actions/runs/39830335195), Windows Server 2025 x64, Python 3.12.10 e NSIS 3.11. **87 testes passaram em 16,50 s**. PyInstaller gerou o EXE no Windows. O Setup foi instalado silenciosamente em pasta isolada, todos os hashes instalados foram comparados, o binário converteu CSV/PDF para XLSX com zeros e relatórios, e o QtPdf abriu o PDF sintético. A interface instalada abriu com `QT_QPA_PLATFORM=windows` e gerou captura. Desinstalação removeu o programa e preservou o sentinela no estado por usuário. Não houve Wine na compilação ou validação.
- **RPM Fedora 44 x86_64:** payload compilado no próprio Fedora 44, Python 3.14.8/Qt 6.12.0/glibc 2.43. RPM foi instalado com DNF em container Fedora 44; binário executado como usuário comum, com self-test JSON confirmado, abertura offscreen e abertura Qt/xcb em Xvfb. `rpm -V` não apontou diferenças e `rpm --checksig` confirmou os digests. A remoção via DNF eliminou o aplicativo e manteve o estado/sentinela. A receita declara glibc >= 2.43 e bibliotecas gráficas; não há certificação para outros RPMs/distribuições.
- **Conteúdo:** 36 modelos derivados vazios, regras, preset público Transmute, runtime e licenças. O staging verificou hashes, formato PE/ELF e ausência de dados nos modelos. Não inclui `.local`, histórico, credenciais ou exemplos preenchidos. Estado instalado fica fora da pasta do programa; originais e versões anteriores foram preservados.

A validação nativa encontrou e corrigiu conexões SQLite não fechadas, retenção do arquivo pelo QtPdf, formulários largos no estilo Windows, nome de ZIP truncado pelos pontos da versão e coleta cíclica de objetos Qt em worker Python 3.14. O teste de ciclo de vida verifica que objetos aposentados são coletados na thread gráfica e que a coleta é restaurada ao terminar a tarefa. O payload Ubuntu/Qt testado apresentou falha xcb no Fedora e foi descartado para o RPM; a entrega usa o build Fedora verificado.

Limites: instalador EXE sem assinatura Authenticode, RPM sem assinatura OpenPGP, sem atualização automática. O runner Windows Server comprova execução Windows nativa; não substitui teste manual em cada Windows 10/11, escala de tela, drag and drop, cofre do sistema ou hardware. Nenhuma importação real no ERP ou API externa foi realizada. Capturas, JSONs e logs locais estão em `.local/rpm-validation/` e `.local/windows-native-final.log`; o workflow mantém os artefatos Windows.

## Registro da revisão do dashboard — antes da aprovação

Em 22/10/2026, após a referência visual e a correção sobre temas, **82 testes passaram em 22,01 s** (68 anteriores + 14 casos/variações do dashboard). Lint passou, índice de símbolos foi regenerado e os **38 hashes originais** permanecem preservados. O self-test CSV/PDF/QtPdf da fonte passou. A abertura gráfica nativa Linux com saída automática também passou, além das verificações Qt offscreen.

Implementado e exercitado: dashboard inicial, sidebar recolhível com preferência persistida, atalhos para todas as áreas, quatro trabalhos recentes com abertura direta, busca por nome no cabeçalho, taxa calculada dos últimos estados sem percentual fictício, caminhos de modelos/regras com copiar/abrir, editor de regras, temas claro/escuro, cor livre nos dois modos, persistência e prévia de aparência. Troca de tema/acento preservou uma sessão processada. Aparência mantém Salvar em rodapé fixo e campos em área rolável; o dashboard não cria rolagem horizontal em 1100×760, inclusive com menu expandido.

Telas claras/escuras, menu expandido, janela compacta, estado vazio e revisão avançada foram capturados e inspecionados. As capturas compartilháveis usam apenas dados sintéticos em estado isolado. A pintura dos painéis não cacheia seus controles filhos, evitando recortes encontrados durante navegação/redimensionamento. As cores de erro/aviso/sucesso da revisão também acompanham o modo.

Naquela etapa, fonte e documentação ficaram disponíveis para avaliação. **Nenhum novo .exe, .rpm ou ZIP foi gerado naquela revisão**, conforme a instrução de aguardar aprovação da interface. Os pacotes listados abaixo são registros de entregas anteriores. Abertura Linux não comprova execução Windows nem aceitação no ERP. Detalhes e fórmula: DASHBOARD.md.

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

- **Windows:** execução nativa e instalador verificados na versão 1.2, descrita no início. Testes manuais em outras versões de Windows, hardware e escala permanecem específicos de cada destino.
- **Outras distribuições Linux:** build local Fedora não prova compatibilidade universal de glibc, drivers e dependências gráficas. Há receita de runner Ubuntu para builds adicionais.
- **ERP:** nenhuma importação real foi realizada. Campos obrigatórios, enumerações e detalhes não declarados no material de origem precisam de confirmação e teste parcial no ERP.
- **APIs/CLI:** nenhum dado real, chave ou chamada paga foi utilizado. Protocolos HTTP e isolamento de argumentos foram testados com mocks; --help das CLIs foi inspecionado. Login, modelos disponíveis, cotas e respostas reais dependem das contas do usuário.
- **Geografia/tributação:** sem pesquisa automática de UF ou classificação fiscal externa. Operador registra conferência/fonte; pendências bloqueiam exportação. Código não transforma decisões históricas da Riske em defaults para outras empresas.
- **PDF na versão 1.0:** não implementado naquela entrega. Na versão 1.1 há extração posicional limitada a tabelas reconhecíveis, descrita abaixo; não há OCR nem validação de documentos reais.
- **Distribuição:** ZIP portátil e instaladores nativos EXE/RPM na versão 1.2. Sem assinatura de código ou atualização automática. Revisões/local storage não são sincronizados entre computadores.
- **Disco:** sessões temporárias/relatórios não são criptografados pelo app. Crash pode deixar temporários; remoção normal não é apagamento forense.

## Antes de usar uma base real

Revise o perfil executável e os conflitos aplicáveis, confira UF/documentos a partir da fonte autorizada, faça uma parcial representativa e valide no ERP. Preserve diagnósticos e originais. Amplie regras/testes quando o ERP revelar requisito ainda não documentado.
