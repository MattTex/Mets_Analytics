# New York Mets — 2024 & 2025 Dashboard

Pequeno projeto com dashboard Streamlit para analisar as temporadas 2024 e 2025 do New York Mets.

## Estrutura
- `streamlit_app.py` — Dashboard principal (Streamlit).
- `data_pipeline.py` — Baixa dados (schedule / linescore) da MLB Stats API e salva em `data/`.
- `eda.py` — Scripts para análises adicionais.
- `model_predictor.py` — Exemplo de projeto separado: preditor simples.
- `requirements.txt` — Dependências.

## Como rodar
1. Instale dependências:
```bash
pip install -r requirements.txt
```
2. Baixe dados:
```bash
python data_pipeline.py
```
3. Rode o dashboard:
```bash
streamlit run streamlit_app.py
```

## Notas
- O pipeline utiliza a MLB Stats API (`statsapi.mlb.com`). Use com respeito às políticas e rate limits.
- Recomendo não commitar a pasta `data/` no GitHub; use `.gitignore` para evitar subir datasets brutos.
- Para análises mais profundas, enriqueça com boxscore/play-by-play/Statcast (pode requerer endpoints adicionais).

## Licença
MIT
