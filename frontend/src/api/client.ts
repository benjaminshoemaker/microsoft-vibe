const BASE_URL = '/api/v1'

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`)
  }
  if (resp.status === 204) return undefined as T
  return resp.json()
}

// --- Runs ---

export interface RunFilters {
  agent_name?: string
  status?: string
  time_start?: string
  time_end?: string
  search?: string
  page?: number
  page_size?: number
  sort?: string
}

export async function fetchRuns(filters: RunFilters = {}) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value != null && value !== '') params.set(key, String(value))
  }
  const qs = params.toString()
  return fetchJson<{
    runs: Array<Record<string, unknown>>
    total: number
    page: number
    page_size: number
  }>(`/runs${qs ? `?${qs}` : ''}`)
}

export async function fetchRunStats(filters: RunFilters = {}) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value != null && value !== '') params.set(key, String(value))
  }
  const qs = params.toString()
  return fetchJson<Record<string, unknown>>(`/runs/stats${qs ? `?${qs}` : ''}`)
}

export async function fetchRunDetail(runId: string) {
  return fetchJson<Record<string, unknown>>(`/runs/${runId}`)
}

// --- Agents ---

export async function fetchAgents() {
  return fetchJson<{ agents: Array<Record<string, unknown>> }>('/agents')
}

// --- Alerts ---

export async function fetchAlertRules() {
  return fetchJson<{ rules: Array<Record<string, unknown>> }>('/alerts/rules')
}

export async function createAlertRule(rule: Record<string, unknown>) {
  return fetchJson<Record<string, unknown>>('/alerts/rules', {
    method: 'POST',
    body: JSON.stringify(rule),
  })
}

export async function updateAlertRule(id: number, updates: Record<string, unknown>) {
  return fetchJson<Record<string, unknown>>(`/alerts/rules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  })
}

export async function deleteAlertRule(id: number) {
  return fetchJson<void>(`/alerts/rules/${id}`, { method: 'DELETE' })
}

export async function fetchAlertHistory(filters: Record<string, string> = {}) {
  const params = new URLSearchParams(filters)
  const qs = params.toString()
  return fetchJson<{ alerts: Array<Record<string, unknown>>; total: number }>(
    `/alerts/history${qs ? `?${qs}` : ''}`
  )
}
