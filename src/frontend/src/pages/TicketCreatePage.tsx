import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createTicket, fetchUsers } from '../api/tickets'
import { Banner, FieldError } from '../components/Feedback'
import {
  ALL_PRIORITIES,
  ApiError,
  PRIORITY_LABELS,
  type TicketPriority,
  type User,
} from '../types/api'

export function TicketCreatePage() {
  const navigate = useNavigate()
  const [users, setUsers] = useState<User[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<TicketPriority>('MEDIUM')
  const [assignedTo, setAssignedTo] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    void fetchUsers()
      .then(setUsers)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setFormError(err.message)
        } else {
          setFormError('Network failure — could not load assignees.')
        }
      })
  }, [])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setFieldErrors({})
    setFormError(null)
    setSubmitting(true)
    try {
      const ticket = await createTicket({
        title,
        description,
        priority,
        assigned_to: assignedTo ? Number(assignedTo) : null,
      })
      navigate(`/tickets/${ticket.id}`)
    } catch (err) {
      if (err instanceof ApiError) {
        const fields = err.fieldErrors()
        if (Object.keys(fields).length > 0) {
          setFieldErrors(fields)
        } else {
          setFormError(err.message)
        }
      } else {
        setFormError('Network failure — could not create ticket.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="stack narrow">
      <div className="page-header">
        <div>
          <h1>New ticket</h1>
          <p className="muted">Status starts as Open. You cannot set it here.</p>
        </div>
        <Link className="btn btn-ghost" to="/tickets">
          Back to list
        </Link>
      </div>

      {formError ? <Banner>{formError}</Banner> : null}

      <form className="form-panel" onSubmit={(e) => void onSubmit(e)}>
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
          <span>Assignee (optional)</span>
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

        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create ticket'}
        </button>
      </form>
    </div>
  )
}
