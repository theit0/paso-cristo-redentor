// Fechas AAAA-MM-DD (día de Mendoza); parsear al mediodía evita corrimientos por zona horaria.
export const asDate = (iso: string) => new Date(`${iso}T12:00:00`)
export const weekday = (iso: string) => asDate(iso).toLocaleDateString('es-AR', { weekday: 'short' }).replace('.', '')
export const dayMonth = (iso: string) => asDate(iso).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' }).replace('.', '')
export const pct = (p: number) => `${Math.round(p * 100)}%`
export const round = (n: number) => Math.round(n)

// Códigos WMO de Open-Meteo, agrupados.
export function sky(code: number): string {
  if (code === 0) return 'Despejado'
  if (code <= 3) return 'Nublado'
  if (code <= 48) return 'Niebla'
  if (code <= 67 || (code >= 80 && code <= 82)) return 'Lluvia'
  if (code <= 77 || code === 85 || code === 86) return 'Nieve'
  return 'Tormenta'
}
