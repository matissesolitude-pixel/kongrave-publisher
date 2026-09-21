import type { PositionSize } from '@/domain/calculations/pnl'
import type { Settings, SizingTier } from '@/domain/models/types'

/**
 * Position sizing.
 *
 * MODE "tiers"      — lots stay frozen at the active ladder row until the next
 *                     tier is reached.
 * MODE "continuous" — FX lots = equity / divisor (e.g. $7,000 => 3.5 lots).
 *                     Gold has no linear formula, so it is interpolated from the
 *                     same editable ladder rather than from a hidden constant.
 */

export function sortTiers(tiers: SizingTier[]): SizingTier[] {
  return [...tiers].sort((a, b) => a.minEquity - b.minEquity)
}

/** The active ladder row for an equity value, or `null` when the ladder is empty. */
export function getSizingTier(equity: number, tiers: SizingTier[]): SizingTier | null {
  const sorted = sortTiers(tiers)
  if (sorted.length === 0) return null
  let active: SizingTier = sorted[0] as SizingTier
  for (const tier of sorted) {
    if (equity >= tier.minEquity) active = tier
    else break
  }
  return active
}

/** The next ladder row above `equity`, or `null` when already at the top. */
export function getNextTier(equity: number, tiers: SizingTier[]): SizingTier | null {
  const sorted = sortTiers(tiers)
  return sorted.find((t) => t.minEquity > equity) ?? null
}

/** Progress (0-1) from the active tier towards the next one. */
export function tierProgress(equity: number, tiers: SizingTier[]): number {
  const current = getSizingTier(equity, tiers)
  const next = getNextTier(equity, tiers)
  if (!current || !next) return 1
  const span = next.minEquity - current.minEquity
  if (span <= 0) return 1
  return clamp01((equity - current.minEquity) / span)
}

function clamp01(v: number): number {
  return Math.min(1, Math.max(0, v))
}

/**
 * Gold lots for an arbitrary equity, interpolated linearly between the two
 * surrounding ladder rows. Below the first row / above the last one the ratio of
 * the nearest row is used. Everything derives from the editable table.
 */
export function interpolateGoldLots(equity: number, tiers: SizingTier[]): number {
  const sorted = sortTiers(tiers)
  const first = sorted[0]
  const last = sorted[sorted.length - 1]
  if (!first || !last) return 0
  if (equity <= first.minEquity) {
    return first.minEquity === 0 ? first.goldLots : (equity / first.minEquity) * first.goldLots
  }
  if (equity >= last.minEquity) {
    return last.minEquity === 0 ? last.goldLots : (equity / last.minEquity) * last.goldLots
  }
  for (let i = 0; i < sorted.length - 1; i += 1) {
    const lo = sorted[i] as SizingTier
    const hi = sorted[i + 1] as SizingTier
    if (equity >= lo.minEquity && equity <= hi.minEquity) {
      const span = hi.minEquity - lo.minEquity
      if (span <= 0) return lo.goldLots
      const t = (equity - lo.minEquity) / span
      return lo.goldLots + t * (hi.goldLots - lo.goldLots)
    }
  }
  return last.goldLots
}

export type SizingSettings = Pick<
  Settings,
  'sizingMode' | 'fxSizingDivisor' | 'tiers' | 'manualFxLots' | 'manualGoldLots'
>

/** Resolves the position size to use for a given equity. */
export function resolveSize(equity: number, settings: SizingSettings): PositionSize {
  const tier = getSizingTier(equity, settings.tiers)

  let fxLots: number
  let goldLots: number

  if (settings.sizingMode === 'continuous') {
    fxLots = settings.fxSizingDivisor > 0 ? equity / settings.fxSizingDivisor : 0
    goldLots = interpolateGoldLots(equity, settings.tiers)
  } else {
    fxLots = tier?.fxLots ?? 0
    goldLots = tier?.goldLots ?? 0
  }

  if (settings.manualFxLots !== null) fxLots = settings.manualFxLots
  if (settings.manualGoldLots !== null) goldLots = settings.manualGoldLots

  return { fxLots, goldLots }
}

/**
 * FX size actually applied to one instrument.
 * `sharedTotal` means the FX lots are the *total* exposure split across the two
 * FX instruments; `perInstrument` means each instrument gets the full size.
 */
export function fxLotsForInstrument(
  size: PositionSize,
  exposure: Settings['fxSizingExposure'],
  activeFxInstruments = 2,
): number {
  if (exposure === 'sharedTotal' && activeFxInstruments > 0) {
    return size.fxLots / activeFxInstruments
  }
  return size.fxLots
}
