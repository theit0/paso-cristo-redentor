"""Modelos de referencia. Un modelo real tiene que ganarles para justificar su existencia.

Todos devuelven P(cerrado en t+h) para cada fila de `pairs()`.
"""
import numpy as np
import pandas as pd


def persistence(test: pd.DataFrame) -> np.ndarray:
    return test["closed_t"].astype(float).to_numpy()


def fit_climatology(train_closed: pd.Series, window: int = 15) -> pd.Series:
    """Tasa de cierre por día del año, suavizada ±window días (circular)."""
    by_doy = train_closed.groupby(train_closed.index.dayofyear).mean().reindex(range(1, 367))
    by_doy = by_doy.interpolate().bfill().ffill()  # el 29/2 casi no tiene datos
    ext = pd.concat([by_doy] * 3, ignore_index=True)
    smooth = ext.rolling(2 * window + 1, center=True).mean().iloc[366:732].to_numpy()
    return pd.Series(smooth, index=range(1, 367))


def climatology(clim: pd.Series, test: pd.DataFrame) -> np.ndarray:
    return clim.loc[test["target_date"].dt.dayofyear].to_numpy()


def fit_markov(train: pd.DataFrame) -> pd.Series:
    """P(cerrado en t+h | estado en t, mes de t), con suavizado de Laplace."""
    g = train.groupby([train.index.month, "closed_t"])["y"]
    return (g.sum() + 1) / (g.count() + 2)


def markov(table: pd.Series, test: pd.DataFrame) -> np.ndarray:
    keys = pd.MultiIndex.from_arrays([test.index.month, test["closed_t"]])
    return table.reindex(keys).fillna(0.5).to_numpy()
