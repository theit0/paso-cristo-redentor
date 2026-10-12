import { useEffect, useState } from 'react'
import { fetchHistory, fetchPredict, type DiaHistorial, type Prediccion, type PredictResponse } from './api'

// "Mo-Su 09:00-19:00 open \"Habilitado solo para ...\"" -> texto entre comillas
const note = (s: string | null) => s?.match(/"(.*)"/)?.[1] ?? s

// Las fechas vienen como AAAA-MM-DD (día de Mendoza); parsear al mediodía evita corrimientos por zona horaria.
const asDate = (iso: string) => new Date(`${iso}T12:00:00`)
const dayName = (iso: string, h: number) =>
  h === 0 ? 'Hoy' : h === 1 ? 'Mañana' : asDate(iso).toLocaleDateString('es-AR', { weekday: 'long' })
const shortDate = (iso: string) => asDate(iso).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
const pct = (p: number) => `${Math.round(p * 100)}%`

const VERDICT_TEXT = { abierto: 'Abierto', cerrado: 'Cerrado', incierto: 'Incierto' }
const SOURCE_TEXT = {
  estado_oficial: 'Estado oficial',
  modelo: 'Modelo + pronóstico',
  climatologia: 'Promedio histórico',
}

function DayCard({ p }: { p: Prediccion }) {
  return (
    <article className={`day ${p.veredicto}`}>
      <header>
        <span className="day-name">{dayName(p.fecha, p.dias_adelante)}</span>
        <span className="muted">{shortDate(p.fecha)}</span>
      </header>
      <div className="verdict">{VERDICT_TEXT[p.veredicto]}</div>
      <div className="bar" role="img" aria-label={`Probabilidad de abierto ${pct(p.prob_abierto)}`}>
        <span style={{ width: pct(p.prob_abierto) }} />
      </div>
      <div className="muted small">{pct(p.prob_abierto)} abierto</div>
      {p.nieve_pronosticada_cm !== null && (
        <div className="small">❄ {p.nieve_pronosticada_cm} cm previstos</div>
      )}
      <div className="muted small">Confianza {p.confianza}</div>
    </article>
  )
}

function History({ days }: { days: DiaHistorial[] }) {
  const closed = days.filter(d => d.estado !== 'abierto').length
  return (
    <section className="card">
      <h2>Últimos {days.length} días</h2>
      <div className="strip">
        {days.map(d => (
          <span key={d.fecha} className={`cell ${d.estado}`} title={`${shortDate(d.fecha)}: ${d.estado.replace('_', ' ')}`} />
        ))}
      </div>
      <p className="muted small">
        Cerrado {closed} de {days.length} días ·{' '}
        <span className="legend abierto" /> abierto <span className="legend solo_cargas" /> solo camiones{' '}
        <span className="legend total" /> cerrado
      </p>
    </section>
  )
}

function DateQuery({ today }: { today: string }) {
  const [date, setDate] = useState('')
  const [result, setResult] = useState<Prediccion | null>(null)
  const [error, setError] = useState<string | null>(null)
  const max = new Date(asDate(today).getTime() + 365 * 864e5).toISOString().slice(0, 10)

  const choose = (value: string) => {
    setDate(value)
    setResult(null)
    setError(null)
    if (!value) return
    fetchPredict(value)
      .then(r => setResult(cur => (r.predicciones[0].fecha === value ? r.predicciones[0] : cur)))
      .catch(e => setError(String(e.message ?? e)))
  }

  return (
    <section className="card">
      <h2>¿Viajás otro día?</h2>
      <label className="small">
        Fecha del cruce{' '}
        <input type="date" min={today} max={max} value={date} onChange={e => choose(e.target.value)} />
      </label>
      {error && <p className="error">{error}</p>}
      {result && (
        <p>
          <strong className={`t-${result.veredicto}`}>{VERDICT_TEXT[result.veredicto]}</strong>: {pct(result.prob_abierto)}{' '}
          de probabilidad de que esté abierto el {asDate(result.fecha).toLocaleDateString('es-AR', { dateStyle: 'long' })}.{' '}
          <span className="muted">
            {SOURCE_TEXT[result.fuente]}, confianza {result.confianza}.
            {result.fuente === 'climatologia' && ' A más de 7 días no hay pronóstico confiable: es la tasa de cierre de otros años para esa fecha.'}
          </span>
        </p>
      )}
    </section>
  )
}

export default function App() {
  const [data, setData] = useState<PredictResponse | null>(null)
  const [history, setHistory] = useState<DiaHistorial[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPredict().then(setData).catch(e => setError(String(e.message ?? e)))
    fetchHistory().then(setHistory).catch(() => {}) // el historial es secundario: si falla, no se muestra
  }, [])

  const estado = data?.estado_actual
  const abierto = estado?.estado === 'ABIERTO'

  return (
    <main>
      <h1>Paso Cristo Redentor</h1>
      <p className="muted">¿Va a estar abierto el paso a Chile? Estimación con el estado oficial y el pronóstico del tiempo.</p>

      {error && <p className="card error">No se pudo cargar la predicción: {error}</p>}
      {!data && !error && <p className="card muted">Cargando…</p>}

      {data && estado && (
        <>
          <section className="card now">
            <div className="muted small">Ahora</div>
            <div className={`now-state ${abierto ? 't-abierto' : 't-cerrado'}`}>{abierto ? 'Abierto' : 'Cerrado'}</div>
            {note(estado.horario_cancilleria) && <p>Aviso oficial: {note(estado.horario_cancilleria)}</p>}
            {note(estado.horario) && <p className="muted small">{note(estado.horario)}</p>}
            <p className="muted small">Fuente: Ministerio de Seguridad · actualizado {estado.source_time ?? '—'}</p>
          </section>

          <h2>Próximos días</h2>
          <div className="days">
            {data.predicciones.map(p => <DayCard key={p.fecha} p={p} />)}
          </div>
          <p className="muted small">
            "Incierto" = entre 35% y 65%. En inviernos anteriores el modelo acertó{' '}
            {pct(data.predicciones[1]?.aciertos_historicos_invierno ?? 0)} a 1 día y{' '}
            {pct(data.predicciones[7]?.aciertos_historicos_invierno ?? 0)} a 7 días.
          </p>

          <DateQuery today={data.hoy} />
        </>
      )}

      {history.length > 0 && <History days={history} />}

      <footer className="muted small">
        Es una estimación, no información oficial. Antes de viajar consultá{' '}
        <a href="https://www.argentina.gob.ar/seguridad/pasosinternacionales" target="_blank" rel="noreferrer">pasos internacionales</a>
        {' '}y <a href="https://www.pasosfronterizos.gov.cl/" target="_blank" rel="noreferrer">Pasos Fronterizos Chile</a>.
        {data && ` Modelo del ${data.modelo}.`}
      </footer>
    </main>
  )
}
