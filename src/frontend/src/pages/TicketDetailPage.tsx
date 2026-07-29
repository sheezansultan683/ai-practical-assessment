import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  addComment,
  fetchTicket,
  fetchUsers,
  transitionTicket,
  updateTicket,
} from '../api/tickets'
import { Banner, FieldError } from '../components/Feedback'
import {
  ALL_PRIORITIES,
  ApiError,
  PRIORITY_LABELS,
  STATUS_LABELS,
  formatTransitionRejection,
  isTerminalStatus,
  type Ticket,
  type TicketPriority,
  type TicketStatus,
  type User,
} from '../types/api'

export function TicketDetailPage() {
  const { id } = useParams()
  const ticketId = Number(id)

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<TicketPriority>('MEDIUM')
  const [assignedTo, setAssignedTo] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [editError, setEditError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [transitionError, setTransitionError] = useState<string | null>(null)
  const [transitioning, setTransitioning] = useState<string | null>(null)

  const [comment, setComment] = useState('')
  const [commentError, setCommentError] = useState<string | null>(null)
  const [commentFieldError, setCommentFieldError] = useState<string | undefined>()
  const [commenting, setCommenting] = useState(false)

  useEffect(() => {
    void fetchUsers().then(setUsers).catch(() => undefined)
  }, [])

  useEffect(() => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) {
      setError('Invalid ticket id.')
      setLoading(false)
      return
    }

    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchTicket(ticketId)
        if (cancelled) return
        applyTicket(data)
      } catch (err) {
        if (cancelled) return
        setTicket(null)
        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError('Network failure — could not load ticket.')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [ticketId])

  function applyTicket(data: Ticket) {
    setTicket(data)
    setTitle(data.title)
    setDescription(data.description)
    setPriority(data.priority)
    setAssignedTo(data.assigned_to ? String(data.assigned_to.id) : '')
  }

  const frozen = ticket ? isTerminalStatus(ticket.status) : false

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (!ticket || frozen) return
    setFieldErrors({})
    setEditError(null)
    setSaving(true)
    try {
      const updated = await updateTicket(ticket.id, {
        title,
        description,
        priority,
        assigned_to: assignedTo ? Number(assignedTo) : null,
      })
      applyTicket(updated)
    } catch (err) {
      if (err instanceof ApiError) {
        const fields = err.fieldErrors()
        if (Object.keys(fields).length > 0) {
          setFieldErrors(fields)
        } else {
          setEditError(err.message)
        }
      } else {
        setEditError('Network failure — could not update ticket.')
      }
    } finally {
      setSaving(false)
    }
  }

  async function onTransition(next: TicketStatus) {
    if (!ticket) return
    setTransitionError(null)
    setTransitioning(next)
    try {
      const updated = await transitionTicket(ticket.id, next)
      applyTicket(updated)
    } catch (err) {
      if (err instanceof ApiError) {
        setTransitionError(formatTransitionRejection(err))
      } else {
        setTransitionError('Network failure — could not change status.')
      }
    } finally {
      setTransitioning(null)
    }
  }

  async function onComment(event: FormEvent) {
    event.preventDefault()
    if (!ticket) return
    setCommentError(null)
    setCommentFieldError(undefined)
    setCommenting(true)
    try {
      await addComment(ticket.id, comment)
      const refreshed = await fetchTicket(ticket.id)
      applyTicket(refreshed)
      setComment('')
    } catch (err) {
      if (err instanceof ApiError) {
        const fields = err.fieldErrors()
        if (fields.message) {
          setCommentFieldError(fields.message)
        } else {
          setCommentError(err.message)
        }
      } else {
        setCommentError('Network failure — could not add comment.')
      }
    } finally {
      setCommenting(false)
    }
  }

  if (loading) {
    return <p className="muted state-box">Loading ticket…</p>
  }

  if (error || !ticket) {
    return (
      <div className="stack">
        <Banner>{error ?? 'Ticket not found.'}</Banner>
        <Link className="btn btn-ghost" to="/tickets">
          Back to list
        </Link>
      </div>
    )
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">Ticket #{ticket.id}</p>
          <h1>{ticket.title}</h1>
          <p className="muted">
            Created by {ticket.created_by.name} ·{' '}
            {new Date(ticket.created_at).toLocaleString()}
          </p>
        </div>
        <Link className="btn btn-ghost" to="/tickets">
          Back to list
        </Link>
      </div>

      <div className="meta-row">
        <span className={`badge status-${ticket.status.toLowerCase()}`}>
          {STATUS_LABELS[ticket.status]}
        </span>
        <span className={`badge priority-${ticket.priority.toLowerCase()}`}>
          {PRIORITY_LABELS[ticket.priority]}
        </span>
        <span className="muted">
          Assignee: {ticket.assigned_to?.name ?? 'Unassigned'}
        </span>
        <span className="muted">
          Updated {new Date(ticket.updated_at).toLocaleString()}
        </span>
      </div>

      <section className="form-panel">
        <h2>Status transitions</h2>
        <p className="muted">
          Actions come from the API&apos;s <code>allowed_transitions</code> only.
        </p>
        {transitionError ? <Banner>{transitionError}</Banner> : null}
        {ticket.allowed_transitions.length === 0 ? (
          <p className="muted">No transitions available (terminal status).</p>
        ) : (
          <div className="row gap wrap">
            {ticket.allowed_transitions.map((next) => (
              <button
                key={next}
                type="button"
                className="btn btn-secondary"
                disabled={transitioning !== null}
                onClick={() => void onTransition(next)}
              >
                {transitioning === next
                  ? 'Updating…'
                  : `Move to ${STATUS_LABELS[next]}`}
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="form-panel">
        <h2>Edit fields</h2>
        {frozen ? (
          <Banner tone="info">
            This ticket is {STATUS_LABELS[ticket.status]}. Field edits are
            disabled; comments are still allowed.
          </Banner>
        ) : null}
        {editError ? <Banner>{editError}</Banner> : null}

        <form className="stack" onSubmit={(e) => void onSave(e)}>
          <fieldset disabled={frozen || saving} className="stack bare">
            <label className="field">
              <span>Title</span>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={200}
                required
              />
              <FieldError message={fieldErrors.title} />
            </label>

            <label className="field">
              <span>Description</span>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={5000}
                rows={6}
                required
              />
              <FieldError message={fieldErrors.description} />
            </label>

            <label className="field">
              <span>Priority</span>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as TicketPriority)}
              >
                {ALL_PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {PRIORITY_LABELS[p]}
                  </option>
                ))}
              </select>
              <FieldError message={fieldErrors.priority} />
            </label>

            <label className="field">
              <span>Assignee</span>
              <select
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
              >
                <option value="">Unassigned</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name} ({u.email})
                  </option>
                ))}
              </select>
              <FieldError message={fieldErrors.assigned_to} />
            </label>
          </fieldset>

          <button
            className="btn btn-primary"
            type="submit"
            disabled={frozen || saving}
          >
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </section>

      <section className="form-panel">
        <h2>Comments</h2>
        {commentError ? <Banner>{commentError}</Banner> : null}

        <ul className="comment-list">
          {(ticket.comments ?? []).length === 0 ? (
            <li className="muted">No comments yet.</li>
          ) : (
            (ticket.comments ?? []).map((c) => (
              <li key={c.id}>
                <div className="comment-meta">
                  <strong>{c.created_by.name}</strong>
                  <span className="muted">
                    {new Date(c.created_at).toLocaleString()}
                  </span>
                </div>
                <p>{c.message}</p>
              </li>
            ))
          )}
        </ul>

        <form className="stack" onSubmit={(e) => void onComment(e)}>
          <label className="field">
            <span>Add a comment</span>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              maxLength={2000}
              rows={3}
              required
            />
            <FieldError message={commentFieldError} />
          </label>
          <button className="btn btn-secondary" type="submit" disabled={commenting}>
            {commenting ? 'Posting…' : 'Post comment'}
          </button>
        </form>
      </section>
    </div>
  )
}
