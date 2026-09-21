import { createTrade } from '@/domain/models/factories'
import type { InstrumentId, IsoDate, Trade, TradeOutcome } from '@/domain/models/types'
import { isValidIsoDate } from '@/utils/date'

/**
 * Generic CSV import with explicit column mapping.
 *
 * Deliberately format-agnostic: it does not try to guess a MetaTrader export
 * layout. The user maps their columns onto these fields, which keeps the door
 * open for any broker statement later on.
 */

export interface ParsedCsv {
  headers: string[]
  rows: string[][]
}

/** RFC-4180-ish parser: handles quotes, embedded commas and CRLF. */
export function parseCsv(text: string, delimiter = ','): ParsedCsv {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let inQuotes = false

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i += 1
        } else {
          inQuotes = false
        }
      } else {
        field += char
      }
      continue
    }
    if (char === '"') {
      inQuotes = true
    } else if (char === delimiter) {
      row.push(field)
      field = ''
    } else if (char === '\n') {
      row.push(field)
      rows.push(row)
      row = []
      field = ''
    } else if (char !== '\r') {
      field += char
    }
  }
  if (field !== '' || row.length > 0) {
    row.push(field)
    rows.push(row)
  }

  const nonEmpty = rows.filter((r) => r.some((c) => c.trim() !== ''))
  const headers = nonEmpty.shift() ?? []
  return { headers: headers.map((h) => h.trim()), rows: nonEmpty }
}

export type TradeField =
  | 'date'
  | 'time'
  | 'instrument'
  | 'direction'
  | 'result'
  | 'lots'
  | 'actualPnl'
  | 'outcome'
  | 'fees'
  | 'setup'
  | 'session'
  | 'comment'

export interface TradeFieldSpec {
  field: TradeField
  label: string
  required: boolean
  hint: string
}

export const TRADE_IMPORT_FIELDS: TradeFieldSpec[] = [
  { field: 'date', label: 'Date', required: true, hint: 'YYYY-MM-DD or DD/MM/YYYY' },
  { field: 'instrument', label: 'Instrument', required: true, hint: 'EURUSD / GBPUSD / XAUUSD' },
  { field: 'result', label: 'Result', required: true, hint: 'pips for FX, $ move for Gold' },
  { field: 'lots', label: 'Lots', required: true, hint: 'position size' },
  { field: 'time', label: 'Time', required: false, hint: 'HH:MM' },
  { field: 'direction', label: 'Direction', required: false, hint: 'long / short / buy / sell' },
  { field: 'actualPnl', label: 'Actual P&L', required: false, hint: 'overrides the computed P&L' },
  { field: 'outcome', label: 'Outcome', required: false, hint: 'W / L / BE — else derived' },
  { field: 'fees', label: 'Fees', required: false, hint: 'commission + swap' },
  { field: 'setup', label: 'Setup', required: false, hint: 'free text' },
  { field: 'session', label: 'Session', required: false, hint: 'free text' },
  { field: 'comment', label: 'Comment', required: false, hint: 'free text' },
]

/** Column index per field. `-1` = not mapped. */
export type ColumnMapping = Partial<Record<TradeField, number>>

export interface CsvImportResult {
  trades: Trade[]
  errors: string[]
  skipped: number
}

const INSTRUMENT_ALIASES: Record<string, InstrumentId> = {
  EURUSD: 'EURUSD',
  EU: 'EURUSD',
  'EUR/USD': 'EURUSD',
  GBPUSD: 'GBPUSD',
  GU: 'GBPUSD',
  'GBP/USD': 'GBPUSD',
  XAUUSD: 'XAUUSD',
  GOLD: 'XAUUSD',
  'XAU/USD': 'XAUUSD',
}

/**
 * Accepts `YYYY-MM-DD`, `DD/MM/YYYY` and `YYYY.MM.DD`, with or without a
 * trailing time. The candidate is validated once, at the end.
 */
function normaliseDate(value: string): IsoDate | null {
  const candidate = toDateCandidate(value.trim())
  return isValidIsoDate(candidate) ? candidate : null
}

