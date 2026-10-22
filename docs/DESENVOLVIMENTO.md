# Guia de desenvolvimento e manutenção

## Fronteiras de responsabilidade

`models.py` contém dataclasses compartilhadas sem dependência de Qt ou HTTP. `Control` permite cancelamento/progresso sem acoplar o core à interface.

Importers produzem `(linha física, células, problemas estruturais)`; não decidem destino. `Cell` carrega texto, tipo de origem e observação sobre preservação. Colunas são identificadas por posição, permitindo cabeçalhos duplicados sem perda.

Mapping sugere `Decision`; não transforma. Confirmação é exigida para sugestões de menor confiança. Um destino não recebe duas origens. Perfil salvo só guarda cabeçalho/destino e é vinculado ao fingerprint da estrutura.

Engine recebe valores originais, decisões, opções e perfil. Retorna valores, problemas e mudanças, sem editar fonte. `put()` centraliza antes/depois/regra. Para regra nova, use o interpretador declarativo quando suficiente; lógica de domínio fica em transformation/validation.

Session grava linhas em SQLite temporário, com raw/output/problems/changes/severity/groupkey. Mantém hash de origem, modelo, Markdown e perfil. Uma sessão não deve ser usada após `close()`. Todos os caminhos de erro de processamento fecham/removem a sessão criada.

Exporters validam os snapshots, planejam partes, escrevem XLSX e relatórios em diretório de staging. Cancelamento/erro remove o staging. Publicação usa rename. Nomes finais exclusivos impedem sobrescrita de importações anteriores. Relatórios de diagnóstico podem ser copiados para outra pasta escolhida; se essa cópia falhar, o resultado recém-criado é retirado para não anunciar conclusão incompleta.

Providers recebem apenas payload já sanitizado e schema. Não leem arquivos nem ganham ferramenta para alterar o projeto. `service.py` valida resposta e percorre exclusivamente o fallback configurado. Nenhuma resposta entra diretamente em célula.

Storage persistente guarda biblioteca, branding, perfis, histórico mínimo e configurações sem chaves. Credenciais usam memória ou backend seguro do sistema. `workspace.py` mantém fontes externas como referências e guarda edições/upload em cópias locais.

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

Não há undo/edição em massa de milhares de células na UI, treinamento de IA, reconciliação automática com catálogo de clientes/produtos, consulta automática de UF, extração de PDF ou validação tributária externa. Casos não cobertos permanecem para revisão e regras adicionais, sem inventar dados. A memória SQLite temporária reduz RAM, mas exige espaço em disco proporcional à auditoria. Leitor HTML limita entrada a 64 MB.

O índice completo de símbolos está em CODIGO.md. Os módulos são comentados nos pontos que concentram decisões de segurança, formato e ciclo de vida.
