import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand">
          <Link to="/tickets">Support Tickets</Link>
        </div>
        <nav className="topbar-nav">
          <NavLink to="/tickets">
            Tickets
          </NavLink>
          <NavLink to="/tickets/new">New ticket</NavLink>
        </nav>
        <div className="topbar-user">
          <span className="muted">
            {user?.name} · {user?.email}
          </span>
          <button type="button" className="btn btn-ghost" onClick={() => void logout()}>
            Log out
          </button>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
