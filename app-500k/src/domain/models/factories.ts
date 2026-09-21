import { makeId } from '@/utils/id'
import type { Cashflow, CashflowType, DayEntry, InstrumentId, IsoDate, Trade } from './types'

export function createDayEntry(date: IsoDate, patch: Partial<DayEntry> = {}): DayEntry {
  const now = Date.now()
  return {
    date,
    eurusdPips: 0,
    gbpusdPips: 0,
    xauusdMove: 0,
    fees: 0,
    commission: 0,
    swap: 0,
    notes: '',
    pnlSource: 'daily',
    manualWins: null,
    manualLosses: null,
    fxLotsUsed: null,
    goldLotsUsed: null,
    executionScore: null,
    disciplineScore: null,
    emotion: null,
    whatHappened: '',
    checklist: null,
    createdAt: now,
    updatedAt: now,
    ...patch,
  }
}

export function createTrade(
  date: IsoDate,
  instrument: InstrumentId,
  patch: Partial<Trade> = {},
): Trade {
  const now = Date.now()
  return {
    id: makeId(),
    date,
    time: null,
    instrument,
    direction: 'long',
    result: 0,
    lots: 0,
    actualPnl: null,
    outcome: 'W',
    fees: 0,
    rMultiple: null,
    stopLoss: null,
    plannedTarget: null,
    targetHit: null,
    setup: '',
    session: '',
    comment: '',
    tradingError: false,
    mfe: null,
    mae: null,
    initialRisk: null,
    exitReason: '',
    screenshot: null,
    createdAt: now,
    updatedAt: now,
    ...patch,
  }
}

export function createCashflow(
  date: IsoDate,
  type: CashflowType,
  amount: number,
  note = '',
): Cashflow {
  const now = Date.now()
  return { id: makeId(), date, type, amount, note, createdAt: now, updatedAt: now }
}
