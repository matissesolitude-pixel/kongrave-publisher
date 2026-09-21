import type { IsoDate, Settings } from '@/domain/models/types'
import { addDays, daysBetween, endOfWeek, startOfWeek, weekDates } from '@/utils/date'
import { calculateCompoundRate } from './challenge'
import { equityOpenAt, type DayRecord, type Ledger } from './ledger'
import {
  calculateRequiredGoldMove,
  calculateRequiredPips,
  type PositionSize,
} from './pnl'

/**
 * Weekly objective.
 *
 * `compound`  — the exact rate still required to reach the target by the target
 *               date, recomputed from the equity at the start of the week.
 * `fixedRate` — a user-defined constant (e.g. +35 %/week).
 */

export interface WeeklyTarget {
  weekStart: IsoDate
  weekEnd: IsoDate
  /** Equity at the open of the week. */
  openEquity: number
  /** Weekly growth rate used. */
  rate: number
  /** Target expressed in dollars. */
  targetAmount: number
  /** Equity the week should end at. */
  targetEquity: number
  /** Trading P&L booked so far this week (cash movements excluded). */
  done: number
  remaining: number
  progressRatio: number
  /** Equity right now (includes cash movements). */
  currentEquity: number
}

export function calculateWeeklyTarget(
  settings: Settings,
  ledger: Ledger,
  today: IsoDate,
): WeeklyTarget {
  const weekStart = startOfWeek(today, settings.weekStart)
  const weekEnd = endOfWeek(today, settings.weekStart)
  const openEquity = equityOpenAt(ledger, weekStart)

  let rate: number
  if (settings.weeklyTargetMode === 'fixedRate') {
    rate = settings.fixedWeeklyRate
  } else {
    // Weeks left counted from the *end of this week* to the target date, plus
    // this week itself, so the current week carries its own share of the climb.
    const weeksLeft = Math.max(daysBetween(weekStart, settings.targetDate) / 7, 0)
    const computed = calculateCompoundRate(openEquity, settings.targetCapital, weeksLeft)
    rate = Number.isFinite(computed) ? computed : settings.fixedWeeklyRate
  }

  const targetAmount = openEquity * rate
  const targetEquity = openEquity * (1 + rate)

  const done = weekDates(today, settings.weekStart).reduce((sum, date) => {
    const record = ledger.byDate.get(date)
    return sum + (record ? record.tradingNet : 0)
  }, 0)

  const remaining = Math.max(0, targetAmount - done)
  const progressRatio = targetAmount > 0 ? done / targetAmount : 0

  return {
    weekStart,
    weekEnd,
    openEquity,
    rate,
    targetAmount,
    targetEquity,
    done,
    remaining,
    progressRatio,
    currentEquity: ledger.currentEquity,
  }
}

/** Remaining amount for a weekly target — kept as a named business function. */
export function calculateRemainingTarget(targetAmount: number, done: number): number {
  return Math.max(0, targetAmount - done)
}

export interface Equivalents {
  eurusdPips: number
  gbpusdPips: number
  goldMove: number
}

/** What the remaining amount costs on each instrument, taken alone. */
export function calculateEquivalents(
  amount: number,
  size: PositionSize,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): Equivalents {
  return {
    eurusdPips: calculateRequiredPips(amount, size.fxLots, settings.fxPipValuePerLot),
    gbpusdPips: calculateRequiredPips(amount, size.fxLots, settings.fxPipValuePerLot),
    goldMove: calculateRequiredGoldMove(amount, size.goldLots, settings.goldContractSize),
  }
}

/**
 * "Balanced" means an equal *P&L contribution* per instrument — not the same raw
 * number of pips and dollars.
 */
export function calculateBalancedScenario(
  amount: number,
  size: PositionSize,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): Equivalents {
  const share = amount / 3
  return {
    eurusdPips: calculateRequiredPips(share, size.fxLots, settings.fxPipValuePerLot),
    gbpusdPips: calculateRequiredPips(share, size.fxLots, settings.fxPipValuePerLot),
    goldMove: calculateRequiredGoldMove(share, size.goldLots, settings.goldContractSize),
  }
}

export interface WeekSummary {
  weekStart: IsoDate
  weekEnd: IsoDate
  index: number
  records: DayRecord[]
  tradingNet: number
  openEquity: number
  closeEquity: number
  returnRatio: number
  wins: number
  losses: number
  breakEvens: number
  tradeCount: number
  /** `null` when no detailed trade carries a W/L outcome. */
  winRate: number | null
  /** Every logged day respected the daily loss limit. */
  compliant: boolean
  loggedDays: number
}

/** Every week from the challenge start to the last recorded activity. */
export function buildWeekSummaries(
  settings: Settings,
  ledger: Ledger,
  through: IsoDate,
): WeekSummary[] {
  const first = startOfWeek(
    ledger.days[0]?.date ?? settings.startDate,
    settings.weekStart,
  )
  const summaries: WeekSummary[] = []
  let cursor = first
  let index = 1
  let guard = 0
  while (cursor <= through && guard < 520) {
    const dates = weekDates(cursor, settings.weekStart)
    const records = dates
      .map((d) => ledger.byDate.get(d))
      .filter((r): r is DayRecord => Boolean(r))
    const active = records.filter((r) => r.hasActivity)

    const tradingNet = records.reduce((s, r) => s + r.tradingNet, 0)
    const openEquity = records[0]?.equityOpen ?? equityOpenAt(ledger, cursor)
    const closeEquity = records[records.length - 1]?.equityClose ?? openEquity
    const wins = records.reduce((s, r) => s + r.trades.filter((t) => t.outcome === 'W').length, 0)
    const losses = records.reduce((s, r) => s + r.trades.filter((t) => t.outcome === 'L').length, 0)
    const breakEvens = records.reduce(
      (s, r) => s + r.trades.filter((t) => t.outcome === 'BE').length,
      0,
    )
    const tradeCount = records.reduce((s, r) => s + r.tradeCount, 0)
    const denominator =
      settings.winRateConvention === 'includeBE' ? wins + losses + breakEvens : wins + losses

    summaries.push({
      weekStart: cursor,
      weekEnd: addDays(cursor, 6),
      index,
      records,
      tradingNet,
      openEquity,
      closeEquity,
      returnRatio: openEquity > 0 ? tradingNet / openEquity : 0,
      wins,
      losses,
      breakEvens,
      tradeCount,
      winRate: denominator > 0 ? wins / denominator : null,
      compliant: active.every((r) => r.tradesAfterLimit.length === 0),
      loggedDays: active.length,
    })

    cursor = addDays(cursor, 7)
    index += 1
    guard += 1
  }
  return summaries
}
