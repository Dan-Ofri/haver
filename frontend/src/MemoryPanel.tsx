import { type FormEvent, useState } from 'react'
import { type Memory, addMemory, deleteMemory, editMemory, listMemory } from './api'

/** What the coach remembers about the user. Every fact can be added, edited and deleted. */
export default function MemoryPanel() {
  const [facts, setFacts] = useState<Memory[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)
  const [draft, setDraft] = useState('')
  const [editing, setEditing] = useState<{ id: number; text: string } | null>(null)

  async function run(action: () => Promise<unknown>) {
    try {
      await action()
      setFacts(await listMemory())
      setError(false)
      setLoaded(true)
    } catch {
      setError(true)
    }
  }

  function add(event: FormEvent) {
    event.preventDefault()
    const fact = draft.trim()
    if (!fact) return
    setDraft('')
    void run(() => addMemory(fact))
  }

  function save(event: FormEvent) {
    event.preventDefault()
    if (!editing || !editing.text.trim()) return
    const { id, text } = editing
    setEditing(null)
    void run(() => editMemory(id, text))
  }

  return (
    <details className="memory" onToggle={(e) => e.currentTarget.open && void run(async () => {})}>
      <summary>What I remember about you</summary>
      {error && <p className="error">Something went wrong. Please try again.</p>}
      {loaded && facts.length === 0 && <p className="status">Nothing yet.</p>}
      <ul>
        {facts.map((m) => (
          <li key={m.id}>
            {editing?.id === m.id ? (
              <form onSubmit={save}>
                <input
                  aria-label="Edit fact"
                  dir="auto"
                  value={editing.text}
                  maxLength={300}
                  onChange={(e) => setEditing({ id: m.id, text: e.target.value })}
                />
                <button type="submit">Save</button>
              </form>
            ) : (
              <>
                <span dir="auto">{m.fact}</span>
                <button type="button" onClick={() => setEditing({ id: m.id, text: m.fact })}>
                  Edit
                </button>
                <button type="button" onClick={() => void run(() => deleteMemory(m.id))}>
                  Delete
                </button>
              </>
            )}
          </li>
        ))}
      </ul>
      <form onSubmit={add}>
        <label htmlFor="new-fact" className="visually-hidden">
          New fact about you
        </label>
        <input
          id="new-fact"
          dir="auto"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="For example: sore left knee"
          maxLength={300}
          autoComplete="off"
        />
        <button type="submit" disabled={!draft.trim()}>
          Remember
        </button>
      </form>
    </details>
  )
}
