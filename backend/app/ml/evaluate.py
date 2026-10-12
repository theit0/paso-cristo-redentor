"""Evalúa los baselines con validación dejando un año afuera (entrena con los otros).

Uso (desde backend/): python -m app.ml.evaluate > ../docs/baselines.md
"""
import sys

import numpy as np
import pandas as pd

from app.ml import baselines
from app.ml.data import closed_days, pairs
from app.ml.metrics import brier, log_loss, reliability

HORIZONS = (1, 3, 7, 14)
WINTER = (5, 6, 7, 8, 9, 10)  # meses con nieve; ahí está casi todo el problema


def cross_validate(closed: pd.Series, h: int) -> pd.DataFrame:
    df = pairs(closed, h)
    out = []
    for year in sorted(df.index.year.unique()):
        test = df[df.index.year == year]
        train = df[df.index.year != year]
        clim = baselines.fit_climatology(closed[closed.index.year != year])
        out.append(test.assign(
            persistencia=baselines.persistence(test),
            climatologia=baselines.climatology(clim, test),
            markov=baselines.markov(baselines.fit_markov(train), test),
        ))
    return pd.concat(out)


MODELS = ["persistencia", "climatologia", "markov"]


def md(df: pd.DataFrame) -> str:
    """Tabla markdown sin depender de tabulate."""
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    rows = [[str(i)] + [str(v) for v in r] for i, r in zip(df.index, df.itertuples(index=False))]
    return "\n".join("| " + " | ".join(r) + " |" for r in [cols, ["---"] * len(cols), *rows])


def scores(df: pd.DataFrame) -> pd.DataFrame:
    y = df["y"].to_numpy(float)
    ref = brier(df["climatologia"].to_numpy(), y)
    return pd.DataFrame({
        m: {"brier": brier(df[m].to_numpy(), y),
            "skill_vs_clim": 1 - brier(df[m].to_numpy(), y) / ref,
            "log_loss": log_loss(df[m].to_numpy(), y)}
        for m in MODELS
    }).T


def main() -> None:
    closed = closed_days()
    print(f"# Baselines\n\nDías: {closed.index[0].date()} → {closed.index[-1].date()}, "
          f"cerrado {closed.mean():.1%} del total. Validación: un año afuera por vez.\n")
    print("Brier: menor es mejor (0 = perfecto). skill_vs_clim: mejora sobre climatología (>0 = mejor).\n")
    results = {h: cross_validate(closed, h) for h in HORIZONS}
    for label, mask in [("Todo el año", lambda d: np.full(len(d), True)),
                        ("Invierno (may–oct)", lambda d: d["target_date"].dt.month.isin(WINTER))]:
        print(f"## {label}\n")
        rows = []
        for h, df in results.items():
            sub = df[mask(df)]
            s = scores(sub).round(3)
            s.insert(0, "h", h)
            s.insert(1, "tasa_cierre", round(sub["y"].mean(), 3))
            rows.append(s)
        print(md(pd.concat(rows)))
        print()
    w = results[3][results[3]["target_date"].dt.month.isin(WINTER)]
    print("## Confiabilidad de Markov, h=3, invierno\n")
    print(md(reliability(w["markov"].to_numpy(), w["y"].to_numpy(float)).round(3)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows usa cp1252 al redirigir
    main()
