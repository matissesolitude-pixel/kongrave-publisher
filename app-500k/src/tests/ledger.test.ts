import { describe, expect, it } from 'vitest'
import { buildLedger, calculateEquity, equityAt } from '@/domain/calculations/ledger'
import { DEFAULT_SETTINGS } from '@/domain/models/defaults'
import { createCashflow, createDayEntry, createTrade } from '@/domain/models/factories'
import type { Settings } from '@/domain/models/types'

const S: Settings = { ...DEFAULT_SETTINGS }
const THROUGH = '2026-09-25'

describe('equity curve', () => {
  it('starts at the configured starting capital', () => {
    const ledger = buildLedger({ settings: S, days: [], trades: [], cashflows: [], through: THROUGH })
    expect(ledger.currentEquity).toBe(7000)
  })

  it('books a +$1,850 day and moves the equity to $8,850', () => {
    const day = createDayEntry('2026-09-21', { eurusdPips: 20, gbpusdPips: 20, xauusdMove: 15 })
    const ledger = buildLedger({ settings: S, days: [day], trades: [], cashflows: [], through: THROUGH })
    expect(ledger.byDate.get('2026-09-21')?.tradingNet).toBe(1850)
    expect(ledger.currentEquity).toBe(8850)
  })

  it('replays the whole curve when a past day changes', () => {
    const first = createDayEntry('2026-09-21', { eurusdPips: 20, gbpusdPips: 20, xauusdMove: 15 })
    const second = createDayEntry('2026-09-22', { eurusdPips: 10, gbpusdPips: 0, xauusdMove: 0 })

    const before = buildLedger({
      settings: S,
      days: [first, second],
      trades: [],
      cashflows: [],
      through: THROUGH,
    })
    // 7000 + 1850 = 8850, then 10 pips at the $10k tier... still 3.5 lots (8850 < 10k) => +350
    expect(before.currentEquity).toBe(9200)

    const edited = { ...first, eurusdPips: 0, gbpusdPips: 0, xauusdMove: 0 }
    const after = buildLedger({
      settings: S,
      days: [edited, second],
      trades: [],
      cashflows: [],
      through: THROUGH,
    })
    expect(after.currentEquity).toBe(7350)
  })

  it('drops a deleted day from the curve', () => {
    const day = createDayEntry('2026-09-21', { eurusdPips: 20, gbpusdPips: 20, xauusdMove: 15 })
    const after = buildLedger({ settings: S, days: [], trades: [], cashflows: [], through: THROUGH })
    expect(buildLedger({ settings: S, days: [day], trades: [], cashflows: [], through: THROUGH }).currentEquity).toBe(8850)
    expect(after.currentEquity).toBe(7000)
  })
})

describe('tier crossing', () => {
  it('uses the new tier once equity has crossed the threshold', () => {
    // Day 1 lifts equity from 7,000 to 10,500 (100 pips EU at 3.5 lots = $3,500).
    const d1 = createDayEntry('2026-09-21', { eurusdPips: 100 })
    // Day 2: 10 pips EU. At the $10k tier the size is 5 lots => $500, not $350.
    const d2 = createDayEntry('2026-09-22', { eurusdPips: 10 })
    const ledger = buildLedger({ settings: S, days: [d1, d2], trades: [], cashflows: [], through: THROUGH })

    expect(ledger.byDate.get('2026-09-21')?.tradingNet).toBe(3500)
    expect(ledger.byDate.get('2026-09-22')?.size.fxLots).toBe(5)
    expect(ledger.byDate.get('2026-09-22')?.tradingNet).toBe(500)
    expect(ledger.currentEquity).toBe(11_000)
  })
})

describe('capital movements', () => {
  it('adds deposits and subtracts withdrawals without touching trading P&L', () => {
    const day = createDayEntry('2026-09-21', { eurusdPips: 20 })
    const deposit = createCashflow('2026-09-22', 'deposit', 2000)
    const withdrawal = createCashflow('2026-09-23', 'withdrawal', 500)
    const ledger = buildLedger({
      settings: S,
      days: [day],
      trades: [],
      cashflows: [deposit, withdrawal],
      through: THROUGH,
    })
    expect(ledger.totalTradingPnl).toBe(700)
    expect(ledger.totalDeposits).toBe(2000)
    expect(ledger.totalWithdrawals).toBe(500)
    expect(ledger.currentEquity).toBe(7000 + 700 + 2000 - 500)
  })

  it('treats a standalone fee as a cost and a manual adjustment as signed', () => {
    const fee = createCashflow('2026-09-22', 'fee', 120)
    const adjustment = createCashflow('2026-09-23', 'manual_adjustment', -80)
    const ledger = buildLedger({
      settings: S,
      days: [],
      trades: [],
      cashflows: [fee, adjustment],
      through: THROUGH,
    })
    expect(ledger.currentEquity).toBe(7000 - 120 - 80)
    expect(ledger.totalTradingPnl).toBe(0)
  })

  it('exposes the documented equity formula', () => {
    expect(
      calculateEquity({
        previousEquity: 7000,
        realizedPnl: 1850,
        fees: 50,
        deposits: 1000,
        withdrawals: 200,
      }),
    ).toBe(9600)
  })
})

