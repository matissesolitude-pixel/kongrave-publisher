import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { DexieAdapter } from '@/db/dexieAdapter'
import type { PersistenceAdapter } from '@/db/persistence'
import { DEFAULT_SETTINGS } from '@/domain/models/defaults'
import type {
  BackupPayload,
  Cashflow,
  DayEntry,
  IsoDate,
  Settings,
  Trade,
} from '@/domain/models/types'
import { buildLedger, liveSize, type Ledger } from '@/domain/calculations/ledger'
import {
  calculateChallengeState,
  calculateDrawdown,
  type ChallengeState,
  type DrawdownStats,
} from '@/domain/calculations/challenge'
import {
  buildWeekSummaries,
  calculateWeeklyTarget,
  type WeeklyTarget,
  type WeekSummary,
} from '@/domain/calculations/weekly'
import type { PositionSize } from '@/domain/calculations/pnl'
import { todayIso } from '@/utils/date'

interface RawData {
  settings: Settings
  days: DayEntry[]
  trades: Trade[]
  cashflows: Cashflow[]
}

export interface Derived {
  ledger: Ledger
  weekly: WeeklyTarget
  challenge: ChallengeState
  drawdown: DrawdownStats
  weeks: WeekSummary[]
  size: PositionSize
  today: IsoDate
}

export interface AppActions {
  updateSettings(patch: Partial<Settings>): Promise<void>
  saveDay(day: DayEntry): Promise<void>
  deleteDay(date: IsoDate, alsoTrades: boolean): Promise<void>
  duplicateDay(from: IsoDate, to: IsoDate): Promise<void>
  saveTrade(trade: Trade): Promise<void>
  deleteTrade(id: string): Promise<void>
  addTrades(trades: Trade[]): Promise<void>
  saveCashflow(cashflow: Cashflow): Promise<void>
  deleteCashflow(id: string): Promise<void>
  importBackup(payload: BackupPayload): Promise<void>
  resetAll(): Promise<void>
}

export interface AppState extends RawData, AppActions {
  ready: boolean
  error: string | null
  derived: Derived
  /** Bumped whenever a write succeeds — used for transient UI feedback. */
  revision: number
}

const AppContext = createContext<AppState | null>(null)

const defaultAdapter: PersistenceAdapter = new DexieAdapter()

