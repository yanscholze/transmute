# Estratégia de testes

Todos os registros de teste são sintéticos. Cabeçalhos estruturais dos modelos podem ser consultados; exemplos preenchidos não são usados como fixtures.

```bash
mkdir -p .local
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --basetemp=.local/test-tmp -q
.venv/bin/ruff check app scripts tests
.venv/bin/python run.py --self-test
QT_QPA_PLATFORM=offscreen .venv/bin/python run.py --smoke-test
```

`test_core.py`: hashes de originais, versões, drift de regras, documentos, zeros, CSV, HTML XLS, abas, cabeçalhos duplicados, mapeamento, CPF/IE/RG, contatos, UF, classificação, tributação, KM, fórmulas, exportação, 20.005 registros, divisão, vínculos e cancelamento.

`test_ai.py`: schemas inválidos, chaves duplicadas, NaN/booleano, redaction de cabeçalhos/células, injection como dado, protocolos HTTP via MockTransport, fallback e cofre inseguro. Não há chamadas reais de API.

`test_workspace.py`: biblioteca apontada/importada, modelo genérico, regras declarativas, revisão imutável, branding, mudança de regras após processamento, metadados mínimos e cópia de diagnósticos.

`test_ui.py`: QApplication real offscreen, carregamento em thread, navegação, mapeamento, decisões, processamento, correção e revalidação. Captura a tela de revisão para inspeção visual. Não depende de automação por coordenadas.

`test_import_projects.py`: trabalhos nomeados, várias categorias, todas as abas/tabelas, PDF posicional com zeros/coordenadas, rejeição de PDF sem tabela, conferência obrigatória, arquivo com erro preservado, drift de cabeçalho, correções retomadas, relatórios detalhados e rollback de cancelamento. OS com par único é exportada; cabeçalhos duplicados deixam o trabalho pendente, sem publicação incompleta, e mantêm diagnósticos individuais.

`test_import_ui.py`: início com trabalhos, validação dos passos, fluxo completo com duas categorias, revisão/correção pendente persistida, reprocessamento, cor global, logo copiada com tamanho/intensidade e retomada após reabrir. Capturas das telas são sintéticas.

`test_dashboard.py`: fórmula pelo último estado de cada trabalho, ausência de resultados, 0% real, contraste em ambos os modos e cores extremas, sidebar com nomes acessíveis e preferência persistida, navegação para todas as páginas, atalhos, busca, abertura de trabalho recente, copiar/abrir caminhos e editor das regras. Trocar claro/escuro/acento preserva uma sessão realmente processada. Captura temas, menu expandido e janela 1100×760, verificando ausência de rolagem horizontal no dashboard. Usa estado isolado, sem inserir exemplos no banco real. A documentação explica o comportamento em DASHBOARD.md.

`--self-test`: teste sintético de leitura CSV/PDF, conversão/saída/relatórios e QtPdf disponível no próprio binário sem pytest. O PDF mínimo é criado no diretório temporário pelo próprio teste, sem biblioteca de geração adicional.

PDFs em `tests/fixtures` são exclusivamente sintéticos, com grades/descritivos artificiais. O leitor é exercitado em documento de duas páginas e documento sem tabela. Isso não prova reconhecimento de qualquer layout externo ou OCR.

## Validação manual antes de produção

Execute em máquina Windows e Linux alvo; confira abertura, escala de tela, drag and drop, seleção de diretórios, CSV com acentos, base real autorizada, cofre do sistema e cancelamento. Valide relatórios e faça importação parcial no ERP. Requisitos do ERP ausentes na documentação precisam ser confirmados e adicionados ao perfil. Testes locais não provam aceitação do ERP nem disponibilidade de provedores externos.

`test_distribution.py`: fechamento determinístico SQLite com rollback/handles liberados; estado instalado fora do programa com override explícito; staging com hashes, modelo vazio e recusa de ZIP inseguro. O workflow Windows executa a suíte nativamente e valida instalar, rodar e remover o Setup sem apagar dados.


## Distribuição 1.2 concluída

87 testes na fonte Fedora e 87 no runner Windows nativo. `test_import_ui.py` verifica também que ciclos de widgets aposentados são coletados na thread gráfica, com GC suspenso no worker e restaurado ao terminar. O self-test da fonte e do executável verifica a liberação dos PDFs ao sair do diretório temporário.

Windows: NSIS instalado e removido no próprio runner, hashes e conversões conferidos, interface capturada com backend `windows`. Fedora 44: RPM instalado/removido em container, executado por usuário comum; self-test, Qt offscreen/xcb em Xvfb, `rpm -V` e preservação de estado passaram. Comandos, versões, workflow e limites em VALIDACAO_FINAL.md. Não executar scripts de instaladores dentro de Wine como substituto dessa validação.


## Estúdio 1.3

`test_studio.py` cobre recuperação de perfil temporário sem substituir perfil customizado, CTP/CTR juntos, cobertura e sobreposição, junção exata de estoque, duplicidade de chave, OS com peças/serviços, invariantes de snapshot, pastas/histórico, exclusões explícitas, saídas vazias, constantes auditadas, correções que não migram de registro e regras locais com contagens de alterações.

`test_studio_ai.py` valida planejamento/auditoria por HTTP simulado para OpenAI/Gemini/Claude, isolamento de credenciais/modelos, respostas inválidas/interrompidas e parser de ambiente sem execução. `test_studio_ui.py` percorre criar projeto → consulta consentida simulada → plano → aprovação → execução → auditoria → exportação → correção/reexecução, além da seleção de tabelas, editor de três providers e acessibilidade do rodapé em janela pequena. Os testes clássicos permanecem, com modo clássico explicitamente escolhido onde esse fluxo é o objeto do teste.

Build/instalador abrem o binário duas vezes com o mesmo estado e verificam o perfil durável, reproduzindo a falha reportada no executável. Fakes não comprovam autenticação de APIs; consultar VALIDACAO_FINAL.md para execução efetiva e limites.
