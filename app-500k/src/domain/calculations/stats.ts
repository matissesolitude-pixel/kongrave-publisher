import type {
  Emotion,
  InstrumentId,
  IsoDate,
  Settings,
  Trade,
  WinRateConvention,
} from '@/domain/models/types'
import { INSTRUMENTS } from '@/domain/models/types'
import { grossTradePnl, realizedTradePnl } from './pnl'
import type { DayRecord, Ledger } from './ledger'
import type { WeekSummary } from './weekly'

/**
 * Statistics.
 *
 * Trade-level metrics (win rate, profit factor, expectancy, R) come from the
 * detailed trade log only. Days logged through the quick path never invent a
 * win rate.
 *
 * Default win-rate convention: wins / (wins + losses), break-evens excluded.
 */

export function calculateWinRate(
  wins: number,
  losses: number,
  breakEvens: number,
  convention: WinRateConvention = 'excludeBE',
): number | null {
  const denominator = convention === 'includeBE' ? wins + losses + breakEvens : wins + losses
  if (denominator === 0) return null
  return wins / denominator
}

export function calculateProfitFactor(grossWins: number, grossLosses: number): number | null {
  if (grossLosses === 0) return grossWins > 0 ? Infinity : null
  return grossWins / grossLosses
}

/** Average P&L per trade. */
export function calculateExpectancy(pnls: number[]): number | null {
  if (pnls.length === 0) return null
  return pnls.reduce((a, b) => a + b, 0) / pnls.length
}

export interface InstrumentStats {
  instrument: InstrumentId
  trades: number
  wins: number
  losses: number
  breakEvens: number
  winRate: number | null
  pnl: number
  averageResult: number | null
  /** Share of the total absolute P&L contribution. */
  contribution: number
}

export interface TradeStats {
  totalTrades: number
  wins: number
  losses: number
  breakEvens: number
  winRate: number | null
  netPnl: number
  averageWinner: number | null
  averageLoser: number | null
  profitFactor: number | null
  expectancy: number | null
  averageR: number | null
  currentWinStreak: number
  currentLossStreak: number
  maxWinStreak: number
  maxLossStreak: number
  byInstrument: InstrumentStats[]
  pnlAfterLossLimit: number
  tradesAfterLossLimit: number
}

export function calculateTradeStats(
  ledger: Ledger,
  settings: Settings,
): TradeStats {
  const ordered = ledger.days.flatMap((d) => d.trades)
  const pnls = ordered.map((t) => realizedTradePnl(t, settings))

  let wins = 0
  let losses = 0
  let breakEvens = 0
  let grossWins = 0
  let grossLosses = 0
  const winnerPnls: number[] = []
  const loserPnls: number[] = []
  const rValues: number[] = []

  ordered.forEach((t, i) => {
    const pnl = pnls[i] ?? 0
    if (t.outcome === 'W') wins += 1
    else if (t.outcome === 'L') losses += 1
    else breakEvens += 1
    if (pnl > 0) {
      grossWins += pnl
      winnerPnls.push(pnl)
    } else if (pnl < 0) {
      grossLosses += Math.abs(pnl)
      loserPnls.push(pnl)
    }
    if (t.rMultiple !== null) rValues.push(t.rMultiple)
  })

  const streaks = calculateStreaks(ordered)

  const byInstrument = calculateInstrumentStats(ordered, settings)

  const afterLimit = ledger.days.reduce(
    (acc, d) => {
      acc.pnl += d.pnlAfterLimit
      acc.count += d.tradesAfterLimit.length
      return acc
    },
    { pnl: 0, count: 0 },
  )

  return {
    totalTrades: ordered.length,
    wins,
    losses,
    breakEvens,
    winRate: calculateWinRate(wins, losses, breakEvens, settings.winRateConvention),
    netPnl: pnls.reduce((a, b) => a + b, 0),
    averageWinner: winnerPnls.length ? winnerPnls.reduce((a, b) => a + b, 0) / winnerPnls.length : null,
    averageLoser: loserPnls.length ? loserPnls.reduce((a, b) => a + b, 0) / loserPnls.length : null,
    profitFactor: calculateProfitFactor(grossWins, grossLosses),
    expectancy: calculateExpectancy(pnls),
    averageR: rValues.length ? rValues.reduce((a, b) => a + b, 0) / rValues.length : null,
    currentWinStreak: streaks.currentWin,
    currentLossStreak: streaks.currentLoss,
    maxWinStreak: streaks.maxWin,
    maxLossStreak: streaks.maxLoss,
    byInstrument,
    pnlAfterLossLimit: afterLimit.pnl,
    tradesAfterLossLimit: afterLimit.count,
  }
}

function calculateStreaks(trades: Trade[]): {
  currentWin: number
  currentLoss: number
  maxWin: number
  maxLoss: number
} {
  let maxWin = 0
  let maxLoss = 0
  let runWin = 0
  let runLoss = 0
  for (const t of trades) {
    if (t.outcome === 'W') {
      runWin += 1
      runLoss = 0
    } else if (t.outcome === 'L') {
      runLoss += 1
      runWin = 0
    } else {
      continue // break-evens do not interrupt a streak
    }
    maxWin = Math.max(maxWin, runWin)
    maxLoss = Math.max(maxLoss, runLoss)
  }
  return { currentWin: runWin, currentLoss: runLoss, maxWin, maxLoss }
}

