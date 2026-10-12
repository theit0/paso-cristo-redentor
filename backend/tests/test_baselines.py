import numpy as np
import pytest

pd = pytest.importorskip("pandas")
from app.ml import baselines  # noqa: E402
from app.ml.data import pairs  # noqa: E402
from app.ml.metrics import brier, log_loss  # noqa: E402


def july_closed(years=(2022, 2023, 2024)):
    idx = pd.date_range(f"{years[0]}-01-01", f"{years[-1]}-12-31")
    return pd.Series(idx.month == 7, index=idx)


def test_pairs_aligns_target_h_days_ahead():
    s = july_closed()
    p = pairs(s, 3)
    assert p.loc["2022-06-28", "y"] and not p.loc["2022-06-28", "closed_t"]  # 1/7 cerrado
    assert p.loc["2022-06-27", "y"] == False  # 30/6 abierto
    assert p["target_date"].iloc[0] == p.index[0] + pd.Timedelta(days=3)
    assert p.index[-1] == s.index[-1] - pd.Timedelta(days=3)


def test_climatology_learns_season():
    clim = baselines.fit_climatology(july_closed())
    assert clim[200] > 0.9  # 19/7
    assert clim[15] == 0  # enero
    assert 0.3 < clim[182] < 0.7  # borde 1/7, suavizado


def test_markov_learns_persistence():
    s = july_closed()
    table = baselines.fit_markov(pairs(s, 1))
    assert table[(7, True)] > 0.9  # cerrado en julio sigue cerrado
    assert table[(1, False)] < 0.05


def test_metrics():
    y = np.array([0.0, 1.0])
    assert brier(np.array([0.0, 1.0]), y) == 0
    assert brier(np.array([0.5, 0.5]), y) == 0.25
    assert log_loss(np.array([0.5, 0.5]), y) == pytest.approx(np.log(2))
