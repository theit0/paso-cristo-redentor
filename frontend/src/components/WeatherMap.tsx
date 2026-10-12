import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import type { PuntoClima } from '../api'

// Trazado aproximado RN7 → túnel → Ruta 60 (solo para dibujar).
const ROUTE: [number, number][] = [
  [-32.593, -69.346], [-32.8, -69.65], [-32.855, -69.763], [-32.838, -69.857], [-32.825, -69.912],
  [-32.811, -70.05], [-32.81, -70.065], [-32.835, -70.13], [-32.85, -70.15], [-32.87, -70.17],
  [-32.905, -70.28], [-32.913, -70.31], [-32.834, -70.598],
]

// Puntos cercanos entre sí: etiquetas hacia lados opuestos para que no se pisen.
const TIP: Record<string, L.Direction> = { portillo: 'bottom', las_cuevas: 'top' }

const snow72h = (p: PuntoClima) => p.dias.slice(0, 3).reduce((s, d) => s + (d.nieve_cm ?? 0), 0)

// Más nieve prevista → azul más intenso y círculo más grande.
function style(p: PuntoClima, selected: boolean): L.CircleMarkerOptions {
  const s = snow72h(p)
  const fill = s >= 10 ? '#1e4fa3' : s >= 3 ? '#3b7fd9' : s > 0 ? '#8fb8ec' : '#f2f4f6'
  return {
    radius: 7 + Math.min(s, 20) / 2,
    color: selected ? '#16191d' : '#3d4652',
    weight: selected ? 3 : 1.5,
    fillColor: fill,
    fillOpacity: 0.95,
  }
}

type Props = { points: PuntoClima[]; selected: string; onSelect: (id: string) => void }

export function WeatherMap({ points, selected, onSelect }: Props) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<L.Map | null>(null)
  const layer = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!el.current || map.current) return
    const m = L.map(el.current, { scrollWheelZoom: false, zoomControl: true })
    L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 15,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, SRTM · estilo © <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)',
    }).addTo(m)
    // Doble trazo (halo blanco + línea oscura) para que se lea sobre cualquier relieve.
    L.polyline(ROUTE, { color: '#fff', weight: 7, opacity: 0.9 }).addTo(m)
    L.polyline(ROUTE, { color: '#15191e', weight: 3, dashArray: '8 6' }).addTo(m)
    m.fitBounds(L.latLngBounds(ROUTE).pad(0.08))
    layer.current = L.layerGroup().addTo(m)
    map.current = m
    return () => {
      m.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    const g = layer.current
    if (!g) return
    g.clearLayers()
    for (const p of points) {
      L.circleMarker([p.lat, p.lon], style(p, p.id === selected))
        .bindTooltip(`${Math.round(p.actual.temp)}°`, { permanent: true, direction: TIP[p.id] ?? 'top', className: 'temp-tip', offset: [0, TIP[p.id] === 'bottom' ? 6 : -6] })
        .on('click', () => onSelect(p.id))
        .addTo(g)
    }
  }, [points, selected, onSelect])

  return <div ref={el} className="map" role="region" aria-label="Mapa de la ruta con el clima por punto" />
}
