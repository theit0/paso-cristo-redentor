# Baselines

Días: 2022-01-01 → 2026-10-11, cerrado 18.5% del total. Validación: un año afuera por vez.

Brier: menor es mejor (0 = perfecto). skill_vs_clim: mejora sobre climatología (>0 = mejor).

## Todo el año

|  | h | tasa_cierre | brier | skill_vs_clim | log_loss |
| --- | --- | --- | --- | --- | --- |
| persistencia | 1 | 0.185 | 0.105 | 0.254 | 0.726 |
| climatologia | 1 | 0.185 | 0.141 | 0.0 | 0.435 |
| markov | 1 | 0.185 | 0.087 | 0.383 | 0.3 |
| persistencia | 3 | 0.185 | 0.173 | -0.227 | 1.194 |
| climatologia | 3 | 0.185 | 0.141 | 0.0 | 0.435 |
| markov | 3 | 0.185 | 0.122 | 0.135 | 0.392 |
| persistencia | 7 | 0.185 | 0.195 | -0.382 | 1.348 |
| climatologia | 7 | 0.185 | 0.141 | 0.0 | 0.436 |
| markov | 7 | 0.185 | 0.13 | 0.079 | 0.41 |
| persistencia | 14 | 0.186 | 0.232 | -0.639 | 1.605 |
| climatologia | 14 | 0.186 | 0.142 | 0.0 | 0.438 |
| markov | 14 | 0.186 | 0.143 | -0.007 | 0.439 |

## Invierno (may–oct)

|  | h | tasa_cierre | brier | skill_vs_clim | log_loss |
| --- | --- | --- | --- | --- | --- |
| persistencia | 1 | 0.312 | 0.149 | 0.351 | 1.029 |
| climatologia | 1 | 0.312 | 0.229 | 0.0 | 0.656 |
| markov | 1 | 0.312 | 0.13 | 0.433 | 0.427 |
| persistencia | 3 | 0.312 | 0.261 | -0.138 | 1.804 |
| climatologia | 3 | 0.312 | 0.229 | 0.0 | 0.656 |
| markov | 3 | 0.312 | 0.191 | 0.166 | 0.571 |
| persistencia | 7 | 0.312 | 0.298 | -0.298 | 2.058 |
| climatologia | 7 | 0.312 | 0.229 | 0.0 | 0.656 |
| markov | 7 | 0.312 | 0.206 | 0.103 | 0.603 |
| persistencia | 14 | 0.312 | 0.362 | -0.578 | 2.503 |
| climatologia | 14 | 0.312 | 0.229 | 0.0 | 0.656 |
| markov | 14 | 0.312 | 0.229 | 0.003 | 0.656 |

## Confiabilidad de Markov, h=3, invierno

| bin | predicho | observado | n |
| --- | --- | --- | --- |
| (-0.001, 0.1] | 0.088 | 0.143 | 35 |
| (0.1, 0.2] | 0.161 | 0.244 | 283 |
| (0.2, 0.3] | 0.241 | 0.182 | 292 |
| (0.3, 0.4] | 0.346 | 0.282 | 71 |
| (0.4, 0.5] | 0.456 | 0.56 | 50 |
| (0.5, 0.6] | 0.572 | 0.865 | 52 |
| (0.6, 0.7] | 0.683 | 0.5 | 52 |
| (0.7, 0.8] | 0.737 | 0.538 | 65 |
