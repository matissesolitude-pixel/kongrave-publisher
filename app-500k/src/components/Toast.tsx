import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

interface ToastMessage {
  id: number
  text: string
  tone: 'default' | 'pos' | 'neg'
}

interface ToastApi {
  show(text: string, tone?: ToastMessage['tone']): void
}

const ToastContext = createContext<ToastApi | null>(null)

/** Lightweight confirmation feedback — never a blocking modal. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  const counter = useRef(0)

  const show = useCallback<ToastApi['show']>((text, tone = 'default') => {
    counter.current += 1
    const id = counter.current
    setToasts((list) => [...list, { id, text, tone }])
    window.setTimeout(() => {
      setToasts((list) => list.filter((t) => t.id !== id))
    }, 2200)
  }, [])

  const api = useMemo<ToastApi>(() => ({ show }), [show])

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-24 z-[60] flex flex-col items-center gap-2 px-4"
        aria-live="polite"
        role="status"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className="animate-fade-up rounded-full border border-[var(--color-line)] bg-[var(--color-surface-2)] px-4 py-2 text-sm font-semibold shadow-lg"
            style={{
              color:
                t.tone === 'pos'
                  ? 'var(--color-pos)'
                  : t.tone === 'neg'
                    ? 'var(--color-neg)'
                    : 'var(--color-text)',
            }}
          >
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')
  return ctx
}
