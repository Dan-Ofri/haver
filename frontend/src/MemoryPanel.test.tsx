import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import MemoryPanel from './MemoryPanel'

const json = (body: unknown, status = 200) =>
  new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

/** A tiny in-memory server for /api/memory. */
function fakeServer() {
  let facts = [{ id: 1, fact: 'Sore left knee' }]
  return vi.fn((_url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET'
    const body = init?.body ? (JSON.parse(init.body as string) as { fact: string }) : null
    if (method === 'POST') facts = [...facts, { id: 2, fact: body!.fact }]
    if (method === 'PUT') facts = facts.map((f) => ({ ...f, fact: body!.fact }))
    if (method === 'DELETE') {
      facts = []
      return Promise.resolve(json(null, 204))
    }
    return Promise.resolve(json(method === 'GET' ? facts : facts.at(-1)))
  })
}

describe('MemoryPanel', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('lists the facts when opened, and adds, edits and deletes them', async () => {
    const fetchMock = fakeServer()
    vi.stubGlobal('fetch', fetchMock)
    render(<MemoryPanel />)
    await userEvent.click(screen.getByText('What I remember about you'))
    expect(await screen.findByText('Sore left knee')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('New fact about you'), 'Training for a 10k')
    await userEvent.click(screen.getByRole('button', { name: 'Remember' }))
    expect(await screen.findByText('Training for a 10k')).toBeInTheDocument()

    await userEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0]!)
    const input = screen.getByLabelText('Edit fact')
    await userEvent.clear(input)
    await userEvent.type(input, 'Knee is better')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findAllByText('Knee is better')).not.toHaveLength(0)

    await userEvent.click(screen.getAllByRole('button', { name: 'Delete' })[0]!)
    expect(await screen.findByText('Nothing yet.')).toBeInTheDocument()
    const methods = fetchMock.mock.calls.map(([, init]) => init?.method)
    expect(methods).toContain('PUT')
    expect(methods).toContain('DELETE')
  })

  it('does not call the server until it is opened', () => {
    const fetchMock = fakeServer()
    vi.stubGlobal('fetch', fetchMock)
    render(<MemoryPanel />)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows an error when the server fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({}, 500)))
    render(<MemoryPanel />)
    await userEvent.click(screen.getByText('What I remember about you'))
    expect(await screen.findByText('Something went wrong. Please try again.')).toBeInTheDocument()
  })
})
