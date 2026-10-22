# Instruções gerais para conversão de bases

Este arquivo é a referência principal para conversões nesta pasta. Leia-o antes de iniciar cada conversão e atualize a seção **Histórico de conversões e observações** quando uma conversão trouxer uma regra reutilizável, uma exceção confirmada ou um risco de erro futuro.

## Objetivo

Converter as bases originais para planilhas limpas de conversão, usando os exemplos existentes para entender o formato final. As planilhas limpas de exemplo são somente referência: não editar, substituir ou renomear esses arquivos. Preservar as bases originais e os arquivos de teste.

## Organização observada

- `Importações/`: pasta principal; contém o arquivo geral de instruções e a pasta de bases abaixo.
- `#PLANILHAS DE BASE/`: pasta de modelos limpos de referência, organizada em subpastas `V1`, `V2` etc.; o prefixo `#` mantém a pasta no alto da listagem. Não alterar o conteúdo dos modelos.
- `Importação <empresa>/`: pasta de cada importação.
- Padrão atual confirmado para as empresas: pastas para bases originais/extraídas, parciais de teste e planilhas tratadas. Os nomes devem ser conferidos na pasta antes de cada tarefa; não renomeá-los por conta própria.
- Riske: `Extraidas`, `Parciais`, `Tratadas`.
- Não presumir que os nomes das subpastas são iguais entre empresas. Identificar os arquivos pelo conteúdo e pela função antes de trabalhar.
- Se uma nova importação não tiver pastas claras, organizar sem mover ou sobrescrever dados existentes: originais em uma pasta de arquivo, planilhas de teste em uma pasta de parciais/teste e resultados convertidos em uma pasta de tratadas/limpas. Manter o padrão já usado pela empresa sempre que possível.
- Os modelos limpos ficam em subpastas de versão dentro de `#PLANILHAS DE BASE`; usar a versão correspondente ao grupo de teste. Não alterar seu conteúdo.

## Procedimento obrigatório antes e durante cada conversão

1. Ler este documento e inventariar os arquivos da empresa solicitada.
2. Identificar bases originais, planilhas de teste e modelos limpos sem confiar apenas no nome do arquivo.
3. Examinar cabeçalhos, tipos de dados e amostras das bases. Cruzar campos e registros entre base original, teste e modelo limpo para determinar o significado e o destino de cada coluna.
4. Usar os arquivos limpos existentes como referência de estrutura e preenchimento; nunca alterá-los. Se houver mais de um modelo possível, escolher pelo tipo de cadastro e confirmar o mapeamento com os dados disponíveis.
5. Usar a planilha parcial de teste para validar a conversão. O formato esperado para cadastros/cabeçalhos é 6 linhas ao todo: uma linha de cabeçalho e cinco registros distintos. Selecionar registros variados que cubram os principais cenários e regras da base (por exemplo, cliente com CPF, CNPJ contribuinte com IE e CNPJ não contribuinte sem IE), em vez de escolher automaticamente os primeiros registros. Quando houver mais cenários do que cinco vagas, priorizar diversidade e registrar o que ficou sem cobertura. Em planilhas de itens vinculados a várias OS, preservar todos os itens das OS selecionadas; a quantidade de linhas será maior quando necessária para não perder linhas de serviço/produto.
6. Gerar a conversão em arquivo separado na pasta de resultados da empresa. Preservar os originais e os testes. Não sobrescrever arquivos preexistentes; criar nome de saída distinto quando necessário.
7. Conferir o resultado: cabeçalhos e ordem de colunas esperados, contagem de registros, correspondência com as fontes e regras de validade abaixo. Não inventar dados para preencher lacunas.
8. Ao concluir, executar um diagnóstico documentado da conversão: contagens, vínculo entre cabeçalhos/itens/cadastros auxiliares, campos faltantes, divergências e possíveis erros. Apresentar o diagnóstico no relatório final e salvar uma cópia na pasta `Parciais` da empresa. Não declarar conversão sem erros quando houver incertezas ou campos duvidosos.
9. Avaliar se houve uma descoberta que reduza erros em conversões futuras. Registrar aqui apenas regras gerais confirmadas ou exceções específicas com identificação da empresa/arquivo; manter a anotação curta e objetiva.

