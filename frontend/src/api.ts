export type Dia = { fecha: string; cerrado: boolean | null } // null: más de 7 días, sin pronóstico
export type Anio = { hoy: string; dias: Dia[] }

export async function fetchYear(): Promise<Anio> {
  const r = await fetch('/api/year')
  if (!r.ok) throw new Error((await r.json().catch(() => null))?.detail ?? `HTTP ${r.status}`)
  return r.json()
}
