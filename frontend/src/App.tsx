import { useEffect, useState } from 'react'

type Status = {
  fetched_at: string
  source_time: string | null
  estado: string | null
  estado_vialidad: string | null
  horario: string | null
  horario_cancilleria: string | null
}

// "Mo-Su 09:00-19:00 open \"Habilitado solo para ...\"" -> texto entre comillas
const note = (s: string | null) => s?.match(/"(.*)"/)?.[1] ?? s

export default function App() {
  const [status, setStatus] = useState<Status | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/status')
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setStatus)
      .catch(e => setError(String(e)))
  }, [])

  const partial = status?.horario_cancilleria?.toLowerCase().includes('solo')

  return (
    <main>
      <h1>Paso Cristo Redentor</h1>
      <div className="card">
        {error && <p>No se pudo cargar el estado: {error}</p>}
        {!status && !error && <p className="muted">Cargando…</p>}
        {status && (
          <>
            <div className="muted">Estado actual</div>
            <div className={`estado ${status.estado ?? ''} ${partial ? 'partial' : ''}`}>
              {status.estado ?? '—'}
            </div>
            <p>{note(status.horario_cancilleria)}</p>
            <p className="muted">{note(status.horario)}</p>
            <p className="muted">
              Vialidad: {status.estado_vialidad ?? '—'} · Fuente: {status.source_time ?? '—'} · Registrado:{' '}
              {new Date(status.fetched_at).toLocaleString()}
            </p>
          </>
        )}
      </div>
    </main>
  )
}
