import math

from app import predict


def test_every_feature_has_a_label():
    assert set(predict.model()["features"]) <= set(predict.LABELS)


def test_factors_add_up_to_the_probability():
    """La explicación tiene que ser exacta: intercepto + todos los aportes = log-odds del modelo."""
    m = predict.model()
    row = dict(zip(m["features"], m["medianas"]))
    row.update(closed_t=1, fc_precip=12.0, fc_nieve_acum=20.0, x_cerrado_precip=12.0, x_cerrado_nieve_acum=20.0)
    factors = predict.top_factors(row, n=len(m["features"]))
    z = m["intercepto"] + sum(f["peso"] * (1 if f["empuja_a"] == "cerrado" else -1) for f in factors)
    assert 1 / (1 + math.exp(-z)) == __import__("pytest").approx(predict.probability(row), abs=0.01)
    assert factors == sorted(factors, key=lambda f: f["peso"], reverse=True)
