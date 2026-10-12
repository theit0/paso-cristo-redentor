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

export type DiaClima = {
  fecha: string
  codigo: number
  temp_min: number
  temp_max: number
  nieve_cm: number
  precip_mm: number
  rafagas: number
}

export type PuntoClima = {
  id: string
  nombre: string
  lat: number
  lon: number
  altura: number
  actual: { temp: number; viento: number; rafagas: number; nevando: boolean; codigo: number }
  dias: DiaClima[]
}

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail ?? `HTTP ${r.status}`)
  return r.json()
}

export const fetchPredict = (date?: string) =>
  get<PredictResponse>(date ? `/api/predict?date=${date}` : '/api/predict')
export const fetchYear = (year: number) => get<DiaHistorial[]>(`/api/history?year=${year}`)
export const fetchWeather = () => get<PuntoClima[]>('/api/weather')
