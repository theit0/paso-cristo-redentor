"""Modelos de P(cerrado en t+h). Un solo modelo para todas las anticipaciones (h es una feature)
y para cierre y reapertura a la vez (el estado de hoy es una feature)."""
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def logistic():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=0.5, max_iter=2000))


def boosting():
    # ponytail: hiperparámetros a mano y conservadores (pocos años de datos); tunear si hay más historia.
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.04, max_leaf_nodes=15,
                                          min_samples_leaf=40, l2_regularization=1.0, random_state=0)


MODELS = {"logistica": logistic, "boosting": boosting}
