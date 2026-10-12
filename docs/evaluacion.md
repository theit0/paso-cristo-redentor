# Evaluación

Días: 2022-01-01 → 2026-10-11, cerrado 18.5%. Validación: un año afuera por vez. Target: cerrado para autos en t+h.

Brier: menor es mejor. skill_vs_markov: mejora sobre el mejor baseline (>0 = mejor). Los modelos con clima solo llegan a 7 días (no hay pronóstico archivado más allá).

## Invierno (may–oct)

|  | h | brier | skill_vs_markov | log_loss |
| --- | --- | --- | --- | --- |
| persistencia | 1 | 0.149 | -0.144 | 1.029 |
| climatologia | 1 | 0.229 | -0.764 | 0.656 |
| markov | 1 | 0.13 | 0.0 | 0.427 |
| logistica | 1 | 0.093 | 0.286 | 0.312 |
| boosting | 1 | 0.106 | 0.186 | 0.346 |
| persistencia | 3 | 0.261 | -0.365 | 1.804 |
| climatologia | 3 | 0.229 | -0.2 | 0.656 |
| markov | 3 | 0.191 | 0.0 | 0.571 |
| logistica | 3 | 0.102 | 0.467 | 0.34 |
| boosting | 3 | 0.127 | 0.338 | 0.402 |
| persistencia | 7 | 0.298 | -0.447 | 2.058 |
| climatologia | 7 | 0.229 | -0.115 | 0.656 |
| markov | 7 | 0.206 | 0.0 | 0.603 |
| logistica | 7 | 0.147 | 0.288 | 0.453 |
| boosting | 7 | 0.169 | 0.177 | 0.531 |
| persistencia | 14 | 0.362 | -0.583 | 2.503 |
| climatologia | 14 | 0.229 | -0.003 | 0.656 |
| markov | 14 | 0.229 | 0.0 | 0.656 |

## Todo el año

|  | h | brier | skill_vs_markov | log_loss |
| --- | --- | --- | --- | --- |
| persistencia | 1 | 0.105 | -0.209 | 0.726 |
| climatologia | 1 | 0.141 | -0.62 | 0.435 |
| markov | 1 | 0.087 | 0.0 | 0.3 |
| logistica | 1 | 0.065 | 0.246 | 0.235 |
| boosting | 1 | 0.074 | 0.143 | 0.262 |
| persistencia | 3 | 0.173 | -0.419 | 1.194 |
| climatologia | 3 | 0.141 | -0.157 | 0.435 |
| markov | 3 | 0.122 | 0.0 | 0.392 |
| logistica | 3 | 0.071 | 0.415 | 0.255 |
| boosting | 3 | 0.086 | 0.294 | 0.299 |
| persistencia | 7 | 0.195 | -0.502 | 1.348 |
| climatologia | 7 | 0.141 | -0.086 | 0.436 |
| markov | 7 | 0.13 | 0.0 | 0.41 |
| logistica | 7 | 0.097 | 0.256 | 0.325 |
| boosting | 7 | 0.111 | 0.146 | 0.377 |
| persistencia | 14 | 0.232 | -0.628 | 1.605 |
| climatologia | 14 | 0.142 | 0.007 | 0.438 |
| markov | 14 | 0.143 | 0.0 | 0.439 |

## Confiabilidad de la logística, h=1, invierno

| bin | predicho | observado | n |
| --- | --- | --- | --- |
| (-0.001, 0.1] | 0.051 | 0.04 | 426 |
| (0.1, 0.2] | 0.138 | 0.141 | 156 |
| (0.2, 0.3] | 0.252 | 0.333 | 54 |
| (0.3, 0.4] | 0.347 | 0.541 | 37 |
| (0.4, 0.5] | 0.446 | 0.769 | 26 |
| (0.5, 0.6] | 0.549 | 0.824 | 17 |
| (0.6, 0.7] | 0.648 | 0.944 | 18 |
| (0.7, 0.8] | 0.745 | 0.833 | 24 |
| (0.8, 0.9] | 0.858 | 0.808 | 26 |
| (0.9, 1.0] | 0.98 | 0.966 | 116 |

