import { useEffect, useState } from 'react'

type Status = 'checking' | 'ok' | 'down'

interface Health {
  api: Status
  database: Status
}

const CHECKING: Health = { api: 'checking', database: 'checking' }
const DOWN: Health = { api: 'down', database: 'down' }

export default function App() {
  const [health, setHealth] = useState<Health>(CHECKING)

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/health', { signal: controller.signal })
      .then(async (res) => {
        if (!res.ok) return setHealth(DOWN)
        const body = (await res.json()) as { database?: string }
        setHealth({ api: 'ok', database: body.database === 'ok' ? 'ok' : 'down' })
      })
      .catch(() => {
        if (!controller.signal.aborted) setHealth(DOWN)
      })
    return () => controller.abort()
  }, [])

  return (
    <main className="shell">
      <h1>Haver</h1>
      <p className="tagline">A personal coach that knows you.</p>
      <p className="status" data-state={health.api}>
        API: {health.api}
      </p>
      <p className="status" data-state={health.database}>
        Database: {health.database}
      </p>
    </main>
  )
}
