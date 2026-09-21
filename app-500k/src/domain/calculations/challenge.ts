import type { IsoDate, Settings } from '@/domain/models/types'
import { addDays, daysBetween, startOfWeek } from '@/utils/date'
import type { Ledger } from './ledger'

/**
 * Challenge trajectory maths.
 *
 * Nothing here is hardcoded to +35 %/week: the required compound rate is derived
 * from the live equity, the remaining time and the target. The trajectory is a
 * mathematical tracking curve, not a forecast.
 */

const DAYS_PER_WEEK = 7

/** Fractional weeks between two calendar dates. */
export function weeksBetween(from: IsoDate, to: IsoDate): number {
  return daysBetween(from, to) / DAYS_PER_WEEK
}

/**
 * Compound weekly rate needed to go from `current` to `target` in `weeks`.
 * Returns 0 when the target is already reached and `Infinity` when there is no
 * time left to reach it.
 */
export function calculateCompoundRate(current: number, target: number, weeks: number): number {
  if (current <= 0) return Infinity
  if (target <= current) return 0
  if (weeks <= 0) return Infinity
  return Math.pow(target / current, 1 / weeks) - 1
}

export interface ChallengeState {
  startingCapital: number
  currentEquity: number
  targetCapital: number
  startDate: IsoDate
  targetDate: IsoDate
  daysElapsed: number
  daysRemaining: number
  weeksRemaining: number
  /** Compound weekly rate required from *now* to still hit the target. */
  requiredWeeklyRate: number
  /** Compound weekly rate implied by the original plan (start -> target). */
  plannedWeeklyRate: number
  /** Realised average weekly rate so far, or `null` before any time has passed. */
  actualWeeklyRate: number | null
  progressRatio: number
  /** Equity the reference trajectory expects today. */
  trajectoryEquity: number
  /** Actual minus expected. Positive = ahead of the trajectory. */
  aheadBy: number
  aheadRatio: number
}

export function calculateChallengeState(
  settings: Settings,
  ledger: Ledger,
  today: IsoDate,
): ChallengeState {
  const { startingCapital, targetCapital, startDate, targetDate } = settings
  const daysElapsed = daysBetween(startDate, today)
  const daysRemaining = daysBetween(today, targetDate)
  const weeksRemaining = daysRemaining / DAYS_PER_WEEK
  const totalWeeks = weeksBetween(startDate, targetDate)

  const currentEquity = ledger.currentEquity
  const plannedWeeklyRate = calculateCompoundRate(startingCapital, targetCapital, totalWeeks)
  const requiredWeeklyRate = calculateCompoundRate(currentEquity, targetCapital, weeksRemaining)

  const weeksElapsed = daysElapsed / DAYS_PER_WEEK
  const actualWeeklyRate =
    weeksElapsed > 0 && startingCapital > 0 && currentEquity > 0
      ? Math.pow(currentEquity / startingCapital, 1 / weeksElapsed) - 1
      : null

  const trajectoryEquity = trajectoryEquityAt(settings, today)
  const aheadBy = currentEquity - trajectoryEquity
  const aheadRatio = trajectoryEquity > 0 ? aheadBy / trajectoryEquity : 0

  const span = targetCapital - startingCapital
  const progressRatio = span > 0 ? (currentEquity - startingCapital) / span : 0

  return {
    startingCapital,
    currentEquity,
    targetCapital,
    startDate,
    targetDate,
    daysElapsed,
    daysRemaining,
    weeksRemaining,
    requiredWeeklyRate,
    plannedWeeklyRate,
    actualWeeklyRate,
    progressRatio,
    trajectoryEquity,
    aheadBy,
    aheadRatio,
  }
}

/** Equity the reference (planned) trajectory expects on a given date. */
export function trajectoryEquityAt(settings: Settings, date: IsoDate): number {
  const totalWeeks = weeksBetween(settings.startDate, settings.targetDate)
  const rate = calculateCompoundRate(settings.startingCapital, settings.targetCapital, totalWeeks)
  if (!Number.isFinite(rate)) return settings.targetCapital
  const weeks = weeksBetween(settings.startDate, date)
  if (weeks <= 0) return settings.startingCapital
  if (weeks >= totalWeeks) return settings.targetCapital
  return settings.startingCapital * Math.pow(1 + rate, weeks)
}

