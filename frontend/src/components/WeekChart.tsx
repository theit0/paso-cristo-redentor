import { Snowflake, Wind } from 'lucide-react'
import type { Prediccion } from '@/api'
import { dayLabel, fmt, num, pct, tone, TONE } from '@/lib/format'
import { WeatherIcon } from './WeatherIcon'

const H = 140 // alto del área del gráfico (px)
const y = (p: number) => 8 + (1 - p) * (H - 16)

type Props = { days: Prediccion[]; selected: number; onSelect: (i: number) => void }

export function WeekChart({ days, selected, onSelect }: Props) {
  const n = days.length
  const xs = days.map((_, i) => ((i + 0.5) / n) * 1000)
  const pts = days.map((d, i) => `${xs[i]},${y(d.prob_abierto)}`)
  const area = `M${xs[0]},${H} L${pts.join(' L')} L${xs[n - 1]},${H} Z`

  return (
    <div>
      {/* Curva de probabilidad de abierto */}
      <div className="relative" style={{ height: H }}>
        <svg viewBox={`0 0 1000 ${H}`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden>
          <defs>
            <linearGradient id="area" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#34d399" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#34d399" stopOpacity="0" />
            </linearGradient>
          </defs>
          <line x1="0" x2="1000" y1={y(0.5)} y2={y(0.5)} stroke="white" strokeOpacity="0.18" strokeDasharray="6 6" vectorEffect="non-scaling-stroke" />
          <path d={area} fill="url(#area)" />
          <polyline points={pts.join(' ')} fill="none" stroke="#34d399" strokeWidth="2.5" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
        </svg>
        <span className="absolute right-0 text-[10px] text-white/40" style={{ top: y(0.5) - 14 }}>50%</span>
        {days.map((d, i) => {
          const t = TONE[tone(d.prob_abierto)]
          return (
            <span
              key={d.fecha}
              className={`absolute size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-4 ring-slate-950 transition-transform ${t.bg} ${i === selected ? 'scale-150' : ''}`}
              style={{ left: `${((i + 0.5) / n) * 100}%`, top: y(d.prob_abierto) }}
            />
          )
        })}
      </div>

      {/* Columnas por día */}
      <div className="mt-3 grid gap-1.5" style={{ gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }}>
        {days.map((d, i) => {
          const t = TONE[tone(d.prob_abierto)]
          const active = i === selected
          return (
            <button
              key={d.fecha}
              onClick={() => onSelect(i)}
              className={`group flex flex-col items-center gap-1.5 rounded-2xl px-1 py-3 text-center transition ${
                active ? `bg-white/10 ring-1 ${t.ring}` : 'hover:bg-white/5'
              }`}
            >
              <span className="text-xs font-medium capitalize text-white/80">{dayLabel(d.fecha, d.dias_adelante)}</span>
              <span className="text-[10px] text-white/40">{fmt(d.fecha, 'd MMM')}</span>
              <WeatherIcon c={d.clima} className="my-1 size-6 text-sky-200" />
              <span className={`text-lg font-semibold tabular-nums ${t.text}`}>{pct(d.prob_abierto)}%</span>
              {d.clima && (
                <>
                  <span className="text-[11px] tabular-nums text-white/70">
                    {num(d.clima.temp_max, '°')} <span className="text-white/35">{num(d.clima.temp_min, '°')}</span>
                  </span>
                  <span className={`flex items-center gap-0.5 text-[11px] tabular-nums ${(d.clima.nieve_cm ?? 0) >= 1 ? 'text-sky-300' : 'text-white/30'}`}>
                    <Snowflake className="size-3" />
                    {num(d.clima.nieve_cm)}
                  </span>
                  <span className="hidden items-center gap-0.5 text-[11px] tabular-nums text-white/40 sm:flex">
                    <Wind className="size-3" />
                    {num(d.clima.viento_kmh)}
                  </span>
                </>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
