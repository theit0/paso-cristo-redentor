import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'

export const pct = (p: number) => Math.round(p * 100)
export const fmt = (iso: string, f: string) => format(parseISO(iso), f, { locale: es })
export const dayLabel = (iso: string, h: number) => (h === 0 ? 'Hoy' : h === 1 ? 'Mañana' : fmt(iso, 'EEE'))

// Abierto/Cerrado se decide en 50%; entre 35% y 65% el resultado es ajustado.
export const isOpen = (pOpen: number) => pOpen >= 0.5
export const isClose = (pOpen: number) => pOpen > 0.35 && pOpen < 0.65

export function tone(pOpen: number): 'open' | 'tight' | 'closed' {
  if (isClose(pOpen)) return 'tight'
  return isOpen(pOpen) ? 'open' : 'closed'
}

export const TONE = {
  open: { text: 'text-emerald-400', bg: 'bg-emerald-400', soft: 'bg-emerald-400/15', ring: 'ring-emerald-400/40', hex: '#34d399' },
  tight: { text: 'text-amber-300', bg: 'bg-amber-300', soft: 'bg-amber-300/15', ring: 'ring-amber-300/40', hex: '#fcd34d' },
  closed: { text: 'text-rose-400', bg: 'bg-rose-400', soft: 'bg-rose-400/15', ring: 'ring-rose-400/40', hex: '#fb7185' },
}

export const num = (x: number | null | undefined, unit = '') => (x === null || x === undefined ? '—' : `${Math.round(x)}${unit}`)
