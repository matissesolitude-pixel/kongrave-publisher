import { describe, expect, it } from 'vitest'
import {
  calculateFxPnl,
  calculateGoldPnl,
  calculateRequiredGoldMove,
  calculateRequiredPips,
  calculateDaySummaryPnl,
  fullPositionEquivalentGoldMove,
  fullPositionEquivalentPips,
} from '@/domain/calculations/pnl'
import { DEFAULT_SETTINGS } from '@/domain/models/defaults'
import { createDayEntry } from '@/domain/models/factories'

const S = DEFAULT_SETTINGS
const SIZE_7K = { fxLots: 3.5, goldLots: 0.3 }

describe('FX P&L', () => {
  it('values 20 pips at 3.5 lots as $700', () => {
    expect(calculateFxPnl(20, 3.5, S.fxPipValuePerLot)).toBe(700)
  })

  it('handles negative pips', () => {
    expect(calculateFxPnl(-8, 3.5, S.fxPipValuePerLot)).toBe(-280)
  })

  it('scales with the tier lot size', () => {
    expect(calculateFxPnl(20, 5, S.fxPipValuePerLot)).toBe(1000)
    expect(calculateFxPnl(20, 50, S.fxPipValuePerLot)).toBe(10_000)
  })
})

describe('Gold P&L', () => {
  it('values a $15 move at 0.30 lot as $450', () => {
    expect(calculateGoldPnl(15, 0.3, S.goldContractSize)).toBe(450)
  })

  it('handles a negative move', () => {
    expect(calculateGoldPnl(-12, 0.3, S.goldContractSize)).toBeCloseTo(-360, 10)
  })

  it('is a price movement, not a dollar P&L', () => {
    // "+15 $" on Gold is NOT +$15 of P&L.
    expect(calculateGoldPnl(15, 0.3, S.goldContractSize)).not.toBe(15)
  })
})

describe('day summary', () => {
  it('sums EU +20, GU +20 and Gold +15 to $1,850 gross', () => {
    const day = createDayEntry('2026-09-21', {
      eurusdPips: 20,
      gbpusdPips: 20,
      xauusdMove: 15,
    })
    const r = calculateDaySummaryPnl(day, SIZE_7K, S)
    expect(r.eurusd).toBe(700)
    expect(r.gbpusd).toBe(700)
    expect(r.xauusd).toBe(450)
    expect(r.gross).toBe(1850)
    expect(r.net).toBe(1850)
  })

  it('subtracts commission, swap and other fees from the gross', () => {
    const day = createDayEntry('2026-09-21', {
      eurusdPips: 20,
      gbpusdPips: 20,
      xauusdMove: 15,
      commission: 20,
      swap: 5,
      fees: 25,
    })
    const r = calculateDaySummaryPnl(day, SIZE_7K, S)
    expect(r.gross).toBe(1850)
    expect(r.fees).toBe(50)
    expect(r.net).toBe(1800)
  })

  it('produces a negative net on a losing day', () => {
    const day = createDayEntry('2026-09-22', {
      eurusdPips: -14,
      gbpusdPips: -6,
      xauusdMove: -9,
    })
    const r = calculateDaySummaryPnl(day, SIZE_7K, S)
    expect(r.gross).toBeCloseTo(-970, 10)
  })
})

describe('required results', () => {
  it('needs 70 pips of FX alone for a $2,450 target at 3.5 lots', () => {
    expect(calculateRequiredPips(2450, 3.5, S.fxPipValuePerLot)).toBe(70)
  })

  it('needs ~$81.6667 of Gold movement alone for the same target at 0.30 lot', () => {
    expect(calculateRequiredGoldMove(2450, 0.3, S.goldContractSize)).toBeCloseTo(81.6667, 4)
  })

  it('returns Infinity when the size is zero', () => {
    expect(calculateRequiredPips(100, 0, S.fxPipValuePerLot)).toBe(Infinity)
    expect(calculateRequiredGoldMove(100, 0, S.goldContractSize)).toBe(Infinity)
  })
})

describe('full position equivalent', () => {
  it('converts a scaled-out P&L back into full-size pips', () => {
    // $350 realised while a full 3.5-lot position would have needed 10 pips.
    expect(fullPositionEquivalentPips(350, 3.5, S.fxPipValuePerLot)).toBe(10)
  })

  it('converts a Gold P&L back into full-size dollars of movement', () => {
    expect(fullPositionEquivalentGoldMove(450, 0.3, S.goldContractSize)).toBe(15)
  })
})
