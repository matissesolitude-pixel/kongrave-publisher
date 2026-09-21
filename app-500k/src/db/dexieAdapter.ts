import Dexie, { type EntityTable } from 'dexie'
import type { Cashflow, DayEntry, Settings, Trade } from '@/domain/models/types'
import type { PersistenceAdapter } from './persistence'

interface SettingsRow {
  id: string
  value: Settings
}

class FiveHundredKDb extends Dexie {
  settings!: EntityTable<SettingsRow, 'id'>
  days!: EntityTable<DayEntry, 'date'>
  trades!: EntityTable<Trade, 'id'>
  cashflows!: EntityTable<Cashflow, 'id'>

  constructor() {
    super('500k')
    this.version(1).stores({
      settings: 'id',
      days: 'date, updatedAt',
      trades: 'id, date, instrument, outcome',
      cashflows: 'id, date, type',
    })
  }
}

const SETTINGS_KEY = 'settings'

export class DexieAdapter implements PersistenceAdapter {
  readonly name = 'indexeddb'
  private db = new FiveHundredKDb()

  async loadSettings(): Promise<Settings | null> {
    const row = await this.db.settings.get(SETTINGS_KEY)
    return row?.value ?? null
  }

  async saveSettings(settings: Settings): Promise<void> {
    await this.db.settings.put({ id: SETTINGS_KEY, value: settings })
  }

  listDays(): Promise<DayEntry[]> {
    return this.db.days.orderBy('date').toArray()
  }

  async getDay(date: string): Promise<DayEntry | null> {
    return (await this.db.days.get(date)) ?? null
  }

  async putDay(day: DayEntry): Promise<void> {
    await this.db.days.put(day)
  }

  async deleteDay(date: string): Promise<void> {
    await this.db.days.delete(date)
  }

  listTrades(): Promise<Trade[]> {
    return this.db.trades.toArray()
  }

  async putTrade(trade: Trade): Promise<void> {
    await this.db.trades.put(trade)
  }

  async deleteTrade(id: string): Promise<void> {
    await this.db.trades.delete(id)
  }

  async deleteTradesForDate(date: string): Promise<void> {
    await this.db.trades.where('date').equals(date).delete()
  }

  listCashflows(): Promise<Cashflow[]> {
    return this.db.cashflows.toArray()
  }

  async putCashflow(cashflow: Cashflow): Promise<void> {
    await this.db.cashflows.put(cashflow)
  }

  async deleteCashflow(id: string): Promise<void> {
    await this.db.cashflows.delete(id)
  }

  async clearAll(): Promise<void> {
    await this.db.transaction(
      'rw',
      [this.db.settings, this.db.days, this.db.trades, this.db.cashflows],
      async () => {
        await Promise.all([
          this.db.settings.clear(),
          this.db.days.clear(),
          this.db.trades.clear(),
          this.db.cashflows.clear(),
        ])
      },
    )
  }

  async replaceAll(payload: {
    settings: Settings
    days: DayEntry[]
    trades: Trade[]
    cashflows: Cashflow[]
  }): Promise<void> {
    await this.db.transaction(
      'rw',
      [this.db.settings, this.db.days, this.db.trades, this.db.cashflows],
      async () => {
        await Promise.all([
          this.db.days.clear(),
          this.db.trades.clear(),
          this.db.cashflows.clear(),
        ])
        await this.db.settings.put({ id: SETTINGS_KEY, value: payload.settings })
        await this.db.days.bulkPut(payload.days)
        await this.db.trades.bulkPut(payload.trades)
        await this.db.cashflows.bulkPut(payload.cashflows)
      },
    )
  }
}
