import pandas as pd

from app.config import REPO_DIR

DATASETS = REPO_DIR / "datasets"
# Para quien viaja en auto, "solo cargas" también es cerrado.
CLOSED_SCOPES = ("total", "solo_cargas")


def closed_days() -> pd.Series:
    """Serie diaria (bool) desde 2022-01-01 hasta el último día cubierto por closures.csv."""
    cl = pd.read_csv(DATASETS / "closures.csv", parse_dates=["start", "end"])
    last = cl["end"].max() - pd.Timedelta(days=1)
    s = pd.Series(False, index=pd.date_range("2022-01-01", last), name="closed")
    for r in cl[cl["scope"].isin(CLOSED_SCOPES)].itertuples():
        s[r.start : r.end - pd.Timedelta(days=1)] = True  # end es exclusivo
    return s


def pairs(closed: pd.Series, h: int) -> pd.DataFrame:
    """Una fila por día de emisión t: estado en t y lo que pasó en t+h (target)."""
    df = pd.DataFrame({"closed_t": closed, "y": closed.shift(-h)}).dropna()
    df["y"] = df["y"].astype(bool)
    df["target_date"] = df.index + pd.Timedelta(days=h)
    return df
