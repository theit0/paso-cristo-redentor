import { useEffect, useState } from 'react'
import { fetchYear, type DiaHistorial } from '../api'
import { asDate, dayMonth } from '../format'

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
const STATE_LABEL = { abierto: 'abierto', solo_cargas: 'solo camiones', total: 'cerrado' }

function stats(days: DiaHistorial[]) {
  let closed = 0, events = 0, run = 0, longest = 0
  days.forEach((d, i) => {
    const c = d.estado !== 'abierto'
    if (c) {
      closed++
      run++
      if (i === 0 || days[i - 1].estado === 'abierto') events++
      longest = Math.max(longest, run)
    } else run = 0
  })
  return { closed, events, longest }
}

function Month({ year, month, byDate }: { year: number; month: number; byDate: Map<string, DiaHistorial['estado']> }) {
  const first = new Date(year, month, 1)
  const n = new Date(year, month + 1, 0).getDate()
  const offset = (first.getDay() + 6) % 7 // semana empieza el lunes
  const cells = Array.from({ length: n }, (_, i) => {
    const iso = `${year}-${String(month + 1).padStart(2, '0')}-${String(i + 1).padStart(2, '0')}`
    return { iso, estado: byDate.get(iso) }
  })
  return (
    <div className="month">
      <div className="month-name">{MONTHS[month]}</div>
      <div className="month-grid">
        {Array.from({ length: offset }, (_, i) => <span key={`o${i}`} />)}
        {cells.map(c => (
          <span
            key={c.iso}
            className={`cell ${c.estado ?? 'sin-dato'}`}
            title={c.estado ? `${dayMonth(c.iso)}: ${STATE_LABEL[c.estado]}` : dayMonth(c.iso)}
          />
        ))}
      </div>
    </div>
  )
}

export function YearCalendar({ today }: { today: string }) {
  const lastYear = asDate(today).getFullYear()
  const years = Array.from({ length: lastYear - 2021 }, (_, i) => 2022 + i)
  const [year, setYear] = useState(lastYear)
  const [cache, setCache] = useState<Record<number, DiaHistorial[]>>({})
  const [error, setError] = useState<string | null>(null)
  const days = cache[year]

  useEffect(() => {
    if (cache[year]) return
    fetchYear(year)
      .then(d => setCache(c => ({ ...c, [year]: d })))
      .catch(e => setError(String(e.message ?? e)))
  }, [year, cache])

  const byDate = new Map(days?.map(d => [d.fecha, d.estado]))
  const s = days && stats(days)

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>El paso, día por día</h2>
        <div className="years" role="tablist">
          {years.map(y => (
            <button key={y} role="tab" aria-selected={y === year} className={y === year ? 'on' : ''} onClick={() => setYear(y)}>
              {y}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="error">No se pudo cargar el historial: {error}</p>}
      {s && (
        <div className="stats">
          <div><b>{s.closed}</b><span>días cerrado</span></div>
          <div><b>{s.events}</b><span>cierres</span></div>
          <div><b>{s.longest}</b><span>días del cierre más largo</span></div>
        </div>
      )}
      <div className="months">
        {Array.from({ length: 12 }, (_, m) => <Month key={m} year={year} month={m} byDate={byDate} />)}
      </div>
      <div className="legend muted small">
        <span className="cell abierto" /> abierto <span className="cell solo_cargas" /> solo camiones
        <span className="cell total" /> cerrado <span className="cell sin-dato" /> sin dato
      </div>
    </section>
  )
}
