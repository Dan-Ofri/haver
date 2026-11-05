import { type FormEvent, useState } from 'react'
import { type ChatAnswer, type Citation, type Claim, ask } from './api'

interface Turn {
  question: string
  reply?: ChatAnswer
  error?: boolean
}

/** A claim followed by the numbers of its sources in the list below the answer. */
function withNumbers(claim: Claim, citations: Citation[]): string {
  const numbers = new Set(claim.source_ids.map((id) => citations.findIndex((c) => c.id === id) + 1))
  numbers.delete(0)
  return `${claim.text} ${[...numbers].map((n) => `[${n}]`).join('')}`.trim()
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

  function submit(event: FormEvent) {
    event.preventDefault()
    void send(draft)
  }

  async function send(text: string) {
    const question = text.trim()
    if (!question || busy) return
    if (text === draft) setDraft('')
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
                {turn.reply.claims.map((claim, j) => (
                  <p key={j} dir="auto">
                    {withNumbers(claim, turn.reply!.citations)}
                  </p>
                ))}
                {turn.reply.not_found && (
                  <div className="not-found">
                    <p dir="auto">{turn.reply.not_found.message}</p>
                    {turn.reply.not_found.related.length > 0 && (
                      <p dir="auto">
                        Closest topics I have:{' '}
                        {turn.reply.not_found.related.map((r) => r.title).join(', ')}
                      </p>
                    )}
                    {turn.reply.not_found.ask_instead.length > 0 && (
                      <div className="suggestions">
                        {turn.reply.not_found.ask_instead.map((q, k) => (
                          <button
                            key={k}
                            type="button"
                            dir="auto"
                            disabled={busy}
                            onClick={() => void send(q)}
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
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
