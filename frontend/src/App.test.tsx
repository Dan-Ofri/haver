import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('App', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('shows the API and database as ok when both are healthy', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({ status: 'ok', database: 'ok' })))
    render(<App />)
    expect(await screen.findByText('API: ok')).toBeInTheDocument()
    expect(screen.getByText('Database: ok')).toBeInTheDocument()
  })

  it('shows the database as down when the API reports it unavailable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(json({ status: 'ok', database: 'unavailable' })),
    )
    render(<App />)
    expect(await screen.findByText('API: ok')).toBeInTheDocument()
    expect(screen.getByText('Database: down')).toBeInTheDocument()
  })

  it('shows everything as down when the API returns an error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({}, 500)))
    render(<App />)
    expect(await screen.findByText('API: down')).toBeInTheDocument()
    expect(screen.getByText('Database: down')).toBeInTheDocument()
  })

  it('shows everything as down when the request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network')))
    render(<App />)
    expect(await screen.findByText('API: down')).toBeInTheDocument()
    expect(screen.getByText('Database: down')).toBeInTheDocument()
  })
})
