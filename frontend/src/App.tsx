import { useEffect, useState } from 'react'
import { fetchYear, type Anio } from './api'

const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

// "2026-10-05" → "Lunes 05/10/2026" (se arma a mano para no depender de la zona horaria)
function tooltip(iso: string) {
  const [y, m, d] = iso.split('-')
  const dia = new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString('es-AR', { weekday: 'long' })
  return `${dia[0].toUpperCase()}${dia.slice(1)} ${d}/${m}/${y}`
}

// Pasado (real) en tono claro; hoy y próximos 7 días (predicción) en tono pleno; más adelante, gris.
function color(cerrado: boolean | null, pasado: boolean) {
  if (cerrado === null) return 'bg-neutral-200'
  if (pasado) return cerrado ? 'bg-red-200' : 'bg-green-200'
  return cerrado ? 'bg-red-500' : 'bg-green-500'
}

export default function App() {
  const [data, setData] = useState<Anio | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchYear().then(setData).catch(e => setError(String(e.message ?? e)))
  }, [])

  const byMonth = MESES.map((_, m) => data?.dias.filter(d => Number(d.fecha.slice(5, 7)) === m + 1) ?? [])

  return (
    <main className="flex min-h-svh items-center justify-center px-3 py-10 sm:px-4">
      {error && <p className="text-red-600">No se pudo cargar: {error}</p>}
      {!data && !error && <p className="text-neutral-500">Cargando…</p>}

      {data && (
        <div className="w-full max-w-4xl space-y-1.5">
          {byMonth.map((dias, m) => (
            <div key={m} className="grid grid-cols-[1.75rem_1fr] items-center gap-1.5 sm:grid-cols-[2.5rem_1fr] sm:gap-2">
              <span className="text-xs text-neutral-500">{MESES[m]}</span>
              <div className="grid grid-cols-31 gap-[2px] sm:gap-1">
                {dias.map(d => (
                  <span
                    key={d.fecha}
                    title={tooltip(d.fecha)}
                    className={`aspect-square rounded-[2px] sm:rounded-sm ${color(d.cerrado, d.fecha < data.hoy)} ${
                      d.fecha === data.hoy ? 'ring-2 ring-neutral-900 ring-offset-1' : ''
                    }`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
