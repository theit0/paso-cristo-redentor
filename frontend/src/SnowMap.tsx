import { useEffect, useRef } from 'react'
import relief from './relief.json'

export type SnowGrid = { bbox: number[]; rows: number; cols: number; dias: Record<string, number[]> }

const PASO = { lat: -32.82, lon: -70.07 }
const W = 220
const H = Math.round(W * (Math.abs(relief.bbox[1] - relief.bbox[0]) / (Math.abs(relief.bbox[3] - relief.bbox[2]) * Math.cos((33 * Math.PI) / 180))))

// Escala de nieve en el suelo (cm), de verde a rojo como en snow-forecast.
const SCALE: [number, string][] = [[5, '#bef264'], [30, '#22c55e'], [80, '#facc15'], [150, '#f97316'], [250, '#dc2626']]
const rgb = (hex: string) => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16))
function snowColor(cm: number): number[] | null {
  let c: string | null = null
  for (const [min, color] of SCALE) if (cm >= min) c = color
  return c ? rgb(c) : null
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
    const snow = grid.dias[fecha]
    if (!ctx || !snow) return
    const img = ctx.createImageData(W, H)
    const e = (x: number, y: number) => sample(relief.elev, relief.rows, relief.cols, x, y)
    for (let py = 0; py < H; py++) {
      for (let px = 0; px < W; px++) {
        const x = px / (W - 1), y = py / (H - 1)
        const elev = e(x, y)
        // sombreado de relieve con luz desde el noroeste
        const slope = (e(x - 0.006, y - 0.006) - e(x + 0.006, y + 0.006)) / 400
        const gray = Math.max(70, Math.min(235, 175 + slope * 60 + (elev - 2500) / 60))
        let [r, g, b] = [gray, gray, gray + 6]
        // nieve: solo donde la altura lo permite, así sigue las montañas y no la grilla gruesa del pronóstico
        const cm = sample(snow, grid.rows, grid.cols, x, y) * Math.max(0, Math.min(1, (elev - 1800) / 900))
        const c = snowColor(cm)
        if (c) [r, g, b] = [r * 0.4 + c[0] * 0.6, g * 0.4 + c[1] * 0.6, b * 0.4 + c[2] * 0.6] // deja ver el relieve
        const i = (py * W + px) * 4
        img.data.set([r, g, b, 255], i)
      }
    }
    ctx.putImageData(img, 0, 0)
    // el paso
    const [lat0, lat1, lon0, lon1] = relief.bbox
    const pxp = ((PASO.lon - lon0) / (lon1 - lon0)) * W, pyp = ((PASO.lat - lat0) / (lat1 - lat0)) * H
    ctx.beginPath()
    ctx.arc(pxp, pyp, 4.5, 0, 2 * Math.PI)
    ctx.fillStyle = '#111' // negro: el rojo se perdía sobre la nieve profunda
    ctx.fill()
    ctx.lineWidth = 2
    ctx.strokeStyle = '#fff'
    ctx.stroke()
  }, [grid, fecha])

  return (
    <div>
      <canvas ref={ref} width={W} height={H} className="block rounded" style={{ width: W, height: H }} />
      <div className="mt-1.5 flex items-center gap-1 text-[10px] text-neutral-300">
        <span>Nieve</span>
        {SCALE.map(([min, color]) => (
          <span key={min} className="flex items-center gap-0.5">
            <span className="inline-block size-2 rounded-[1px]" style={{ background: color }} />
            {min}
          </span>
        ))}
        <span>cm</span>
      </div>
    </div>
  )
}
