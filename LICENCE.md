
---

# Boas práticas aplicadas e por quê
- **Modularização**: separa fetch / validation / db / app — facilita manutenção e testes.
- **Config via .env**: evita secrets hardcoded e facilita CI.
- **Logging**: mensagens para debug e audit.
- **Validação (pandera)**: evita inserir lixo no DB.
- **SQLite + SQLAlchemy**: simples e portátil; trocar para Postgres é direto.
- **Tests com pytest**: base para crescer testes unitários e de integração.
- **Docker + CI**: pronto para deploy e integração contínua.
- **Formatação & lint**: black, flake8, isort para código consistente.
- **CLI**: interface simples para operações comuns (ETL, serve).