describe('P&L source', () => {
  it('never adds a daily summary and its detailed trades together', () => {
    const day = createDayEntry('2026-09-21', {
      eurusdPips: 20,
      gbpusdPips: 20,
      xauusdMove: 15,
      pnlSource: 'daily',
    })
    const trade = createTrade('2026-09-21', 'EURUSD', { result: 20, lots: 3.5, outcome: 'W' })
    const ledger = buildLedger({
      settings: S,
      days: [day],
      trades: [trade],
      cashflows: [],
      through: THROUGH,
    })
    expect(ledger.byDate.get('2026-09-21')?.source).toBe('daily')
    expect(ledger.byDate.get('2026-09-21')?.tradingNet).toBe(1850)
  })

  it('uses the detailed trades when the day says so', () => {
    const day = createDayEntry('2026-09-21', {
      eurusdPips: 20,
      gbpusdPips: 20,
      xauusdMove: 15,
      pnlSource: 'trades',
    })
    const trade = createTrade('2026-09-21', 'EURUSD', { result: 20, lots: 3.5, outcome: 'W' })
    const ledger = buildLedger({
      settings: S,
      days: [day],
      trades: [trade],
      cashflows: [],
      through: THROUGH,
    })
    expect(ledger.byDate.get('2026-09-21')?.source).toBe('trades')
    expect(ledger.byDate.get('2026-09-21')?.tradingNet).toBe(700)
  })

  it('prefers a trade actual P&L over its computed one', () => {
    const trade = createTrade('2026-09-21', 'EURUSD', {
      result: 20,
      lots: 3.5,
      outcome: 'W',
      actualPnl: 612.5,
      fees: 12.5,
    })
    const ledger = buildLedger({ settings: S, days: [], trades: [trade], cashflows: [], through: THROUGH })
    expect(ledger.byDate.get('2026-09-21')?.tradingNet).toBe(600)
  })
})

describe('daily loss limit', () => {
  const mk = (i: number, outcome: 'W' | 'L') =>
    createTrade('2026-09-21', 'EURUSD', {
      result: outcome === 'L' ? -10 : 10,
      lots: 3.5,
      outcome,
      time: `0${i}:00`,
    })

  it('counts losses, not trades', () => {
    const trades = [mk(1, 'W'), mk(2, 'W'), mk(3, 'W'), mk(4, 'W'), mk(5, 'L')]
    const ledger = buildLedger({ settings: S, days: [], trades, cashflows: [], through: THROUGH })
    const day = ledger.byDate.get('2026-09-21')
    expect(day?.tradeCount).toBe(5)
    expect(day?.losses).toBe(1)
    expect(day?.limitReached).toBe(false)
    expect(day?.tradesAfterLimit).toHaveLength(0)
  })

  it('marks the day STOP at the third loss', () => {
    const trades = [mk(1, 'L'), mk(2, 'L'), mk(3, 'L')]
    const day = buildLedger({ settings: S, days: [], trades, cashflows: [], through: THROUGH }).byDate.get(
      '2026-09-21',
    )
    expect(day?.losses).toBe(3)
    expect(day?.limitReached).toBe(true)
    expect(day?.tradesAfterLimit).toHaveLength(0)
  })

  it('records trades taken after the limit and their P&L', () => {
    const trades = [mk(1, 'L'), mk(2, 'L'), mk(3, 'L'), mk(4, 'W'), mk(5, 'L')]
    const day = buildLedger({ settings: S, days: [], trades, cashflows: [], through: THROUGH }).byDate.get(
      '2026-09-21',
    )
    expect(day?.tradesAfterLimit).toHaveLength(2)
    // +10 pips then -10 pips at 3.5 lots => 350 - 350 = 0
    expect(day?.pnlAfterLimit).toBe(0)
  })

  it('falls back to the manual loss counter when no trade is detailed', () => {
    const entry = createDayEntry('2026-09-21', { manualLosses: 3, manualWins: 1 })
    const day = buildLedger({ settings: S, days: [entry], trades: [], cashflows: [], through: THROUGH }).byDate.get(
      '2026-09-21',
    )
    expect(day?.losses).toBe(3)
    expect(day?.limitReached).toBe(true)
  })
})

describe('equityAt', () => {
  it('returns the last known equity for a date without activity', () => {
    const day = createDayEntry('2026-09-21', { eurusdPips: 20 })
    const ledger = buildLedger({ settings: S, days: [day], trades: [], cashflows: [], through: THROUGH })
    expect(equityAt(ledger, '2026-09-24')).toBe(7700)
  })
})