## Confiabilidad de la logística, h=3, invierno

| bin | predicho | observado | n |
| --- | --- | --- | --- |
| (-0.001, 0.1] | 0.051 | 0.041 | 386 |
| (0.1, 0.2] | 0.14 | 0.146 | 151 |
| (0.2, 0.3] | 0.245 | 0.267 | 75 |
| (0.3, 0.4] | 0.349 | 0.488 | 41 |
| (0.4, 0.5] | 0.444 | 0.568 | 37 |
| (0.5, 0.6] | 0.544 | 0.667 | 24 |
| (0.6, 0.7] | 0.644 | 0.733 | 30 |
| (0.7, 0.8] | 0.747 | 0.85 | 20 |
| (0.8, 0.9] | 0.851 | 0.867 | 30 |
| (0.9, 1.0] | 0.977 | 0.953 | 106 |

## Confiabilidad de la logística, h=7, invierno

| bin | predicho | observado | n |
| --- | --- | --- | --- |
| (-0.001, 0.1] | 0.054 | 0.078 | 358 |
| (0.1, 0.2] | 0.143 | 0.211 | 161 |
| (0.2, 0.3] | 0.243 | 0.342 | 79 |
| (0.3, 0.4] | 0.353 | 0.452 | 62 |
| (0.4, 0.5] | 0.455 | 0.321 | 28 |
| (0.5, 0.6] | 0.554 | 0.545 | 33 |
| (0.6, 0.7] | 0.649 | 0.556 | 27 |
| (0.7, 0.8] | 0.749 | 0.59 | 39 |
| (0.8, 0.9] | 0.843 | 0.75 | 28 |
| (0.9, 1.0] | 0.972 | 0.918 | 85 |

## Por estado actual: hoy abierto → ¿cierra? (invierno, h=3)

|  | brier | skill_vs_markov | log_loss |
| --- | --- | --- | --- |
| persistencia | 0.19 | -0.212 | 1.316 |
| climatologia | 0.186 | -0.183 | 0.559 |
| markov | 0.157 | 0.0 | 0.495 |
| logistica | 0.09 | 0.429 | 0.312 |
| boosting | 0.104 | 0.337 | 0.34 |

## Por estado actual: hoy cerrado → ¿sigue cerrado? (invierno, h=3)

|  | brier | skill_vs_markov | log_loss |
| --- | --- | --- | --- |
| persistencia | 0.418 | -0.564 | 2.887 |
| climatologia | 0.326 | -0.222 | 0.87 |
| markov | 0.267 | 0.0 | 0.737 |
| logistica | 0.129 | 0.517 | 0.403 |
| boosting | 0.176 | 0.34 | 0.538 |

## Peso de cada feature (logística estandarizada, entrenada con todo)

|  | coef |
| --- | --- |
| fc_precip | 1.76 |
| fc_temp_max | -1.37 |
| x_h_precip | -1.02 |
| fc_nieve_acum | 0.66 |
| x_cerrado_dias | 0.39 |
| fc_temp_min | 0.37 |
| dias_sin_nevada | 0.28 |
| nieve_7d | 0.27 |
| nieve_3d | 0.15 |
| solo_cargas_t | -0.13 |
| nieve_suelo | 0.11 |
| closed_t | 0.09 |
| fc_nieve | 0.09 |
| nieve_14d | 0.07 |
| temp_min_ayer | 0.07 |
| x_cerrado_precip | 0.07 |
| estacion_cos | 0.06 |
| estacion_sin | 0.05 |
| fc_nieve_max_dia | 0.05 |
| fc_viento | 0.03 |
| h | -0.02 |
| dias_en_estado | 0.02 |
| x_cerrado_nieve_acum | -0.01 |
