import { useEffect, useState } from 'react'
import { fetchSnowMap, fetchYear, type Anio, type Dia } from './api'
import { SnowMap, type SnowGrid } from './SnowMap'

const COLS = 31 // los días van seguidos, sin cortar por mes
const CARD_H = 420 // alto aproximado de la tarjeta con mapa, para decidir si abre arriba o abajo

// "2026-10-05" → "Lunes 05/10/2026" (se arma a mano para no depender de la zona horaria)
function tooltip(iso: string) {
  const [y, m, d] = iso.split('-')
  const dia = new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString('es-AR', { weekday: 'long' })
  return `${dia[0].toUpperCase()}${dia.slice(1)} ${d}/${m}/${y}`
}

// Segunda línea del tooltip: en los días predichos, % de abierto y de cerrado; en pasado y hoy, el dato real.
function status(d: Dia) {
  if (d.cerrado === null) return 'Sin pronóstico'
  if (d.prob_cerrado === null) return d.cerrado ? 'Cerrado' : 'Abierto'
  const cerrado = Math.round(d.prob_cerrado * 100)
  return `Abierto ${100 - cerrado}% · Cerrado ${cerrado}%` // 100 - x para que siempre sumen 100
}

// Días predichos: el cuadrado se llena de rojo desde abajo según P(cerrado) y el resto queda verde.
// (Las variables las define Tailwind porque bg-red-500/bg-green-500 se usan abajo.)
const fill = (prob: number) => {
  const p = Math.round(prob * 100)
  return { background: `linear-gradient(to top, var(--color-red-500) ${p}%, var(--color-green-500) ${p}%)` }
}

// Pasado (real) en tono claro; hoy (estado oficial) en tono pleno; más adelante, gris.
function color(cerrado: boolean | null, pasado: boolean) {
  if (cerrado === null) return 'bg-neutral-200'
  if (pasado) return cerrado ? 'bg-red-200' : 'bg-green-200'
  return cerrado ? 'bg-red-500' : 'bg-green-500'
}

export default function App() {
  const [data, setData] = useState<Anio | null>(null)
  const [snow, setSnow] = useState<SnowGrid | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hover, setHover] = useState<{ fecha: string; below: boolean } | null>(null)

  useEffect(() => {
    fetchYear().then(setData).catch(e => setError(String(e.message ?? e)))
    fetchSnowMap().then(setSnow).catch(() => {}) // el mapa es un extra: si falla, queda el tooltip simple
  }, [])

  return (
    <main className="flex min-h-svh items-center justify-center px-3 py-10 sm:px-4">
      {error && <p className="text-red-600">No se pudo cargar: {error}</p>}
      {!data && !error && (
        <div role="status" aria-label="Cargando" className="size-8 animate-spin rounded-full border-4 border-neutral-200 border-t-neutral-500" />
      )}

      {data && (
        <div className="grid w-full max-w-6xl grid-cols-31 gap-[2px] sm:gap-1">
          {data.dias.map((d, i) => {
            const col = i % COLS
            // cerca de los bordes, el tooltip se alinea hacia adentro para no salirse de la pantalla
            const align = col < 6 ? 'left-0' : col >= COLS - 6 ? 'right-0' : 'left-1/2 -translate-x-1/2'
            const withMap = !!snow?.dias[d.fecha] && d.cerrado !== null && d.fecha >= data.hoy
            const open = withMap && hover?.fecha === d.fecha
            return (
              <span
                key={d.fecha}
                aria-label={`${tooltip(d.fecha)}: ${status(d)}`}
                onMouseEnter={e => withMap && setHover({ fecha: d.fecha, below: e.currentTarget.getBoundingClientRect().top < CARD_H })}
                onMouseLeave={() => withMap && setHover(null)}
                style={d.prob_cerrado === null ? undefined : fill(d.prob_cerrado)}
                className={`group relative aspect-square rounded-[2px] transition-transform sm:rounded-sm ${
                  d.prob_cerrado === null ? color(d.cerrado, d.fecha < data.hoy) : ''
                } ${
                  open ? 'z-20 scale-150' : '' // mismo estado que la tarjeta: si no, su compensación de escala puede quedar desfasada
                }`}
              >
                {withMap ? (
                  open && (
                    <span
                      className={`pointer-events-none absolute z-30 rounded-lg bg-neutral-900 p-2.5 text-xs text-white shadow-xl ${align} ${
                        hover.below ? 'top-full mt-2' : 'bottom-full mb-2'
                      }`}
                      style={{ scale: '0.667' /* compensa el scale-150 del cuadrado */, transformOrigin: hover.below ? 'top' : 'bottom' }}
                    >
                      <span className="block whitespace-nowrap">{tooltip(d.fecha)}</span>
                      <span className="mb-2 block text-neutral-300">{status(d)}</span>
                      <SnowMap grid={snow!} fecha={d.fecha} />
                    </span>
                  )
                ) : (
                  <span
                    className={`pointer-events-none absolute bottom-full z-10 mb-1.5 whitespace-nowrap rounded-md bg-neutral-900 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100 ${align}`}
                  >
                    {tooltip(d.fecha)}
                    <span className="block text-neutral-300">{status(d)}</span>
                  </span>
                )}
              </span>
            )
          })}
        </div>
      )}
    </main>
  )
}
