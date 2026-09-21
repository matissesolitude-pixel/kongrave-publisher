import type { Cashflow, DayEntry, Settings, Trade } from '@/domain/models/types'

/**
 * Persistence contract.
 *
 * The app only ever talks to this interface, so the IndexedDB implementation can
 * be swapped for a remote backend later without touching any feature code.
 */
export interface PersistenceAdapter {
  readonly name: string

  loadSettings(): Promise<Settings | null>
  saveSettings(settings: Settings): Promise<void>

  listDays(): Promise<DayEntry[]>
  getDay(date: string): Promise<DayEntry | null>
  putDay(day: DayEntry): Promise<void>
  deleteDay(date: string): Promise<void>

  listTrades(): Promise<Trade[]>
  putTrade(trade: Trade): Promise<void>
  deleteTrade(id: string): Promise<void>
  deleteTradesForDate(date: string): Promise<void>

  listCashflows(): Promise<Cashflow[]>
  putCashflow(cashflow: Cashflow): Promise<void>
  deleteCashflow(id: string): Promise<void>

  /** Wipes every table (settings included). */
  clearAll(): Promise<void>
  /** Replaces the whole dataset atomically. */
  replaceAll(payload: {
    settings: Settings
    days: DayEntry[]
    trades: Trade[]
    cashflows: Cashflow[]
  }): Promise<void>
}
