import pandas as pd

from app.config import REPO_DIR

DATASETS = REPO_DIR / "datasets"


def status_days() -> pd.Series:
    """Estado diario ('abierto' / 'solo_cargas' / 'total') desde 2022-01-01 hasta el último día de closures.csv."""
    cl = pd.read_csv(DATASETS / "closures.csv", parse_dates=["start", "end"])
    last = cl["end"].max() - pd.Timedelta(days=1)
    s = pd.Series("abierto", index=pd.date_range("2022-01-01", last), name="status")
    for r in cl.itertuples():
        s[r.start : r.end - pd.Timedelta(days=1)] = r.scope  # end es exclusivo
    return s


def closed_days() -> pd.Series:
    """Cerrado para autos: total o solo cargas."""
    return (status_days() != "abierto").rename("closed")


def pairs(closed: pd.Series, h: int) -> pd.DataFrame:
    """Una fila por día de emisión t: estado en t y lo que pasó en t+h (target)."""
    df = pd.DataFrame({"closed_t": closed, "y": closed.shift(-h)}).dropna()
    df["y"] = df["y"].astype(bool)
    df["target_date"] = df.index + pd.Timedelta(days=h)
    return df