## Regras de qualidade e preservação

- **Limite de linhas:** cada planilha exportada pode ter no máximo 10.000 linhas no total, incluindo o cabeçalho. Se a conversão exceder esse limite, dividir em arquivos numerados, preservando todos os registros e a ordem. Quando houver dados vinculados (como OS e itens), dividir os arquivos relacionados em conjunto, usando os mesmos grupos de OS: cada arquivo de cabeçalhos deve acompanhar o arquivo de itens correspondente. Manter cada OS e todos os seus itens na mesma parte; não separar cabeçalhos e itens em arquivos sem correspondência.

- **Clientes e fornecedores em arquivos separados:** nunca combinar cadastros de clientes e fornecedores na mesma planilha de importacao. Converter cada base no modelo correspondente e salvar em arquivo proprio.

- **Identificadores são dados críticos.** Nunca alterar, completar, truncar, recalcular, remover dígitos ou substituir valores de CNPJ, CPF, IE ou IM. Remover somente caracteres de formatação quando necessário, preservando todos os dígitos e zeros à esquerda. Manter como texto para evitar perda de zeros ou notação científica.
- **CPF, IE e RG:** se o cliente tem CPF, não preencher `Inscrição Estadual`. Conferir os cabeçalhos e valores da planilha extraída, inclusive campos combinados ou variantes como `IE/RG` ou `IE/EG`. Para pessoa física, colocar o valor de RG fornecido pela origem em uma coluna `RG` separada; não copiar esse valor para IE. Preservar o identificador sem alterar dígitos ou zeros à esquerda. Se o modelo limpo não tiver coluna `RG`, acrescentá-la somente à planilha convertida/parcial, sem editar o modelo de referência. Para CNPJ, mapear IE apenas quando a origem a identificar como IE; não confundir com RG.
- Não alterar outros dados relevantes da fonte sem uma regra explícita. Não deduzir nem corrigir conteúdo por suposição.
- Remover caracteres especiais de telefones e documentos quando a saída exigir apenas números; essa limpeza não autoriza mudar a sequência numérica.
- Manter somente dados válidos nos campos de contato e endereço. E-mail vazio, claramente inválido ou preenchido apenas com placeholders como `x`, `.`, `0` deve ficar em branco. Aplicar o mesmo critério a telefone; não tratar um valor inválido como contato real.
- Endereço e CEP só devem ser preenchidos com informação válida disponível na fonte. Não fabricar endereço ou CEP. Preservar zeros à esquerda no CEP. A UF nunca pode ficar vazia e deve corresponder ao endereço. Se a UF estiver ausente ou houver dúvida, pesquisar fontes confiáveis na Internet antes de preencher; confirmar que a localidade/endereço e a UF são compatíveis e registrar fonte/decisão no diagnóstico. Nunca escolher UF por suposição ou apenas por proximidade textual.
- Preservar células realmente vazias como vazias; não converter ausência em zero, texto de placeholder ou dado inferido.
- Ao encontrar conflito entre fontes, priorizar o dado rastreável e consistente; não resolver conflito alterando identificadores. Registrar a divergência e deixar o valor em branco quando não for possível determinar um dado válido sem adivinhar.
- Para relatórios em PDF, identificar visualmente/por posição os campos quando o texto extraído misturar colunas ou rótulos. Usar o PDF como fonte primária para OS e seus itens, e cruzar cliente, veículo e produto com as bases auxiliares disponíveis. Se o rótulo e o conteúdo forem incompatíveis, só reposicionar o dado quando o significado for inequívoco; registrar a decisão no diagnóstico. Não colocar justificativas internas em campos destinados a cliente, OS, item ou veículo. Se não puder ser lido com segurança, deixar vazio; nunca inferir por proximidade de texto.
- **KM e leitura posicional de OS:** aceitar `Quilometragem` somente quando o valor do campo for numerico (com separadores usuais). Se trouxer texto alfanumerico que identifique claramente o modelo, mover o valor completo para `Modelo`; nao remover letras e exportar apenas os digitos como KM. Ler cada campo dentro da propria linha do PDF, sem capturar o rotulo ou conteudo da linha seguinte quando estiver vazio.
- Se código de produto e descrição do PDF apontarem para produtos de naturezas distintas, não associar automaticamente pelo código. Manter a linha da OS, preservar os dois valores e registrar a divergência para revisão.
- Em relatórios sequenciais, selecionar os cinco primeiros registros de OS efetivamente presentes no relatório; numeração ausente não deve ser inventada nem usada para deslocar dados de uma OS para outra.

