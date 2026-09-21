import { DEFAULT_SETTINGS } from '@/domain/models/defaults'
import { createCashflow, createDayEntry, createTrade } from '@/domain/models/factories'
import {
  SCHEMA_VERSION,
  type BackupPayload,
  type Cashflow,
  type CashflowType,
  type DayEntry,
  type InstrumentId,
  type Settings,
  type Trade,
  type TradeOutcome,
} from '@/domain/models/types'
import { isValidIsoDate } from '@/utils/date'

/**
 * Backup import / export.
 *
 * Imported data is validated against the schema *before* it is allowed to touch
 * the database, and the payload carries a schema version so future migrations
 * have something to key off.
 */

export interface ValidationResult {
  ok: boolean
  errors: string[]
  warnings: string[]
  payload: BackupPayload | null
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function num(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function nullableNum(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function str(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function bool(value: unknown, fallback = false): boolean {
  return typeof value === 'boolean' ? value : fallback
}

const INSTRUMENT_SET = new Set<string>(['EURUSD', 'GBPUSD', 'XAUUSD'])
const OUTCOME_SET = new Set<string>(['W', 'L', 'BE'])
const CASHFLOW_SET = new Set<string>(['deposit', 'withdrawal', 'fee', 'manual_adjustment'])

export function validateBackup(raw: unknown): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (!isRecord(raw)) {
    return { ok: false, errors: ['File is not a JSON object.'], warnings, payload: null }
  }
  if (raw.app !== '500k') {
    errors.push('Not a 500K backup file (missing "app": "500k").')
  }
  const version = num(raw.schemaVersion, -1)
  if (version < 0) errors.push('Missing or invalid "schemaVersion".')
  if (version > SCHEMA_VERSION) {
    errors.push(
      `Backup schema v${version} is newer than this app (v${SCHEMA_VERSION}). Update the app first.`,
    )
  }
  if (errors.length > 0) return { ok: false, errors, warnings, payload: null }

  const settings = parseSettings(raw.settings, warnings)

  const days: DayEntry[] = []
  for (const [i, item] of asArray(raw.days).entries()) {
    const parsed = parseDay(item)
    if (parsed) days.push(parsed)
    else warnings.push(`days[${i}] skipped: invalid date.`)
  }

  const trades: Trade[] = []
  for (const [i, item] of asArray(raw.trades).entries()) {
    const parsed = parseTrade(item)
    if (parsed) trades.push(parsed)
    else warnings.push(`trades[${i}] skipped: invalid date or instrument.`)
  }

  const cashflows: Cashflow[] = []
  for (const [i, item] of asArray(raw.cashflows).entries()) {
    const parsed = parseCashflow(item)
    if (parsed) cashflows.push(parsed)
    else warnings.push(`cashflows[${i}] skipped: invalid date or type.`)
  }

  return {
    ok: true,
    errors,
    warnings,
    payload: {
      app: '500k',
      schemaVersion: SCHEMA_VERSION,
      exportedAt: str(raw.exportedAt, new Date().toISOString()),
      settings,
      days,
      trades,
      cashflows,
    },
  }
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function parseSettings(raw: unknown, warnings: string[]): Settings {
  if (!isRecord(raw)) {
    warnings.push('No settings in backup — defaults used.')
    return { ...DEFAULT_SETTINGS }
  }
  const merged: Settings = { ...DEFAULT_SETTINGS, ...(raw as Partial<Settings>) }
  merged.schemaVersion = SCHEMA_VERSION
  if (!isValidIsoDate(merged.startDate)) merged.startDate = DEFAULT_SETTINGS.startDate
  if (!isValidIsoDate(merged.targetDate)) merged.targetDate = DEFAULT_SETTINGS.targetDate
  if (!Array.isArray(merged.tiers) || merged.tiers.length === 0) {
    merged.tiers = DEFAULT_SETTINGS.tiers
    warnings.push('Sizing tiers missing or empty — defaults used.')
  }
  if (!merged.scaleOut?.legs) merged.scaleOut = DEFAULT_SETTINGS.scaleOut
  return merged
}

function parseDay(raw: unknown): DayEntry | null {
  if (!isRecord(raw) || !isValidIsoDate(raw.date)) return null
  const base = createDayEntry(raw.date)
  return {
    ...base,
    eurusdPips: num(raw.eurusdPips),
    gbpusdPips: num(raw.gbpusdPips),
    xauusdMove: num(raw.xauusdMove),
    fees: num(raw.fees),
    commission: num(raw.commission),
    swap: num(raw.swap),
    notes: str(raw.notes),
    pnlSource: raw.pnlSource === 'trades' ? 'trades' : 'daily',
    manualWins: nullableNum(raw.manualWins),
    manualLosses: nullableNum(raw.manualLosses),
    fxLotsUsed: nullableNum(raw.fxLotsUsed),
    goldLotsUsed: nullableNum(raw.goldLotsUsed),
    executionScore: nullableNum(raw.executionScore),
    disciplineScore: nullableNum(raw.disciplineScore),
    emotion: (typeof raw.emotion === 'string' ? raw.emotion : null) as DayEntry['emotion'],
    whatHappened: str(raw.whatHappened),
    checklist: isRecord(raw.checklist)
      ? {
          planFollowed: bool(raw.checklist.planFollowed),
          maxLossesRespected: bool(raw.checklist.maxLossesRespected),
          noRevengeTrade: bool(raw.checklist.noRevengeTrade),
          correctSizing: bool(raw.checklist.correctSizing),
          onlyValidSetups: bool(raw.checklist.onlyValidSetups),
        }
      : null,
    createdAt: num(raw.createdAt, base.createdAt),
    updatedAt: num(raw.updatedAt, base.updatedAt),
  }
}

function parseTrade(raw: unknown): Trade | null {
  if (!isRecord(raw) || !isValidIsoDate(raw.date)) return null
  if (typeof raw.instrument !== 'string' || !INSTRUMENT_SET.has(raw.instrument)) return null
  const base = createTrade(raw.date, raw.instrument as InstrumentId)
  return {
    ...base,
    id: str(raw.id, base.id),
    time: typeof raw.time === 'string' ? raw.time : null,
    direction: raw.direction === 'short' ? 'short' : 'long',
    result: num(raw.result),
    lots: num(raw.lots),
    actualPnl: nullableNum(raw.actualPnl),
    outcome:
      typeof raw.outcome === 'string' && OUTCOME_SET.has(raw.outcome)
        ? (raw.outcome as TradeOutcome)
        : 'BE',
    fees: num(raw.fees),
    rMultiple: nullableNum(raw.rMultiple),
    stopLoss: nullableNum(raw.stopLoss),
    plannedTarget: nullableNum(raw.plannedTarget),
    targetHit: typeof raw.targetHit === 'boolean' ? raw.targetHit : null,
    setup: str(raw.setup),
    session: str(raw.session),
    comment: str(raw.comment),
    tradingError: bool(raw.tradingError),
    mfe: nullableNum(raw.mfe),
    mae: nullableNum(raw.mae),
    initialRisk: nullableNum(raw.initialRisk),
    exitReason: str(raw.exitReason),
    screenshot: typeof raw.screenshot === 'string' ? raw.screenshot : null,
    createdAt: num(raw.createdAt, base.createdAt),
    updatedAt: num(raw.updatedAt, base.updatedAt),
  }
}

function parseCashflow(raw: unknown): Cashflow | null {
  if (!isRecord(raw) || !isValidIsoDate(raw.date)) return null
  if (typeof raw.type !== 'string' || !CASHFLOW_SET.has(raw.type)) return null
  const base = createCashflow(raw.date, raw.type as CashflowType, num(raw.amount))
  return {
    ...base,
    id: str(raw.id, base.id),
    note: str(raw.note),
    createdAt: num(raw.createdAt, base.createdAt),
    updatedAt: num(raw.updatedAt, base.updatedAt),
  }
}

export function buildBackup(data: {
  settings: Settings
  days: DayEntry[]
  trades: Trade[]
  cashflows: Cashflow[]
}): BackupPayload {
  return {
    app: '500k',
    schemaVersion: SCHEMA_VERSION,
    exportedAt: new Date().toISOString(),
    settings: data.settings,
    days: data.days,
    trades: data.trades,
    cashflows: data.cashflows,
  }
}

// --- CSV ---------------------------------------------------------------

function csvEscape(value: string | number | boolean | null): string {
  const s = value === null ? '' : String(value)
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export function daysToCsv(days: DayEntry[]): string {
  const header = [
    'date',
    'eurusd_pips',
    'gbpusd_pips',
    'xauusd_move',
    'commission',
    'swap',
    'other_fees',
    'pnl_source',
    'manual_wins',
    'manual_losses',
    'execution_score',
    'discipline_score',
    'emotion',
    'notes',
    'what_happened',
  ]
  const rows = [...days]
    .sort((a, b) => (a.date < b.date ? -1 : 1))
    .map((d) =>
      [
        d.date,
        d.eurusdPips,
        d.gbpusdPips,
        d.xauusdMove,
        d.commission,
        d.swap,
        d.fees,
        d.pnlSource,
        d.manualWins,
        d.manualLosses,
        d.executionScore,
        d.disciplineScore,
        d.emotion,
        d.notes,
        d.whatHappened,
      ]
        .map(csvEscape)
        .join(','),
    )
  return [header.join(','), ...rows].join('\n')
}

export function tradesToCsv(trades: Trade[]): string {
  const header = [
    'id',
    'date',
    'time',
    'instrument',
    'direction',
    'result',
    'lots',
    'actual_pnl',
    'outcome',
    'fees',
    'r_multiple',
    'stop_loss',
    'planned_target',
    'target_hit',
    'setup',
    'session',
    'trading_error',
    'mfe',
    'mae',
    'initial_risk',
    'exit_reason',
    'comment',
  ]
  const rows = [...trades]
    .sort((a, b) => (a.date < b.date ? -1 : 1))
    .map((t) =>
      [
        t.id,
        t.date,
        t.time,
        t.instrument,
        t.direction,
        t.result,
        t.lots,
        t.actualPnl,
        t.outcome,
        t.fees,
        t.rMultiple,
        t.stopLoss,
        t.plannedTarget,
        t.targetHit,
        t.setup,
        t.session,
        t.tradingError,
        t.mfe,
        t.mae,
        t.initialRisk,
        t.exitReason,
        t.comment,
      ]
        .map(csvEscape)
        .join(','),
    )
  return [header.join(','), ...rows].join('\n')
}

export function cashflowsToCsv(cashflows: Cashflow[]): string {
  const header = ['id', 'date', 'type', 'amount', 'note']
  const rows = [...cashflows]
    .sort((a, b) => (a.date < b.date ? -1 : 1))
    .map((c) => [c.id, c.date, c.type, c.amount, c.note].map(csvEscape).join(','))
  return [header.join(','), ...rows].join('\n')
}
