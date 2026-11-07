import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import MemoryPanel from './MemoryPanel'

type Fact = { id: number; fact: string }

const json = (body: unknown, status = 200) =>
  new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

/** A small in-memory /api/memory server that is aware of ids, and records every call. */
function fakeServer(initial: Fact[]) {
  let facts = initial
  let next = 100
  return vi.fn((url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET'
    const id = Number(url.split('/')[3])
    const body = init?.body ? (JSON.parse(init.body as string) as { fact: string }) : null
    if (method === 'POST') facts = [...facts, { id: next++, fact: body!.fact }]
    if (method === 'PUT') facts = facts.map((f) => (f.id === id ? { id, fact: body!.fact } : f))
    if (method === 'DELETE') {
      facts = facts.filter((f) => f.id !== id)
      return Promise.resolve(json(null, 204))
    }
    return Promise.resolve(json(method === 'GET' ? facts : facts.at(-1)))
  })
}

const calls = (mock: ReturnType<typeof fakeServer>) =>
  mock.mock.calls.map(([url, init]) => `${init?.method ?? 'GET'} ${url}`)

const open = () => userEvent.click(screen.getByText('What I remember about you'))

describe('MemoryPanel', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('lists the facts when opened and adds a new one', async () => {
    const mock = fakeServer([{ id: 1, fact: 'Sore left knee' }])
    vi.stubGlobal('fetch', mock)
    render(<MemoryPanel />)
    await open()
    expect(await screen.findByText('Sore left knee')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('New fact about you'), 'Training for a 10k')
    await userEvent.click(screen.getByRole('button', { name: 'Remember' }))
    expect(await screen.findByText('Training for a 10k')).toBeInTheDocument()
    expect(calls(mock)).toContain('POST /api/memory')
  })

  it('edits only the chosen fact', async () => {
    const mock = fakeServer([
      { id: 1, fact: 'Sore left knee' },
      { id: 2, fact: 'Vegetarian' },
    ])
    vi.stubGlobal('fetch', mock)
    render(<MemoryPanel />)
    await open()
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Vegetarian' }))
    const input = screen.getByLabelText('Edit fact')
    await userEvent.clear(input)
    await userEvent.type(input, '  Vegan ')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Vegan')).toBeInTheDocument()
    expect(screen.getByText('Sore left knee')).toBeInTheDocument()
    expect(calls(mock)).toContain('PUT /api/memory/2')
    const put = mock.mock.calls.find(([, init]) => init?.method === 'PUT')!
    expect(JSON.parse(put[1]!.body as string)).toEqual({ fact: 'Vegan' })
  })

  it('deletes only the chosen fact', async () => {
    const mock = fakeServer([
      { id: 1, fact: 'Sore left knee' },
      { id: 2, fact: 'Vegetarian' },
    ])
    vi.stubGlobal('fetch', mock)
    render(<MemoryPanel />)
    await open()
    await userEvent.click(await screen.findByRole('button', { name: 'Delete Sore left knee' }))

    await vi.waitFor(() => expect(screen.queryByText('Sore left knee')).not.toBeInTheDocument())
    expect(screen.getByText('Vegetarian')).toBeInTheDocument()
    expect(calls(mock)).toContain('DELETE /api/memory/1')
  })

  it('says so when there is nothing yet', async () => {
    vi.stubGlobal('fetch', fakeServer([]))
    render(<MemoryPanel />)
    await open()
    expect(await screen.findByText('Nothing yet.')).toBeInTheDocument()
  })

  it('does not call the server until it is opened', () => {
    const mock = fakeServer([])
    vi.stubGlobal('fetch', mock)
    render(<MemoryPanel />)
    expect(mock).not.toHaveBeenCalled()
  })

  it('keeps the typed text when saving fails, and shows an error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({}, 500)))
    render(<MemoryPanel />)
    await open()
    expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong')
    await userEvent.type(screen.getByLabelText('New fact about you'), 'Sore knee')
    await userEvent.click(screen.getByRole('button', { name: 'Remember' }))
    await screen.findByRole('alert')
    expect(screen.getByLabelText('New fact about you')).toHaveValue('Sore knee')
  })
})