## Modelos limpos disponíveis nas pastas de versão

Os arquivos abaixo estão em cada conjunto versionado (referência somente; não editar). Conferir `#PLANILHAS DE BASE/VERSOES.md` para saber qual versão corresponde a cada grupo.

- `cad_veiculo.xlsx`
- `clientes_limpo.xlsx`
- `contas_a_pagar_limpo.xlsx`
- `contas_a_receber_limpo.xlsx`
- `fornecedores_limpo.xlsx`
- `ordens_de_servio_-_cabealhos_e_itens_juntos_limpo(1).xlsx`
- `ordens_de_servio_-_somente_cabealhos_limpo.xlsx`
- `ordens_de_servio_-_somente_itens_limpo(1).xlsx`
- `produtos_limpo.xlsx`
- `vendas_-_cabealhos_e_itens_juntos_limpo.xlsx`
- `vendas_-_somente_cabealhos_limpo.xlsx`
- `vendas_-_somente_itens_limpo.xlsx`

Os nomes acima são um inventário inicial, não uma garantia de que cada arquivo seja o modelo correto para toda empresa. Conferir conteúdo e cabeçalhos antes de mapear.

## Histórico de conversões e observações

- **2026-10-09 — limite de planilhas solicitado por Yan:** cada arquivo deve conter no máximo 10.000 linhas, incluindo cabeçalho. Conversões maiores devem ser divididas em arquivos numerados; para OS, dividir cabeçalhos e itens em conjunto, com os mesmos grupos de OS em arquivos correspondentes e sem separar uma OS de seus itens.

- **2026-10-09 — preparação do padrão geral:** mapeada a estrutura inicial. Os modelos limpos foram organizados em `#PLANILHAS DE BASE`; manter essa pasta e os exemplos intactos.
- **2026-10-09 — atualização solicitada por Yan:** manter a organização atual das pastas por empresa; usar os modelos em `#PLANILHAS DE BASE`. Cada conversão exige diagnóstico final salvo em `Parciais`, cobrindo possíveis erros e incoerências. Ao ler PDF, validar visualmente campos que possam ter sido misturados na extração e cruzar OS com cadastros auxiliares.
- **2026-10-09 — Riske, teste das cinco primeiras OS presentes no PDF:** OS `000001`, `000003`, `000004`, `000005` e `000006`; `000002` não aparece no relatório e não foi inventada. As cinco geram 66 linhas de itens. Valores textuais em campos `KM` (modelo) e `CHASSI` (cor) foram reposicionados apenas quando o conteúdo era inequívoco e a decisão foi documentada. O código de produto `006456` conflita com a descrição do cadastro e não deve ser associado sem revisão. Três linhas genéricas `MAO DE OBRA` não têm produto exato no catálogo. Ver `Importação Riske/Parciais/V1/Diagnostico_conversao_OS_Riske_5_primeiras.md`.
- **Pessoa usuária:** Yan. Começar as mensagens chamando-o pelo nome.

## Regras adicionadas por Yan — aplicação em todas as conversões

