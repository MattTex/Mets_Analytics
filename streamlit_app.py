# streamlit_app.py
import streamlit as st
import pandas as pd
import os
from pathlib import Path
import requests
import plotly.express as px

DATA_DIR = Path("data")
TEAM_NAME = "New York Mets"

st.set_page_config(page_title="New York Mets — 2024/2025 Analysis", layout="wide")

@st.cache_data(show_spinner=False)
def load_csv_or_fetch(season):
    path = DATA_DIR / f"mets_games_{season}.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["gameDate"])
    # fallback: try to fetch like pipeline
    st.info(f"CSV for {season} not found — baixando via API (fallback).")
    # minimal fetch using statsapi schedule endpoint (teamId 121 typically Mets)
    url = ("https://statsapi.mlb.com/api/v1/schedule"
           f"?sportId=1&teamId=121&startDate={season}-03-01&endDate={season}-11-30&hydrate=linescore")
    r = requests.get(url, timeout=20)
    data = r.json()
    rows = []
    for date_block in data.get("dates", []):
        for g in date_block.get("games", []):
            linescore = g.get("linescore", {})
            home_runs = linescore.get("teams", {}).get("home", {}).get("runs")
            away_runs = linescore.get("teams", {}).get("away", {}).get("runs")
            rows.append({
                "gamePk": g.get("gamePk"),
                "gameDate": g.get("gameDate"),
                "status": g.get("status", {}).get("detailedState"),
                "home_team_name": g.get("teams", {}).get("home", {}).get("team", {}).get("name"),
                "away_team_name": g.get("teams", {}).get("away", {}).get("team", {}).get("name"),
                "home_runs": home_runs,
                "away_runs": away_runs,
                "venue": g.get("venue", {}).get("name"),
                "gameType": g.get("gameType")
            })
    df = pd.DataFrame(rows)
    df["gameDate"] = pd.to_datetime(df["gameDate"])
    df["season"] = season
    return df

def normalize_games(df):
    df = df.copy()
    def is_home(row):
        return "Mets" in str(row.get("home_team_name",""))
    df["is_home"] = df.apply(is_home, axis=1)
    df["mets_runs"] = df.apply(lambda r: r["home_runs"] if r["is_home"] else r["away_runs"], axis=1)
    df["opp_runs"]  = df.apply(lambda r: r["away_runs"] if r["is_home"] else r["home_runs"], axis=1)
    df["opp_name"]  = df.apply(lambda r: r["away_team_name"] if r["is_home"] else r["home_team_name"], axis=1)
    def res(r):
        if pd.isna(r["mets_runs"]) or pd.isna(r["opp_runs"]):
            return "NA"
        return "W" if r["mets_runs"] > r["opp_runs"] else ("L" if r["mets_runs"] < r["opp_runs"] else "T")
    df["result"] = df.apply(res, axis=1)
    df["month"] = df["gameDate"].dt.to_period("M").astype(str)
    df["date"] = df["gameDate"].dt.date
    return df

st.title("📊 New York Mets — Seasons 2024 & 2025")
st.write("Dashboard interativo mostrando rendimento por temporada, por casa/fora, por adversário, e pontos fortes/fracos.")

col1, col2 = st.columns([1,3])
with col1:
    seasons = st.multiselect("Escolha temporadas", [2024,2025], default=[2024,2025])
    refresh = st.button("Recarregar dados")
with col2:
    st.markdown("**Resumo rápido** — use os filtros para explorar onde o time foi melhor/pior.")

if refresh:
    load_csv_or_fetch.clear()

dfs = []
for s in seasons:
    df = load_csv_or_fetch(s)
    if "season" not in df.columns:
        df["season"] = s
    dfs.append(df)
if not dfs:
    st.warning("Nenhuma temporada selecionada.")
    st.stop()

full = pd.concat(dfs, ignore_index=True)
full = normalize_games(full)

metrics = full[full["result"].isin(["W","L"])].groupby("season").agg(
    games_played=("gamePk", "count"),
    wins=("result", lambda x: (x=="W").sum()),
    losses=("result", lambda x: (x=="L").sum()),
    runs_scored=("mets_runs", "sum"),
    runs_allowed=("opp_runs", "sum"),
)
metrics["win_pct"] = metrics["wins"] / metrics["games_played"]
st.dataframe(metrics.reset_index().round(3), use_container_width=True)

st.subheader("Desempenho mensal")
monthly = full[full["result"].isin(["W","L"])].groupby(["season","month"]).agg(
    wins=("result", lambda x: (x=="W").sum()),
    games=("result", "count"),
    runs_scored=("mets_runs","sum"),
    runs_allowed=("opp_runs","sum")
).reset_index()
monthly["win_pct"] = monthly["wins"] / monthly["games"]
fig = px.bar(monthly, x="month", y="win_pct", color="season", barmode="group",
             labels={"win_pct":"Win %","month":"Mês"})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Casa vs Fora")
ha = full[full["result"].isin(["W","L"])].groupby(["season","is_home"]).agg(
    games=("gamePk","count"),
    wins=("result", lambda x: (x=="W").sum()),
    runs_scored=("mets_runs","sum"),
    runs_allowed=("opp_runs","sum")
).reset_index()
ha["win_pct"] = ha["wins"]/ha["games"]
ha["loc"] = ha["is_home"].map({True:"Home", False:"Away"})
fig2 = px.bar(ha, x="loc", y="win_pct", color="season", barmode="group", labels={"win_pct":"Win %"})
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Adversários — melhor e pior contra")
agg_vs = full[full["result"].isin(["W","L"])].groupby(["opp_name"]).agg(
    games=("gamePk","count"),
    wins=("result", lambda x: (x=="W").sum()),
    runs_scored=("mets_runs","sum"),
    runs_allowed=("opp_runs","sum")
).reset_index()
agg_vs = agg_vs[agg_vs["games"] >= 3]
agg_vs["win_pct"] = agg_vs["wins"]/agg_vs["games"]
best = agg_vs.sort_values("win_pct", ascending=False).head(10)
worst = agg_vs.sort_values("win_pct", ascending=True).head(10)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Melhores adversários (>=3 jogos)**")
    st.dataframe(best[["opp_name","games","win_pct","runs_scored","runs_allowed"]].round(3))
with c2:
    st.markdown("**Piores adversários (>=3 jogos)**")
    st.dataframe(worst[["opp_name","games","win_pct","runs_scored","runs_allowed"]].round(3))

st.subheader("Desempenho por estádio (venues)")
venue_agg = full[full["result"].isin(["W","L"])].groupby("venue").agg(
    games=("gamePk","count"),
    wins=("result", lambda x: (x=="W").sum()),
    runs_scored=("mets_runs","sum"),
    runs_allowed=("opp_runs","sum")
).reset_index()
venue_agg["win_pct"] = venue_agg["wins"]/venue_agg["games"]
venue_agg = venue_agg.sort_values("win_pct", ascending=False).head(20)
fig3 = px.scatter(venue_agg, x="games", y="win_pct", size="games", hover_name="venue",
                  labels={"win_pct":"Win %","games":"Games"})
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Top issues (resumo)")
worst_months = monthly.sort_values("win_pct").head(5)
st.table(worst_months[["season","month","win_pct","games"]].round(3))

st.markdown("---")
st.caption("Dados via MLB Stats API. Se quiser, rode `python data_pipeline.py` para baixar CSVs locais e acelerar o dashboard. (Nota: jogos futuros podem ter linhas vazias).")
