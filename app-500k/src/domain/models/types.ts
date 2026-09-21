/**
 * Domain model for the 500K trading challenge tracker.
 *
 * Every financial assumption lives in `Settings` so it stays visible and editable.
 * Nothing in here invents a value the user has not supplied or configured.
 */

/** Current persisted schema version. Bump when a migration is required. */
export const SCHEMA_VERSION = 1

export type InstrumentId = 'EURUSD' | 'GBPUSD' | 'XAUUSD'

export const INSTRUMENTS: readonly InstrumentId[] = ['EURUSD', 'GBPUSD', 'XAUUSD']

/** Instruments quoted in pips vs. instruments quoted in dollars of price movement. */
export const FX_INSTRUMENTS: readonly InstrumentId[] = ['EURUSD', 'GBPUSD']

export const INSTRUMENT_LABEL: Record<InstrumentId, string> = {
  EURUSD: 'EURUSD',
  GBPUSD: 'GBPUSD',
  XAUUSD: 'XAUUSD',
}

export const INSTRUMENT_SHORT: Record<InstrumentId, string> = {
  EURUSD: 'EU',
  GBPUSD: 'GU',
  XAUUSD: 'Gold',
}

/** `YYYY-MM-DD`, always a *local* calendar date (never a UTC instant). */
export type IsoDate = string

export type TradeDirection = 'long' | 'short'
export type TradeOutcome = 'W' | 'L' | 'BE'

export type Emotion =
  | 'calm'
  | 'confident'
  | 'hesitant'
  | 'fomo'
  | 'frustrated'
  | 'revenge'
  | 'tired'
  | 'other'

export const EMOTIONS: readonly Emotion[] = [
  'calm',
  'confident',
  'hesitant',
  'fomo',
  'frustrated',
  'revenge',
  'tired',
  'other',
]

export const EMOTION_LABEL: Record<Emotion, string> = {
  calm: 'Calm',
  confident: 'Confident',
  hesitant: 'Hesitant',
  fomo: 'FOMO',
  frustrated: 'Frustrated',
  revenge: 'Revenge',
  tired: 'Tired',
  other: 'Other',
}

/** One row of the editable position-sizing ladder. */
export interface SizingTier {
  /** Equity at which this tier becomes active (inclusive). */
  minEquity: number
  /** Max FX lots (EURUSD / GBPUSD) at this tier. */
  fxLots: number
  /** Gold lots (XAUUSD) at this tier. */
  goldLots: number
}

export type SizingMode = 'continuous' | 'tiers'
export type FxSizingExposure = 'perInstrument' | 'sharedTotal'
export type TierApplyMode = 'immediate' | 'nextDay' | 'nextWeek'
export type WeeklyTargetMode = 'compound' | 'fixedRate'
export type WinRateConvention = 'excludeBE' | 'includeBE'
/** 0 = Sunday … 6 = Saturday. */
export type WeekStartDay = 0 | 1 | 2 | 3 | 4 | 5 | 6

export interface ScaleOutLeg {
  /** First take-profit level: pips for FX, dollars of movement for Gold. */
  firstTakeProfit: number
  /** Percentage of the position closed at the first take profit (0-100). */
  closedPct: number
  /** Percentage left running towards the final target (0-100). */
  runnerPct: number
}

export interface ScaleOutSettings {
  enabled: boolean
  legs: Record<InstrumentId, ScaleOutLeg>
}

export interface Settings {
  schemaVersion: number

  // --- Challenge ---
  startingCapital: number
  targetCapital: number
  startDate: IsoDate
  targetDate: IsoDate

  // --- Weekly target methodology ---
  weeklyTargetMode: WeeklyTargetMode
  /** Used when `weeklyTargetMode === 'fixedRate'`. 0.35 = +35 %/week. */
  fixedWeeklyRate: number

  // --- Sizing ---
  sizingMode: SizingMode
  /** MODE A: fxLots = equity / fxSizingDivisor. */
  fxSizingDivisor: number
  fxSizingExposure: FxSizingExposure
  tiers: SizingTier[]
  tierApplyMode: TierApplyMode
  /** Manual override, `null` = derive from equity. */
  manualFxLots: number | null
  manualGoldLots: number | null