- Em planilhas de itens de OS, o nome do serviço deve refletir a descrição do serviço no relatório. Não substituir `MÃO DE OBRA` pelo técnico; a informação do técnico só entra em um campo próprio quando o modelo de destino o tiver e houver instrução para usá-lo. Deixar `Descrição livre do item` vazia, salvo se contiver dado de origem útil solicitado para importação.
- Campos destinados ao cliente devem conter somente dados da origem apropriados àquele campo. Não escrever resumos criados pelo agente, diagnósticos, identificadores internos, explicações de mapeamento ou outras anotações em `Observação da OS`, `Observações` do cliente/veículo ou campos livres. Se não houver conteúdo correspondente na fonte, deixar em branco. Registrar interpretação e incerteza no diagnóstico salvo em `Parciais`.
- Quando Yan solicitar campo adicional ausente do modelo, acrescentá-lo somente às parciais/resultados da conversão, mantendo o modelo limpo de referência intacto. Para OS de Riske, a coluna `Situação` foi incluída por solicitação e preenchida como `Encerrada` nas dez OS das duas parciais.
- Gerar veículos somente quando a fonte trouxer dados suficientes para identificar o veículo. Não criar veículo vazio para completar a contagem de OS; documentar OS sem dados de veículo no diagnóstico.
- Além do diagnóstico em Markdown, salvar um resumo curto da conversão em `.txt` dentro de `Parciais` e apresentar o resumo também na mensagem final.

- **2026-10-09 — Riske, OS 000007 a 000011:** 5 cabeçalhos, 5 clientes, 49 produtos/serviços vinculados (46 produtos por código e 3 serviços por descrição exata), 55 itens e 3 veículos. Os totais por OS e os cálculos de linha conferem. OS 000010 e 000011 não informam veículo. A pedido de Yan, todas as dez OS nas duas parciais têm Situação = Encerrada; os modelos limpos não foram alterados. Técnicos não devem ocupar o nome do serviço, descrições livres e observações devem ficar sem comentários internos; resumos curtos também devem ser salvos em TXT. Ver `Importação Riske/Parciais/V2/Diagnostico_conversao_OS_Riske_000007-000011.md`.



## Versionamento das planilhas e das parciais

- Os modelos limpos ficam em `#PLANILHAS DE BASE/V1`, `V2` etc. Cada nova parcial de teste recebe a próxima versão e uma pasta correspondente em `Importação <empresa>/Parciais/Vn`.
- `V1` corresponde ao primeiro grupo de teste da Riske (cinco OS efetivamente presentes: `000001`, `000003`, `000004`, `000005`, `000006`); `V2` corresponde ao grupo seguinte (`000007` a `000011`). Os arquivos de cada grupo ficam juntos com seus diagnósticos e resumos.
- Na organização de 2026-10-09, os 12 modelos limpos originais foram movidos para `#PLANILHAS DE BASE/V1`; cópias byte a byte foram guardadas em `V2`. Os dois conjuntos têm hashes idênticos e não incorporam mudanças de layout. A coluna `Situação` foi solicitada para as parciais e não foi inserida nos modelos limpos.
- Para uma próxima parcial, criar a próxima versão numerada (atualmente `V4`) copiando o conjunto de modelos vigente, manter o conjunto anterior intacto e registrar qual modelo foi usado. Se Yan fornecer uma nova versão de modelo, usar essa versão na próxima pasta sem editar as versões anteriores.
- A pasta `Parciais` no nível da empresa contém somente as subpastas de versão e um índice geral. Não deixar planilhas de versões diferentes misturadas na raiz.


- **2026-10-09 — regra de clientes solicitada por Yan:** CPF identifica pessoa física e não deve ter IE preenchida. Verificar colunas compostas (IE/RG, IE/EG ou variantes), separar RG em coluna própria e manter IE vazia. Aplicada retroativamente às parciais de clientes Riske V1 e V2: valores da origem IE/RG foram movidos para RG, e as planilhas limpas permaneceram intactas.
- **Colunas sem dados:** antes de salvar qualquer parcial/conversão, avaliar cada coluna de saída considerando todos os cadastros/linhas selecionados. Se nenhum registro tiver valor real, omitir a coluna inteira do arquivo. Manter a ordem das colunas restantes e todos os dados existentes; uma coluna deve permanecer se ao menos um registro tiver valor. Não aplicar essa remoção aos modelos limpos de referência.

