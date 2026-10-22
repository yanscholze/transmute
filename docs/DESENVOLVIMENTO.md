# Guia de desenvolvimento e manutenção

## Fronteiras de responsabilidade

`models.py` contém dataclasses compartilhadas sem dependência de Qt ou HTTP. `Control` permite cancelamento/progresso sem acoplar o core à interface.

Importers produzem `(linha física, células, problemas estruturais)`; não decidem destino. `Cell` carrega texto, tipo de origem e observação sobre preservação. Colunas são identificadas por posição, permitindo cabeçalhos duplicados sem perda.

Mapping sugere `Decision`; não transforma. Confirmação é exigida para sugestões de menor confiança. Um destino não recebe duas origens. Perfil salvo só guarda cabeçalho/destino e é vinculado ao fingerprint da estrutura.

Engine recebe valores originais, decisões, opções e perfil. Retorna valores, problemas e mudanças, sem editar fonte. `put()` centraliza antes/depois/regra. Para regra nova, use o interpretador declarativo quando suficiente; lógica de domínio fica em transformation/validation.

Session grava linhas em SQLite temporário, com raw/output/problems/changes/severity/groupkey. Mantém hash de origem, modelo, Markdown e perfil. Uma sessão não deve ser usada após `close()`. Todos os caminhos de erro de processamento fecham/removem a sessão criada.

Exporters validam os snapshots, planejam partes, escrevem XLSX e relatórios em diretório de staging. Cancelamento/erro remove o staging. Publicação usa rename. Nomes finais exclusivos impedem sobrescrita de importações anteriores. Relatórios de diagnóstico podem ser copiados para outra pasta escolhida; se essa cópia falhar, o resultado recém-criado é retirado para não anunciar conclusão incompleta.

Providers recebem apenas payload já sanitizado e schema. Não leem arquivos nem ganham ferramenta para alterar o projeto. `service.py` valida resposta e percorre exclusivamente o fallback configurado. Nenhuma resposta entra diretamente em célula.

Storage persistente guarda biblioteca, branding, perfis, histórico mínimo, trabalhos nomeados e configurações sem chaves. O manifesto de trabalho contém caminhos e correções manuais potencialmente sensíveis. Credenciais usam memória ou backend seguro do sistema. `workspace.py` mantém fontes externas como referências e guarda edições/upload de modelos e logo em cópias locais.

UI divide biblioteca, entradas, mapeamento, decisões, revisão, configuração e shell. `Window.run_job` é o ponto de tarefas em thread. Desabilita telas durante operação, mantém Cancelar acessível e espera término antes de fechar. Nunca crie chamadas HTTP ou leitura integral de base dentro de callbacks de widgets.

## Convenções

- Código Python 3.12+, imports absolutos `app.*`, UTF-8.
- Texto de UI/documentação em português; contratos internos em inglês.
- Não adicionar regra de negócio em widget, prompt ou adapter.
- Não usar float para aritmética de negócio; preços/quantidades usam Decimal na interpretação. Valores desconhecidos são preservados ou rejeitados, não completados.
- Uma sugestão não deve virar confirmação só por ter confiança alta de IA.
- Exceções externas podem conter dados pessoais/chaves; logging registra somente tipo e evento. Não adicionar dumps de payload, stderr ou respostas.
- Altere testes para cobrir a intenção, não somente a implementação. Dados devem ser sintéticos.

## Extensões

**Novo formato:** implemente detect/sheets/raw_rows ou extraia adapter específico; mantenha protocolo e linha física. Teste encoding, vazios, cabeçalho, fórmulas, danos numéricos e cancelamento. PDF depende de extração posicional e inspeção visual própria; não basta passar texto corrido ao mapeador.

**Nova regra:** tente JSON primeiro. Para operação nova, adicione à whitelist e ao interpretador, defina tratamento de vazio e falha, teste preservação e atualize REGRAS.md. Para nova família, documente a fonte, associe na UI e mantenha genérico como opção segura.

**Novo provider:** implemente `generate(data, schema, control)` e registre no seletor/configuração. Use sanitização central e teste por MockTransport, incluindo erro HTTP, resposta excessiva, schema inválido e cancelamento. Não reutilizar argumentos de shell montados por interpolação.

