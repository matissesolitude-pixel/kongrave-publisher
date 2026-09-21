import { describe, expect, it } from 'vitest'
import { buildBackup, daysToCsv, tradesToCsv, validateBackup } from '@/db/backup'
import { buildTradesFromCsv, guessMapping, parseCsv } from '@/db/csvImport'
import { DEFAULT_SETTINGS } from '@/domain/models/defaults'
import { createCashflow, createDayEntry, createTrade } from '@/domain/models/factories'
import {
  addDays,
  dayOfWeek,
  daysBetween,
  isValidIsoDate,
  startOfWeek,
  weekDates,
} from '@/utils/date'

const settings = DEFAULT_SETTINGS

describe('backup round trip', () => {
  const payload = buildBackup({
    settings,
    days: [createDayEntry('2026-09-21', { eurusdPips: 20 })],
    trades: [createTrade('2026-09-21', 'EURUSD', { result: 20, lots: 3.5 })],
    cashflows: [createCashflow('2026-09-22', 'deposit', 1000)],
  })

  it('validates its own export', () => {
    const result = validateBackup(JSON.parse(JSON.stringify(payload)) as unknown)
    expect(result.ok).toBe(true)
    expect(result.payload?.days).toHaveLength(1)
    expect(result.payload?.trades).toHaveLength(1)
    expect(result.payload?.cashflows).toHaveLength(1)
    expect(result.payload?.days[0]?.eurusdPips).toBe(20)
  })

  it('refuses a file that is not a 500K backup', () => {
    expect(validateBackup({ hello: 'world' }).ok).toBe(false)
    expect(validateBackup('nope').ok).toBe(false)
  })

  it('refuses a backup from a newer schema', () => {
    const result = validateBackup({ ...payload, schemaVersion: 999 })
    expect(result.ok).toBe(false)
    expect(result.errors.join(' ')).toContain('newer')
  })

  it('skips malformed rows with a warning instead of importing them', () => {
    const result = validateBackup({
      ...payload,
      days: [{ date: 'not-a-date' }],
      trades: [{ date: '2026-09-21', instrument: 'DOGE' }],
    })
    expect(result.ok).toBe(true)
    expect(result.payload?.days).toHaveLength(0)
    expect(result.payload?.trades).toHaveLength(0)
    expect(result.warnings.length).toBe(2)
  })
})

describe('CSV export', () => {
  it('quotes fields containing commas', () => {
    const csv = daysToCsv([createDayEntry('2026-09-21', { notes: 'hello, world' })])
    expect(csv.split('\n')[0]).toContain('date')
    expect(csv).toContain('"hello, world"')
  })

  it('exports one row per trade', () => {
    const csv = tradesToCsv([
      createTrade('2026-09-21', 'EURUSD', { result: 20, lots: 3.5 }),
      createTrade('2026-09-22', 'XAUUSD', { result: 15, lots: 0.3 }),
    ])
    expect(csv.split('\n')).toHaveLength(3)
  })
})

describe('CSV import', () => {
  const text = [
    'Time,Symbol,Type,Volume,Pips,Profit',
    '2026-09-21 08:30,EURUSD,buy,3.5,20,700',
    '21/09/2026,XAUUSD,sell,0.3,15,450',
    'oops,EURUSD,buy,1,1,1',
  ].join('\n')

  it('parses headers and rows', () => {
    const parsed = parseCsv(text)
    expect(parsed.headers).toEqual(['Time', 'Symbol', 'Type', 'Volume', 'Pips', 'Profit'])
    expect(parsed.rows).toHaveLength(3)
  })

  it('maps columns and normalises dates, instruments and directions', () => {
    const parsed = parseCsv(text)
    const mapping = { date: 0, instrument: 1, direction: 2, lots: 3, result: 4, actualPnl: 5 }
    const result = buildTradesFromCsv(parsed, mapping)
    expect(result.trades).toHaveLength(2)
    expect(result.skipped).toBe(1)
    expect(result.trades[0]?.date).toBe('2026-09-21')
    expect(result.trades[0]?.direction).toBe('long')
    expect(result.trades[1]?.date).toBe('2026-09-21')
    expect(result.trades[1]?.instrument).toBe('XAUUSD')
    expect(result.trades[1]?.direction).toBe('short')
    expect(result.trades[1]?.outcome).toBe('W')
  })

  it('suggests a mapping from the headers', () => {
    const mapping = guessMapping(parseCsv(text).headers)
    expect(mapping.instrument).toBe(1)
    expect(mapping.lots).toBe(3)
  })

  it('handles quoted fields with embedded commas', () => {
    const parsed = parseCsv('a,b\n"x, y",2')
    expect(parsed.rows[0]).toEqual(['x, y', '2'])
  })
})

describe('local calendar dates', () => {
  it('validates the ISO shape and the calendar itself', () => {
    expect(isValidIsoDate('2026-09-21')).toBe(true)
    expect(isValidIsoDate('2026-02-30')).toBe(false)
    expect(isValidIsoDate('21/09/2026')).toBe(false)
  })

  it('adds days without slipping a day across a timezone boundary', () => {
    expect(addDays('2026-09-21', 1)).toBe('2026-09-22')
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01')
    expect(addDays('2026-09-21', -1)).toBe('2026-09-20')
    expect(daysBetween('2026-09-21', '2027-01-01')).toBe(102)
  })

  it('anchors the week on the configured first day', () => {
    // 2026-09-21 is a Monday.
    expect(dayOfWeek('2026-09-21')).toBe(1)
    expect(startOfWeek('2026-09-24', 1)).toBe('2026-09-21')
    expect(startOfWeek('2026-09-24', 0)).toBe('2026-09-20')
    expect(weekDates('2026-09-24', 1)).toEqual([
      '2026-09-21',
      '2026-09-22',
      '2026-09-23',
      '2026-09-24',
      '2026-09-25',
      '2026-09-26',
      '2026-09-27',
    ])
  })
})
