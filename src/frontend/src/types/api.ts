export type TicketStatus =
  | 'OPEN'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'CLOSED'
  | 'CANCELLED'

export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH'

export type UserRole = 'AGENT' | 'ADMIN'

export interface User {
  id: number
  name: string
  email: string
  role: UserRole
}

export interface Comment {
  id: number
  ticket_id: number
  message: string
  created_by: User
  created_at: string
}

export interface Ticket {
  id: number
  title: string
  description: string
  priority: TicketPriority
  status: TicketStatus
  assigned_to: User | null
  created_by: User
  created_at: string
  updated_at: string
  allowed_transitions: TicketStatus[]
  comments?: Comment[]
}

export interface PaginatedTickets {
  count: number
  page: number
  page_size: number
  results: Ticket[]
}

export interface TicketListParams {
  status?: TicketStatus | ''
  priority?: TicketPriority | ''
  assigned_to?: string
  q?: string
  page?: number
  page_size?: number
}

export interface TicketCreatePayload {
  title: string
  description: string
  priority: TicketPriority
  assigned_to?: number | null
}

export interface TicketUpdatePayload {
  title?: string
  description?: string
  priority?: TicketPriority
  assigned_to?: number | null
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details?: Record<string, string[] | string> | null
  }
}

export class ApiError extends Error {
  status: number
  code: string
  details: Record<string, string[] | string> | null

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message)
    this.name = 'ApiError'
    this.status = status
    this.code = body.error.code
    this.details = body.error.details ?? null
  }

  fieldErrors(): Record<string, string> {
    const out: Record<string, string> = {}
    if (!this.details || typeof this.details !== 'object') return out
    for (const [key, value] of Object.entries(this.details)) {
      if (Array.isArray(value) && value.length > 0) {
        out[key] = value[0]
      } else if (typeof value === 'string') {
        out[key] = value
      }
    }
    return out
  }
}

export const STATUS_LABELS: Record<TicketStatus, string> = {
  OPEN: 'Open',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
  CLOSED: 'Closed',
  CANCELLED: 'Cancelled',
}

export const PRIORITY_LABELS: Record<TicketPriority, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
}

export const ALL_STATUSES: TicketStatus[] = [
  'OPEN',
  'IN_PROGRESS',
  'RESOLVED',
  'CLOSED',
  'CANCELLED',
]

export const ALL_PRIORITIES: TicketPriority[] = ['LOW', 'MEDIUM', 'HIGH']

export function isTerminalStatus(status: TicketStatus): boolean {
  return status === 'CLOSED' || status === 'CANCELLED'
}

export function formatTransitionRejection(error: ApiError): string {
  const details = error.details
  if (
    details &&
    typeof details === 'object' &&
    'current_status' in details &&
    'attempted_status' in details
  ) {
    const current = String(details.current_status)
    const attempted = String(details.attempted_status)
    const allowed = details.allowed_transitions
    const allowedList = Array.isArray(allowed)
      ? allowed.join(', ')
      : typeof allowed === 'string'
        ? allowed
        : 'none'
    return `Cannot change status from ${STATUS_LABELS[current as TicketStatus] ?? current} to ${STATUS_LABELS[attempted as TicketStatus] ?? attempted}. Allowed: ${allowedList || 'none'}.`
  }
  return error.message
}
