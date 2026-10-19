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

// Segunda línea del tooltip: en los días predichos, % de abierto y de cerrado; en pasado y hoy, el dato real
// y, si se había guardado, qué se predijo y si acertó.
function status(d: Dia) {
  if (d.cerrado === null) return 'Sin pronóstico'
  if (d.prob_cerrado === null) {
    const real = d.cerrado ? 'Cerrado' : 'Abierto'
    if (d.predicho === null) return real
    // se nombra lo que se predijo (con su %) para que se lea directo contra lo real
    const p = Math.round(d.predicho * 100)
    const predicho = d.predicho > 0.5 ? `cerrado (${p}%)` : `abierto (${100 - p}%)` // mismo umbral que el backend
    return `${real} · se predijo ${predicho}: ${d.acerto ? 'acertó' : 'falló'}`
  }
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

const NAV = 'rounded p-0.5 hover:bg-neutral-100 hover:text-neutral-700 disabled:pointer-events-none disabled:opacity-30'
// mientras carga el año pedido, el chevron que se tocó gira (mismo spinner que la carga inicial, en chico)
const Chevron = ({ d, loading }: { d: string; loading: boolean }) =>
  loading ? (
    <span role="status" aria-label="Cargando" className="block size-4 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-500" />
  ) : (
    <svg viewBox="0 0 16 16" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  )

export default function App() {
  const [data, setData] = useState<Anio | null>(null)
  const [snow, setSnow] = useState<SnowGrid | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hover, setHover] = useState<{ fecha: string; below: boolean } | null>(null)
  const [anio, setAnio] = useState<number>() // undefined: el año en curso
  const loading = !!data && anio !== undefined && anio !== data.anio

  useEffect(() => {
    fetchYear(anio).then(setData).catch(e => setError(String(e.message ?? e)))
  }, [anio])
  useEffect(() => {
    fetchSnowMap().then(setSnow).catch(() => {}) // el mapa es un extra: si falla, queda el tooltip simple
  }, [])

  return (
    <main className="flex min-h-svh items-center justify-center px-3 py-10 sm:px-4">
      {error && <p className="text-red-600">No se pudo cargar: {error}</p>}
      {!data && !error && (
        <div role="status" aria-label="Cargando" className="size-8 animate-spin rounded-full border-4 border-neutral-200 border-t-neutral-500" />
      )}

      {data && (
        <div className="w-full max-w-6xl">
          <div className="mb-2 flex items-center justify-between text-xs text-neutral-400">
            <span className="flex items-center gap-1">
              <button aria-label="Año anterior" disabled={data.anio <= data.primer_anio} onClick={() => !loading && setAnio(data.anio - 1)} className={NAV}>
                <Chevron d="M10 4 6 8l4 4" loading={loading && anio! < data.anio} />
              </button>
              <span className="tabular-nums">{data.anio}</span>
              <button aria-label="Año siguiente" disabled={data.anio >= Number(data.hoy.slice(0, 4))} onClick={() => !loading && setAnio(data.anio + 1)} className={NAV}>
                <Chevron d="m6 4 4 4-4 4" loading={loading && anio! > data.anio} />
              </button>
            </span>
            {data.aciertos.total > 0 && (
              <span title={`${data.aciertos.acertados} de ${data.aciertos.total} días`}>
                {Math.round((data.aciertos.acertados / data.aciertos.total) * 100)}% de aciertos
              </span>
            )}
          </div>
          <div className="grid grid-cols-31 gap-[2px] sm:gap-1">
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
                  {/* solo los errores llevan marca: la esquina con el color que se había predicho (el contrario al real) */}
                  {d.acerto === false && (
                    <span
                      aria-hidden
                      className={`absolute right-0 bottom-0 size-1/2 rounded-br-[2px] [clip-path:polygon(100%_0,100%_100%,0_100%)] sm:rounded-br-sm ${
                        d.cerrado ? 'bg-green-500' : 'bg-red-500'
                      }`}
                    />
                  )}
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
        </div>
      )}
    </main>
  )
}
