# eda.py
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
files = list(DATA_DIR.glob("mets_games_*.csv"))
if not files:
    print("Nenhum arquivo encontrado em data/. Rode data_pipeline.py primeiro.")
    raise SystemExit(1)

dfs = [pd.read_csv(f, parse_dates=["gameDate"]) for f in files]
df = pd.concat(dfs, ignore_index=True)

def normalize_games(df):
    df = df.copy()
    df["is_home"] = df["home_team_name"].str.contains("Mets", na=False)
    df["mets_runs"] = df.apply(lambda r: r["home_runs"] if r["is_home"] else r["away_runs"], axis=1)
    df["opp_runs"]  = df.apply(lambda r: r["away_runs"] if r["is_home"] else r["home_runs"], axis=1)
    df["opp_name"]  = df.apply(lambda r: r["away_team_name"] if r["is_home"] else r["home_team_name"], axis=1)
    df["result"] = df.apply(lambda r: "W" if r["mets_runs"]>r["opp_runs"] else ("L" if r["mets_runs"]<r["opp_runs"] else "T"), axis=1)
    return df

df = normalize_games(df)
by_month = df.groupby(df["gameDate"].dt.to_period("M")).agg(
    games=("gamePk","count"),
    wins=("result", lambda x: (x=="W").sum())
)
by_month["win_pct"] = by_month["wins"]/by_month["games"]
by_month.to_csv("data/summary_by_month.csv")
print("Saved data/summary_by_month.csv")
