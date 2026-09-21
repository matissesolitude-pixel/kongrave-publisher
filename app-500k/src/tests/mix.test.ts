import { describe, expect, it } from 'vitest'
import { evaluateMix, solveMix } from '@/domain/calculations/mix'
import { DEFAULT_SETTINGS } from '@/domain/models/defaults'

const S = DEFAULT_SETTINGS
const SIZE = { fxLots: 3.5, goldLots: 0.3 }

describe('mix evaluation', () => {
  it('values EU +20 / GU +20 / Gold +15 at $1,850', () => {
    const r = evaluateMix({ EURUSD: 20, GBPUSD: 20, XAUUSD: 15 }, SIZE, S)
    expect(r.total).toBe(1850)
  })
})

describe('mix solving', () => {
  it('puts the whole target on one instrument at 100 % weight', () => {
    const r = solveMix({
      target: 2450,
      size: SIZE,
      settings: S,
      locked: {},
      weights: { EURUSD: 1, GBPUSD: 0, XAUUSD: 0 },
    })
    expect(r.required.EURUSD).toBe(70)
    expect(r.required.GBPUSD).toBe(0)
    expect(r.required.XAUUSD).toBe(0)
  })

  it('balances by equal dollar contribution, not by equal pips', () => {
    const r = solveMix({
      target: 2450,
      size: SIZE,
      settings: S,
      locked: {},
      weights: { EURUSD: 1 / 3, GBPUSD: 1 / 3, XAUUSD: 1 / 3 },
    })
    expect(r.contribution.EURUSD).toBeCloseTo(2450 / 3, 10)
    expect(r.contribution.XAUUSD).toBeCloseTo(2450 / 3, 10)
    expect(r.required.EURUSD).toBeCloseTo(70 / 3, 10)
    expect(r.required.XAUUSD).toBeCloseTo(81.6667 / 3, 3)
    // Same dollars, different raw numbers.
    expect(r.required.EURUSD).not.toBeCloseTo(r.required.XAUUSD, 3)
  })

  it('subtracts a locked leg before splitting the rest', () => {
    const r = solveMix({
      target: 2450,
      size: SIZE,
      settings: S,
      locked: { XAUUSD: 15 },
      weights: { EURUSD: 0.5, GBPUSD: 0.5, XAUUSD: 0 },
    })
    expect(r.lockedPnl).toBe(450)
    expect(r.remaining).toBe(2000)
    expect(r.contribution.EURUSD).toBe(1000)
    expect(r.required.EURUSD).toBeCloseTo(1000 / 35, 10)
    expect(r.required.GBPUSD).toBeCloseTo(1000 / 35, 10)
  })

  it('flags an unreachable allocation when every free weight is zero', () => {
    const r = solveMix({
      target: 1000,
      size: SIZE,
      settings: S,
      locked: {},
      weights: { EURUSD: 0, GBPUSD: 0, XAUUSD: 0 },
    })
    expect(r.unreachable).toBe(true)
  })
})
