export type Prediccion = {
  fecha: string
  dias_adelante: number
  prob_cerrado: number
  prob_abierto: number
  confianza: 'alta' | 'media' | 'baja'
  fuente: 'estado_oficial' | 'modelo' | 'climatologia'
}

type PredictResponse = { predicciones: Prediccion[] }

export async function fetchPrediction(date: string): Promise<Prediccion> {
  const r = await fetch(`/api/predict?date=${date}`)
  if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail ?? `HTTP ${r.status}`)
  return ((await r.json()) as PredictResponse).predicciones[0]
}
