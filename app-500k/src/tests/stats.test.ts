import { describe, expect, it } from 'vitest'
import {
  calculateExpectancy,
  calculateProfitFactor,
  calculateTradeStats,
  calculateWinRate,
} from '@/domain/calculations/stats'
import { buildLedger } from '@/domain/calculations/ledger'
import { buildWeekSummaries } from '@/domain/calculations/weekly'
import { DEFAULT_SETTINGS } from '@/domain/models/defaults'
import { createDayEntry, createTrade } from '@/domain/models/factories'

const S = DEFAULT_SETTINGS

describe('win rate convention', () => {
  it('excludes break-evens from the denominator by default', () => {
    expect(calculateWinRate(6, 4, 2, 'excludeBE')).toBeCloseTo(0.6, 10)
  })

  it('includes them when configured to', () => {
    expect(calculateWinRate(6, 4, 2, 'includeBE')).toBeCloseTo(0.5, 10)
  })

  it('returns null rather than inventing a rate', () => {
    expect(calculateWinRate(0, 0, 0)).toBeNull()
    expect(calculateWinRate(0, 0, 3, 'excludeBE')).toBeNull()
  })
})

describe('profit factor and expectancy', () => {
  it('divides gross wins by gross losses', () => {
    expect(calculateProfitFactor(2000, 800)).toBeCloseTo(2.5, 10)
  })

  it('is infinite with no loss and null with nothing at all', () => {
    expect(calculateProfitFactor(500, 0)).toBe(Infinity)
    expect(calculateProfitFactor(0, 0)).toBeNull()
  })

  it('averages the P&L per trade', () => {
    expect(calculateExpectancy([100, -50, 250])).toBeCloseTo(100, 10)
    expect(calculateExpectancy([])).toBeNull()
  })
})

describe('trade statistics', () => {
  const trades = [
    createTrade('2026-09-21', 'EURUSD', { result: 20, lots: 3.5, outcome: 'W', time: '08:00' }),
    createTrade('2026-09-21', 'GBPUSD', { result: -10, lots: 3.5, outcome: 'L', time: '09:00' }),
    createTrade('2026-09-22', 'XAUUSD', { result: 15, lots: 0.3, outcome: 'W', time: '10:00' }),
    createTrade('2026-09-22', 'EURUSD', { result: 0, lots: 3.5, outcome: 'BE', time: '11:00' }),
  ]
  const ledger = buildLedger({ settings: S, days: [], trades, cashflows: [], through: '2026-09-25' })
  const stats = calculateTradeStats(ledger, S)

  it('counts outcomes and applies the configured convention', () => {
    expect(stats.totalTrades).toBe(4)
    expect(stats.wins).toBe(2)
    expect(stats.losses).toBe(1)
    expect(stats.breakEvens).toBe(1)
    expect(stats.winRate).toBeCloseTo(2 / 3, 10)
  })

  it('computes the net P&L from the realised trades', () => {
    // 700 - 350 + 450 + 0
    expect(stats.netPnl).toBe(800)
  })

  it('breaks the P&L down per instrument', () => {
    const eu = stats.byInstrument.find((s) => s.instrument === 'EURUSD')
    const gold = stats.byInstrument.find((s) => s.instrument === 'XAUUSD')
    expect(eu?.pnl).toBe(700)
    expect(gold?.pnl).toBe(450)
    expect(eu?.trades).toBe(2)
  })
})

describe('weekly summaries', () => {
  it('reports N/A instead of a win rate for quick-logged weeks', () => {
    const day = createDayEntry('2026-09-21', { eurusdPips: 20 })
    const ledger = buildLedger({ settings: S, days: [day], trades: [], cashflows: [], through: '2026-09-25' })
    const weeks = buildWeekSummaries(S, ledger, '2026-09-25')
    const first = weeks[0]
    expect(first?.tradingNet).toBe(700)
    expect(first?.winRate).toBeNull()
  })

  it('computes a win rate once trades carry outcomes', () => {
    const trades = [
      createTrade('2026-09-21', 'EURUSD', { result: 10, lots: 3.5, outcome: 'W' }),
      createTrade('2026-09-22', 'EURUSD', { result: -10, lots: 3.5, outcome: 'L' }),
      createTrade('2026-09-23', 'EURUSD', { result: 10, lots: 3.5, outcome: 'W' }),
    ]
    const ledger = buildLedger({ settings: S, days: [], trades, cashflows: [], through: '2026-09-25' })
    const weeks = buildWeekSummaries(S, ledger, '2026-09-25')
    expect(weeks[0]?.winRate).toBeCloseTo(2 / 3, 10)
  })
})
