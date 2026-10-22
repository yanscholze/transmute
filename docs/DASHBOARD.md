# Dashboard e identidade visual — revisão para aprovação

## Referência e escopo

A referência visual enviada pelo usuário define o shell: cabeçalho em cápsulas, fundo neutro, navegação lateral isolada, grandes painéis arredondados com sombras suaves e blocos de ação. O laranja é apenas um exemplo. A implementação mantém PySide6 e os fluxos determinísticos existentes, acrescentando temas claro/escuro e acento independente. A interface foi aprovada pelo usuário em 22/10/2026; a etapa de instaladores foi autorizada.

## Áreas do dashboard

| Área | Conteúdo | Ação |
|---|---|---|
| Últimas importações | Até quatro trabalhos por atualização; nome, data, categoria e estado | Abre o trabalho; Ver todas abre Importações |
| Nova importação | Ação principal destacada | Abre nome → categorias → arquivos → conferência |
| Taxa de sucesso | Resultado local calculado dos manifestos | Fórmula no tooltip e contagens no próprio painel |
| Seu espaço | Resumo de Importações, Biblioteca, Aparência, IA/perfis e Diagnóstico | Navega para cada área |
| Planilhas de base | Quantidade de modelos/categorias, pasta configurada e uploads | Configurar biblioteca, copiar caminho e abrir pasta |
| Regras de conversão | Caminho do Markdown e estado de revisão do perfil | Abrir editor, copiar caminho e abrir pasta |

Modelos são as abas/layouts carregados no catálogo, incluindo versões distintas. O resumo de IA mostra configuração local e quantidade de perfis; não afirma conexão, login ou saldo de API. Eventos técnicos são os últimos até 500 registros do histórico existente, sem confundi-los com trabalhos nomeados.

## Indicadores e estados vazios

`storage/dashboard.summarize` recebe somente manifestos. Uma importação é contada uma vez, pelo último estado salvo. Repetir processamento não cria tentativas artificiais na taxa.

- Numerador: trabalhos Pronta para exportar + Exportada.
- Denominador: trabalhos Pronta para exportar + Exportada + Revisar pendências.
- Aguardando processamento, Em processamento e Interrompida ficam fora do denominador.
- Pendências no resumo incluem Revisar pendências e Interrompida.
- Sem resultado: travessão e explicação, sem 0%/100% inventado. Se todos os resultados tiverem pendências, mostra 0% real.
- Percentual é arredondado para inteiro; contagens exatas permanecem ao lado.

O estado é o último resultado salvo, não uma garantia de exportação imediata: reabrir o app continua exigindo reprocessar as fontes para recuperar sessões temporárias. Essa taxa não mede aceite de dados no ERP.

Alterações de trabalhos e biblioteca atualizam o dashboard; entrar novamente também atualiza os metadados. A tela não lê células das bases nem cria eventos de histórico ao ser visitada. A ordenação usa timestamps com microssegundos para distinguir trabalhos atualizados no mesmo segundo; datas antigas continuam compatíveis.

## Navegação e acessibilidade

A sidebar recolhida possui 76 px; expandida, 218 px. O botão expõe o estado marcado e o nome Expandir/Recolher menu. Preferência `ui_sidebar_expanded` fica na tabela settings do SQLite existente. O menu não anima sua largura, evitando transições que desloquem o foco ou dependam de movimento para comunicar estado.

Ícones são SVGs geométricos locais renderizados pelo Qt, sem fontes, emojis, downloads ou dependência de conexão. Botões têm nome acessível, tooltip, estado selecionado, foco e navegação por teclado. Texto longo é truncado visualmente, com conteúdo completo no tooltip/nome acessível. Caminhos ficam em campos somente leitura selecionáveis, com ações explícitas de copiar/abrir. Pasta ausente desabilita a abertura e orienta configurar a biblioteca.

