import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { downloadExportCsv, fetchTickets, fetchUsers } from '../api/tickets'
import { Banner } from '../components/Feedback'
import {
  ALL_PRIORITIES,
  ALL_STATUSES,
  ApiError,
  PRIORITY_LABELS,
  STATUS_LABELS,
  type Ticket,
  type TicketPriority,
  type TicketStatus,
  type User,
} from '../types/api'

export function TicketListPage() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [status, setStatus] = useState<TicketStatus | ''>('')
  const [priority, setPriority] = useState<TicketPriority | ''>('')
  const [assignedTo, setAssignedTo] = useState('')
  const [q, setQ] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    void fetchUsers()
      .then(setUsers)
      .catch(() => {
        /* assignee filter still usable without names */
      })
  }, [])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchTickets({
          status,
          priority,
          assigned_to: assignedTo,
          q,
          page,
          page_size: 20,
        })
        if (cancelled) return
        setTickets(data.results)
        setCount(data.count)
        setPageSize(data.page_size)
        setPage(data.page)
      } catch (err) {
        if (cancelled) return
        setTickets([])
        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError('Network failure — could not load tickets.')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [status, priority, assignedTo, q, page])

  function onSearch(event: FormEvent) {
    event.preventDefault()
    setPage(1)
    setQ(searchInput.trim())
  }

  async function onExport() {
    setExporting(true)
    setError(null)
    try {
      await downloadExportCsv()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Network failure — could not export CSV.')
      }
    } finally {
      setExporting(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(count / pageSize))

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Tickets</h1>
          <p className="muted">Filter, search, and open any ticket.</p>
        </div>
        <div className="row gap">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => void onExport()}
            disabled={exporting}
          >
            {exporting ? 'Exporting…' : 'Export my CSV'}
          </button>
          <Link className="btn btn-primary" to="/tickets/new">
            New ticket
          </Link>
        </div>
      </div>

      <form className="filters" onSubmit={onSearch}>
        <label className="field">
          <span>Status</span>
          <select
            value={status}
            onChange={(e) => {
              setPage(1)
              setStatus(e.target.value as TicketStatus | '')
            }}
          >
            <option value="">All</option>
            {ALL_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Priority</span>
          <select
            value={priority}
            onChange={(e) => {
              setPage(1)
              setPriority(e.target.value as TicketPriority | '')
            }}
          >
            <option value="">All</option>
            {ALL_PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABELS[p]}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Assignee</span>
          <select
            value={assignedTo}
            onChange={(e) => {
              setPage(1)
              setAssignedTo(e.target.value)
            }}
          >
            <option value="">All</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </label>

        <label className="field field-grow">
          <span>Search</span>
          <div className="row gap">
            <input
              type="search"
              placeholder="Title or description"
              value={searchInput}
              maxLength={200}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit" className="btn btn-secondary">
              Search
            </button>
          </div>
        </label>
      </form>

      {error ? <Banner>{error}</Banner> : null}

      {loading ? (
        <p className="muted state-box">Loading tickets…</p>
      ) : !error && tickets.length === 0 ? (
        <p className="muted state-box">No tickets match these filters.</p>
      ) : tickets.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assignee</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.id}>
                    <td>{ticket.id}</td>
                    <td>
                      <Link to={`/tickets/${ticket.id}`}>{ticket.title}</Link>
                    </td>
                    <td>
                      <span className={`badge status-${ticket.status.toLowerCase()}`}>
                        {STATUS_LABELS[ticket.status]}
                      </span>
                    </td>
                    <td>
                      <span className={`badge priority-${ticket.priority.toLowerCase()}`}>
                        {PRIORITY_LABELS[ticket.priority]}
                      </span>
                    </td>
                    <td>{ticket.assigned_to?.name ?? '—'}</td>
                    <td>{new Date(ticket.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              type="button"
              className="btn btn-ghost"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <span className="muted">
              Page {page} of {totalPages} · {count} total
            </span>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      ) : null}
    </div>
  )
}
