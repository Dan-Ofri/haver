import { type FormEvent, useState } from 'react'
import { type ChatAnswer, type Citation, ask } from './api'

interface Turn {
  question: string
  reply?: ChatAnswer
  error?: boolean
}

const CITATION = /\s*\[doc:([\w-]+)\]/g

/** Replace [doc:id] markers with the citation's number in the sources list. */
function withNumbers(text: string, citations: Citation[]): string {
  return text.replace(CITATION, (_, id: string) => {
    const index = citations.findIndex((c) => c.id === id)
    return index === -1 ? '' : ` [${index + 1}]`
  })
}

/** One quiet line: which tools ran, how long it took, how many tokens it used. */
function trace(reply: ChatAnswer): string {
  const steps = reply.steps.map((s) => `${s.tool}: ${s.detail}`)
  const seconds = (reply.duration_ms / 1000).toFixed(1)
  const tokens = reply.input_tokens + reply.output_tokens
  return [...steps, `${seconds} s`, `${tokens} tokens`].join(' · ')
}

export default function App() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [draft, setDraft] = useState('')
  const busy = turns.length > 0 && !turns.at(-1)?.reply && !turns.at(-1)?.error

  async function submit(event: FormEvent) {
    event.preventDefault()
    const question = draft.trim()
    if (!question || busy) return
    setDraft('')
    setTurns((prev) => [...prev, { question }])
    const update = (patch: Partial<Turn>) =>
      setTurns((prev) => prev.map((t, i) => (i === prev.length - 1 ? { ...t, ...patch } : t)))
    try {
      update({ reply: await ask(question) })
    } catch {
      update({ error: true })
    }
  }

  return (
    <main className="shell">
      <h1>Haver</h1>
      <p className="tagline">A personal coach that knows you.</p>

      <ol className="turns" aria-live="polite">
        {turns.map((turn, i) => (
          <li key={i}>
            <p className="question" dir="auto">{turn.question}</p>
            {turn.error && <p className="error">Something went wrong. Please try again.</p>}
            {!turn.reply && !turn.error && <p className="status">Thinking…</p>}
            {turn.reply && (
              <div className="reply">
                <p dir="auto">{withNumbers(turn.reply.answer, turn.reply.citations)}</p>
                {turn.reply.citations.length > 0 && (
                  <ol className="sources" aria-label="Sources">
                    {turn.reply.citations.map((c) => (
                      <li key={c.id}>
                        <a href={c.url} target="_blank" rel="noreferrer">
                          {c.title}
                        </a>
                      </li>
                    ))}
                  </ol>
                )}
                <p className="status">{trace(turn.reply)}</p>
              </div>
            )}
          </li>
        ))}
      </ol>

      <form onSubmit={submit}>
        <label htmlFor="message" className="visually-hidden">
          Your question
        </label>
        <input
          id="message"
          dir="auto"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about training, sleep or nutrition"
          maxLength={2000}
          autoComplete="off"
        />
        <button type="submit" disabled={busy || !draft.trim()}>
          Ask
        </button>
      </form>
    </main>
  )
}
