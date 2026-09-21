import { SCHEMA_VERSION, type ScaleOutSettings, type Settings, type SizingTier } from './types'

/**
 * Initial sizing ladder supplied by the user.
 * Editable in Settings — never treated as immutable by the calculations.
 */
export const DEFAULT_TIERS: SizingTier[] = [
  { minEquity: 7_000, fxLots: 3.5, goldLots: 0.3 },
  { minEquity: 10_000, fxLots: 5, goldLots: 0.4 },
  { minEquity: 15_000, fxLots: 7.5, goldLots: 0.6 },
  { minEquity: 20_000, fxLots: 10, goldLots: 0.85 },
  { minEquity: 30_000, fxLots: 15, goldLots: 1.25 },
  { minEquity: 50_000, fxLots: 25, goldLots: 2.1 },
  { minEquity: 75_000, fxLots: 37.5, goldLots: 3.2 },
  { minEquity: 100_000, fxLots: 50, goldLots: 4.25 },
  { minEquity: 150_000, fxLots: 75, goldLots: 6.4 },
  { minEquity: 200_000, fxLots: 100, goldLots: 8.5 },
  { minEquity: 300_000, fxLots: 150, goldLots: 12.75 },
  { minEquity: 400_000, fxLots: 200, goldLots: 17 },
  { minEquity: 500_000, fxLots: 250, goldLots: 21 },
]

export const DEFAULT_SCALE_OUT: ScaleOutSettings = {
  enabled: false,
  legs: {
    EURUSD: { firstTakeProfit: 10, closedPct: 60, runnerPct: 40 },
    GBPUSD: { firstTakeProfit: 12, closedPct: 60, runnerPct: 40 },
    XAUUSD: { firstTakeProfit: 15, closedPct: 60, runnerPct: 40 },
  },
}

export const DEFAULT_SETTINGS: Settings = {
  schemaVersion: SCHEMA_VERSION,

  startingCapital: 7_000,
  targetCapital: 500_000,
  startDate: '2026-09-21',
  targetDate: '2027-01-01',

  weeklyTargetMode: 'compound',
  fixedWeeklyRate: 0.35,

  sizingMode: 'tiers',
  fxSizingDivisor: 2_000,
  fxSizingExposure: 'perInstrument',
  tiers: DEFAULT_TIERS,
  tierApplyMode: 'immediate',
  manualFxLots: null,
  manualGoldLots: null,

  fxPipValuePerLot: 10,
  goldContractSize: 100,

  dailyLossLimit: 3,
  weekStart: 1,
  scaleOut: DEFAULT_SCALE_OUT,

  currency: 'USD',
  theme: 'dark',
  winRateConvention: 'excludeBE',
  reduceMotion: false,
}

export const DISCLAIMER =
  '500K is a personal tracking and calculation tool. Targets are mathematical tracking goals, not predictions or guarantees of future trading performance.'