**Mudança em biblioteca:** UI reinicia conversão em curso ao mudar fontes/famílias, preservando originais. Não alterar arquivos a que outra sessão ainda se refere. Usuários devem fechar a sessão antes de remover temporários deixados por crash.

## Trabalhos e ciclo de vida das sessões (1.1)

`ImportStore` cria tabela aditiva `imports_v1(id, manifest)` na base existente. O manifesto é JSON com versão indicada pelo nome da tabela. Não salvar base completa nem credenciais nele. Caminhos, decisões e correções por `(linha, campo)` permitem retomar o trabalho; a política de privacidade precisa acompanhar qualquer ampliação desses dados. Estados Em processamento deixados por encerramento são mostrados como Interrompida. Use uma instância por diretório de estado; não há coordenação de workers entre processos.

`process_import` copia o manifesto antes de modificá-lo, expande todas as abas/tabelas e conserva falhas por anexo. Mapeamento salvo só é reaplicado se os cabeçalhos ainda corresponderem. Opções e correções são reaplicadas antes da validação. Cancelamento fecha todas as sessões produzidas e não publica resultados parciais como concluídos. O manifesto entregue ao callback só é persistido depois da conclusão.

`ImportDetail` possui as sessões. A revisão avançada reutiliza `ConversionPane`: `release_sessions()` devolve a posse sem fechar o banco temporário. `processed_event` atualiza o trabalho; ajustes ainda não revalidados ficam salvos, mas retiram os resultados antigos da exportação. Ao reprocessar todo o trabalho, as sessões anteriores são fechadas antes de iniciar; cancelar exige processar novamente. Abrir outro trabalho/fechar a janela remove as sessões. Reabrir o app exige novo processamento, mesmo se o manifesto guardar o último resultado.

`groups()` exige um par único de cabeçalho/itens por família, pasta de modelos e grupo declarado. Ambiguidade precisa de classificação humana. Relatórios de pendências podem ser produzidos sem um par válido: cada sessão fornece seu diagnóstico, e o resumo mantém falhas anteriores à criação da sessão. `export_import` usa staging único e rollback; Tratadas recebe tabelas e relatórios, Parciais recebe diagnósticos. Não sobrescreve exportações anteriores.

`theme.py` concentra tokens derivados da cor. `Backdrop` pinta a marca antes dos filhos, preserva proporção e limita a área vertical. Os widgets continuam recebendo eventos normalmente. `AppearancePane` valida raster, copia logo para assets e salva parâmetros; não descarte sessões ao aplicar marca. Biblioteca, assistente e detalhes não devem implementar uma segunda paleta.

## Atualizar e reempacotar

1. Leia descoberta, arquitetura, conflitos e validação final.
2. Crie alteração pequena e documente comportamento/riscos.
3. Execute testes e lint pelo mesmo `.venv`.
4. Regere `docs/CODIGO.md` com `scripts/document_code.py`.
5. Execute self-test e smoke test; valide telas alteradas.
6. Rebuild nativo pelo script. Execute self-test e smoke test do binário.
7. Atualize `docs/VALIDACAO_FINAL.md` com o que foi realmente executado. Windows exige runner Windows.
8. Preserve `.local` do usuário para configurações; nunca copie estado local/credenciais em pacote.

## Limites intencionais

Não há undo/edição em massa de milhares de células na UI, treinamento de IA, reconciliação automática com catálogo de clientes/produtos, consulta automática de UF, OCR de PDF ou validação tributária externa. PDF suporta somente tabelas posicionais reconhecidas, com conferência obrigatória e limite de 500 páginas; layouts novos exigem validação própria. Casos não cobertos permanecem para revisão e regras adicionais, sem inventar dados. A memória SQLite temporária reduz RAM, mas exige espaço em disco proporcional à auditoria. Leitor HTML limita entrada a 64 MB.

O índice completo de símbolos está em CODIGO.md. Os módulos são comentados nos pontos que concentram decisões de segurança, formato e ciclo de vida.
