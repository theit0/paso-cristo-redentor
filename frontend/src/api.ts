// cerrado null: más de 7 días, sin pronóstico. prob_cerrado: solo en los días predichos (1–7).
export type Dia = { fecha: string; cerrado: boolean | null; prob_cerrado: number | null }
export type Anio = { hoy: string; dias: Dia[] }

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail ?? `HTTP ${r.status}`)
  return r.json()
}

export const fetchYear = () => get<Anio>('/api/year')
export const fetchSnowMap = () => get<import('./SnowMap').SnowGrid>('/api/snowmap')
