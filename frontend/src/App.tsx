import { addDays, format, startOfToday } from 'date-fns'
import { es } from 'date-fns/locale'
import { CalendarIcon } from 'lucide-react'
import { useState } from 'react'

import { fetchPrediction, type Prediccion } from '@/api'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Progress } from '@/components/ui/progress'

const FUENTE = {
  estado_oficial: 'Estado oficial de hoy',
  modelo: 'Pronóstico del tiempo + historial',
  climatologia: 'Promedio de otros años (a más de 7 días no hay pronóstico)',
}

function Result({ p }: { p: Prediccion }) {
  const cerrado = p.prob_cerrado >= 0.5
  const abiertoPct = Math.round(p.prob_abierto * 100)
  const cerradoPct = 100 - abiertoPct // complementarios: redondear ambos por separado puede sumar 101
  const prob = cerrado ? cerradoPct : abiertoPct
  return (
    <div className="space-y-4 text-center">
      <p className={`text-5xl font-semibold tracking-tight ${cerrado ? 'text-red-600' : 'text-emerald-600'}`}>
        {cerrado ? 'Cerrado' : 'Abierto'}
      </p>
      <p className="text-muted-foreground">
        {prob}% de probabilidad de que esté {cerrado ? 'cerrado' : 'abierto'}
      </p>
      <div className="space-y-1 text-left">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Abierto {abiertoPct}%</span>
          <span>Cerrado {cerradoPct}%</span>
        </div>
        <Progress value={p.prob_abierto * 100} aria-label="Probabilidad de abierto" />
      </div>
      <p className="text-xs text-muted-foreground">
        {FUENTE[p.fuente]} · confianza {p.confianza}
      </p>
    </div>
  )
}

export default function App() {
  const today = startOfToday()
  const [date, setDate] = useState<Date>()
  const [open, setOpen] = useState(false)
  const [result, setResult] = useState<Prediccion | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const choose = (d: Date | undefined) => {
    setDate(d)
    setOpen(false)
    setResult(null)
    setError(null)
    if (!d) return
    const iso = format(d, 'yyyy-MM-dd')
    setLoading(true)
    fetchPrediction(iso)
      .then(p => setResult(cur => (p.fecha === iso ? p : cur)))
      .catch(e => setError(String(e.message ?? e)))
      .finally(() => setLoading(false))
  }

  return (
    <main className="flex min-h-svh items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Paso Cristo Redentor</CardTitle>
          <CardDescription>¿Va a estar abierto el paso a Chile?</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full justify-start font-normal">
                <CalendarIcon />
                {date ? format(date, "EEEE d 'de' MMMM yyyy", { locale: es }) : 'Elegí la fecha del viaje'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="center">
              <Calendar
                mode="single"
                locale={es}
                selected={date}
                onSelect={choose}
                disabled={{ before: today, after: addDays(today, 365) }}
                startMonth={today}
                endMonth={addDays(today, 365)}
              />
            </PopoverContent>
          </Popover>

          {loading && <p className="text-center text-sm text-muted-foreground">Calculando…</p>}
          {error && <p className="text-center text-sm text-red-600">No se pudo calcular: {error}</p>}
          {result && <Result p={result} />}
        </CardContent>
      </Card>
    </main>
  )
}
