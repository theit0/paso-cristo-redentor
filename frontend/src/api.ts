export type Clima = {
  nieve_cm: number | null
  precip_mm: number | null
  viento_kmh: number | null
  temp_min: number | null
  temp_max: number | null
}

export type Factor = { factor: string; empuja_a: 'abierto' | 'cerrado'; peso: number }

export type Prediccion = {
  fecha: string
  dias_adelante: number
  prob_cerrado: number
  prob_abierto: number
  confianza: 'alta' | 'media' | 'baja'
  fuente: 'estado_oficial' | 'modelo' | 'climatologia'
  aciertos_historicos_invierno: number | null
  clima: Clima | null
  factores: Factor[]
  base_abierto: number | null
}

export type Contexto = {
  dias_en_estado: number
  nieve_3d_cm: number | null
  nieve_7d_cm: number | null
  nieve_14d_cm: number | null
  nieve_suelo_cm: number | null
  dias_sin_nevada: number
  temp_min_ayer: number | null
}

export type Pronostico = {
  hoy: string
  estado_actual: {
    estado: string | null
    estado_vialidad: string | null
    horario: string | null
    horario_cancilleria: string | null
    source_time: string | null
  }
  modelo: string
  contexto: Contexto
  predicciones: Prediccion[]
}

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail ?? `HTTP ${r.status}`)
  return r.json()
}

export const fetchWeek = () => get<Pronostico>('/api/predict')
export const fetchDay = (date: string) => get<Pronostico>(`/api/predict?date=${date}`).then(r => r.predicciones[0])
