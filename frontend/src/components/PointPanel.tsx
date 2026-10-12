import type { PuntoClima } from '../api'
import { round, sky, weekday } from '../format'

export function PointPanel({ p }: { p: PuntoClima }) {
  const maxSnow = Math.max(5, ...p.dias.map(d => d.nieve_cm ?? 0))
  return (
    <aside className="point">
      <div className="eyebrow">{p.altura.toLocaleString('es-AR')} m</div>
      <h3>{p.nombre}</h3>
      <div className="point-now">
        <span className="big">{round(p.actual.temp)}°</span>
        <span>
          {p.actual.nevando ? 'Nevando' : sky(p.actual.codigo)}
          <br />
          <span className="muted">ráfagas {round(p.actual.rafagas)} km/h</span>
        </span>
      </div>
      <div className="snow-chart" aria-label="Nieve prevista por día">
        {p.dias.map(d => (
          <div key={d.fecha} className="snow-col" title={`${d.fecha}: ${d.nieve_cm} cm de nieve, ${round(d.temp_min)}° / ${round(d.temp_max)}°, ráfagas ${round(d.rafagas)} km/h`}>
            <span className="snow-val">{d.nieve_cm >= 0.5 ? round(d.nieve_cm) : ''}</span>
            <span className="snow-bar" style={{ height: `${(Math.max(d.nieve_cm ?? 0, 0) / maxSnow) * 100}%` }} />
            <span className="snow-day">{weekday(d.fecha)}</span>
          </div>
        ))}
      </div>
      <div className="muted small">Nieve prevista (cm) · tocá otro punto del mapa</div>
    </aside>
  )
}
