import { useEffect, useState } from 'react'
import { fetchYear, type Anio, type Dia } from './api'

// "2026-10-05" → "Lunes 05/10/2026" (se arma a mano para no depender de la zona horaria)
function tooltip(iso: string) {
  const [y, m, d] = iso.split('-')
  const dia = new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString('es-AR', { weekday: 'long' })
  return `${dia[0].toUpperCase()}${dia.slice(1)} ${d}/${m}/${y}`
}

// Segunda línea del tooltip: porcentajes en los días predichos, el estado real en pasado/hoy.
function status(d: Dia) {
  if (d.cerrado === null) return 'Sin pronóstico'
  if (d.prob_cerrado === null) return d.cerrado ? 'Cerrado' : 'Abierto'
  const abierto = Math.round((1 - d.prob_cerrado) * 100)
  return `Abierto ${abierto}% · Cerrado ${100 - abierto}%` // complementarios: siempre suman 100
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

  // Una fila por mes, un cuadrado por día.
  const months = Array.from({ length: 12 }, (_, m) => data?.dias.filter(d => Number(d.fecha.slice(5, 7)) === m + 1) ?? [])

  return (
    <main className="flex min-h-svh items-center justify-center px-3 py-10 sm:px-4">
      {error && <p className="text-red-600">No se pudo cargar: {error}</p>}
      {!data && !error && <p className="text-neutral-500">Cargando…</p>}

      {data && (
        <div className="w-full max-w-4xl space-y-1.5">
          {months.map((dias, m) => (
            <div key={m} className="grid grid-cols-31 gap-[2px] sm:gap-1">
              {dias.map(d => {
                const day = Number(d.fecha.slice(8, 10))
                // cerca de los bordes, el tooltip se alinea hacia adentro para no salirse de la pantalla
                const align = day <= 4 ? 'left-0' : day >= 28 ? 'right-0' : 'left-1/2 -translate-x-1/2'
                return (
                  <span
                    key={d.fecha}
                    aria-label={`${tooltip(d.fecha)}: ${status(d)}`}
                    className={`group relative aspect-square rounded-[2px] sm:rounded-sm ${color(d.cerrado, d.fecha < data.hoy)}`}
                  >
                    <span
                      className={`pointer-events-none absolute bottom-full z-10 mb-1.5 whitespace-nowrap rounded-md bg-neutral-900 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100 ${align}`}
                    >
                      {tooltip(d.fecha)}
                      <span className="block text-neutral-300">{status(d)}</span>
                    </span>
                  </span>
                )
              })}
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
