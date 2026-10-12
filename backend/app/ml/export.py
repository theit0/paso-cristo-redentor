"""Entrena el modelo final con todos los datos y lo exporta a app/model.json.

En producción se usa ese JSON con Python puro: el servidor no necesita pandas ni scikit-learn.
Uso (desde backend/): python -m app.ml.export
"""
import json
from datetime import date

import numpy as np

from app.config import REPO_DIR
from app.ml import baselines, features
from app.ml.data import status_days
from app.ml.model import logistic

OUT = REPO_DIR / "backend" / "app" / "model.json"
WINTER = (5, 6, 7, 8, 9, 10)


def metrics_by_horizon(table) -> dict:
    """Aciertos y Brier fuera de muestra (un año afuera), en invierno, por anticipación."""
    X, y = table[features.FEATURES], table["y"].to_numpy(float)
    p = np.empty(len(table))
    for year in sorted(table.index.year.unique()):
        test = table.index.year == year
        p[test] = logistic().fit(X[~test], y[~test]).predict_proba(X[test])[:, 1]
    winter = table["target_date"].dt.month.isin(WINTER).to_numpy()
    out = {}
    for h in features.HORIZONS:
        m = winter & (table["h"] == h).to_numpy()
        out[h] = {"aciertos": round(float(((p[m] >= 0.5) == y[m]).mean()), 3),
                  "brier": round(float(np.mean((p[m] - y[m]) ** 2)), 3)}
    return out


def main() -> None:
    status = status_days()
    table = features.build(status)
    pipe = logistic().fit(table[features.FEATURES], table["y"])
    imputer, scaler, lr = pipe.named_steps.values()
    clim = baselines.fit_climatology(status != "abierto")
    model = {
        "version": date.today().isoformat(),
        "datos_hasta": status.index[-1].date().isoformat(),
        "features": features.FEATURES,
        "medianas": imputer.statistics_.round(6).tolist(),
        "media": scaler.mean_.round(6).tolist(),
        "escala": scaler.scale_.round(6).tolist(),
        "coef": lr.coef_[0].round(6).tolist(),
        "intercepto": round(float(lr.intercept_[0]), 6),
        "climatologia": clim.round(4).tolist(),  # índice 0 = día del año 1
        "metricas_invierno": metrics_by_horizon(table),
    }
    OUT.write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"modelo exportado a {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
