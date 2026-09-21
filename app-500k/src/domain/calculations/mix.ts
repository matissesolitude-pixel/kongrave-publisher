import type { InstrumentId, Settings } from '@/domain/models/types'
import {
  calculateRequiredGoldMove,
  calculateRequiredPips,
  instrumentPnl,
  type PositionSize,
} from './pnl'

/**
 * Mix calculator.
 *
 * Weights are shares of the *P&L contribution*, never shares of raw pips —
 * "balanced" means each instrument brings the same number of dollars.
 */

export type MixPresetId =
  | 'eu'
  | 'gu'
  | 'gold'
  | 'fx5050'
  | 'balanced'
  | 'fxDominant'
  | 'goldDominant'
  | 'custom'

export type Weights = Record<InstrumentId, number>

export interface MixPreset {
  id: MixPresetId
  label: string
  weights: Weights | null
}

export const MIX_PRESETS: MixPreset[] = [
  { id: 'eu', label: '100% EU', weights: { EURUSD: 1, GBPUSD: 0, XAUUSD: 0 } },
  { id: 'gu', label: '100% GU', weights: { EURUSD: 0, GBPUSD: 1, XAUUSD: 0 } },
  { id: 'gold', label: '100% Gold', weights: { EURUSD: 0, GBPUSD: 0, XAUUSD: 1 } },
  { id: 'fx5050', label: 'EU + GU 50/50', weights: { EURUSD: 0.5, GBPUSD: 0.5, XAUUSD: 0 } },
  {
    id: 'balanced',
    label: 'Balanced',
    weights: { EURUSD: 1 / 3, GBPUSD: 1 / 3, XAUUSD: 1 / 3 },
  },
  {
    id: 'fxDominant',
    label: 'FX dominant',
    weights: { EURUSD: 0.4, GBPUSD: 0.4, XAUUSD: 0.2 },
  },
  {
    id: 'goldDominant',
    label: 'Gold dominant',
    weights: { EURUSD: 0.2, GBPUSD: 0.2, XAUUSD: 0.6 },
  },
  { id: 'custom', label: 'Custom', weights: null },
]

export interface MixInput {
  /** Amount still to produce, in dollars. */
  target: number
  size: PositionSize
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>
  /**
   * Instruments whose raw result is fixed by the user (pips for FX, $ of
   * movement for Gold). Their P&L is subtracted from the target first.
   */
  locked: Partial<Record<InstrumentId, number>>
  /** Contribution weights for the unlocked instruments. Normalised internally. */
  weights: Weights
}

export interface MixResult {
  /** Raw result required per instrument: pips for FX, $ of movement for Gold. */
  required: Record<InstrumentId, number>
  /** Dollar contribution per instrument. */
  contribution: Record<InstrumentId, number>
  lockedPnl: number
  /** Target left after the locked legs. */
  remaining: number
  total: number
  /** `true` when every unlocked weight is zero and money is still missing. */
  unreachable: boolean
}

const ZERO: Record<InstrumentId, number> = { EURUSD: 0, GBPUSD: 0, XAUUSD: 0 }

function rawResultFor(
  instrument: InstrumentId,
  amount: number,
  size: PositionSize,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): number {
  if (instrument === 'XAUUSD') {
    return calculateRequiredGoldMove(amount, size.goldLots, settings.goldContractSize)
  }
  return calculateRequiredPips(amount, size.fxLots, settings.fxPipValuePerLot)
}

export function solveMix(input: MixInput): MixResult {
  const { target, size, settings, locked, weights } = input
  const required: Record<InstrumentId, number> = { ...ZERO }
  const contribution: Record<InstrumentId, number> = { ...ZERO }

  let lockedPnl = 0
  const free: InstrumentId[] = []
  for (const instrument of ['EURUSD', 'GBPUSD', 'XAUUSD'] as const) {
    const lockedValue = locked[instrument]
    if (lockedValue !== undefined) {
      const pnl = instrumentPnl(instrument, lockedValue, size, settings)
      required[instrument] = lockedValue
      contribution[instrument] = pnl
      lockedPnl += pnl
    } else {
      free.push(instrument)
    }
  }

  const remaining = target - lockedPnl
  const weightSum = free.reduce((s, i) => s + Math.max(0, weights[i]), 0)

  if (weightSum <= 0) {
    return {
      required,
      contribution,
      lockedPnl,
      remaining,
      total: lockedPnl,
      unreachable: Math.abs(remaining) > 1e-9,
    }
  }

  for (const instrument of free) {
    const share = (Math.max(0, weights[instrument]) / weightSum) * remaining
    contribution[instrument] = share
    required[instrument] = share === 0 ? 0 : rawResultFor(instrument, share, size, settings)
  }

  const total =
    contribution.EURUSD + contribution.GBPUSD + contribution.XAUUSD

  return { required, contribution, lockedPnl, remaining, total, unreachable: false }
}

/** P&L of an explicit mix of raw results. */
export function evaluateMix(
  results: Record<InstrumentId, number>,
  size: PositionSize,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): { perInstrument: Record<InstrumentId, number>; total: number } {
  const perInstrument: Record<InstrumentId, number> = {
    EURUSD: instrumentPnl('EURUSD', results.EURUSD, size, settings),
    GBPUSD: instrumentPnl('GBPUSD', results.GBPUSD, size, settings),
    XAUUSD: instrumentPnl('XAUUSD', results.XAUUSD, size, settings),
  }
  return {
    perInstrument,
    total: perInstrument.EURUSD + perInstrument.GBPUSD + perInstrument.XAUUSD,
  }
}
