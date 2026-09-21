import { describe, expect, it } from 'vitest'
import {
  getNextTier,
  getSizingTier,
  interpolateGoldLots,
  resolveSize,
  fxLotsForInstrument,
} from '@/domain/sizing/sizing'
import { DEFAULT_SETTINGS, DEFAULT_TIERS } from '@/domain/models/defaults'

const S = DEFAULT_SETTINGS

describe('tier lookup', () => {
  it('picks the active tier at and above its threshold', () => {
    expect(getSizingTier(7000, DEFAULT_TIERS)?.fxLots).toBe(3.5)
    expect(getSizingTier(9999, DEFAULT_TIERS)?.fxLots).toBe(3.5)
    expect(getSizingTier(10_000, DEFAULT_TIERS)?.fxLots).toBe(5)
    expect(getSizingTier(500_000, DEFAULT_TIERS)?.fxLots).toBe(250)
  })

  it('falls back to the lowest tier below the ladder', () => {
    expect(getSizingTier(1000, DEFAULT_TIERS)?.fxLots).toBe(3.5)
  })

  it('exposes the next tier', () => {
    expect(getNextTier(7000, DEFAULT_TIERS)?.minEquity).toBe(10_000)
    expect(getNextTier(500_000, DEFAULT_TIERS)).toBeNull()
  })
})

describe('sizing modes', () => {
  it('MODE B freezes the lots until the next tier is reached', () => {
    const settings = { ...S, sizingMode: 'tiers' as const }
    expect(resolveSize(9_999, settings)).toEqual({ fxLots: 3.5, goldLots: 0.3 })
    expect(resolveSize(10_000, settings)).toEqual({ fxLots: 5, goldLots: 0.4 })
  })

  it('MODE A computes FX lots as equity / 2000', () => {
    const settings = { ...S, sizingMode: 'continuous' as const }
    expect(resolveSize(7_000, settings).fxLots).toBe(3.5)
    expect(resolveSize(15_000, settings).fxLots).toBe(7.5)
    expect(resolveSize(100_000, settings).fxLots).toBe(50)
  })

  it('MODE A interpolates Gold from the editable ladder', () => {
    expect(interpolateGoldLots(7_000, DEFAULT_TIERS)).toBeCloseTo(0.3, 10)
    expect(interpolateGoldLots(8_500, DEFAULT_TIERS)).toBeCloseTo(0.35, 10)
    expect(interpolateGoldLots(10_000, DEFAULT_TIERS)).toBeCloseTo(0.4, 10)
  })

  it('honours manual overrides in both modes', () => {
    const settings = { ...S, manualFxLots: 2, manualGoldLots: 0.1 }
    expect(resolveSize(100_000, settings)).toEqual({ fxLots: 2, goldLots: 0.1 })
  })
})

describe('FX exposure mode', () => {
  it('gives each instrument the full size per instrument', () => {
    expect(fxLotsForInstrument({ fxLots: 3.5, goldLots: 0.3 }, 'perInstrument')).toBe(3.5)
  })

  it('splits a shared total across the FX instruments', () => {
    expect(fxLotsForInstrument({ fxLots: 3.5, goldLots: 0.3 }, 'sharedTotal')).toBe(1.75)
  })
})