  // --- Contract specifications ---
  /** USD per pip for one standard FX lot. */
  fxPipValuePerLot: number
  /** Ounces per Gold lot (1 lot = 100 oz => $1 move = $100 per lot). */
  goldContractSize: number

  // --- Rules ---
  dailyLossLimit: number
  weekStart: WeekStartDay
  scaleOut: ScaleOutSettings

  // --- Presentation / conventions ---
  currency: string
  theme: 'dark' | 'light'
  winRateConvention: WinRateConvention
  reduceMotion: boolean
}

export interface RuleChecklist {
  planFollowed: boolean
  maxLossesRespected: boolean
  noRevengeTrade: boolean
  correctSizing: boolean
  onlyValidSetups: boolean
}

export const CHECKLIST_LABEL: Record<keyof RuleChecklist, string> = {
  planFollowed: 'Plan followed',
  maxLossesRespected: 'Max 3 losses respected',
  noRevengeTrade: 'No revenge trade',
  correctSizing: 'Correct sizing',
  onlyValidSetups: 'Only valid setups',
}

/** Which ledger source produces the P&L of a given day. Never summed together. */
export type DayPnlSource = 'daily' | 'trades'

/** A quick daily summary entry — the primary, 15-second logging path. */
export interface DayEntry {
  /** Primary key: local calendar date. */
  date: IsoDate
  eurusdPips: number
  gbpusdPips: number
  xauusdMove: number
  /** Commission + swap + other fees for the day (positive number = cost). */
  fees: number
  commission: number
  swap: number
  notes: string

  /** Whether the day's P&L comes from this summary or from its detailed trades. */
  pnlSource: DayPnlSource

  /**
   * Optional counters for the quick path (no detailed trades).
   * Used only for the daily loss-limit display — never for win-rate statistics.
   */
  manualWins: number | null
  manualLosses: number | null

  /** Sizing actually used that day; `null` = derive from the equity curve. */
  fxLotsUsed: number | null
  goldLotsUsed: number | null

  // --- Psychology / discipline (all optional) ---
  executionScore: number | null
  disciplineScore: number | null
  emotion: Emotion | null
  whatHappened: string
  checklist: RuleChecklist | null

  createdAt: number
  updatedAt: number
}

export interface Trade {
  id: string
  date: IsoDate
  /** `HH:MM`, optional. */
  time: string | null
  instrument: InstrumentId
  direction: TradeDirection
  /** Pips for FX, dollars of Gold price movement for XAUUSD. */
  result: number
  lots: number
  /** Overrides the theoretical P&L in statistics when set. */
  actualPnl: number | null
  outcome: TradeOutcome
  fees: number

  rMultiple: number | null
  /** Stop distance: pips for FX, dollars of movement for Gold. */
  stopLoss: number | null
  plannedTarget: number | null
  targetHit: boolean | null

  setup: string
  session: string
  comment: string
  tradingError: boolean

  /** Reserved for later analytics — optional everywhere in V1. */
  mfe: number | null
  mae: number | null
  initialRisk: number | null
  exitReason: string

  /** Data URL of an optional screenshot, stored locally. */
  screenshot: string | null

  createdAt: number
  updatedAt: number
}

export type CashflowType = 'deposit' | 'withdrawal' | 'fee' | 'manual_adjustment'

export const CASHFLOW_LABEL: Record<CashflowType, string> = {
  deposit: 'Deposit',
  withdrawal: 'Withdrawal',
  fee: 'Fee',
  manual_adjustment: 'Manual adjustment',
}

export interface Cashflow {
  id: string
  date: IsoDate
  type: CashflowType
  /**
   * Always stored as entered. Effect on equity:
   * deposit `+amount`, withdrawal `-amount`, fee `-amount`,
   * manual_adjustment `+amount` (may be negative).
   */
  amount: number
  note: string
  createdAt: number
  updatedAt: number
}

/** Full snapshot used by export / import. */
export interface BackupPayload {
  app: '500k'
  schemaVersion: number
  exportedAt: string
  settings: Settings
  days: DayEntry[]
  trades: Trade[]
  cashflows: Cashflow[]
}
