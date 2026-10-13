import { Cloud, CloudRain, CloudSnow, Sun } from 'lucide-react'
import type { Clima } from '@/api'

export function WeatherIcon({ c, className }: { c: Clima | null; className?: string }) {
  if (!c) return <Cloud className={className} />
  const precip = c.precip_mm ?? 0
  const cold = (c.temp_max ?? 99) <= 1 // con máximas bajo cero, la precipitación es nieve
  if ((c.nieve_cm ?? 0) >= 1 || (precip >= 1 && cold)) return <CloudSnow className={className} />
  if (precip >= 1) return <CloudRain className={className} />
  if (precip > 0.2) return <Cloud className={className} />
  return <Sun className={className} />
}
