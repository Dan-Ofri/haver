import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const answer = {
  safety: null,
  claims: [{ text: 'About 1.6 g per kg a day.', source_ids: ['protein'] }],
  not_found: null,
  citations: [{ id: 'protein', title: 'Protein for muscle', url: 'https://example.org/p' }],
  steps: [{ tool: 'search_knowledge', ok: true, detail: '1 result(s)' }],
  input_tokens: 300,
  output_tokens: 45,
  duration_ms: 1234,
}

async function askQuestion(text: string) {
  await userEvent.type(screen.getByLabelText('Your question'), text)
  await userEvent.click(screen.getByRole('button', { name: 'Ask' }))
}

describe('App', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('sends the question and shows the answer with numbered sources', async () => {
    const fetchMock = vi.fn().mockResolvedValue(json(answer))
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    await askQuestion('How much protein?')

    expect(await screen.findByText('About 1.6 g per kg a day. [1]')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Protein for muscle' })).toHaveAttribute(
      'href',
      'https://example.org/p',
    )
    expect(
      screen.getByText('search_knowledge: 1 result(s) · 1.2 s · 345 tokens'),
    ).toBeInTheDocument()
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/chat')
    expect(JSON.parse(init.body as string)).toEqual({ message: 'How much protein?' })
  })

  it('shows a safety alert and no coaching content for a red flag', async () => {
    const alert = { ...answer, claims: [], citations: [], steps: [], safety: { flag_id: 'nerve', message: 'Please stop and see a doctor.' } }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json(alert)))
    render(<App />)
    await askQuestion('My leg is numb')

    expect(await screen.findByRole('alert')).toHaveTextContent('Please stop and see a doctor.')
  })

  it('turns a not-found answer into close topics and questions to ask instead', async () => {
    const notFound = {
      ...answer,
      claims: [],
      citations: [],
      not_found: {
        message: "I couldn't find a reliable source on keto recipes.",
        topic: 'keto recipes',
        out_of_steps: false,
        ask_instead: ['How much protein do I need?'],
        related: [{ id: 'protein', title: 'Protein for muscle', url: 'https://example.org/p' }],
      },
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json(notFound))
      .mockResolvedValueOnce(json(answer))
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    await askQuestion('Keto dinner?')

    expect(
      await screen.findByText("I couldn't find a reliable source on keto recipes."),
    ).toBeInTheDocument()
    expect(screen.getByText('Closest topics I have: Protein for muscle')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'How much protein do I need?' }))
    expect(await screen.findByText('About 1.6 g per kg a day. [1]')).toBeInTheDocument()
    const [, init] = fetchMock.mock.calls[1] as [string, RequestInit]
    expect(JSON.parse(init.body as string)).toEqual({ message: 'How much protein do I need?' })
  })

  it('shows an error when the request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({}, 500)))
    render(<App />)
    await askQuestion('Hello')
    expect(await screen.findByText('Something went wrong. Please try again.')).toBeInTheDocument()
  })

  it('does not send an empty question', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: 'Ask' })).toBeDisabled()
  })
})
