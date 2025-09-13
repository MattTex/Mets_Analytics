# model_predictor.py
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

data_files = list(Path("data").glob("mets_games_*.csv"))
if not data_files:
    print("Nenhum arquivo em data/. Rode data_pipeline.py primeiro.")
    raise SystemExit(1)

df = pd.concat([pd.read_csv(p, parse_dates=["gameDate"]) for p in data_files], ignore_index=True)
df["is_home"] = df["home_team_name"].str.contains("Mets", na=False).astype(int)
df["mets_runs"] = df.apply(lambda r: r["home_runs"] if r["is_home"] else r["away_runs"], axis=1)
df["opp_runs"] = df.apply(lambda r: r["away_runs"] if r["is_home"] else r["home_runs"], axis=1)
df = df.dropna(subset=["mets_runs","opp_runs"])
df = df.sort_values("gameDate").reset_index(drop=True)
df["result_bin"] = (df["mets_runs"] > df["opp_runs"]).astype(int)
df["last_result"] = df["result_bin"].shift(1).fillna(0)
df["month"] = df["gameDate"].dt.month
X = df[["is_home","last_result","month"]]
y = df["result_bin"]
Xtrain,Xtest,ytrain,ytest = train_test_split(X, y, test_size=0.2, random_state=42)
model = LogisticRegression(max_iter=500)
model.fit(Xtrain, ytrain)
pred = model.predict(Xtest)
print("Acc:", accuracy_score(ytest, pred))
print(classification_report(ytest, pred))
Path("models").mkdir(parents=True, exist_ok=True)
joblib.dump(model, "models/simple_win_predictor.joblib")
print("Saved model to models/simple_win_predictor.joblib")
