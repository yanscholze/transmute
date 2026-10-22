# Fixtures sintéticas

`sintetico_biff.xls` foi gerado exclusivamente para testes com xlwt 1.3.0. Contém cabeçalhos Código/Descrição, número 123 com formato 000000 e texto Peça sintética ç. Não contém dados de clientes. A biblioteca xlwt só foi usada para gerar esta fixture e não é dependência do aplicativo.

`tabelas_sinteticas.pdf` possui duas páginas, uma tabela com grade por página e identificadores textuais 000001–000004. `sem_tabela_sintetico.pdf` possui apenas texto artificial, para verificar rejeição explícita. Ambos foram gerados localmente com reportlab, usado somente na preparação das fixtures; não é dependência do aplicativo. Nenhum exemplo de modelo preenchido foi usado. O self-test do executável gera seu próprio PDF mínimo com objetos/xref, sem essas fixtures.
