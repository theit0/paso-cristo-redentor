import { useEffect, useState } from 'react'
import { fetchYear, type Anio } from './api'

const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

// "2026-10-05" → "Lunes 05/10/2026" (se arma a mano para no depender de la zona horaria)
function tooltip(iso: string) {
  const [y, m, d] = iso.split('-')
  const dia = new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString('es-AR', { weekday: 'long' })
  return `${dia[0].toUpperCase()}${dia.slice(1)} ${d}/${m}/${y}`
}

// Pasado (real) en tono claro; hoy y futuro (predicción) en tono pleno.
function color(cerrado: boolean, pasado: boolean) {
  if (pasado) return cerrado ? 'bg-red-200' : 'bg-green-200'
  return cerrado ? 'bg-red-500' : 'bg-green-500'
}

export default function App() {
  const [data, setData] = useState<Anio | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchYear().then(setData).catch(e => setError(String(e.message ?? e)))
  }, [])

  const year = data?.hoy.slice(0, 4)
  const byMonth = MESES.map((_, m) => data?.dias.filter(d => Number(d.fecha.slice(5, 7)) === m + 1) ?? [])

  return (
    <main className="mx-auto max-w-4xl px-3 py-10 sm:px-4">
      <h1 className="text-2xl font-semibold text-neutral-900">Paso Cristo Redentor {year}</h1>

      {error && <p className="mt-6 text-red-600">No se pudo cargar: {error}</p>}
      {!data && !error && <p className="mt-6 text-neutral-500">Cargando…</p>}

      {data && (
        <>
          <div className="mt-6 space-y-1.5">
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

          <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-xs text-neutral-600">
            <span className="flex items-center gap-1.5"><span className="size-3 rounded-sm bg-green-500" />Abierto</span>
            <span className="flex items-center gap-1.5"><span className="size-3 rounded-sm bg-red-500" />Cerrado</span>
            <span className="flex items-center gap-1.5"><span className="size-3 rounded-sm bg-green-200" /><span className="size-3 rounded-sm bg-red-200" />Días pasados</span>
          </div>
        </>
      )}
    </main>
  )
}
