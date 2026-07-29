import type { ReactNode } from 'react'

export function FieldError({ message }: { message?: string }) {
  if (!message) return null
  return <p className="field-error">{message}</p>
}

export function Banner({
  tone = 'error',
  children,
}: {
  tone?: 'error' | 'info' | 'success'
  children: ReactNode
}) {
  return <div className={`banner banner-${tone}`}>{children}</div>
}
