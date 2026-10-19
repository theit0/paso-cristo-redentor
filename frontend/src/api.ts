// cerrado null: más de 7 días, sin pronóstico. prob_cerrado: solo en los días predichos (1–7).
// predicho/acerto: en pasado y hoy, la P(cerrado) que se había predicho la víspera y si acertó (null si no se guardó).
export type Dia = {
  fecha: string
  cerrado: boolean | null
  prob_cerrado: number | null
  predicho: number | null
  acerto: boolean | null
}
// aciertos: todos los días con predicción guardada desde que existe la app, no solo los de este año.
export type Anio = {
  hoy: string
  anio: number
  primer_anio: number
  dias: Dia[]
  aciertos: { acertados: number; total: number }
}

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail ?? `HTTP ${r.status}`)
  return r.json()
}

export const fetchYear = (anio?: number) => get<Anio>(anio ? `/api/year?anio=${anio}` : '/api/year')
export const fetchSnowMap = () => get<import('./SnowMap').SnowGrid>('/api/snowmap')
