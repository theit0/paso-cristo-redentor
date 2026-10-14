import { useEffect, useState } from 'react'
import { fetchSnowMap, fetchYear, type Anio, type Dia } from './api'
import { SnowMap, type SnowGrid } from './SnowMap'

const COLS = 31 // los días van seguidos, sin cortar por mes
const TILE_H = 400 // alto aproximado del cuadrado agrandado, para decidir si crece hacia arriba o hacia abajo

// "2026-10-05" → "Lunes 05/10/2026" (se arma a mano para no depender de la zona horaria)
function tooltip(iso: string) {
  const [y, m, d] = iso.split('-')
  const dia = new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString('es-AR', { weekday: 'long' })
  return `${dia[0].toUpperCase()}${dia.slice(1)} ${d}/${m}/${y}`
}

// Segunda línea del tooltip: el resultado que muestra el cuadrado, con su % en los días predichos.
function status(d: Dia) {
  if (d.cerrado === null) return 'Sin pronóstico'
  const label = d.cerrado ? 'Cerrado' : 'Abierto'
  if (d.prob_cerrado === null) return label // pasado y hoy: dato real
  return `${label} ${pct(d)}%`
}

// % del resultado que muestra el cuadrado (cerrado si es rojo, abierto si es verde)
function pct(d: Dia) {
  return Math.round((d.cerrado ? d.prob_cerrado! : 1 - d.prob_cerrado!) * 100)
}

// Pasado (real) en tono claro; hoy y próximos 7 días (predicción) en tono pleno; más adelante, gris.
function color(cerrado: boolean | null, pasado: boolean) {
  if (cerrado === null) return 'bg-neutral-200'
  if (pasado) return cerrado ? 'bg-red-200' : 'bg-green-200'
  return cerrado ? 'bg-red-500' : 'bg-green-500'
}

export default function App() {
  const [data, setData] = useState<Anio | null>(null)
  const [snow, setSnow] = useState<SnowGrid | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hover, setHover] = useState<{ fecha: string; down: boolean } | null>(null)

  useEffect(() => {
    fetchYear().then(setData).catch(e => setError(String(e.message ?? e)))
    fetchSnowMap().then(setSnow).catch(() => {}) // el mapa es un extra: si falla, queda el tooltip simple
  }, [])

  return (
    <main className="flex min-h-svh items-center justify-center px-3 py-10 sm:px-4">
      {error && <p className="text-red-600">No se pudo cargar: {error}</p>}
      {!data && !error && <p className="text-neutral-500">Cargando…</p>}

      {data && (
        <div className="grid w-full max-w-4xl grid-cols-31 gap-[2px] sm:gap-1">
          {data.dias.map((d, i) => {
            const col = i % COLS
            // cerca de los bordes, el tooltip se alinea hacia adentro para no salirse de la pantalla
            const align = col < 6 ? 'left-0' : col >= COLS - 6 ? 'right-0' : 'left-1/2 -translate-x-1/2'
            const withMap = !!snow?.dias[d.fecha] && d.cerrado !== null && d.fecha >= data.hoy
            const open = withMap && hover?.fecha === d.fecha
            // el cuadrado crece desde su esquina hacia donde haya lugar
            const right = col < COLS / 2
            const corner = `${hover?.down ? 'top-0' : 'bottom-0'} ${right ? 'left-0' : 'right-0'}`
            const origin = `${hover?.down ? 'top' : 'bottom'} ${right ? 'left' : 'right'}`
            return (
              <span
                key={d.fecha}
                aria-label={`${tooltip(d.fecha)}: ${status(d)}`}
                onMouseEnter={e => withMap && setHover({ fecha: d.fecha, down: e.currentTarget.getBoundingClientRect().bottom < TILE_H })}
                onMouseLeave={() => withMap && setHover(null)}
                className={`group relative flex aspect-square items-center justify-center rounded-[2px] sm:rounded-sm ${color(d.cerrado, d.fecha < data.hoy)} ${
                  open ? 'z-30' : ''
                }`}
              >
                {/* % del resultado, siempre visible en los días predichos (no entra en pantallas chicas) */}
                {d.prob_cerrado !== null && (
                  <span className="hidden text-[10px] font-semibold leading-none text-white tabular-nums sm:block">{pct(d)}%</span>
                )}
                {withMap ? (
                  open && (
                    // el mismo cuadrado, agrandado: mismo color, fecha y % arriba, mapa adentro
                    <span
                      className={`grow-tile absolute flex flex-col gap-1.5 rounded-md p-1.5 text-xs text-white shadow-2xl ${corner} ${color(d.cerrado, false)}`}
                      style={{ transformOrigin: origin }}
                    >
                      <span className="flex justify-between gap-3 px-0.5 font-semibold whitespace-nowrap">
                        <span>{tooltip(d.fecha)}</span>
                        <span>{status(d)}</span>
                      </span>
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
