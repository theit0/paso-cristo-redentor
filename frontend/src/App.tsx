import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { fetchSnowMap, fetchYear, type Anio, type Dia } from './api'
import { SnowLegend, SnowMap, type SnowGrid } from './SnowMap'

const COLS = 31 // los días van seguidos, sin cortar por mes
// Tamaño del cuadrado ampliado, en casilleros (proporción del mapa). En celular los casilleros miden ~8 px:
// ahí el mapa ocupa todo el ancho de la grilla.
const SMALL = typeof window !== 'undefined' && window.innerWidth < 640
const SPAN_C = SMALL ? COLS : 8
const SPAN_R = SMALL ? 42 : 11
const HOVER_DELAY = 120 // ms quieto sobre un cuadrado antes de ampliarlo: evita que la grilla tiemble al pasar el mouse

// "2026-10-05" → "Lunes 05/10/2026" (se arma a mano para no depender de la zona horaria)
function tooltip(iso: string) {
  const [y, m, d] = iso.split('-')
  const dia = new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString('es-AR', { weekday: 'long' })
  return `${dia[0].toUpperCase()}${dia.slice(1)} ${d}/${m}/${y}`
}

// % del resultado que muestra el cuadrado (solo días predichos)
const pct = (d: Dia) => (d.prob_cerrado === null ? null : Math.round((d.cerrado ? d.prob_cerrado : 1 - d.prob_cerrado) * 100))

function status(d: Dia) {
  if (d.cerrado === null) return 'Sin pronóstico'
  const label = d.cerrado ? 'Cerrado' : 'Abierto'
  const p = pct(d)
  return p === null ? label : `${label} ${p}%`
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
  const [open, setOpen] = useState<string | null>(null)

  const cells = useRef(new Map<string, HTMLElement>())
  const before = useRef<Map<string, DOMRect> | null>(null)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => {
    fetchYear().then(setData).catch(e => setError(String(e.message ?? e)))
    fetchSnowMap().then(setSnow).catch(() => {}) // el mapa es un extra: si falla, los cuadrados no se amplían
  }, [])

  // Animación FLIP: se anota dónde estaba cada cuadrado, se cambia la grilla y se anima desde la posición vieja.
  const change = (next: string | null) => {
    if (next === open) return
    before.current = new Map([...cells.current].map(([k, el]) => [k, el.getBoundingClientRect()]))
    setOpen(next)
  }
  useLayoutEffect(() => {
    const prev = before.current
    if (!prev) return
    before.current = null
    for (const [k, el] of cells.current) {
      const a = prev.get(k)
      if (!a) continue
      const b = el.getBoundingClientRect()
      const dx = a.left - b.left, dy = a.top - b.top, sx = a.width / b.width, sy = a.height / b.height
      if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5 && Math.abs(sx - 1) < 0.01 && Math.abs(sy - 1) < 0.01) continue
      el.animate(
        [{ transformOrigin: 'top left', transform: `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})` }, { transformOrigin: 'top left', transform: 'none' }],
        { duration: 380, easing: 'cubic-bezier(.2,.8,.2,1)' },
      )
    }
  }, [open])

  return (
    <main className="flex min-h-svh items-center justify-center px-3 py-10 sm:px-4">
      {error && <p className="text-red-600">No se pudo cargar: {error}</p>}
      {!data && !error && <p className="text-neutral-500">Cargando…</p>}

      {data && (
        <div className="grid w-full max-w-4xl grid-cols-31 gap-[2px] sm:gap-1">
          {data.dias.map((d, i) => {
            const col = i % COLS
            const row = Math.floor(i / COLS)
            const expandable = !!snow?.dias[d.fecha] && d.cerrado !== null && d.fecha >= data.hoy
            const isOpen = expandable && open === d.fecha
            const p = pct(d)
            // Ampliado: se fija en su fila y en una columna que entre en la grilla; el resto de los días se acomoda alrededor.
            const placement = isOpen
              ? { gridRow: `${row + 1} / span ${SPAN_R}`, gridColumn: `${Math.min(col, COLS - SPAN_C) + 1} / span ${SPAN_C}`, aspectRatio: `${SPAN_C} / ${SPAN_R}` }
              : undefined
            return (
              <span
                key={d.fecha}
                ref={el => {
                  if (el) cells.current.set(d.fecha, el)
                  else cells.current.delete(d.fecha)
                }}
                aria-label={`${tooltip(d.fecha)}: ${status(d)}`}
                style={placement}
                onMouseEnter={() => {
                  window.clearTimeout(timer.current)
                  if (expandable) timer.current = window.setTimeout(() => change(d.fecha), HOVER_DELAY)
                }}
                onMouseLeave={() => {
                  window.clearTimeout(timer.current)
                  if (isOpen) change(null)
                }}
                onClick={() => expandable && change(isOpen ? null : d.fecha)} // en celular no hay hover: se toca
                className={`group relative overflow-hidden rounded-[2px] sm:rounded-sm ${color(d.cerrado, d.fecha < data.hoy)} ${
                  isOpen ? 'z-10 ring-2 ring-neutral-900' : 'aspect-square'
                } ${expandable ? 'cursor-pointer' : ''}`}
              >
                {isOpen ? (
                  <>
                    <SnowMap grid={snow!} fecha={d.fecha} />
                    <span className="absolute inset-x-0 top-0 bg-gradient-to-b from-black/75 to-transparent px-2 pb-4 pt-1.5 text-xs text-white">
                      <span className="block font-semibold">{tooltip(d.fecha)}</span>
                      <span className="block text-white/85">{status(d)}</span>
                    </span>
                    <span className="absolute inset-x-0 bottom-0 bg-black/60 px-2 py-1">
                      <SnowLegend />
                    </span>
                  </>
                ) : expandable ? (
                  p !== null && (
                    <span className="absolute inset-0 hidden items-center justify-center text-[9px] font-semibold leading-none text-white sm:flex">
                      {p}%
                    </span>
                  )
                ) : (
                  <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1.5 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-neutral-900 px-2 py-1 text-xs text-white group-hover:block">
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
