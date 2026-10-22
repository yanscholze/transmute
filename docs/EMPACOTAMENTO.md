# Distribuição, atualizações e personalização

## Instaladores 1.2

O usuário aprovou o dashboard em 22/10/2026 e autorizou .exe/.rpm. Windows deve usar **Windows nativo**, sem Wine. `.github/workflows/build.yml` compila com Python/PyInstaller no runner Windows, cria Setup com NSIS e testa instalação silenciosa, hashes, self-test, abertura Qt e desinstalação preservando dados. O job Linux é independente (`fail-fast: false`). A execução do workflow não publica GitHub Release automaticamente.

`scripts/package_installers.py` recebe um ZIP nativo produzido por build.py, verifica hashes, assinatura de formato PE/ELF e ausência de linhas nos modelos, adiciona o preset público de `packaging/brand.json` e `installation.json`, e cria novo instalador. Não lê estado pessoal, correções, credenciais ou importações reais. Arquivos finais ficam em `dist/releases/1.2.0/` e não são sobrescritos silenciosamente.

Windows: executar `Transmute-1.2.0-Windows-x64-Setup.exe`. Instala para o usuário em `%LOCALAPPDATA%\Programs\Transmute`, com atalhos no menu Iniciar e desinstalador. Exige Windows 10/11 de 64 bits. Runtime é incluído; não exige Python ou Wine. Instalador não possui assinatura Authenticode neste projeto.

Fedora: `sudo dnf install ./transmute-1.2.0-1.fc44.x86_64.rpm`. Arquivos imutáveis ficam em `/opt/transmute`, launcher em `/usr/bin/transmute` e atalho no menu de aplicativos. O RPM contém runtime Python/Qt; dependências gráficas do sistema são declaradas. É uma distribuição externa com runtime empacotado, não um pacote submetido ao repositório oficial Fedora. Campo LicenseRef-NotSpecified documenta a ausência de licença própria escolhida pelo titular, sem inventar uma licença para o código. Licenças das dependências continuam incluídas.

`installation.json` seleciona estado por usuário: Windows `%LOCALAPPDATA%\Transmute`; Linux `${XDG_DATA_HOME:-~/.local/share}/transmute`. `CONVERSOR_STATE_DIR` continua tendo prioridade. Atualizar ou desinstalar não remove esses dados. O NSIS enumera somente arquivos da distribuição ao remover o programa; arquivos desconhecidos inseridos manualmente na instalação também não são apagados recursivamente. A distribuição ZIP continua portátil, com `.local` ao lado do executável.

Para RPM, após obter o ZIP Linux nativo:

```bash
.venv/bin/python scripts/package_installers.py --linux-zip CAMINHO_DO_ZIP
```

Para Windows, execute no Windows com NSIS instalado:

```powershell
python scripts/package_installers.py --windows-zip CAMINHO_DO_ZIP --makensis "C:\Program Files (x86)\NSIS\makensis.exe"
python scripts/validate_installer.py CAMINHO_DO_SETUP_EXE
```

`packaging/transmute.spec` desabilita strip do binário PyInstaller, preservando o runtime anexado. `packaging/windows.nsi` usa instalação por usuário. Receitas, preset e ícone são editáveis. Consulte VALIDACAO_FINAL.md para distinguir o que foi executado dos passos ainda pendentes.

## Assets para download

A entrega validada fica em `dist/releases/1.2.0/`, com os dois instaladores, `LEIA-ME-INSTALACAO.md`, `SHA256SUMS.txt` e evidências. Publique-os como assets de uma GitHub Release para obter links de download direto. Não versionar os binários grandes no histórico Git. O workflow autorizado gerou artefatos de Actions; nenhuma Release foi criada automaticamente.

O EXE final vem do workflow 39830335195, commit 1a696c5. O RPM vem do ZIP Fedora `Transmute-1.2.0-Linux-x86_64-20261022-151945.zip`, da mesma revisão de código. Os documentos externos de entrega registram a validação após os builds; os documentos embutidos são o snapshot disponível durante a compilação. Veja VALIDACAO_FINAL.md para o registro consolidado.

## Build nativo

Instale dependências de desenvolvimento no `.venv` e execute `python scripts/build.py` com esse Python. No Windows use `.venv\Scripts\python`; Linux usa `.venv/bin/python`.

PyInstaller inclui intérprete, dependências, módulos UI e perfil original. O script acrescenta documentos, licenças e modelos derivados vazios. Não copia `.local`, histórico, sessões, credenciais, `.env`, caches ou exemplos preenchidos. Originais permanecem no projeto.