function toDateCandidate(v: string): string {
  const slash = /^(\d{1,2})[/.](\d{1,2})[/.](\d{4})/.exec(v)
  if (slash) {
    const [, d = '', m = '', y = ''] = slash
    return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`
  }
  const dotted = /^(\d{4})[.](\d{2})[.](\d{2})/.exec(v)
  if (dotted) return `${dotted[1]}-${dotted[2]}-${dotted[3]}`
  return v.slice(0, 10)
}

function toNumber(value: string | undefined): number | null {
  if (value === undefined) return null
  const cleaned = value.replace(/[\s$]/g, '').replace(/,/g, '.')
  if (cleaned === '') return null
  const n = Number(cleaned)
  return Number.isFinite(n) ? n : null
}

export function buildTradesFromCsv(parsed: ParsedCsv, mapping: ColumnMapping): CsvImportResult {
  const errors: string[] = []
  const trades: Trade[] = []
  let skipped = 0

  const cell = (row: string[], field: TradeField): string | undefined => {
    const index = mapping[field]
    if (index === undefined || index < 0) return undefined
    return row[index]
  }

  parsed.rows.forEach((row, i) => {
    const line = i + 2
    const date = normaliseDate(cell(row, 'date') ?? '')
    if (!date) {
      errors.push(`Line ${line}: unreadable date.`)
      skipped += 1
      return
    }
    const rawInstrument = (cell(row, 'instrument') ?? '').trim().toUpperCase()
    const instrument = INSTRUMENT_ALIASES[rawInstrument]
    if (!instrument) {
      errors.push(`Line ${line}: unknown instrument "${rawInstrument}".`)
      skipped += 1
      return
    }
    const result = toNumber(cell(row, 'result'))
    const lots = toNumber(cell(row, 'lots'))
    if (result === null || lots === null) {
      errors.push(`Line ${line}: result and lots must both be numbers.`)
      skipped += 1
      return
    }

    const actualPnl = toNumber(cell(row, 'actualPnl'))
    const rawOutcome = (cell(row, 'outcome') ?? '').trim().toUpperCase()
    const outcome: TradeOutcome =
      rawOutcome === 'W' || rawOutcome === 'WIN'
        ? 'W'
        : rawOutcome === 'L' || rawOutcome === 'LOSS'
          ? 'L'
          : rawOutcome === 'BE'
            ? 'BE'
            : result > 0
              ? 'W'
              : result < 0
                ? 'L'
                : 'BE'

    const rawDirection = (cell(row, 'direction') ?? '').trim().toLowerCase()
    const direction = rawDirection === 'short' || rawDirection === 'sell' ? 'short' : 'long'
    const time = (cell(row, 'time') ?? '').trim()

    trades.push(
      createTrade(date, instrument, {
        time: /^\d{1,2}:\d{2}/.test(time) ? time.slice(0, 5) : null,
        direction,
        result,
        lots,
        actualPnl,
        outcome,
        fees: toNumber(cell(row, 'fees')) ?? 0,
        setup: (cell(row, 'setup') ?? '').trim(),
        session: (cell(row, 'session') ?? '').trim(),
        comment: (cell(row, 'comment') ?? '').trim(),
      }),
    )
  })

  return { trades, errors, skipped }
}

/** Suggests a column index per field by fuzzy-matching the CSV headers. */
export function guessMapping(headers: string[]): ColumnMapping {
  const norm = headers.map((h) => h.toLowerCase().replace(/[^a-z]/g, ''))
  const find = (...needles: string[]): number =>
    norm.findIndex((h) => needles.some((n) => h.includes(n)))

  return {
    date: find('date', 'opentime', 'time'),
    time: find('time', 'hour'),
    instrument: find('symbol', 'instrument', 'pair', 'asset'),
    direction: find('type', 'direction', 'side'),
    result: find('pips', 'points', 'result'),
    lots: find('lots', 'volume', 'size'),
    actualPnl: find('profit', 'pnl', 'netpl'),
    outcome: find('outcome', 'wl'),
    fees: find('commission', 'swap', 'fees'),
    setup: find('setup', 'strategy'),
    session: find('session'),
    comment: find('comment', 'note'),
  }
}
