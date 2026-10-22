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
