import { CloudRain, Snowflake, Thermometer, Wind } from 'lucide-react'
import type { Prediccion } from '@/api'
import { fmt, isClose, isOpen, num, pct, tone, TONE } from '@/lib/format'

function Gauge({ p, color }: { p: number; color: string }) {
  const r = 52
  const c = 2 * Math.PI * r
  return (
    <svg viewBox="0 0 120 120" className="size-36 -rotate-90">
      <circle cx="60" cy="60" r={r} fill="none" stroke="white" strokeOpacity="0.08" strokeWidth="10" />
      <circle
        cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={`${c * p} ${c}`} className="transition-[stroke-dasharray] duration-700"
      />
    </svg>
  )
}

const SOURCE = {
  estado_oficial: 'Estado oficial informado hoy por el Ministerio de Seguridad.',
  modelo: 'Modelo entrenado con 5 inviernos + pronóstico del tiempo.',
  climatologia: 'Promedio de otros años: a más de 7 días no hay pronóstico confiable.',
}

function Stat({ icon: Icon, label, value }: { icon: typeof Wind; label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/5 p-3">
      <div className="flex items-center gap-1.5 text-[11px] text-white/50"><Icon className="size-3.5" />{label}</div>
      <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
    </div>
  )
}

export function DayDetail({ d }: { d: Prediccion }) {
  const t = TONE[tone(d.prob_abierto)]
  const open = isOpen(d.prob_abierto)
  const prob = open ? pct(d.prob_abierto) : 100 - pct(d.prob_abierto)
  const maxW = Math.max(...d.factores.map(f => f.peso), 0.01)

  return (
    <div className="grid gap-6 md:grid-cols-[auto_1fr_1fr]">
      {/* Medidor */}
      <div className="flex flex-col items-center justify-center">
        <div className="relative">
          <Gauge p={d.prob_abierto} color={t.hex} />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-semibold tabular-nums ${t.text}`}>{pct(d.prob_abierto)}%</span>
            <span className="text-[11px] text-white/50">abierto</span>
          </div>
        </div>
      </div>

      {/* Veredicto y factores */}
      <div className="space-y-3">
        <div>
          <p className="text-xs text-white/50 first-letter:uppercase">{fmt(d.fecha, "EEEE d 'de' MMMM")}</p>
          <p className={`text-4xl font-semibold tracking-tight ${t.text}`}>{open ? 'Abierto' : 'Cerrado'}</p>
          <p className="text-sm text-white/60">
            {prob}% de probabilidad{isClose(d.prob_abierto) && ' · resultado ajustado'}
          </p>
        </div>
        {d.factores.length > 0 ? (
          <div className="space-y-2">
            <p className="text-[11px] text-white/45">
              Un día típico arranca en <b className="text-white/70">{pct(d.base_abierto ?? 0)}% abierto</b>; esto es lo que más lo mueve:
            </p>
            {d.factores.map(f => (
              <div key={f.factor} className="grid grid-cols-[1fr_1fr] items-center gap-2 text-xs">
                <span className="text-white/70">{f.factor}</span>
                <div className="relative h-2 rounded-full bg-white/5">
                  <span
                    className={`absolute top-0 h-2 rounded-full ${f.empuja_a === 'cerrado' ? 'left-1/2 bg-rose-400' : 'right-1/2 bg-emerald-400'}`}
                    style={{ width: `${(f.peso / maxW) * 50}%` }}
                  />
                  <span className="absolute left-1/2 top-[-3px] h-[14px] w-px bg-white/30" />
                </div>
              </div>
            ))}
            <div className="grid grid-cols-[1fr_1fr] gap-2 text-[10px] text-white/35">
              <span />
              <span className="flex justify-between"><span>← abre</span><span>cierra →</span></span>
            </div>
          </div>
        ) : (
          <p className="text-sm text-white/50">{SOURCE[d.fuente]}</p>
        )}
      </div>

      {/* Clima y confianza */}
      <div className="space-y-3">
        {d.clima && (
          <div className="grid grid-cols-2 gap-2">
            <Stat icon={Snowflake} label="Nieve" value={`${d.clima.nieve_cm ?? '—'} cm`} />
            <Stat icon={CloudRain} label="Precipitación" value={`${d.clima.precip_mm ?? '—'} mm`} />
            <Stat icon={Thermometer} label="Mín / máx" value={`${num(d.clima.temp_min, '°')} / ${num(d.clima.temp_max, '°')}`} />
            <Stat icon={Wind} label="Viento máx" value={`${num(d.clima.viento_kmh)} km/h`} />
          </div>
        )}
        <div className="flex flex-wrap gap-2 text-[11px]">
          <span className="rounded-full bg-white/5 px-2.5 py-1 text-white/60">Confianza {d.confianza}</span>
          {d.aciertos_historicos_invierno !== null && (
            <span className="rounded-full bg-white/5 px-2.5 py-1 text-white/60">
              Acertó {pct(d.aciertos_historicos_invierno)}% a {d.dias_adelante} {d.dias_adelante === 1 ? 'día' : 'días'}
            </span>
          )}
        </div>
        {d.factores.length > 0 && <p className="text-[11px] text-white/35">{SOURCE[d.fuente]}</p>}
      </div>
    </div>
  )
}
