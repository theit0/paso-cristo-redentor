import { useEffect, useRef } from 'react'
import relief from './relief.json'

export type SnowDay = { nieve: number[]; lluvia: number[] }
export type SnowGrid = { bbox: number[]; rows: number; cols: number; dias: Record<string, SnowDay> }

const PASO = { lat: -32.82, lon: -70.07 }
// Ciudades de referencia (left: etiqueta a la izquierda del punto para no tapar la cordillera)
const CITIES = [
  { name: 'Valparaíso', lat: -33.05, lon: -71.62, left: false },
  { name: 'Santiago', lat: -33.45, lon: -70.67, left: true },
  { name: 'Los Andes', lat: -32.83, lon: -70.6, left: true },
  { name: 'Mendoza', lat: -32.89, lon: -68.84, left: true },
]
const W = 240
const DPR = 2
const H = Math.round(W * (Math.abs(relief.bbox[1] - relief.bbox[0]) / (Math.abs(relief.bbox[3] - relief.bbox[2]) * Math.cos((33 * Math.PI) / 180))))

// Nieve nueva del día (cm), de verde a rojo como en snow-forecast; la lluvia va en violeta.
const SNOW: [number, string][] = [[1, '#86efac'], [5, '#16a34a'], [15, '#f59e0b'], [30, '#dc2626']]
const RAIN = '#7c6fd8'
const rgb = (hex: string) => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16))
const RAIN_RGB = rgb(RAIN)
function snowColor(cm: number): number[] | null {
  let c: string | null = null
  for (const [min, color] of SNOW) if (cm >= min) c = color
  return c ? rgb(c) : null
}
const mix = (a: number[], b: number[], t: number) => a.map((v, i) => v * (1 - t) + b[i] * t)
// lat/lon → píxeles del mapa
function toXY(lat: number, lon: number) {
  const [lat0, lat1, lon0, lon1] = relief.bbox
  return [((lon - lon0) / (lon1 - lon0)) * W, ((lat - lat0) / (lat1 - lat0)) * H]
}

// Valor de una grilla (filas × columnas, de norte a sur y de oeste a este) en la posición fraccional (x, y) ∈ [0,1].
function sample(grid: number[], rows: number, cols: number, x: number, y: number) {
  const clamp = (v: number) => Math.min(1, Math.max(0, v))
  const fx = clamp(x) * (cols - 1), fy = clamp(y) * (rows - 1)
  const x0 = Math.floor(fx), y0 = Math.floor(fy)
  const x1 = Math.min(x0 + 1, cols - 1), y1 = Math.min(y0 + 1, rows - 1)
  const tx = fx - x0, ty = fy - y0
  const at = (r: number, c: number) => grid[r * cols + c]
  return (at(y0, x0) * (1 - tx) + at(y0, x1) * tx) * (1 - ty) + (at(y1, x0) * (1 - tx) + at(y1, x1) * tx) * ty
}

export function SnowMap({ grid, fecha }: { grid: SnowGrid; fecha: string }) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const ctx = ref.current?.getContext('2d')
    const day = grid.dias[fecha]
    if (!ctx || !day) return
    const PW = W * DPR, PH = H * DPR // se dibuja al doble de resolución para que el texto se lea nítido
    const img = ctx.createImageData(PW, PH)
    const e = (x: number, y: number) => sample(relief.elev, relief.rows, relief.cols, x, y)
    for (let py = 0; py < PH; py++) {
      for (let px = 0; px < PW; px++) {
        const x = px / (PW - 1), y = py / (PH - 1)
        const elev = e(x, y)
        let c: number[]
        if (elev <= 0) {
          c = [184, 188, 212] // mar
        } else {
          // relieve gris con luz desde el noroeste
          const slope = (e(x - 0.005, y - 0.005) - e(x + 0.005, y + 0.005)) / 500
          const gray = Math.max(95, Math.min(240, 200 + slope * 55 + (elev - 2000) / 90))
          c = [gray, gray, gray]
        }
        // lluvia: violeta translúcido, más fuerte cuanto más llueve
        const mm = sample(day.lluvia, grid.rows, grid.cols, x, y)
        if (mm >= 1) c = mix(c, RAIN_RGB, Math.min(0.65, 0.25 + mm / 40))
        // nieve nueva: sigue el relieve (en la grilla gruesa del pronóstico se vería en bloques)
        const cm = sample(day.nieve, grid.rows, grid.cols, x, y) * Math.max(0, Math.min(1, (elev - 1000) / 800))
        const s = snowColor(cm)
        if (s) c = mix(c, s, 0.75)
        img.data.set([c[0], c[1], c[2], 255], (py * PW + px) * 4)
      }
    }
    ctx.putImageData(img, 0, 0)
    ctx.save()
    ctx.scale(DPR, DPR)
    // texto con borde blanco para que se lea sobre cualquier color
    const label = (text: string, x: number, y: number, font: string, color: string, align: CanvasTextAlign = 'left') => {
      ctx.font = font
      ctx.textAlign = align
      ctx.textBaseline = 'middle'
      ctx.lineWidth = 3
      ctx.strokeStyle = 'rgba(255,255,255,0.9)'
      ctx.strokeText(text, x, y)
      ctx.fillStyle = color
      ctx.fillText(text, x, y)
    }
    label('CHILE', W * 0.2, H * 0.06, '600 9px system-ui', 'rgba(60,60,70,0.55)', 'center')
    label('ARGENTINA', W * 0.82, H * 0.06, '600 9px system-ui', 'rgba(60,60,70,0.55)', 'center')
    for (const c of CITIES) {
      const [x, y] = toXY(c.lat, c.lon)
      ctx.beginPath()
      ctx.arc(x, y, 1.8, 0, 2 * Math.PI)
      ctx.fillStyle = '#333'
      ctx.fill()
      label(c.name, x + (c.left ? -4 : 4), y, '10px system-ui', '#333', c.left ? 'right' : 'left')
    }
    // el paso
    const [px, py] = toXY(PASO.lat, PASO.lon)
    ctx.beginPath()
    ctx.arc(px, py, 4.5, 0, 2 * Math.PI)
    ctx.fillStyle = '#111'
    ctx.fill()
    ctx.lineWidth = 2
    ctx.strokeStyle = '#fff'
    ctx.stroke()
    label('Paso Cristo Redentor', px, py - 12, '600 10px system-ui', '#111', 'center')
    ctx.restore()
  }, [grid, fecha])

  return (
    // el canvas llena el contenedor (el cuadrado ampliado de la grilla)
    <canvas ref={ref} width={W * DPR} height={H * DPR} className="absolute inset-0 block h-full w-full" />
  )
}

export function SnowLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-[10px] text-neutral-200">
      <span>Nieve nueva</span>
      {SNOW.map(([min, color]) => (
        <span key={min} className="flex items-center gap-0.5">
          <span className="inline-block size-2 rounded-[1px]" style={{ background: color }} />
          {min}
        </span>
      ))}
      <span>cm</span>
      <span className="ml-1 flex items-center gap-0.5">
        <span className="inline-block size-2 rounded-[1px]" style={{ background: RAIN }} />
        lluvia
      </span>
      <span className="ml-1 flex items-center gap-0.5">
        <span className="inline-block size-2 rounded-full border border-white bg-neutral-950" />
        paso
      </span>
    </div>
  )
}
