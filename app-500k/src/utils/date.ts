import type { IsoDate, WeekStartDay } from '@/domain/models/types'

/**
 * Dates are handled as *local calendar dates* (`YYYY-MM-DD`).
 * Nothing here ever crosses a UTC boundary, so a day never shifts to its
 * neighbour because of a timezone offset.
 */

const pad = (n: number): string => String(n).padStart(2, '0')

export function toIsoDate(d: Date): IsoDate {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** Parses `YYYY-MM-DD` into a Date at local midnight. */
export function fromIsoDate(iso: IsoDate): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y ?? 1970, (m ?? 1) - 1, d ?? 1)
}

export function todayIso(): IsoDate {
  return toIsoDate(new Date())
}

export function isValidIsoDate(value: unknown): value is IsoDate {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const d = fromIsoDate(value)
  return toIsoDate(d) === value
}

export function addDays(iso: IsoDate, days: number): IsoDate {
  const d = fromIsoDate(iso)
  d.setDate(d.getDate() + days)
  return toIsoDate(d)
}

/** Whole calendar days between two local dates (b - a). */
export function daysBetween(a: IsoDate, b: IsoDate): number {
  const MS_PER_DAY = 86_400_000
  // Use UTC of the local Y/M/D triple so DST shifts cannot produce 0.96 days.
  const ua = Date.UTC(...ymd(a))
  const ub = Date.UTC(...ymd(b))
  return Math.round((ub - ua) / MS_PER_DAY)
}

function ymd(iso: IsoDate): [number, number, number] {
  const d = fromIsoDate(iso)
  return [d.getFullYear(), d.getMonth(), d.getDate()]
}

/** 0 = Sunday … 6 = Saturday. */
export function dayOfWeek(iso: IsoDate): number {
  return fromIsoDate(iso).getDay()
}

/** First day of the week containing `iso`, honouring the configured week start. */
export function startOfWeek(iso: IsoDate, weekStart: WeekStartDay): IsoDate {
  const offset = (dayOfWeek(iso) - weekStart + 7) % 7
  return addDays(iso, -offset)
}

export function endOfWeek(iso: IsoDate, weekStart: WeekStartDay): IsoDate {
  return addDays(startOfWeek(iso, weekStart), 6)
}

/** The 7 dates of the week containing `iso`, in display order. */
export function weekDates(iso: IsoDate, weekStart: WeekStartDay): IsoDate[] {
  const start = startOfWeek(iso, weekStart)
  return Array.from({ length: 7 }, (_, i) => addDays(start, i))
}

const WEEKDAY_SHORT = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'] as const

export function weekdayShort(iso: IsoDate): string {
  return WEEKDAY_SHORT[dayOfWeek(iso)] ?? ''
}

export function formatDayLabel(iso: IsoDate): string {
  const d = fromIsoDate(iso)
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

export function formatFullDate(iso: IsoDate): string {
  const d = fromIsoDate(iso)
  return d.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

/** Inclusive list of calendar dates from `from` to `to`. */
export function dateRange(from: IsoDate, to: IsoDate): IsoDate[] {
  const out: IsoDate[] = []
  const n = daysBetween(from, to)
  for (let i = 0; i <= n; i += 1) out.push(addDays(from, i))
  return out
}

export function minIso(a: IsoDate, b: IsoDate): IsoDate {
  return a <= b ? a : b
}

export function maxIso(a: IsoDate, b: IsoDate): IsoDate {
  return a >= b ? a : b
}

/** Month grid (6 rows x 7 cols) covering the month of `iso`. */
export function monthGrid(iso: IsoDate, weekStart: WeekStartDay): IsoDate[] {
  const d = fromIsoDate(iso)
  const first = toIsoDate(new Date(d.getFullYear(), d.getMonth(), 1))
  const gridStart = startOfWeek(first, weekStart)
  return Array.from({ length: 42 }, (_, i) => addDays(gridStart, i))
}

export function sameMonth(a: IsoDate, b: IsoDate): boolean {
  return a.slice(0, 7) === b.slice(0, 7)
}

export function monthLabel(iso: IsoDate): string {
  return fromIsoDate(iso).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}

export function addMonths(iso: IsoDate, months: number): IsoDate {
  const d = fromIsoDate(iso)
  d.setDate(1)
  d.setMonth(d.getMonth() + months)
  return toIsoDate(d)
}
