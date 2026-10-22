# Distribuição, atualizações e personalização

## Build nativo

Instale dependências de desenvolvimento no `.venv` e execute `python scripts/build.py` com esse Python. No Windows use `.venv\Scripts\python`; Linux usa `.venv/bin/python`.

PyInstaller inclui intérprete, dependências, módulos UI e perfil original. O script acrescenta documentos, licenças e modelos derivados vazios. Não copia `.local`, histórico, sessões, credenciais, `.env`, caches ou exemplos preenchidos. Originais permanecem no projeto.

Cada release usa diretório timestamped em dist, preservando releases anteriores. O script testa o próprio binário com --self-test e --smoke-test e verifica integridade do ZIP. SHA256.json registra o conteúdo do pacote. Logs de build não comprovam execução em outro sistema.

Build Windows exige Windows. Workflow `.github/workflows/build.yml` contém matriz Windows/Linux e pode ser disparado manualmente em um repositório GitHub. Nenhum workflow foi publicado/disparado nesta sessão. Binário local Linux foi construído no Fedora; compatibilidade com outras distribuições/versões de glibc requer teste ou build no runner mais antigo suportado.

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

Não redistribua a pasta `.local` de uma instalação em uso: pode conter base temporária, mapeamentos, referências privadas e configurações. Para levar apenas identidade/configuração, configure uma instalação limpa. Assinatura de código, instalador MSI/AppImage/DEB/RPM e atualização automática não estão implementados; o pacote portátil é a unidade de entrega.

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
