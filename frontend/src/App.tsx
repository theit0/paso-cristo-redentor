import { addDays, format, startOfToday } from 'date-fns'
import { es } from 'date-fns/locale'
import { CalendarDays, CalendarSearch, Clock, Mountain, Snowflake, Sun, Thermometer, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'

import { fetchDay, fetchWeek, type Contexto, type Prediccion, type Pronostico } from '@/api'
import { DayDetail } from '@/components/DayDetail'
import { WeekChart } from '@/components/WeekChart'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { fmt, isOpen, num, pct, tone, TONE } from '@/lib/format'

// "Mo-Su 09:00-19:00 open \"Habilitado solo para ...\"" -> texto entre comillas
const note = (s: string | null) => s?.match(/"(.*)"/)?.[1] ?? s

const panel = 'rounded-3xl border border-white/10 bg-white/[0.04] p-5'

const NOW = {
  abierto: { label: 'Abierto', text: 'text-emerald-400', dot: 'bg-emerald-400', glow: 'bg-emerald-500/25' },
  solo_cargas: { label: 'Solo camiones', text: 'text-amber-300', dot: 'bg-amber-300', glow: 'bg-amber-400/25' },
  total: { label: 'Cerrado', text: 'text-rose-400', dot: 'bg-rose-400', glow: 'bg-rose-500/25' },
}

function Hero({ data }: { data: Pronostico }) {
  const e = data.estado_actual
  const s = NOW[e.estado_hoy]
  const parte = e.parte_mendoza
  const fresh = parte?.es_de_hoy && parte.aviso
  const week = data.predicciones.slice(1)
  const openDays = week.filter(d => isOpen(d.prob_abierto)).length
  const best = week.reduce((a, b) => (b.prob_abierto > a.prob_abierto ? b : a))
  return (
    <section className="grid gap-4 md:grid-cols-[1.3fr_1fr]">
      <div className={`${panel} relative overflow-hidden`}>
        <div className={`absolute -right-16 -top-16 size-56 rounded-full blur-3xl ${s.glow}`} />
        <div className="relative flex items-center gap-2 text-xs text-white/60">
          <span className="relative flex size-2.5">
            <span className={`absolute inline-flex size-full animate-ping rounded-full opacity-60 ${s.dot}`} />
            <span className={`relative inline-flex size-2.5 rounded-full ${s.dot}`} />
          </span>
          En vivo · Ministerio de Seguridad {e.source_time?.slice(11, 16) ?? '—'} h
        </div>
        <p className={`relative mt-2 text-6xl font-semibold tracking-tight md:text-7xl ${s.text}`}>{s.label}</p>
        {fresh ? (
          <p className="relative mt-2 text-sm text-white/80">
            {parte.aviso}{' '}
            <a href={parte.link} target="_blank" rel="noreferrer" className="text-white/40 underline-offset-2 hover:underline">
              Parte del Gobierno de Mendoza · {parte.publicado.slice(11, 16)} h
            </a>
          </p>
        ) : (
          <p className="relative mt-2 text-sm text-white/70">
            {note(e.horario_cancilleria) ?? note(e.horario)}{' '}
            <span className="text-white/40">· aviso del Ministerio, puede estar desactualizado</span>
          </p>
        )}
        {!fresh && note(e.horario) && (
          <p className="relative mt-1 flex items-center gap-1.5 text-xs text-white/40">
            <Clock className="size-3.5" />
            {note(e.horario)}
          </p>
        )}
        {parte && Object.keys(parte.temperaturas).length > 0 && (
          <div className="relative mt-4 flex flex-wrap gap-2">
            {Object.entries(parte.temperaturas).map(([place, t]) => (
              <span key={place} className="rounded-full bg-white/5 px-2.5 py-1 text-[11px] text-white/60">
                {place} <b className="tabular-nums text-sky-200">{Math.round(t)}°</b>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className={`${panel} grid grid-cols-2 gap-4`}>
        <div>
          <p className="flex items-center gap-1.5 text-xs text-white/50"><CalendarDays className="size-3.5" />Próximos 7 días</p>
          <p className="mt-1 text-4xl font-semibold tabular-nums">{openDays}<span className="text-lg text-white/40">/7</span></p>
          <p className="text-xs text-white/50">probablemente abierto</p>
        </div>
        <div>
          <p className="flex items-center gap-1.5 text-xs text-white/50"><TrendingUp className="size-3.5" />Mejor día</p>
          <p className="mt-1 text-4xl font-semibold capitalize">{fmt(best.fecha, 'EEE d')}</p>
          <p className={`text-xs ${TONE[tone(best.prob_abierto)].text}`}>{pct(best.prob_abierto)}% abierto</p>
        </div>
        <div className="col-span-2 h-2 overflow-hidden rounded-full bg-white/5">
          <div className="flex h-full">
            {week.map(d => (
              <span key={d.fecha} className={`h-full flex-1 border-r border-slate-950 ${TONE[tone(d.prob_abierto)].bg}`} style={{ opacity: 0.35 + Math.abs(d.prob_abierto - 0.5) * 1.3 }} />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function ContextTiles({ c, open }: { c: Contexto; open: boolean }) {
  const tiles = [
    { icon: Clock, value: `${c.dias_en_estado}${c.dias_en_estado >= 60 ? '+' : ''}`, label: `días ${open ? 'abierto' : 'cerrado'} seguidos` },
    { icon: Snowflake, value: num(c.nieve_7d_cm, ' cm'), label: 'nieve última semana' },
    { icon: Snowflake, value: num(c.nieve_14d_cm, ' cm'), label: 'nieve últimas 2 semanas' },
    { icon: Mountain, value: num(c.nieve_suelo_cm, ' cm'), label: 'nieve en el suelo' },
    { icon: Sun, value: `${c.dias_sin_nevada}${c.dias_sin_nevada >= 60 ? '+' : ''}`, label: 'días sin nevada fuerte' },
    { icon: Thermometer, value: num(c.temp_min_ayer, '°'), label: 'mínima de ayer' },
  ]
  return (
    <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {tiles.map(t => (
        <div key={t.label} className={`${panel} p-4`}>
          <t.icon className="size-4 text-sky-300" />
          <p className="mt-2 text-2xl font-semibold tabular-nums">{t.value}</p>
          <p className="text-[11px] text-white/50">{t.label}</p>
        </div>
      ))}
    </section>
  )
}

function OtherDate() {
  const today = startOfToday()
  const [date, setDate] = useState<Date>()
  const [open, setOpen] = useState(false)
  const [res, setRes] = useState<Prediccion | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const choose = (d: Date | undefined) => {
    setDate(d)
    setOpen(false)
    setRes(null)
    setErr(null)
    if (!d) return
    const iso = format(d, 'yyyy-MM-dd')
    fetchDay(iso).then(p => setRes(cur => (p.fecha === iso ? p : cur))).catch(e => setErr(String(e.message ?? e)))
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button className="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/80 transition hover:bg-white/10">
            <CalendarSearch className="size-4" />
            {date ? format(date, "EEE d 'de' MMM", { locale: es }) : 'Consultar otra fecha'}
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="end">
          <Calendar
            mode="single" locale={es} selected={date} onSelect={choose}
            disabled={{ before: today, after: addDays(today, 365) }} startMonth={today} endMonth={addDays(today, 365)}
          />
        </PopoverContent>
      </Popover>
      {err && <span className="text-sm text-rose-400">{err}</span>}
      {res && (
        <span className="text-sm">
          <b className={TONE[tone(res.prob_abierto)].text}>
            {isOpen(res.prob_abierto) ? 'Abierto' : 'Cerrado'} {isOpen(res.prob_abierto) ? pct(res.prob_abierto) : 100 - pct(res.prob_abierto)}%
          </b>
          <span className="text-white/40"> · {res.fuente === 'climatologia' ? 'promedio de otros años' : `confianza ${res.confianza}`}</span>
        </span>
      )}
    </div>
  )
}

export default function App() {
  const [data, setData] = useState<Pronostico | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState(1)

  useEffect(() => {
    fetchWeek().then(setData).catch(e => setError(String(e.message ?? e)))
  }, [])

  return (
    <div className="min-h-svh bg-slate-950 bg-[radial-gradient(ellipse_at_top,rgba(56,189,248,0.12),transparent_60%)] text-white">
      <div className="mx-auto max-w-6xl space-y-4 px-4 py-6 md:py-10">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-sky-300/80">Mendoza ⇄ Los Andes · 3.200 m</p>
            <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">Paso Cristo Redentor</h1>
          </div>
          <OtherDate />
        </header>

        {error && <p className={`${panel} text-rose-400`}>No se pudo cargar la predicción: {error}</p>}
        {!data && !error && (
          <div className="space-y-4">
            {[0, 1, 2].map(i => <div key={i} className={`${panel} h-40 animate-pulse`} />)}
          </div>
        )}

        {data && (
          <>
            <Hero data={data} />

            <section className={panel}>
              <div className="mb-2 flex items-baseline justify-between">
                <h2 className="text-sm font-medium text-white/80">Probabilidad de que esté abierto · 8 días</h2>
                <span className="hidden text-[11px] text-white/40 sm:inline">Tocá un día para ver el detalle</span>
              </div>
              {/* En pantallas angostas el gráfico se desliza de costado para no apretar las 8 columnas */}
              <div className="-mx-5 overflow-x-auto px-5 pb-1">
                <div className="min-w-[620px]">
                  <WeekChart days={data.predicciones} selected={selected} onSelect={setSelected} />
                </div>
              </div>
            </section>

            <section className={panel}>
              <DayDetail d={data.predicciones[selected]} />
            </section>

            <ContextTiles c={data.contexto} open={data.estado_actual.estado_hoy === 'abierto'} />

            <footer className="pt-4 text-[11px] leading-relaxed text-white/35">
              Estimación, no información oficial. Antes de viajar consultá{' '}
              <a className="underline hover:text-white/60" href="https://www.argentina.gob.ar/seguridad/pasosinternacionales" target="_blank" rel="noreferrer">pasos internacionales</a>{' '}
              y <a className="underline hover:text-white/60" href="https://www.pasosfronterizos.gov.cl/" target="_blank" rel="noreferrer">Pasos Fronterizos Chile</a>.
              Clima: Open-Meteo (modelo JMA). Modelo del {data.modelo}.
            </footer>
          </>
        )}
      </div>
    </div>
  )
}
