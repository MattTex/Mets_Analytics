# data_pipeline.py
import requests
import pandas as pd
from datetime import datetime
from dateutil import parser
import os
import time

TEAM_NAME = "New York Mets"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_team_id(team_name):
    url = "https://statsapi.mlb.com/api/v1/teams?sportIds=1"
    r = requests.get(url, timeout=30)
    teams = r.json().get("teams", [])
    for t in teams:
        if t.get("name","").lower() == team_name.lower() or team_name.lower() in t.get("teamName","").lower() or team_name.lower() in t.get("name","").lower():
            return t.get("id")
    raise ValueError(f"Team '{team_name}' not found")

def fetch_games_for_season(team_id, season):
    start_date = f"{season}-03-01"
    end_date   = f"{season}-11-30"
    url = ("https://statsapi.mlb.com/api/v1/schedule"
           f"?sportId=1&teamId={team_id}&startDate={start_date}&endDate={end_date}&hydrate=game,linescore")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    games = []
    for date_block in data.get("dates", []):
        for g in date_block.get("games", []):
            games.append(g)
    return games

def games_to_df(games):
    rows = []
    for g in games:
        gamePk = g.get("gamePk")
        gameDate = g.get("gameDate")
        status = g.get("status", {}).get("detailedState")
        home = g.get("teams", {}).get("home", {})
        away = g.get("teams", {}).get("away", {})
        linescore = g.get("linescore", {}) 
        home_runs = linescore.get("teams", {}).get("home", {}).get("runs") if linescore else None
        away_runs = linescore.get("teams", {}).get("away", {}).get("runs") if linescore else None

        rows.append({
            "gamePk": gamePk,
            "gameDate": gameDate,
            "status": status,
            "home_team_id": home.get("team", {}).get("id"),
            "home_team_name": home.get("team", {}).get("name"),
            "away_team_id": away.get("team", {}).get("id"),
            "away_team_name": away.get("team", {}).get("name"),
            "home_runs": home_runs,
            "away_runs": away_runs,
            "venue": g.get("venue", {}).get("name"),
            "game_type": g.get("gameType"),
        })
    df = pd.DataFrame(rows)
    df["gameDate"] = pd.to_datetime(df["gameDate"])
    df["season"] = df["gameDate"].dt.year
    return df

def save_csv(df, season):
    out = os.path.join(DATA_DIR, f"mets_games_{season}.csv")
    df.to_csv(out, index=False)
    print("Saved", out)

def main():
    team_id = get_team_id(TEAM_NAME)
    print("Team id for", TEAM_NAME, "=", team_id)
    seasons = [2024, 2025]
    for s in seasons:
        print("Fetching season", s)
        games = fetch_games_for_season(team_id, s)
        df = games_to_df(games)
        save_csv(df, s)
        time.sleep(1)

if __name__ == "__main__":
    main()
