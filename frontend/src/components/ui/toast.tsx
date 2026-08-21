import { useEffect } from 'react'

type ToastProps = {
  message: string
  type?: 'success' | 'error' | 'info'
  onDismiss: () => void
}

const toneStyles = {
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
  error: 'border-rose-500/30 bg-rose-500/10 text-rose-200',
  info: 'border-sky-500/30 bg-sky-500/10 text-sky-200',
}

export function Toast({ message, type = 'info', onDismiss }: ToastProps) {
  useEffect(() => {
    const timeoutId = window.setTimeout(onDismiss, 3200)
    return () => window.clearTimeout(timeoutId)
  }, [onDismiss])

  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm shadow-lg backdrop-blur ${toneStyles[type]}`} role="status" aria-live="polite">
      {message}
    </div>
  )
}