Cada release usa diretório timestamped em dist, preservando releases anteriores. O script testa o próprio binário com --self-test e --smoke-test e verifica integridade do ZIP. SHA256.json registra o conteúdo do pacote. Logs de build não comprovam execução em outro sistema.

Build Windows exige Windows. Workflow `.github/workflows/build.yml` contém matriz Windows/Linux e pode ser disparado manualmente em um repositório GitHub. O workflow foi enviado à branch build/installers-1.2.0 e disparado com autorização do usuário. O RPM usa payload compilado nativamente no Fedora 44 (glibc 2.43); a receita declara esse mínimo. O ZIP do job Ubuntu é uma distribuição independente: no teste de compatibilidade, seu backend Qt/xcb falhou no Fedora, e ele não foi usado no RPM final. Compatibilidade com outras distribuições requer execução correspondente.

## Estrutura portátil

```text
ConversorDeBases[.exe]
INSTRUCOES_CONVERSOES.md
#PLANILHAS DE BASE/
docs/
licencas/
SHA256.json
LEIA-ME.txt
```

O app não depende de código-fonte, ambiente Python externo ou antigos arquivos de cliente. Na primeira abertura cria `.local` na pasta do executável. Se a pasta não for gravável, defina `CONVERSOR_STATE_DIR` para um diretório autorizado.

Modelos e regras podem ser escolhidos em Biblioteca mesmo se as referências padrão estiverem ausentes. Não renomeie executável/dependências internas para personalizar: use nome, cor global e logo em Aparência. Para uma distribuição pré-configurada, forneça modelos/regras desejados e `regras_perfil.json` aprovado ao lado do executável. Novas famílias desconhecidas devem permanecer genéricas até configuração explícita.

Não redistribua a pasta `.local` de uma instalação em uso: pode conter base temporária, mapeamentos, referências privadas e configurações. Para levar apenas identidade/configuração, configure uma instalação limpa. Os instaladores EXE/RPM são descritos acima; assinatura de código, MSI/AppImage/DEB e atualização automática permanecem fora desta entrega.

## Distribuição de outra biblioteca/marca

Configure a biblioteca pela UI, revise suas regras e identidade e execute, com o Python de desenvolvimento:

```bash
.venv/bin/python scripts/build.py --library .local/workspace
```

O diretório informado precisa conter workspace.json. O script lê apenas modelos, Markdown, perfil aprovado, nome/cor, logo/parâmetros visuais e associações de família. Cria cópias vazias dos modelos, `regras_perfil.json` e `library_preset.json` com caminhos relativos. A logo selecionada, se existente, é copiada para `marca/logo.ext`; tamanho, intensidade e posição acompanham o preset. Não copia o histórico, trabalhos, correções ou cofre. A geração é bloqueada se o hash das regras não corresponder ao perfil aprovado.

Modelos da mesma pasta de origem permanecem juntos no pacote: esse vínculo estrutural permite reconhecer cabeçalhos/itens da mesma versão. Pastas de nome repetido recebem prefixos distintos, sem misturar conjuntos. Não mover cada modelo para um diretório isolado durante o build.

O smoke test do binário usa estado novo por release para realmente carregar o preset. O self-test padrão depende da família Veículos da biblioteca original e é executado automaticamente apenas no build padrão. Ele verifica CSV, PDF sintético com grade, exportação e carregamento QtPdf. A validação independente `scripts/validate_release.py ARQUIVO.zip` executa também esse teste no pacote extraído; só se aplica a bibliotecas compatíveis com esse modelo. Em biblioteca personalizada, execute uma conversão sintética correspondente ao próprio modelo antes de distribuir. O nome técnico do executável permanece estável; nome visual, cor e logo vêm do preset.

## Licenças

PySide6/Qt possui condições LGPL/GPL/comerciais. Arquivos de licença das dependências instaladas são copiados ao pacote; mantenha-os. O responsável pela distribuição deve conferir suas obrigações de licença, inclusive disponibilidade de componentes e possibilidade de substituir bibliotecas conforme a modalidade aplicável. O projeto não seleciona uma licença proprietária para o código criado sem decisão do titular.

## Troca de versão

Extraia versão nova em pasta distinta. Se migrar estado, feche instâncias e faça backup controlado de `.local`. Confira referências absolutas em workspace.json após mover pastas. Depois revalide modelos/regras e execute uma conversão sintética. Não há migração automática de schema de histórico além de criação das tabelas atuais; alterações futuras precisam de migração versionada.
