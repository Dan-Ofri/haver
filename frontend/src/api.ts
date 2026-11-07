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

export interface Memory {
  id: number
  fact: string
}

async function call<T>(url: string, method: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T)
}

export const listMemory = () => call<Memory[]>('/api/memory', 'GET')
export const addMemory = (fact: string) => call<Memory>('/api/memory', 'POST', { fact })
export const editMemory = (id: number, fact: string) =>
  call<Memory>(`/api/memory/${id}`, 'PUT', { fact })
export const deleteMemory = (id: number) => call<void>(`/api/memory/${id}`, 'DELETE')
