from pathlib import Path
from src.pipeline import run_pipeline

if __name__ == "__main__":
    result = run_pipeline(Path(__file__).resolve().parent)
    print("Poultry pipeline complete.")
    print(result[["date", "flock_id", "mortality_rate_pct", "water_feed_ratio", "estimated_fcr"]].tail())
