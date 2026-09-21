import { describe, expect, it } from 'vitest'
import {
  calculateChallengeState,
  calculateCompoundRate,
  calculateDrawdown,
  generateCheckpoints,
  trajectoryEquityAt,
  weeksBetween,
} from '@/domain/calculations/challenge'
import { buildLedger } from '@/domain/calculations/ledger'
import { calculateWeeklyTarget } from '@/domain/calculations/weekly'
import { DEFAULT_SETTINGS } from '@/domain/models/defaults'
import { createDayEntry } from '@/domain/models/factories'

const S = DEFAULT_SETTINGS
const empty = (through: string) =>
  buildLedger({ settings: S, days: [], trades: [], cashflows: [], through })

describe('compound rate', () => {
  it('derives the exact weekly rate from equity, target and time', () => {
    const weeks = weeksBetween('2026-09-21', '2027-01-01')
    expect(weeks).toBeCloseTo(102 / 7, 10)
    const rate = calculateCompoundRate(7000, 500_000, weeks)
    // Not hardcoded to 35 % — it lands near it because of the chosen dates.
    expect(rate).toBeGreaterThan(0.3)
    expect(rate).toBeLessThan(0.4)
    // Compounding at that rate over the period reaches the target.
    expect(7000 * Math.pow(1 + rate, weeks)).toBeCloseTo(500_000, 6)
  })

  it('returns 0 once the target is reached and Infinity with no time left', () => {
    expect(calculateCompoundRate(600_000, 500_000, 5)).toBe(0)
    expect(calculateCompoundRate(7000, 500_000, 0)).toBe(Infinity)
  })
})

describe('trajectory', () => {
  it('starts at the starting capital and ends at the target', () => {
    expect(trajectoryEquityAt(S, S.startDate)).toBe(S.startingCapital)
    expect(trajectoryEquityAt(S, S.targetDate)).toBeCloseTo(S.targetCapital, 6)
  })

  it('generates its own weekly checkpoints, ending on the target date', () => {
    const checkpoints = generateCheckpoints(S, null, S.startDate)
    expect(checkpoints.length).toBeGreaterThan(10)
    expect(checkpoints.at(-1)?.date).toBe(S.targetDate)
    expect(checkpoints.at(-1)?.equity).toBe(500_000)
    // Monotonically increasing.
    for (let i = 1; i < checkpoints.length; i += 1) {
      expect(checkpoints[i]!.equity).toBeGreaterThan(checkpoints[i - 1]!.equity)
    }
  })

  it('reports being ahead of or behind the trajectory', () => {
    const day = createDayEntry('2026-09-21', { eurusdPips: 100, gbpusdPips: 100 })
    const ledger = buildLedger({ settings: S, days: [day], trades: [], cashflows: [], through: '2026-09-22' })
    const state = calculateChallengeState(S, ledger, '2026-09-22')
    expect(state.currentEquity).toBe(14_000)
    expect(state.aheadBy).toBeGreaterThan(0)
  })
})

describe('weekly target', () => {
  it('falls back to the fixed rate when configured', () => {
    const settings = { ...S, weeklyTargetMode: 'fixedRate' as const, fixedWeeklyRate: 0.35 }
    const weekly = calculateWeeklyTarget(settings, empty('2026-09-21'), '2026-09-21')
    expect(weekly.openEquity).toBe(7000)
    expect(weekly.targetAmount).toBeCloseTo(2450, 10)
    expect(weekly.targetEquity).toBeCloseTo(9450, 10)
    expect(weekly.remaining).toBeCloseTo(2450, 10)
  })

  it('derives the compound target from the remaining weeks', () => {
    const weekly = calculateWeeklyTarget(S, empty('2026-09-21'), '2026-09-21')
    expect(weekly.rate).toBeGreaterThan(0.25)
    expect(weekly.rate).toBeLessThan(0.45)
    expect(weekly.targetAmount).toBeCloseTo(7000 * weekly.rate, 10)
  })

  it('counts the week progress and the amount left', () => {
    const settings = { ...S, weeklyTargetMode: 'fixedRate' as const, fixedWeeklyRate: 0.35 }
    const day = createDayEntry('2026-09-21', { eurusdPips: 20, gbpusdPips: 20, xauusdMove: 15 })
    const ledger = buildLedger({ settings, days: [day], trades: [], cashflows: [], through: '2026-09-22' })
    const weekly = calculateWeeklyTarget(settings, ledger, '2026-09-22')
    expect(weekly.done).toBe(1850)
    expect(weekly.remaining).toBeCloseTo(600, 10)
    expect(weekly.progressRatio).toBeCloseTo(1850 / 2450, 10)
  })

  it('clamps the remaining amount at zero once the target is beaten', () => {
    const settings = { ...S, weeklyTargetMode: 'fixedRate' as const, fixedWeeklyRate: 0.35 }
    const day = createDayEntry('2026-09-21', { eurusdPips: 100, gbpusdPips: 100 })
    const ledger = buildLedger({ settings, days: [day], trades: [], cashflows: [], through: '2026-09-22' })
    const weekly = calculateWeeklyTarget(settings, ledger, '2026-09-22')
    expect(weekly.remaining).toBe(0)
  })
})

describe('drawdown', () => {
  it('tracks peak, current and max drawdown', () => {
    const up = createDayEntry('2026-09-21', { eurusdPips: 100 }) // +3500 -> 10,500
    const down = createDayEntry('2026-09-22', { eurusdPips: -50 }) // 5 lots => -2500 -> 8,000
    const ledger = buildLedger({
      settings: S,
      days: [up, down],
      trades: [],
      cashflows: [],
      through: '2026-09-23',
    })
    const dd = calculateDrawdown(ledger, S, '2026-09-23')
    expect(dd.peakEquity).toBe(10_500)
    expect(dd.currentEquity).toBe(8_000)
    expect(dd.currentDrawdown).toBe(2_500)
    expect(dd.currentDrawdownPct).toBeCloseTo(2500 / 10500, 10)
    expect(dd.maxDrawdown).toBe(2_500)
  })
})
