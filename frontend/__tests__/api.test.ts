import { describe, expect, it, vi } from 'vitest'
import { apiFetch } from '../lib/api'

describe('apiFetch', () => {
  it('throws on non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }))
    await expect(apiFetch('/health')).rejects.toThrow('API error 404')
    vi.unstubAllGlobals()
  })
})