function calculateInstrumentStats(trades: Trade[], settings: Settings): InstrumentStats[] {
  const totals = INSTRUMENTS.map((instrument) => {
    const list = trades.filter((t) => t.instrument === instrument)
    const wins = list.filter((t) => t.outcome === 'W').length
    const losses = list.filter((t) => t.outcome === 'L').length
    const breakEvens = list.filter((t) => t.outcome === 'BE').length
    const pnl = list.reduce((s, t) => s + realizedTradePnl(t, settings), 0)
    return {
      instrument,
      trades: list.length,
      wins,
      losses,
      breakEvens,
      winRate: calculateWinRate(wins, losses, breakEvens, settings.winRateConvention),
      pnl,
      averageResult: list.length ? pnl / list.length : null,
      contribution: 0,
    }
  })
  const absTotal = totals.reduce((s, t) => s + Math.abs(t.pnl), 0)
  return totals.map((t) => ({
    ...t,
    contribution: absTotal > 0 ? t.pnl / absTotal : 0,
  }))
}

export interface DayExtreme {
  date: IsoDate
  value: number
}

export interface LedgerStats {
  bestDay: DayExtreme | null
  worstDay: DayExtreme | null
  bestWeek: { weekStart: IsoDate; value: number } | null
  worstWeek: { weekStart: IsoDate; value: number } | null
  loggedDays: number
  greenDays: number
  redDays: number
  flatDays: number
  compliantDays: number
  complianceRatio: number | null
  checklistCompliance: number | null
}

export function calculateLedgerStats(ledger: Ledger, weeks: WeekSummary[]): LedgerStats {
  const active = ledger.days.filter((d) => d.hasActivity)
  const traded = active.filter((d) => d.source !== 'none')

  const best = traded.reduce<DayRecord | null>(
    (acc, d) => (acc === null || d.tradingNet > acc.tradingNet ? d : acc),
    null,
  )
  const worst = traded.reduce<DayRecord | null>(
    (acc, d) => (acc === null || d.tradingNet < acc.tradingNet ? d : acc),
    null,
  )

  const weeksWithActivity = weeks.filter((w) => w.loggedDays > 0)
  const bestWeek = weeksWithActivity.reduce<WeekSummary | null>(
    (acc, w) => (acc === null || w.tradingNet > acc.tradingNet ? w : acc),
    null,
  )
  const worstWeek = weeksWithActivity.reduce<WeekSummary | null>(
    (acc, w) => (acc === null || w.tradingNet < acc.tradingNet ? w : acc),
    null,
  )

  const compliantDays = active.filter((d) => d.tradesAfterLimit.length === 0).length

  const checklistDays = active.filter((d) => d.entry?.checklist)
  const checklistScore = checklistDays.reduce((sum, d) => {
    const c = d.entry?.checklist
    if (!c) return sum
    const values = Object.values(c)
    return sum + values.filter(Boolean).length / values.length
  }, 0)

  return {
    bestDay: best ? { date: best.date, value: best.tradingNet } : null,
    worstDay: worst ? { date: worst.date, value: worst.tradingNet } : null,
    bestWeek: bestWeek ? { weekStart: bestWeek.weekStart, value: bestWeek.tradingNet } : null,
    worstWeek: worstWeek ? { weekStart: worstWeek.weekStart, value: worstWeek.tradingNet } : null,
    loggedDays: active.length,
    greenDays: traded.filter((d) => d.tradingNet > 0).length,
    redDays: traded.filter((d) => d.tradingNet < 0).length,
    flatDays: traded.filter((d) => d.tradingNet === 0).length,
    compliantDays,
    complianceRatio: active.length ? compliantDays / active.length : null,
    checklistCompliance: checklistDays.length ? checklistScore / checklistDays.length : null,
  }
}

export interface PsychologyBucket {
  key: string
  label: string
  days: number
  totalPnl: number
  averagePnl: number
}

/** Average day P&L grouped by recorded emotion. */
export function calculateEmotionStats(
  ledger: Ledger,
  labels: Record<Emotion, string>,
): PsychologyBucket[] {
  const buckets = new Map<Emotion, { days: number; total: number }>()
  for (const day of ledger.days) {
    const emotion = day.entry?.emotion
    if (!emotion) continue
    const b = buckets.get(emotion) ?? { days: 0, total: 0 }
    b.days += 1
    b.total += day.tradingNet
    buckets.set(emotion, b)
  }
  return [...buckets.entries()]
    .map(([key, b]) => ({
      key,
      label: labels[key],
      days: b.days,
      totalPnl: b.total,
      averagePnl: b.total / b.days,
    }))
    .sort((a, b) => b.averagePnl - a.averagePnl)
}

/** Average day P&L grouped by discipline score bucket. */
export function calculateDisciplineStats(ledger: Ledger): PsychologyBucket[] {
  const low = { days: 0, total: 0 }
  const high = { days: 0, total: 0 }
  for (const day of ledger.days) {
    const score = day.entry?.disciplineScore
    if (score === null || score === undefined) continue
    const bucket = score <= 2 ? low : high
    bucket.days += 1
    bucket.total += day.tradingNet
  }
  const out: PsychologyBucket[] = []
  if (low.days) {
    out.push({
      key: 'low',
      label: 'Discipline ≤ 2',
      days: low.days,
      totalPnl: low.total,
      averagePnl: low.total / low.days,
    })
  }
  if (high.days) {
    out.push({
      key: 'high',
      label: 'Discipline ≥ 3',
      days: high.days,
      totalPnl: high.total,
      averagePnl: high.total / high.days,
    })
  }
  return out
}

/** Total gross P&L of all detailed trades, used for reconciliation displays. */
export function totalGrossTradePnl(trades: Trade[], settings: Settings): number {
  return trades.reduce((s, t) => s + grossTradePnl(t, settings), 0)
}
