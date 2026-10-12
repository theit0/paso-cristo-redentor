import type { Prediccion } from '../api'
import { dayMonth, pct, round, weekday } from '../format'

const LABEL = { abierto: 'Abierto', cerrado: 'Cerrado', incierto: 'Incierto' }

function DayCard({ p }: { p: Prediccion }) {
  const title = p.dias_adelante === 0 ? 'Hoy' : p.dias_adelante === 1 ? 'Mañana' : weekday(p.fecha)
  return (
    <article className={`day ${p.veredicto}`} title={`Confianza ${p.confianza}`}>
      <div className="day-fill" style={{ height: pct(p.prob_abierto) }} />
      <div className="day-body">
        <div className="day-head">
          <span className="day-name">{title}</span>
          <span className="day-date">{dayMonth(p.fecha)}</span>
        </div>
        <div className="day-pct">{pct(p.prob_abierto)}</div>
        <div className="day-sub">chance de abierto</div>
        <div className="day-foot">
          <span className={`chip ${p.veredicto}`}>{LABEL[p.veredicto]}</span>
          {p.nieve_pronosticada_cm !== null && p.nieve_pronosticada_cm >= 0.5 && (
            <span className="day-snow">❄ {round(p.nieve_pronosticada_cm)} cm</span>
          )}
        </div>
      </div>
    </article>
  )
}

export function DayStrip({ days }: { days: Prediccion[] }) {
  return (
    <div className="days">
      {days.map(p => <DayCard key={p.fecha} p={p} />)}
    </div>
  )
}
