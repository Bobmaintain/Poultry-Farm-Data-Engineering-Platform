from pathlib import Path
import sqlite3
import pandas as pd

REQUIRED = [
    "date", "flock_id", "house_id", "opening_birds", "deaths", "culls",
    "feed_kg", "water_l", "avg_weight_kg", "sampled_birds"
]

def run_pipeline(project_dir: Path) -> pd.DataFrame:
    raw_path = project_dir / "data" / "raw" / "daily_flock.csv"
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(raw_path)
    missing = sorted(set(REQUIRED) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric = [c for c in REQUIRED if c not in {"date", "flock_id", "house_id"}]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=REQUIRED).copy()
    if (df[["opening_birds", "sampled_birds"]] <= 0).any().any():
        raise ValueError("opening_birds and sampled_birds must be positive")
    if (df[["deaths", "culls", "feed_kg", "water_l", "avg_weight_kg"]] < 0).any().any():
        raise ValueError("Counts, consumption and weight cannot be negative")
    if (df["deaths"] + df["culls"] > df["opening_birds"]).any():
        raise ValueError("Deaths plus culls cannot exceed opening birds")
    if (df["sampled_birds"] > df["opening_birds"]).any():
        raise ValueError("Sampled birds cannot exceed opening birds")

    df = df.sort_values(["flock_id", "date"]).drop_duplicates(
        subset=["flock_id", "date"], keep="last"
    )
    df["closing_birds"] = df["opening_birds"] - df["deaths"] - df["culls"]
    df["mortality_rate_pct"] = (df["deaths"] / df["opening_birds"] * 100).round(3)
    df["water_feed_ratio"] = (df["water_l"] / df["feed_kg"]).round(3)

    # Simplified cumulative estimate: current flock liveweight less first-day liveweight.
    df["estimated_liveweight_kg"] = df["closing_birds"] * df["avg_weight_kg"]
    df["initial_liveweight_kg"] = (
        df.groupby("flock_id")["estimated_liveweight_kg"].transform("first")
    )
    df["cumulative_feed_kg"] = df.groupby("flock_id")["feed_kg"].cumsum()
    gain = (df["estimated_liveweight_kg"] - df["initial_liveweight_kg"]).clip(lower=0)
    df["estimated_fcr"] = (df["cumulative_feed_kg"] / gain.replace(0, pd.NA)).round(3)

    curated = df.copy()
    curated["date"] = curated["date"].dt.strftime("%Y-%m-%d")
    curated.to_csv(output_dir / "poultry_daily_curated.csv", index=False)

    db_path = output_dir / "poultry_farm.db"
    with sqlite3.connect(db_path) as conn:
        curated.to_sql("daily_flock_kpis", conn, if_exists="replace", index=False)

    summary = df.groupby("flock_id").agg(
        days_recorded=("date", "count"),
        total_deaths=("deaths", "sum"),
        total_culls=("culls", "sum"),
        total_feed_kg=("feed_kg", "sum"),
        total_water_l=("water_l", "sum"),
        latest_avg_weight_kg=("avg_weight_kg", "last"),
        latest_closing_birds=("closing_birds", "last"),
    ).reset_index()
    summary.to_csv(output_dir / "flock_summary.csv", index=False)
    return df
