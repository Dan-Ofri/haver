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

export interface Claim {
  text: string
  source_ids: string[]
}

export interface NotFound {
  message: string
  topic: string | null
  out_of_steps: boolean
  ask_instead: string[]
  related: Citation[]
}

export interface SafetyAlert {
  flag_id: string
  message: string
}

export interface ChatAnswer {
  safety: SafetyAlert | null
  claims: Claim[]
  citations: Citation[]
  not_found: NotFound | null
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
