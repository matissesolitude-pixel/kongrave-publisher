import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react'
import { useApp } from './store'
import { HomeScreen } from '@/features/dashboard/HomeScreen'
import { JournalScreen } from '@/features/journal/JournalScreen'
import { CalculatorScreen } from '@/features/calculator/CalculatorScreen'
import { StatsScreen } from '@/features/stats/StatsScreen'
import { SettingsScreen } from '@/features/settings/SettingsScreen'
// The trajectory chart pulls in the charting library: load it on demand so the
// first paint of the daily-logging path stays light.
const RoadScreen = lazy(() =>
  import('@/features/challenge/RoadScreen').then((m) => ({ default: m.RoadScreen })),
)
import { LevelUpBanner } from '@/features/dashboard/LevelUpBanner'
import { cx } from '@/components/ui'

const TABS = [
  { id: 'home', label: 'Home', icon: '◎' },
  { id: 'journal', label: 'Journal', icon: '▤' },
  { id: 'calculator', label: 'Calc', icon: '⌗' },
  { id: 'stats', label: 'Stats', icon: '◫' },
  { id: 'settings', label: 'Settings', icon: '⚙' },
] as const

type Route = (typeof TABS)[number]['id'] | 'road'

const ROUTES = new Set<string>([...TABS.map((t) => t.id), 'road'])

function readHash(): Route {
  const raw = window.location.hash.replace(/^#\/?/, '')
  return (ROUTES.has(raw) ? raw : 'home') as Route
}

export function App() {
  const { ready, error, settings } = useApp()
  const [route, setRoute] = useState<Route>(readHash)

  useEffect(() => {
    const onHash = () => setRoute(readHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const navigate = useCallback((next: string) => {
    window.location.hash = `#/${next}`
    setRoute((ROUTES.has(next) ? next : 'home') as Route)
    window.scrollTo({ top: 0 })
  }, [])

  // Theme and motion preferences are applied on the document root.
  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme
    document.documentElement.dataset.motion = settings.reduceMotion ? 'reduced' : 'full'
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) meta.setAttribute('content', settings.theme === 'light' ? '#f6f7f9' : '#08090a')
  }, [settings.theme, settings.reduceMotion])

  const title = useMemo(() => {
    switch (route) {
      case 'journal':
        return 'Journal'
      case 'calculator':
        return 'Calculator'
      case 'stats':
        return 'Stats'
      case 'settings':
        return 'Settings'
      case 'road':
        return 'Road to 500K'
      default:
        return '500K'
    }
  }, [route])

  if (!ready) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <p className="text-sm text-[var(--color-muted)]">Loading…</p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-xl flex-col">
      <header className="safe-top sticky top-0 z-30 border-b border-[var(--color-line)] bg-[var(--color-bg)]/90 backdrop-blur-md">
        <div className="flex items-baseline justify-between px-4 py-3">
          <h1 className="text-lg font-bold tracking-tight">{title}</h1>
          {route === 'home' ? (
            <span className="text-[11px] font-semibold tracking-[0.14em] text-[var(--color-muted)] uppercase">
              Trading Challenge
            </span>
          ) : null}
        </div>
      </header>

      {error ? (
        <p className="mx-4 mt-3 rounded-xl border border-[var(--color-neg)]/40 bg-[var(--color-neg)]/10 px-3 py-2 text-xs text-[var(--color-neg)]">
          Storage error: {error}
        </p>
      ) : null}

      <LevelUpBanner />

      <main className="flex-1 px-4 pt-4 pb-32">
        {route === 'home' ? <HomeScreen onNavigate={navigate} /> : null}
        {route === 'journal' ? <JournalScreen /> : null}
        {route === 'calculator' ? <CalculatorScreen /> : null}
        {route === 'stats' ? <StatsScreen /> : null}
        {route === 'settings' ? <SettingsScreen /> : null}
        {route === 'road' ? (
          <Suspense
            fallback={<p className="py-8 text-center text-sm text-[var(--color-muted)]">Loading…</p>}
          >
            <RoadScreen onBack={() => navigate('home')} />
          </Suspense>
        ) : null}
      </main>

      <nav
        aria-label="Main"
        className="safe-bottom fixed inset-x-0 bottom-0 z-40 mx-auto w-full max-w-xl border-t border-[var(--color-line)] bg-[var(--color-bg)]/95 backdrop-blur-md"
      >
        <ul className="flex">
          {TABS.map((tab) => {
            const active = route === tab.id || (route === 'road' && tab.id === 'home')
            return (
              <li key={tab.id} className="flex-1">
                <button
                  type="button"
                  onClick={() => navigate(tab.id)}
                  aria-current={active ? 'page' : undefined}
                  className={cx(
                    'flex min-h-14 w-full flex-col items-center justify-center gap-0.5 py-2 transition',
                    active ? 'text-[var(--color-accent)]' : 'text-[var(--color-dim)]',
                  )}
                >
                  <span aria-hidden="true" className="text-base leading-none">
                    {tab.icon}
                  </span>
                  <span className="text-[10px] font-semibold tracking-wide">{tab.label}</span>
                </button>
              </li>
            )
          })}
        </ul>
      </nav>
    </div>
  )
}
