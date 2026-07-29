import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppLayout } from './components/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { TicketCreatePage } from './pages/TicketCreatePage'
import { TicketDetailPage } from './pages/TicketDetailPage'
import { TicketListPage } from './pages/TicketListPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Navigate to="/tickets" replace />} />
              <Route path="/tickets" element={<TicketListPage />} />
              <Route path="/tickets/new" element={<TicketCreatePage />} />
              <Route path="/tickets/:id" element={<TicketDetailPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/tickets" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
