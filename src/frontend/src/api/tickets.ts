import { apiRequest } from './client'
import type {
  PaginatedTickets,
  Ticket,
  TicketCreatePayload,
  TicketListParams,
  TicketUpdatePayload,
  User,
} from '../types/api'

function buildQuery(params: TicketListParams): string {
  const search = new URLSearchParams()
  if (params.status) search.set('status', params.status)
  if (params.priority) search.set('priority', params.priority)
  if (params.assigned_to) search.set('assigned_to', params.assigned_to)
  if (params.q) search.set('q', params.q)
  if (params.page) search.set('page', String(params.page))
  if (params.page_size) search.set('page_size', String(params.page_size))
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export function fetchMe(): Promise<User> {
  return apiRequest<User>('/api/me/')
}

export function fetchUsers(): Promise<User[]> {
  return apiRequest<User[]>('/api/users/')
}

export function fetchTickets(
  params: TicketListParams = {},
): Promise<PaginatedTickets> {
  return apiRequest<PaginatedTickets>(`/api/tickets/${buildQuery(params)}`)
}

export function fetchTicket(id: number): Promise<Ticket> {
  return apiRequest<Ticket>(`/api/tickets/${id}/`)
}

export function createTicket(payload: TicketCreatePayload): Promise<Ticket> {
  return apiRequest<Ticket>('/api/tickets/', {
    method: 'POST',
    body: payload,
  })
}

export function updateTicket(
  id: number,
  payload: TicketUpdatePayload,
): Promise<Ticket> {
  return apiRequest<Ticket>(`/api/tickets/${id}/`, {
    method: 'PATCH',
    body: payload,
  })
}

export function transitionTicket(
  id: number,
  status: string,
): Promise<Ticket> {
  return apiRequest<Ticket>(`/api/tickets/${id}/transition/`, {
    method: 'POST',
    body: { status },
  })
}

export function addComment(id: number, message: string): Promise<unknown> {
  return apiRequest(`/api/tickets/${id}/comments/`, {
    method: 'POST',
    body: { message },
  })
}

export async function downloadExportCsv(): Promise<void> {
  const response = await apiRequest<Response>('/api/tickets/export/', {
    raw: true,
  })
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'my-tickets.csv'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
