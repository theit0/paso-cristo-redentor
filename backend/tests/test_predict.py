"""El cálculo de producción (Python puro) tiene que dar lo mismo que el de entrenamiento (pandas/sklearn).
Si algún día divergen, el modelo vería en vivo datos distintos a los que aprendió, sin que nada falle."""
import math
from datetime import date

import numpy as np
import pytest

pd = pytest.importorskip("pandas")
from app import predict  # noqa: E402
from app.ml import features  # noqa: E402
from app.ml.data import status_days  # noqa: E402
from app.ml.model import logistic  # noqa: E402


@pytest.fixture(scope="module")
def training():
    status = status_days()
    table = features.build(status)
    obs, fc = features.load_weather()
    return status, table, obs, fc


def live_inputs(status, obs, fc, t: pd.Timestamp):
    """Arma los insumos de producción para el día de emisión t a partir de los datasets."""
    st = {d.date(): s for d, s in status[:t].items()}
    ob = {d.date(): r.to_dict() for d, r in obs[:t - pd.Timedelta(days=1)].iterrows()}
    fcd = {}
    for k in range(1, 8):
        d = t + pd.Timedelta(days=k)
        if (d, k) in fc.index:
            fcd[d.date()] = fc.loc[(d, k)].to_dict()
    return st, ob, fcd


def sample(table, n=150):
    rows = table[(table.index >= "2022-04-01") & table["target_date"].dt.month.isin([5, 6, 7, 8, 9])]
    return rows.sample(n, random_state=0)


def test_features_match_training(training):
    status, table, obs, fc = training
    for t, row in sample(table).iterrows():
        st, ob, fcd = live_inputs(status, obs, fc, t)
        live = predict.features_row(st, ob, fcd, t.date(), int(row["h"]))
        for name in features.FEATURES:
            a, b = row[name], live[name]
            if pd.isna(a):
                assert b is None, (t, row["h"], name, a, b)
            else:
                assert b == pytest.approx(a, abs=1e-6), (t, row["h"], name, a, b)


def test_probability_matches_sklearn(training, monkeypatch):
    _, table, _, _ = training
    pipe = logistic().fit(table[features.FEATURES], table["y"])
    imputer, scaler, lr = pipe.named_steps.values()
    monkeypatch.setattr(predict, "model", lambda: {
        "features": features.FEATURES, "medianas": imputer.statistics_.tolist(), "media": scaler.mean_.tolist(),
        "escala": scaler.scale_.tolist(), "coef": lr.coef_[0].tolist(), "intercepto": float(lr.intercept_[0]),
    })
    rows = sample(table)
    expected = pipe.predict_proba(rows[features.FEATURES])[:, 1]
    got = [predict.probability({k: (None if pd.isna(v) else v) for k, v in r.items()})
           for r in rows[features.FEATURES].to_dict("records")]
    np.testing.assert_allclose(got, expected, atol=1e-9)


def test_run_length_caps_and_defaults_to_open():
    st = {date(2024, 6, 1): "total", date(2024, 6, 2): "solo_cargas"}
    assert predict.run_length(st, date(2024, 6, 2)) == 2
    assert predict.run_length(st, date(2024, 6, 4)) == 2  # 3 y 4 sin dato = abierto
    assert predict.run_length({}, date(2024, 6, 4)) == 60
    assert math.isclose(predict.run_length({}, date(2024, 6, 4), cap=5), 5)


def test_export_rejects_worse_model():
    from app.ml.export import worse_horizons
    old = {"1": {"brier": 0.10}, "7": {"brier": 0.15}}
    assert worse_horizons({"1": {"brier": 0.105}, "7": {"brier": 0.14}}, old) == []
    assert worse_horizons({"1": {"brier": 0.12}, "7": {"brier": 0.15}}, old) == ["1"]
