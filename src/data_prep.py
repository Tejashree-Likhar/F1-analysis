"""
Data preparation for the F1 WDC Predictor project.

Loads the raw per-race dataset (2000-2024), fixes a data-leakage issue in the
championship-points/wins columns (they are cumulative *including* the current
race), attaches human-readable driver/constructor/circuit names, and writes
a clean, model-ready CSV.
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_raw():
    df = pd.read_csv(DATA_DIR / "race_data_raw.csv")
    return df


def fix_leakage(df: pd.DataFrame) -> pd.DataFrame:
    """
    wins, points_driver_champ, wins_cons, points_cons_champ are cumulative
    totals THROUGH the current race (i.e. they already include this race's
    result). Using them as predictive features would leak the target, and
    they can't be reproduced at simulation/inference time anyway (we don't
    know the outcome of the race we're trying to predict). We shift them by
    one race within each (year, driver) / (year, constructor) group so they
    represent the state ENTERING the race.
    """
    df = df.sort_values(["year", "round"]).reset_index(drop=True)

    df["driver_wins_entering"] = (
        df.groupby(["year", "driverId"])["wins"].shift(1).fillna(0)
    )
    df["driver_champ_pts_entering"] = (
        df.groupby(["year", "driverId"])["points_driver_champ"].shift(1).fillna(0)
    )
    df["cons_wins_entering"] = (
        df.groupby(["year", "constructorId"])["wins_cons"].shift(1).fillna(0)
    )
    df["cons_champ_pts_entering"] = (
        df.groupby(["year", "constructorId"])["points_cons_champ"].shift(1).fillna(0)
    )
    return df


def add_race_points(df: pd.DataFrame) -> pd.DataFrame:
    """
    IMPORTANT DATA QUIRK: the raw `points` column is identical to
    `points_driver_champ` -- it's the driver's CUMULATIVE championship total
    through that race, not the points scored IN that race. (Verified: the
    two columns are byte-for-byte equal across all 9,839 rows.) That means
    anything wanting "how many points did they score at this Grand Prix"
    needs a derived column: the race-over-race increase in the cumulative
    total within each (year, driver) group.
    """
    df = df.sort_values(["year", "driverId", "round"]).reset_index(drop=True)
    race_pts = df.groupby(["year", "driverId"])["points"].diff()
    # first race of a driver's season: cumulative total IS the race total
    race_pts = race_pts.fillna(df["points"])
    df["race_points"] = race_pts.clip(lower=0)
    return df


def attach_names(df: pd.DataFrame) -> pd.DataFrame:
    drivers = pd.read_csv(DATA_DIR / "drivers.csv")
    constructors = pd.read_csv(DATA_DIR / "constructors.csv")
    circuits = pd.read_csv(DATA_DIR / "circuits.csv")
    races = pd.read_csv(DATA_DIR / "races.csv")[["raceId", "name"]].rename(
        columns={"name": "race_name"}
    )

    drivers["driver_name"] = drivers["forename"] + " " + drivers["surname"]
    df = df.merge(
        drivers[["driverId", "driver_name", "code", "nationality"]],
        on="driverId", how="left"
    )
    df = df.merge(
        constructors[["constructorId", "name"]].rename(columns={"name": "constructor_name"}),
        on="constructorId", how="left"
    )
    df = df.merge(
        circuits[["circuitId", "name", "country"]].rename(
            columns={"name": "circuit_name", "country": "circuit_country"}
        ),
        on="circuitId", how="left"
    )
    df = df.merge(races, on="raceId", how="left")
    return df


FEATURE_COLUMNS = [
    "grid",
    "Driver Top 3 Finish Percentage (Last Year)",
    "Constructor Top 3 Finish Percentage (Last Year)",
    "Driver Top 3 Finish Percentage (This Year till last race)",
    "Constructor Top 3 Finish Percentage (This Year till last race)",
    "Driver Avg position (Last Year)",
    "Constructor Avg position (Last Year)",
    "Driver Average Position (This Year till last race)",
    "Constructor Average Position (This Year till last race)",
    "driver_age",
    "cons_wins_entering",
    "cons_champ_pts_entering",
    "driver_wins_entering",
    "driver_champ_pts_entering",
    "Weighted_Top_3_Probability",
    "Weighted_Top_3_Prob_Length",
    "position_previous_race",
    "nro_cond_escuderia",
    "prom_points_10",
    "Turns",
    "Length",
    "rainy",
]

TARGET_POINTS = "race_points"
TARGET_PODIUM = "Top 3 Finish"


def build_dataset():
    df = load_raw()
    df = fix_leakage(df)
    df = add_race_points(df)
    df = attach_names(df)
    # drop rows with missing target
    df = df.dropna(subset=[TARGET_POINTS, TARGET_PODIUM])
    for c in FEATURE_COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df[FEATURE_COLUMNS] = df[FEATURE_COLUMNS].fillna(0)
    out_path = DATA_DIR / "race_data_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved clean dataset: {out_path}  ({len(df)} rows)")
    return df


if __name__ == "__main__":
    build_dataset()
