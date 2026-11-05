export interface Citation {
  id: string
  title: string
  url: string
}

export interface Step {
  tool: string
  ok: boolean
  detail: string
}

export interface ChatAnswer {
  answer: string
  citations: Citation[]
  steps: Step[]
  input_tokens: number
  output_tokens: number
  duration_ms: number
}

export async function ask(message: string): Promise<ChatAnswer> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  return (await res.json()) as ChatAnswer
}