export function AppProvider({
  children,
  adapter = defaultAdapter,
}: {
  children: ReactNode
  adapter?: PersistenceAdapter
}) {
  const [data, setData] = useState<RawData>({
    settings: DEFAULT_SETTINGS,
    days: [],
    trades: [],
    cashflows: [],
  })
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [revision, setRevision] = useState(0)
  // Recomputed at midnight-crossing renders; cheap enough to read each load.
  const [today, setToday] = useState<IsoDate>(todayIso)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const [settings, days, trades, cashflows] = await Promise.all([
          adapter.loadSettings(),
          adapter.listDays(),
          adapter.listTrades(),
          adapter.listCashflows(),
        ])
        if (cancelled) return
        if (!settings) await adapter.saveSettings(DEFAULT_SETTINGS)
        setData({ settings: settings ?? DEFAULT_SETTINGS, days, trades, cashflows })
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      } finally {
        if (!cancelled) setReady(true)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [adapter])

  // Keep "today" honest without polling hard.
  useEffect(() => {
    const id = window.setInterval(() => {
      const now = todayIso()
      setToday((prev) => (prev === now ? prev : now))
    }, 60_000)
    return () => window.clearInterval(id)
  }, [])

  const bump = useCallback(() => setRevision((r) => r + 1), [])

  const updateSettings = useCallback<AppActions['updateSettings']>(
    async (patch) => {
      const next = { ...data.settings, ...patch }
      await adapter.saveSettings(next)
      setData((d) => ({ ...d, settings: next }))
      bump()
    },
    [adapter, bump, data.settings],
  )

  const saveDay = useCallback<AppActions['saveDay']>(
    async (day) => {
      const stamped = { ...day, updatedAt: Date.now() }
      await adapter.putDay(stamped)
      setData((d) => ({
        ...d,
        days: [...d.days.filter((x) => x.date !== stamped.date), stamped].sort((a, b) =>
          a.date < b.date ? -1 : 1,
        ),
      }))
      bump()
    },
    [adapter, bump],
  )

  const deleteDay = useCallback<AppActions['deleteDay']>(
    async (date, alsoTrades) => {
      await adapter.deleteDay(date)
      if (alsoTrades) await adapter.deleteTradesForDate(date)
      setData((d) => ({
        ...d,
        days: d.days.filter((x) => x.date !== date),
        trades: alsoTrades ? d.trades.filter((t) => t.date !== date) : d.trades,
      }))
      bump()
    },
    [adapter, bump],
  )

  const duplicateDay = useCallback<AppActions['duplicateDay']>(
    async (from, to) => {
      const source = data.days.find((d) => d.date === from)
      if (!source) return
      const copy: DayEntry = {
        ...source,
        date: to,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      }
      await adapter.putDay(copy)
      setData((d) => ({
        ...d,
        days: [...d.days.filter((x) => x.date !== to), copy].sort((a, b) =>
          a.date < b.date ? -1 : 1,
        ),
      }))
      bump()
    },
    [adapter, bump, data.days],
  )

  const saveTrade = useCallback<AppActions['saveTrade']>(
    async (trade) => {
      const stamped = { ...trade, updatedAt: Date.now() }
      await adapter.putTrade(stamped)
      setData((d) => ({
        ...d,
        trades: [...d.trades.filter((t) => t.id !== stamped.id), stamped],
      }))
      bump()
    },
    [adapter, bump],
  )

  const deleteTrade = useCallback<AppActions['deleteTrade']>(
    async (id) => {
      await adapter.deleteTrade(id)
      setData((d) => ({ ...d, trades: d.trades.filter((t) => t.id !== id) }))
      bump()
    },
    [adapter, bump],
  )

  const addTrades = useCallback<AppActions['addTrades']>(
    async (trades) => {
      for (const t of trades) await adapter.putTrade(t)
      setData((d) => ({ ...d, trades: [...d.trades, ...trades] }))
      bump()
    },
    [adapter, bump],
  )

  const saveCashflow = useCallback<AppActions['saveCashflow']>(
    async (cashflow) => {
      const stamped = { ...cashflow, updatedAt: Date.now() }
      await adapter.putCashflow(stamped)
      setData((d) => ({
        ...d,
        cashflows: [...d.cashflows.filter((c) => c.id !== stamped.id), stamped],
      }))
      bump()
    },
    [adapter, bump],
  )

  const deleteCashflow = useCallback<AppActions['deleteCashflow']>(
    async (id) => {
      await adapter.deleteCashflow(id)
      setData((d) => ({ ...d, cashflows: d.cashflows.filter((c) => c.id !== id) }))
      bump()
    },
    [adapter, bump],
  )

  const importBackup = useCallback<AppActions['importBackup']>(
    async (payload) => {
      await adapter.replaceAll({
        settings: payload.settings,
        days: payload.days,
        trades: payload.trades,
        cashflows: payload.cashflows,
      })
      setData({
        settings: payload.settings,
        days: [...payload.days].sort((a, b) => (a.date < b.date ? -1 : 1)),
        trades: payload.trades,
        cashflows: payload.cashflows,
      })
      bump()
    },
    [adapter, bump],
  )

  const resetAll = useCallback<AppActions['resetAll']>(async () => {
    await adapter.clearAll()
    await adapter.saveSettings(DEFAULT_SETTINGS)
    setData({ settings: DEFAULT_SETTINGS, days: [], trades: [], cashflows: [] })
    bump()
  }, [adapter, bump])

  const derived = useMemo<Derived>(() => {
    const ledger = buildLedger({
      settings: data.settings,
      days: data.days,
      trades: data.trades,
      cashflows: data.cashflows,
      through: today,
    })
    return {
      ledger,
      weekly: calculateWeeklyTarget(data.settings, ledger, today),
      challenge: calculateChallengeState(data.settings, ledger, today),
      drawdown: calculateDrawdown(ledger, data.settings, today),
      weeks: buildWeekSummaries(data.settings, ledger, today),
      size: liveSize(ledger, data.settings, today),
      today,
    }
  }, [data, today])

  const value = useMemo<AppState>(
    () => ({
      ...data,
      ready,
      error,
      revision,
      derived,
      updateSettings,
      saveDay,
      deleteDay,
      duplicateDay,
      saveTrade,
      deleteTrade,
      addTrades,
      saveCashflow,
      deleteCashflow,
      importBackup,
      resetAll,
    }),
    [
      data,
      ready,
      error,
      revision,
      derived,
      updateSettings,
      saveDay,
      deleteDay,
      duplicateDay,
      saveTrade,
      deleteTrade,
      addTrades,
      saveCashflow,
      deleteCashflow,
      importBackup,
      resetAll,
    ],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp(): AppState {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside <AppProvider>')
  return ctx
}
