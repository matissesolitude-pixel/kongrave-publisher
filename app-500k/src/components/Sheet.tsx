import { useEffect, type ReactNode } from 'react'
import { Button } from './ui'

/** Bottom sheet — the single modal pattern used across the app. */
export function Sheet({
  open,
  title,
  onClose,
  children,
  footer,
}: {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = previous
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      {/* Presentational backdrop: the real affordances are the header button
          and the Escape key, so it must not duplicate them for screen readers. */}
      <div
        aria-hidden="true"
        onClick={onClose}
        className="absolute inset-0 bg-black/65 backdrop-blur-sm"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="animate-fade-up safe-bottom relative flex max-h-[92vh] w-full max-w-xl flex-col rounded-t-3xl border border-[var(--color-line)] bg-[var(--color-surface)] sm:rounded-3xl"
      >
        <header className="flex items-center justify-between gap-3 border-b border-[var(--color-line)] px-4 py-3">
          <h2 className="text-base font-semibold">{title}</h2>
          <Button size="sm" variant="ghost" onClick={onClose} aria-label="Close">
            Close
          </Button>
        </header>
        <div className="flex-1 overflow-y-auto px-4 py-4">{children}</div>
        {footer ? (
          <footer className="border-t border-[var(--color-line)] px-4 py-3">{footer}</footer>
        ) : null}
      </div>
    </div>
  )
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  destructive,
  requireText,
  onConfirm,
  onCancel,
  children,
}: {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  destructive?: boolean
  requireText?: string
  onConfirm: () => void
  onCancel: () => void
  children?: ReactNode
}) {
  return (
    <Sheet
      open={open}
      title={title}
      onClose={onCancel}
      footer={
        <div className="flex gap-2">
          <Button full onClick={onCancel}>
            Cancel
          </Button>
          <Button
            full
            variant={destructive ? 'danger' : 'primary'}
            onClick={onConfirm}
            disabled={Boolean(requireText) && !children}
          >
            {confirmLabel}
          </Button>
        </div>
      }
    >
      <p className="text-sm text-[var(--color-muted)]">{message}</p>
      {children}
    </Sheet>
  )
}
