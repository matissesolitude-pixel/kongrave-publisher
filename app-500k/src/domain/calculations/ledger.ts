import {
  calculateDaySummaryPnl,
  calculateTradesPnl,
  grossTradePnl,
  type DayPnlBreakdown,
  type PositionSize,
} from '@/domain/calculations/pnl'
import { resolveSize } from '@/domain/sizing/sizing'
import type {
  Cashflow,
  DayEntry,
  IsoDate,
  Settings,
  Trade,
} from '@/domain/models/types'
import { addDays, dateRange, maxIso, startOfWeek, todayIso } from '@/utils/date'

/**
 * The ledger is the single source of truth.
 *
 * It replays every event in calendar order — daily summaries, detailed trades and
 * cash movements — and rebuilds the whole equity curve. Editing or deleting a past
 * day therefore recomputes everything after it; the current balance is never
 * patched in isolation.
 *
 * Double counting is impossible by construction: each day draws its P&L from
 * exactly one source (`daily` summary or `trades`), never from both.
 */

export interface DayRecord {
  date: IsoDate
  entry: DayEntry | null
  trades: Trade[]
  cashflows: Cashflow[]

  /** Position size used to value this day. */
  size: PositionSize
  /** Where the P&L came from. */
  source: 'daily' | 'trades' | 'none'
  breakdown: DayPnlBreakdown

  /** Trading result only (gross - fees). Excludes cash movements. */
  tradingNet: number
  /** Net effect of deposits / withdrawals / standalone fees / adjustments. */
  cashflowNet: number
  deposits: number
  withdrawals: number
  /** Fees from the day entry, its trades, and standalone fee cashflows. */
  fees: number

  equityOpen: number
  equityClose: number

  wins: number
  losses: number
  breakEvens: number
  tradeCount: number

  /** `true` once the daily loss limit has been reached. */
  limitReached: boolean
  /** Trades opened after the daily loss limit was already reached. */
  tradesAfterLimit: Trade[]
  pnlAfterLimit: number
  /** `false` when neither a summary, a trade nor a cash movement exists. */
  hasActivity: boolean
}

export interface Ledger {
  days: DayRecord[]
  byDate: Map<IsoDate, DayRecord>
  startingCapital: number
  currentEquity: number
  peakEquity: number
  totalTradingPnl: number
  totalDeposits: number
  totalWithdrawals: number
  totalFees: number
  lastDate: IsoDate
}

export interface LedgerInput {
  settings: Settings
  days: DayEntry[]
  trades: Trade[]
  cashflows: Cashflow[]
  /** Defaults to today; injectable so tests stay deterministic. */
  through?: IsoDate
}

function groupBy<T>(items: T[], key: (item: T) => IsoDate): Map<IsoDate, T[]> {
  const map = new Map<IsoDate, T[]>()
  for (const item of items) {
    const k = key(item)
    const list = map.get(k)
    if (list) list.push(item)
    else map.set(k, [item])
  }
  return map
}

/** Trades in the order they were taken (time first, then insertion order). */
export function sortTrades(trades: Trade[]): Trade[] {
  return [...trades].sort((a, b) => {
    const ta = a.time ?? '99:99'
    const tb = b.time ?? '99:99'
    if (ta !== tb) return ta < tb ? -1 : 1
    return a.createdAt - b.createdAt
  })
}

const EMPTY_BREAKDOWN: DayPnlBreakdown = {
  eurusd: 0,
  gbpusd: 0,
  xauusd: 0,
  gross: 0,
  fees: 0,
  net: 0,
}

function cashflowEffect(c: Cashflow): number {
  switch (c.type) {
    case 'deposit':
      return c.amount
    case 'withdrawal':
      return -c.amount
    case 'fee':
      return -c.amount
    case 'manual_adjustment':
      return c.amount
  }
}

/**
 * Equity snapshot used to size a given day.
 *
 * `immediate` and `nextDay` both size from the previous close — at daily
 * granularity that is the earliest knowable moment. They differ only for the
 * *live* sizing readout (see `liveSize`), where `immediate` also counts today's
 * logged P&L. `nextWeek` freezes the size for the whole week.
 */
