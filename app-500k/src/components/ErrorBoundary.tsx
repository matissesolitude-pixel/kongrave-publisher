import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/** Keeps a rendering failure in one screen from taking the whole app down. */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('500K crashed:', error, info.componentStack)
  }

  override render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-md p-6">
          <h1 className="text-lg font-semibold">Something broke</h1>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            Your data is safe on this device. Reload to continue.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-xl border border-[var(--color-line)] bg-[var(--color-surface)] p-3 text-xs text-[var(--color-neg)]">
            {this.state.error.message}
          </pre>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 min-h-11 w-full rounded-xl bg-[var(--color-accent)] px-4 font-semibold text-white"
          >
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