export interface Checkpoint {
  date: IsoDate
  equity: number
  /** Actual equity on that date, when the date is in the past. */
  actual: number | null
}

/**
 * Weekly checkpoints generated from the exact compound rate — derived, never
 * transcribed from a previously computed table.
 */
export function generateCheckpoints(
  settings: Settings,
  ledger: Ledger | null,
  today: IsoDate,
): Checkpoint[] {
  const out: Checkpoint[] = []
  const firstCheckpoint = startOfWeek(settings.startDate, settings.weekStart) === settings.startDate
    ? addDays(settings.startDate, 7)
    : nextWeekBoundary(settings.startDate, settings)
  let cursor = firstCheckpoint
  let guard = 0
  while (cursor < settings.targetDate && guard < 520) {
    out.push({
      date: cursor,
      equity: trajectoryEquityAt(settings, cursor),
      actual: ledger && cursor <= today ? equityCloseOn(ledger, cursor) : null,
    })
    cursor = addDays(cursor, 7)
    guard += 1
  }
  out.push({
    date: settings.targetDate,
    equity: settings.targetCapital,
    actual: ledger && settings.targetDate <= today ? equityCloseOn(ledger, settings.targetDate) : null,
  })
  return out
}

function nextWeekBoundary(from: IsoDate, settings: Settings): IsoDate {
  const start = startOfWeek(from, settings.weekStart)
  return addDays(start, 7)
}

function equityCloseOn(ledger: Ledger, date: IsoDate): number | null {
  const record = ledger.byDate.get(date)
  if (record) return record.equityClose
  let equity: number | null = null
  for (const d of ledger.days) {
    if (d.date > date) break
    equity = d.equityClose
  }
  return equity
}

export interface DrawdownStats {
  peakEquity: number
  currentEquity: number
  currentDrawdown: number
  currentDrawdownPct: number
  maxDrawdown: number
  maxDrawdownPct: number
  maxDrawdownDate: IsoDate | null
  dailyDrawdown: number
  dailyDrawdownPct: number
  weeklyDrawdown: number
  weeklyDrawdownPct: number
}

export function calculateDrawdown(
  ledger: Ledger,
  settings: Settings,
  today: IsoDate,
): DrawdownStats {
  let peak = ledger.startingCapital
  let maxDd = 0
  let maxDdPct = 0
  let maxDdDate: IsoDate | null = null

  for (const day of ledger.days) {
    peak = Math.max(peak, day.equityClose)
    const dd = peak - day.equityClose
    const ddPct = peak > 0 ? dd / peak : 0
    if (dd > maxDd) {
      maxDd = dd
      maxDdPct = ddPct
      maxDdDate = day.date
    }
  }

  const currentEquity = ledger.currentEquity
  const peakEquity = Math.max(peak, ledger.peakEquity)
  const currentDrawdown = Math.max(0, peakEquity - currentEquity)
  const currentDrawdownPct = peakEquity > 0 ? currentDrawdown / peakEquity : 0

  const todayRecord = ledger.byDate.get(today)
  const dayOpen = todayRecord?.equityOpen ?? currentEquity
  const dailyDrawdown = Math.max(0, dayOpen - currentEquity)
  const dailyDrawdownPct = dayOpen > 0 ? dailyDrawdown / dayOpen : 0

  const weekStart = startOfWeek(today, settings.weekStart)
  const weekRecord = ledger.byDate.get(weekStart)
  const weekOpen = weekRecord?.equityOpen ?? currentEquity
  const weeklyDrawdown = Math.max(0, weekOpen - currentEquity)
  const weeklyDrawdownPct = weekOpen > 0 ? weeklyDrawdown / weekOpen : 0

  return {
    peakEquity,
    currentEquity,
    currentDrawdown,
    currentDrawdownPct,
    maxDrawdown: maxDd,
    maxDrawdownPct: maxDdPct,
    maxDrawdownDate: maxDdDate,
    dailyDrawdown,
    dailyDrawdownPct,
    weeklyDrawdown,
    weeklyDrawdownPct,
  }
}
