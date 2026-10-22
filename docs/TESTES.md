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

`--self-test`: teste sintético de leitura/conversão/saída/relatórios disponível no próprio binário sem pytest.

## Validação manual antes de produção

Execute em máquina Windows e Linux alvo; confira abertura, escala de tela, drag and drop, seleção de diretórios, CSV com acentos, base real autorizada, cofre do sistema e cancelamento. Valide relatórios e faça importação parcial no ERP. Requisitos do ERP ausentes na documentação precisam ser confirmados e adicionados ao perfil. Testes locais não provam aceitação do ERP nem disponibilidade de provedores externos.
