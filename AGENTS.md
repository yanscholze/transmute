# Manutenção do Conversor de Bases

- Leia README.md, docs/ARQUITETURA.md, docs/REGRAS.md e docs/VALIDACAO_FINAL.md antes de alterar comportamento.
- Não edite `INSTRUCOES_CONVERSOES.md` nem os modelos originais sem instrução explícita. Valide os hashes em docs/originais.sha256.json.
- Use um único `.venv` por checkout. Testes: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --basetemp=.local/test-tmp -q`; crie `.local` primeiro.
- Dados de testes são sintéticos. Não copiar exemplos preenchidos dos modelos ou dados de clientes para fixtures, logs ou prompts.
- Toda mudança de comportamento precisa de atualização da documentação, comentários nos pontos de decisão e testes proporcionais. Regenere docs/CODIGO.md ao alterar símbolos.
- Regras de negócio pertencem a core/rules, transformation ou validation. Widgets e providers não podem definir regras paralelas.
- Biblioteca é configurável e white label. Não voltar a exigir nomes fixos de modelos nem editar referências externas ao importar/editar regras pela UI.
- IA opcional, off-line funcional. Secrets nunca em texto puro; nenhum envio externo sem consentimento específico do payload.
- Não declarar Windows, API, CLI, ERP ou outra distribuição Linux verificados sem execução correspondente. Receita de build não é prova de runtime.
- Pacotes não incluem estado `.local` nem linhas de exemplo dos modelos. Cada release é nova; não apague versões ou configurações do usuário.