function sizingEquity(
  date: IsoDate,
  equityOpen: number,
  weekOpenEquity: Map<IsoDate, number>,
  settings: Settings,
): number {
  if (settings.tierApplyMode === 'nextWeek') {
    const weekStart = startOfWeek(date, settings.weekStart)
    return weekOpenEquity.get(weekStart) ?? equityOpen
  }
  return equityOpen
}

export function buildLedger(input: LedgerInput): Ledger {
  const { settings } = input
  const daysByDate = groupBy(input.days, (d) => d.date)
  const tradesByDate = groupBy(input.trades, (t) => t.date)
  const cashByDate = groupBy(input.cashflows, (c) => c.date)

  const allDates = [
    ...input.days.map((d) => d.date),
    ...input.trades.map((t) => t.date),
    ...input.cashflows.map((c) => c.date),
  ]
  const through = input.through ?? todayIso()
  const lastDate = allDates.reduce<IsoDate>((acc, d) => maxIso(acc, d), through)
  const firstDate = allDates.reduce<IsoDate>(
    (acc, d) => (d < acc ? d : acc),
    settings.startDate,
  )

  const dates = dateRange(firstDate, lastDate)
  const weekOpenEquity = new Map<IsoDate, number>()

  let equity = settings.startingCapital
  let peak = settings.startingCapital
  let totalTradingPnl = 0
  let totalDeposits = 0
  let totalWithdrawals = 0
  let totalFees = 0

  const records: DayRecord[] = []

  for (const date of dates) {
    const equityOpen = equity
    const weekStart = startOfWeek(date, settings.weekStart)
    if (!weekOpenEquity.has(weekStart)) weekOpenEquity.set(weekStart, equityOpen)

    const entry = daysByDate.get(date)?.[0] ?? null
    const dayTrades = sortTrades(tradesByDate.get(date) ?? [])
    const dayCash = cashByDate.get(date) ?? []

    const sizeEquity = sizingEquity(date, equityOpen, weekOpenEquity, settings)
    const derivedSize = resolveSize(sizeEquity, settings)
    const size: PositionSize = {
      fxLots: entry?.fxLotsUsed ?? derivedSize.fxLots,
      goldLots: entry?.goldLotsUsed ?? derivedSize.goldLots,
    }

    // --- Exactly one P&L source per day ---
    let source: DayRecord['source'] = 'none'
    let breakdown: DayPnlBreakdown = EMPTY_BREAKDOWN
    if (entry && entry.pnlSource === 'daily') {
      source = 'daily'
      breakdown = calculateDaySummaryPnl(entry, size, settings)
    } else if (dayTrades.length > 0) {
      source = 'trades'
      const fromTrades = calculateTradesPnl(dayTrades, settings)
      const extraFees = entry ? entry.fees + entry.commission + entry.swap : 0
      breakdown = {
        ...fromTrades,
        fees: fromTrades.fees + extraFees,
        net: fromTrades.gross - fromTrades.fees - extraFees,
      }
    } else if (entry) {
      // Entry marked as "trades" but no trade recorded yet: no P&L, only its fees.
      source = 'daily'
      breakdown = calculateDaySummaryPnl(
        { ...entry, eurusdPips: 0, gbpusdPips: 0, xauusdMove: 0 },
        size,
        settings,
      )
    }

    // --- Cash movements ---
    let cashflowNet = 0
    let deposits = 0
    let withdrawals = 0
    let standaloneFees = 0
    for (const c of dayCash) {
      cashflowNet += cashflowEffect(c)
      if (c.type === 'deposit') deposits += c.amount
      else if (c.type === 'withdrawal') withdrawals += c.amount
      else if (c.type === 'fee') standaloneFees += c.amount
    }

    // --- Daily loss limit ---
    let lossesSoFar = 0
    const tradesAfterLimit: Trade[] = []
    let pnlAfterLimit = 0
    let wins = 0
    let losses = 0
    let breakEvens = 0
    for (const t of dayTrades) {
      if (lossesSoFar >= settings.dailyLossLimit) {
        tradesAfterLimit.push(t)
        pnlAfterLimit += grossTradePnl(t, settings) - t.fees
      }
      if (t.outcome === 'W') wins += 1
      else if (t.outcome === 'L') {
        losses += 1
        lossesSoFar += 1
      } else breakEvens += 1
    }
    if (dayTrades.length === 0 && entry) {
      wins = entry.manualWins ?? 0
      losses = entry.manualLosses ?? 0
    }

    const tradingNet = breakdown.net
    equity = equityOpen + tradingNet + cashflowNet
    peak = Math.max(peak, equity)
    totalTradingPnl += tradingNet
    totalDeposits += deposits
    totalWithdrawals += withdrawals
    totalFees += breakdown.fees + standaloneFees

    const hasActivity = Boolean(entry) || dayTrades.length > 0 || dayCash.length > 0

    records.push({
      date,
      entry,
      trades: dayTrades,
      cashflows: dayCash,
      size,
      source,
      breakdown,
      tradingNet,
      cashflowNet,
      deposits,
      withdrawals,
      fees: breakdown.fees + standaloneFees,
      equityOpen,
      equityClose: equity,
      wins,
      losses,
      breakEvens,
      tradeCount: dayTrades.length,
      limitReached: losses >= settings.dailyLossLimit,
      tradesAfterLimit,
      pnlAfterLimit,
      hasActivity,
    })
  }

  const byDate = new Map(records.map((r) => [r.date, r]))

  return {
    days: records,
    byDate,
    startingCapital: settings.startingCapital,
    currentEquity: equity,
    peakEquity: peak,
    totalTradingPnl,
    totalDeposits,
    totalWithdrawals,
    totalFees,
    lastDate,
  }
}

