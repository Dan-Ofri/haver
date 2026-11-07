import { type FormEvent, useRef, useState } from 'react'
import { type Memory, addMemory, deleteMemory, editMemory, listMemory } from './api'

/** What the coach remembers about the user. Every fact can be added, edited and deleted. */
export default function MemoryPanel() {
  const [facts, setFacts] = useState<Memory[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)
  const [draft, setDraft] = useState('')
  const [editing, setEditing] = useState<{ id: number; text: string } | null>(null)

  const latest = useRef(0)

  /** Reload the list. A slower, older response never overwrites a newer one. */
  async function load() {
    const ticket = ++latest.current
    try {
      const list = await listMemory()
      if (ticket === latest.current) {
        setFacts(list)
        setLoaded(true)
      }
    } catch {
      setError(true)
    }
  }

  /** Run a change, then reload. Returns false when the change failed. */
  async function change(action: () => Promise<unknown>): Promise<boolean> {
    try {
      await action()
      setError(false)
      await load()
      return true
    } catch {
      setError(true)
      return false
    }
  }

  async function add(event: FormEvent) {
    event.preventDefault()
    const fact = draft.trim()
    if (!fact) return
    if (await change(() => addMemory(fact))) setDraft('')
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    const text = editing?.text.trim()
    if (!editing || !text) return
    if (await change(() => editMemory(editing.id, text))) setEditing(null)
  }

  return (
    <details className="memory" onToggle={(e) => e.currentTarget.open && void load()}>
      <summary>What I remember about you</summary>
      {error && (
        <p className="error" role="alert">Something went wrong. Please try again.
        </p>
      )}
      {loaded && facts.length === 0 && <p className="status">Nothing yet.</p>}
      <ul>
        {facts.map((m) => (
          <li key={m.id}>
            {editing?.id === m.id ? (
              <form onSubmit={(e) => void save(e)}>
                <input
                  aria-label="Edit fact"
                  dir="auto"
                  value={editing.text}
                  autoFocus
                  maxLength={300}
                  onChange={(e) => setEditing({ id: m.id, text: e.target.value })}
                />
                <button type="submit">Save</button>
              </form>
            ) : (
              <>
                <span dir="auto">{m.fact}</span>
                <button
                  type="button"
                  aria-label={`Edit ${m.fact}`}
                  onClick={() => setEditing({ id: m.id, text: m.fact })}
                >
                  Edit
                </button>
                <button
                  type="button"
                  aria-label={`Delete ${m.fact}`}
                  onClick={() => void change(() => deleteMemory(m.id))}
                >
                  Delete
                </button>
              </>
            )}
          </li>
        ))}
      </ul>
      <form onSubmit={(e) => void add(e)}>
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
