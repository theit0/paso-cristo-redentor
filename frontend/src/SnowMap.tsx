import { useEffect, useRef } from 'react'
import relief from './relief.json'

export type SnowDay = { nieve: number[]; lluvia: number[] }
export type SnowGrid = { bbox: number[]; rows: number; cols: number; dias: Record<string, SnowDay> }

const PASO = { lat: -32.82, lon: -70.07 }
const W = 200
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
    const img = ctx.createImageData(W, H)
    const e = (x: number, y: number) => sample(relief.elev, relief.rows, relief.cols, x, y)
    for (let py = 0; py < H; py++) {
      for (let px = 0; px < W; px++) {
        const x = px / (W - 1), y = py / (H - 1)
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
        img.data.set([c[0], c[1], c[2], 255], (py * W + px) * 4)
      }
    }
    ctx.putImageData(img, 0, 0)
    // el paso
    const [lat0, lat1, lon0, lon1] = relief.bbox
    ctx.beginPath()
    ctx.arc(((PASO.lon - lon0) / (lon1 - lon0)) * W, ((PASO.lat - lat0) / (lat1 - lat0)) * H, 4, 0, 2 * Math.PI)
    ctx.fillStyle = '#111'
    ctx.fill()
    ctx.lineWidth = 2
    ctx.strokeStyle = '#fff'
    ctx.stroke()
  }, [grid, fecha])

  return (
    <div>
      <canvas ref={ref} width={W} height={H} className="block rounded" style={{ width: W, height: H }} />
      <div className="mt-1.5 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-[10px] text-neutral-300">
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
      </div>
    </div>
  )
}