A busca do cabeçalho atua no nome dos trabalhos; Enter abre a lista e limpa o filtro de andamento para não ocultar resultados. Revisão de regras abre a Biblioteca e o editor atual. Fechar pelo menu respeita cancelamento/espera do worker e fechamento das sessões existentes.

Em 1100×760, o dashboard usa rolagem vertical quando necessário e mantém a largura da janela, inclusive com menu expandido. Não cria rolagem horizontal para seus cartões. Telas avançadas mantêm a rolagem própria das tabelas existentes.

## Temas, cor e logo

`workspace.json` mantém `theme_mode` (`light` ou `dark`) e `primary_color` (`#RRGGBB`). Configurações anteriores sem modo começam claras; a marca/cor já escolhidas não são substituídas. Aparência salva ambos; o botão no cabeçalho alterna só o modo e sincroniza o seletor, sem salvar outros rascunhos nem fechar sessões.

`theme.palette` concentra superfícies, texto, bordas, foco e acento. Cores neutras não mudam arbitrariamente com o destaque; ações, avatar, seleção e indicadores usam a cor configurada. Texto de ação escolhe foreground por contraste, com fallback preto quando necessário. Foco escolhe acento ou cor de texto conforme contraste contra a superfície. O modo também configura QPalette para popups/indicadores nativos. Cores semânticas de erro/aviso/sucesso da revisão usam versões claras no tema escuro para manter leitura.

Aparência mantém seus campos/prévia em área rolável, com feedback e botão Salvar fixos no rodapé da página. Assim o comando de salvar permanece visível em janela menor, inclusive com sidebar expandida. Sugestões de cor ficam em linha própria para evitar estourar a largura do formulário.

`SoftPanel` pinta sombra e borda no próprio painel, sem cachear o conteúdo dos controles filhos; isso evita recortes ao navegar/redimensionar. No modo escuro ajusta a sombra para não clarear artificialmente as superfícies. Ícones seguem os tokens. A prévia de Aparência usa o tema do rascunho, mesmo quando diferente do modo salvo. A marca d'água continua preservando proporção e parâmetros; painéis opacos mantêm leitura dos dados.

## Responsabilidades e extensão

| Módulo | Responsabilidade |
|---|---|
| `storage/dashboard.py` | Indicadores puros, sem Qt ou leitura de células |
| `ui/dashboard.py` | Composição dos painéis, estados vazios, metadados e atalhos |
| `ui/navigation.py` | Sidebar, destinos e preferência de expansão |
| `ui/icons.py` | Ícones vetoriais locais e renderização |
| `ui/surfaces.py` | Superfície com sombra e rótulos truncáveis |
| `ui/theme.py` | Tokens claros/escuros, contraste, QSS, QPalette e logo |
| `ui/window.py` | Cabeçalho, rotas, worker, aplicação do tema e integração |
| `ui/appearance.py` | Rascunho, prévia e persistência da identidade |

Ao adicionar página, atualize DESTINATIONS, ordem das páginas e atalhos correspondentes, mantendo os testes de destino. Regras de negócio continuam no core. Não coloque exemplos, percentuais fixos ou status de conexão presumidos nos cartões.

## Avaliação e limites

Execute `.venv/bin/python run.py` no projeto para avaliar a interface nova. As capturas `interface-dashboard-claro.png`, `interface-dashboard-escuro.png`, `interface-dashboard-expandido.png` e `interface-dashboard-compacto.png` usam **exclusivamente trabalhos sintéticos** em estado isolado; nenhum desses trabalhos é inserido no estado real do usuário.

Testes cobrem a fórmula, ausência de dados, contraste, destinos, busca, caminhos, edição de regras, expansão, persistência e sessões preservadas ao trocar tema. A avaliação nesta máquina é Linux/Qt; não comprova execução Windows, importação no ERP ou APIs reais. Os binários/ZIPs da versão anterior não contêm este dashboard. A etapa de .exe/.rpm foi autorizada após a aprovação; consulte EMPACOTAMENTO.md.
