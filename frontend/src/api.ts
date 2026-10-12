export type Prediccion = {
  fecha: string
  dias_adelante: number
  prob_cerrado: number
  prob_abierto: number
  veredicto: 'abierto' | 'cerrado' | 'incierto'
  confianza: 'alta' | 'media' | 'baja'
  fuente: 'estado_oficial' | 'modelo' | 'climatologia'
  aciertos_historicos_invierno: number | null
  nieve_pronosticada_cm: number | null
}

export type PredictResponse = {
  hoy: string
  estado_actual: {
    estado: string | null
    estado_vialidad: string | null
    horario: string | null
    horario_cancilleria: string | null
    source_time: string | null
  }
  modelo: string
  predicciones: Prediccion[]
}

export type DiaHistorial = { fecha: string; estado: 'abierto' | 'solo_cargas' | 'total' }

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail ?? `HTTP ${r.status}`)
  return r.json()
}

export const fetchPredict = (date?: string) =>
  get<PredictResponse>(date ? `/api/predict?date=${date}` : '/api/predict')
export const fetchHistory = (days = 60) => get<DiaHistorial[]>(`/api/history?days=${days}`)