- **2026-10-09 — regra solicitada por Yan:** remover dos arquivos convertidos/parciais qualquer coluna totalmente sem dados nos registros daquela versão. Manter coluna com pelo menos um valor; nunca remover do modelo limpo de referência. Aplicada às planilhas parciais Riske V1 e V2.
- **Clientes — classificação, UF e regime tributário:** em cada nova conversão, perguntar se todos os clientes devem receber `Ativo = ATIVO`; só aplicar após resposta. Conferir `UF` em todos os cadastros e validar sua compatibilidade com o endereço. A UF nunca pode ficar vazia; se faltar ou houver dúvida, pesquisar fontes confiáveis na Internet antes de preencher e documentar a fonte e a decisão no diagnóstico. Quando `Regime Tributário` estiver vazio na origem, preencher `Normal`.

- **2026-10-09 — regra de colunas vazias solicitada por Yan:** não exportar colunas sem nenhum valor entre os registros selecionados. Anotar no resumo final os nomes das colunas omitidas por planilha e versão. Manter intactos os modelos limpos de referência.

- **2026-10-09 — regras de cadastro de clientes confirmadas por Yan para Riske V1 e V2:** todos os dez têm UF SC; todos recebem Ativo = ATIVO; como a fonte não informa regime tributário, todos recebem Normal. Em conversões futuras, perguntar sobre classificação ATIVO e pesquisar e preencher UFs ausentes/duvidosas, documentando a fonte; nunca deixar UF vazia.


- **2026-10-09 — regras de seleção e UF solicitadas por Yan:** parciais devem priorizar cadastros distintos que cubram cenários e validações importantes (por exemplo CPF, CNPJ contribuinte com IE e CNPJ não contribuinte sem IE), não simplesmente os primeiros registros; registrar cenários sem cobertura. A UF deve sempre estar preenchida e ser compatível com o endereço. Se ausente ou duvidosa, pesquisar fontes confiáveis na Internet antes de preencher e documentar a fonte/decisão no diagnóstico.
## Regras de produtos e tributação

- **Servicos:** se `Tipo do item` for `Serviço`, usar `Situação tributária = SERVIÇOS`, `CFOP Dentro = 5933` e `CFOP Fora = 6933`. Essa regra especifica a tributacao de servicos; nao usar `VENDA NORMAL` nem os CFOPs de mercadorias nesses registros.
- **Tipo do Item (campo exigido pelo sistema):** usar códigos textuais conforme a tabela do sistema: `00` Mercadoria para revenda; `01` Matéria-prima; `02` Embalagem; `03` Produto em processo; `04` Produto acabado; `05` Subproduto; `06` Produto intermediário; `07` Material de uso e consumo; `08` Ativo imobilizado; `09` Serviços; `10` Outros insumos; `99` Outras. Usar o cabeçalho exatamente como `Tipo do Item`. A imagem de referência foi fornecida por Yan em 2026-10-16. Aplicar o código conforme a natureza confirmada pela origem e pelas regras da conversão; não classificar automaticamente toda mercadoria como `00` se a origem indicar outra categoria. Esse campo não substitui `Situação tributária`: serviços continuam com `SERVIÇOS` e CFOP Dentro/Fora `5933`/`6933`; mercadorias seguem a classificação tributária aplicável.

- Todo registro com `Tipo do item = Produto` deve ter `Situação tributária`. Se estiver vazia na origem, preencher `VENDA NORMAL`. Serviços seguem a regra própria logo acima.
- Para produtos `VENDA NORMAL`, usar `CFOP Dentro = 5.102` e `CFOP Fora = 6.102`.
- Classificar como `OLEOS E LUBRIFICANTES` somente o próprio óleo/lubrificante vendido como produto (por exemplo, óleo sintético, óleo de motor ou óleo para transmissão). Filtros, bombas, tampas, tubos e demais peças/produtos apenas relacionados a óleo ficam como `VENDA NORMAL`, assim como fluidos que não sejam óleo/lubrificante.
- Para `OLEOS E LUBRIFICANTES`, usar as CFOPs de ST correspondentes; na referência limpa de Riske, o exemplo de produto lubrificante usa CFOP dentro `5405` e fora `6405`. Confirmar pela referência/base aplicável e registrar qualquer incerteza, sem inventar códigos.
- Usar descrição e dados da origem para classificar os produtos; registrar casos realmente ambíguos para revisão.
- **2026-10-09 — regra tributária de produtos solicitada por Yan:** Situação tributária é obrigatória; quando vazia, usar VENDA NORMAL, com CFOP dentro 5.102 e fora 6.102. Óleos e lubrificantes usam OLEOS E LUBRIFICANTES e as CFOPs correspondentes confirmadas na referência/base; não presumir códigos se não houver evidência.


