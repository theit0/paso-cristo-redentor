import { useCallback, useEffect, useState } from 'react'
import { fetchPredict, fetchWeather, type Prediccion, type PredictResponse, type PuntoClima } from './api'
import { DayStrip } from './components/DayStrip'
import { PointPanel } from './components/PointPanel'
import { WeatherMap } from './components/WeatherMap'
import { YearCalendar } from './components/YearCalendar'
import { asDate, pct } from './format'

// "Mo-Su 09:00-19:00 open \"Habilitado solo para ...\"" -> texto entre comillas
const note = (s: string | null) => s?.match(/"(.*)"/)?.[1] ?? s

function DateQuery({ today }: { today: string }) {
  const [result, setResult] = useState<Prediccion | null>(null)
  const [error, setError] = useState<string | null>(null)
  const max = new Date(asDate(today).getTime() + 365 * 864e5).toISOString().slice(0, 10)

  const choose = (value: string) => {
    setResult(null)
    setError(null)
    if (!value) return
    fetchPredict(value)
      .then(r => setResult(cur => (r.predicciones[0].fecha === value ? r.predicciones[0] : cur)))
      .catch(e => setError(String(e.message ?? e)))
  }

  return (
    <div className="query">
      <label>
        ¿Otra fecha? <input type="date" min={today} max={max} onChange={e => choose(e.target.value)} />
      </label>
      {error && <span className="error">{error}</span>}
      {result && (
        <span>
          <b className={`t-${result.veredicto}`}>{pct(result.prob_abierto)} abierto</b>{' '}
          <span className="muted">
            {result.fuente === 'climatologia' ? '· promedio de otros años (sin pronóstico a esa distancia)' : `· confianza ${result.confianza}`}
          </span>
        </span>
      )}
    </div>
  )
}

export default function App() {
  const [data, setData] = useState<PredictResponse | null>(null)
  const [weather, setWeather] = useState<PuntoClima[]>([])
  const [selected, setSelected] = useState('las_cuevas')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPredict().then(setData).catch(e => setError(String(e.message ?? e)))
    fetchWeather().then(setWeather).catch(() => {}) // el mapa es secundario: si falla, no se muestra
  }, [])

  const onSelect = useCallback((id: string) => setSelected(id), [])
  const estado = data?.estado_actual
  const abierto = estado?.estado === 'ABIERTO'
  const point = weather.find(p => p.id === selected)

  return (
    <>
      <header className={`top ${estado ? (abierto ? 'is-open' : 'is-closed') : ''}`}>
        <div className="wrap top-inner">
          <div>
            <div className="eyebrow">Paso internacional · Mendoza ↔ Los Andes</div>
            <h1>Cristo Redentor</h1>
          </div>
          {estado && (
            <div className="sign">
              <div className="sign-state">{abierto ? 'Abierto' : 'Cerrado'}</div>
              <div className="sign-note">{note(estado.horario_cancilleria) ?? note(estado.horario)}</div>
              <div className="sign-src">Fuente oficial · {estado.source_time?.slice(11, 16) ?? '—'} h</div>
            </div>
          )}
        </div>
      </header>

      <main className="wrap">
        {error && <p className="panel error">No se pudo cargar la predicción: {error}</p>}
        {!data && !error && <p className="panel muted">Cargando…</p>}

        {data && (
          <section className="panel">
            <div className="panel-head">
              <h2>Próximos días</h2>
              <DateQuery today={data.hoy} />
            </div>
            <DayStrip days={data.predicciones} />
            <p className="muted small">
              La barra de cada día se llena con la chance de que esté abierto. "Incierto" = entre 35% y 65%.
              En inviernos anteriores acertó {pct(data.predicciones[1]?.aciertos_historicos_invierno ?? 0)} a 1 día
              y {pct(data.predicciones[7]?.aciertos_historicos_invierno ?? 0)} a 7.
            </p>
          </section>
        )}

        {weather.length > 0 && (
          <section className="panel map-panel">
            <div className="panel-head">
              <h2>Clima en la ruta</h2>
              <span className="muted small">Círculo más grande y más azul = más nieve en las próximas 72 h</span>
            </div>
            <div className="map-layout">
              <WeatherMap points={weather} selected={selected} onSelect={onSelect} />
              {point && <PointPanel p={point} />}
            </div>
          </section>
        )}

        {data && <YearCalendar today={data.hoy} />}

        <footer className="muted small">
          Estimación, no información oficial. Antes de viajar consultá{' '}
          <a href="https://www.argentina.gob.ar/seguridad/pasosinternacionales" target="_blank" rel="noreferrer">pasos internacionales</a>
          {' '}y <a href="https://www.pasosfronterizos.gov.cl/" target="_blank" rel="noreferrer">Pasos Fronterizos Chile</a>.
          Clima: <a href="https://open-meteo.com" target="_blank" rel="noreferrer">Open-Meteo</a>.
          {data && ` Modelo del ${data.modelo}.`}
        </footer>
      </main>
    </>
  )
}
