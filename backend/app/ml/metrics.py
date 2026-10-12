import numpy as np
import pandas as pd


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray, eps: float = 1e-3) -> float:
    p = np.clip(p, eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def reliability(p: np.ndarray, y: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """Por tramo de probabilidad predicha: cuánto se predijo vs. cuánto pasó."""
    df = pd.DataFrame({"p": p, "y": y})
    df["bin"] = pd.cut(df["p"], np.linspace(0, 1, bins + 1), include_lowest=True)
    return df.groupby("bin", observed=True).agg(predicho=("p", "mean"), observado=("y", "mean"), n=("y", "size"))