- **2026-10-09 — validação tributária de produtos Riske V2:** a regra foi aplicada à tabela de produtos da parcial de OS 000007–000011 em arquivo revisado separado, preservando o arquivo anterior. Quatro óleos identificados na origem (grupo ÓLEO ou descrição inequívoca de óleo comercializado) receberam OLEOS E LUBRIFICANTES e CFOPs 5405/6405; os demais 45 itens, incluindo filtros e peças com referência a óleo, receberam VENDA NORMAL e CFOPs 5102/6102 (5.102/6.102). CFOP 5405/6405 foi confirmado pelo exemplo de lubrificante do modelo limpo Riske; CST continua omitido porque a origem fornece CSOSN 500, sem mapeamento confirmado para o CST do modelo. Ver diagnóstico V2.



- **2026-10-09 — conversao total Riske:** convertidos 1.020 clientes (classificacao ATIVO confirmada por Yan), 166 fornecedores, 6.450 produtos, 2.124 cabecalhos de OS, 10981 itens e 645 veiculos deduplicados por placa. Reconciliados os totais das OS extraidos; descontos de linha calculados pela diferenca entre quantidade x valor unitario e total. Quatro divergencias de centavos na soma de descontos foram registradas no diagnostico. Ha 52 placas com dados repetidos divergentes; mantida primeira ocorrencia. 11 UFs de fornecedores foram pesquisadas e preenchidas; a associacao do fornecedor 000060 a Riosulence nao tem endereco corroborante. 5 transportadoras nao foram convertidas por falta de modelo; sem fontes de vendas/contas a pagar/receber. Colunas vazias listadas em `Importacao Riske/Tratadas/Conversao_total_2026-10-09/Diagnostico_conversao_total_Riske.md`. Bases `.xls` sao HTML UTF-8; ler o conteudo/codificacao, nao a extensao. Para PDF OS, preservar coordenadas/colunas durante extracao; o texto corrido embaralha itens.
- **2026-10-09 — regra solicitada por Yan:** a importacao exige uma tabela/arquivo de clientes e outra tabela/arquivo de fornecedores; manter os dois cadastros separados e usar o modelo correspondente para cada um.
- **2026-10-09 — regra de produtos solicitada por Yan:** registros cujo `Tipo do item` seja `Serviço` usam situação tributária `SERVIÇOS` e CFOP Dentro/Fora `5933`/`6933`. Revisada e aplicada aos 34 servicos da conversao total Riske.
- **2026-10-09 — revisao da conversao total Riske:** corrigidos valores alfanumericos extraidos como KM numerico (por exemplo, `PAJERO TR4`) e campos vazios que capturavam texto da linha seguinte no PDF. A regra de KM/leitura posicional foi registrada acima.
- **2026-10-16 — regra de produtos solicitada por Yan:** o campo de sistema `Tipo do Item` usa código textual `00` para mercadorias de revenda e `09` para serviços. Aplicada à conversão total Riske: 6.416 mercadorias e 34 serviços. A regra é independente de situação tributária e CFOP.
- **2026-10-16 — tabela oficial de Tipo do Item enviada por Yan:** acrescentada a lista de códigos `00`, `01`–`10` e `99` à referência geral. Usar somente a classificação apoiada pela origem; a tabela completa não altera os códigos já aplicados à Riske.