/** Equity at the close of `date`, or the last known equity before it. */
export function equityAt(ledger: Ledger, date: IsoDate): number {
  const exact = ledger.byDate.get(date)
  if (exact) return exact.equityClose
  let equity = ledger.startingCapital
  for (const d of ledger.days) {
    if (d.date > date) break
    equity = d.equityClose
  }
  return equity
}

/** Equity at the open of `date` (= close of the previous day). */
export function equityOpenAt(ledger: Ledger, date: IsoDate): number {
  const exact = ledger.byDate.get(date)
  if (exact) return exact.equityOpen
  return equityAt(ledger, addDays(date, -1))
}

/**
 * Convenience wrapper matching the documented business API:
 * `new equity = previous + realized P&L - fees + deposits - withdrawals`.
 */
export function calculateEquity(params: {
  previousEquity: number
  realizedPnl: number
  fees: number
  deposits: number
  withdrawals: number
  adjustments?: number
}): number {
  return (
    params.previousEquity +
    params.realizedPnl -
    params.fees +
    params.deposits -
    params.withdrawals +
    (params.adjustments ?? 0)
  )
}

/** The size to display as "current sizing", honouring the tier apply mode. */
export function liveSize(ledger: Ledger, settings: Settings, today = todayIso()): PositionSize {
  if (settings.tierApplyMode === 'immediate') {
    return applyOverride(resolveSize(ledger.currentEquity, settings), settings)
  }
  if (settings.tierApplyMode === 'nextWeek') {
    const weekStart = startOfWeek(today, settings.weekStart)
    const record = ledger.byDate.get(weekStart)
    const equity = record ? record.equityOpen : equityOpenAt(ledger, weekStart)
    return applyOverride(resolveSize(equity, settings), settings)
  }
  return applyOverride(resolveSize(equityOpenAt(ledger, today), settings), settings)
}

function applyOverride(size: PositionSize, settings: Settings): PositionSize {
  return {
    fxLots: settings.manualFxLots ?? size.fxLots,
    goldLots: settings.manualGoldLots ?? size.goldLots,
  }
}
