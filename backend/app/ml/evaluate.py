"""Evalúa baselines y modelos con validación dejando un año afuera (entrena con los otros).

Uso (desde backend/): python -m app.ml.evaluate > ../docs/evaluacion.md
"""
import sys

import numpy as np
import pandas as pd

from app.ml import baselines, features
from app.ml.data import pairs, status_days
from app.ml.metrics import brier, log_loss, reliability
from app.ml.model import MODELS

HORIZONS = (1, 3, 7, 14)
WINTER = (5, 6, 7, 8, 9, 10)  # meses con nieve; ahí está casi todo el problema
BASELINES = ["persistencia", "climatologia", "markov"]


def baseline_cv(closed: pd.Series, h: int) -> pd.DataFrame:
    df = pairs(closed, h)
    out = []
    for year in sorted(df.index.year.unique()):
        test, train = df[df.index.year == year], df[df.index.year != year]
        clim = baselines.fit_climatology(closed[closed.index.year != year])
        out.append(test.assign(
            persistencia=baselines.persistence(test),
            climatologia=baselines.climatology(clim, test),
            markov=baselines.markov(baselines.fit_markov(train), test),
        ))
    return pd.concat(out)


def model_cv(table: pd.DataFrame) -> pd.DataFrame:
    """Predicciones fuera de muestra de cada modelo, indexadas por (t, h)."""
    X, y = table[features.FEATURES], table["y"]
    preds = pd.DataFrame(index=pd.MultiIndex.from_arrays([table.index, table["h"]], names=["t", "h"]))
    for name, make in MODELS.items():
        p = np.empty(len(table))
        for year in sorted(table.index.year.unique()):
            test = table.index.year == year
            p[test] = make().fit(X[~test], y[~test]).predict_proba(X[test])[:, 1]
        preds[name] = p
    return preds


def scores(df: pd.DataFrame, models: list[str]) -> pd.DataFrame:
    y = df["y"].to_numpy(float)
    ref = brier(df["markov"].to_numpy(), y)
    return pd.DataFrame({
        m: {"brier": brier(df[m].to_numpy(), y),
            "skill_vs_markov": 1 - brier(df[m].to_numpy(), y) / ref,
            "log_loss": log_loss(df[m].to_numpy(), y)}
        for m in models if df[m].notna().all()
    }).T


def md(df: pd.DataFrame) -> str:
    """Tabla markdown sin depender de tabulate."""
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    rows = [[str(i)] + [str(v) for v in r] for i, r in zip(df.index, df.itertuples(index=False))]
    return "\n".join("| " + " | ".join(r) + " |" for r in [cols, ["---"] * len(cols), *rows])


def main() -> None:
    status = status_days()
    closed = status != "abierto"
    table = features.build(status)
    preds = model_cv(table)
    models = BASELINES + list(MODELS)

    results = {}
    for h in HORIZONS:
        r = baseline_cv(closed, h)
        if h in features.HORIZONS:
            r = r.join(preds.xs(h, level="h"))
        results[h] = r.reindex(columns=[*r.columns.difference(list(MODELS)), *MODELS])

    print(f"# Evaluación\n\nDías: {closed.index[0].date()} → {closed.index[-1].date()}, cerrado {closed.mean():.1%}. "
          "Validación: un año afuera por vez. Target: cerrado para autos en t+h.\n")
    print("Brier: menor es mejor. skill_vs_markov: mejora sobre el mejor baseline (>0 = mejor). "
          "Los modelos con clima solo llegan a 7 días (no hay pronóstico archivado más allá).\n")
    for label, winter_only in [("Invierno (may–oct)", True), ("Todo el año", False)]:
        print(f"## {label}\n")
        rows = []
        for h, df in results.items():
            sub = df[df["target_date"].dt.month.isin(WINTER)] if winter_only else df
            s = scores(sub, models).round(3)
            s.insert(0, "h", h)
            rows.append(s)
        print(md(pd.concat(rows)) + "\n")

    for h in (1, 3, 7):
        w = results[h][results[h]["target_date"].dt.month.isin(WINTER)]
        print(f"## Confiabilidad de la logística, h={h}, invierno\n")
        print(md(reliability(w["logistica"].to_numpy(), w["y"].to_numpy(float)).round(3)) + "\n")

    for state, label in [(False, "hoy abierto → ¿cierra?"), (True, "hoy cerrado → ¿sigue cerrado?")]:
        print(f"## Por estado actual: {label} (invierno, h=3)\n")
        w = results[3][(results[3]["target_date"].dt.month.isin(WINTER)) & (results[3]["closed_t"] == state)]
        print(md(scores(w, models).round(3)) + "\n")

    lr = MODELS["logistica"]().fit(table[features.FEATURES], table["y"])
    coef = pd.Series(lr[-1].coef_[0], index=features.FEATURES).sort_values(key=abs, ascending=False)
    print("## Peso de cada feature (logística estandarizada, entrenada con todo)\n")
    print(md(coef.round(2).to_frame("coef")))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows usa cp1252 al redirigir
    main()
