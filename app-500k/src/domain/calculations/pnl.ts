import type { DayEntry, InstrumentId, Settings, Trade } from '@/domain/models/types'

/**
 * P&L primitives. Pure functions, no rounding, no React.
 *
 *   FX:   pips * lots * pipValuePerLot          (3.5 lots => $35 / pip)
 *   Gold: dollarsOfMovement * lots * contract   (0.30 lot => $30 per $1 move)
 */

export function calculateFxPnl(pips: number, lots: number, pipValuePerLot: number): number {
  return pips * lots * pipValuePerLot
}

export function calculateGoldPnl(
  dollarMove: number,
  lots: number,
  goldContractSize: number,
): number {
  return dollarMove * lots * goldContractSize
}

/** USD earned per pip at the given FX size. */
export function fxValuePerPip(lots: number, pipValuePerLot: number): number {
  return lots * pipValuePerLot
}

/** USD earned per $1 of Gold price movement at the given Gold size. */
export function goldValuePerDollar(lots: number, goldContractSize: number): number {
  return lots * goldContractSize
}

export interface PositionSize {
  fxLots: number
  goldLots: number
}

/**
 * P&L of one instrument's raw result.
 * `result` is pips for FX instruments and dollars of movement for Gold.
 */
export function instrumentPnl(
  instrument: InstrumentId,
  result: number,
  size: PositionSize,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): number {
  if (instrument === 'XAUUSD') {
    return calculateGoldPnl(result, size.goldLots, settings.goldContractSize)
  }
  return calculateFxPnl(result, size.fxLots, settings.fxPipValuePerLot)
}

export interface DayPnlBreakdown {
  eurusd: number
  gbpusd: number
  xauusd: number
  gross: number
  fees: number
  net: number
}

/** P&L of a quick daily summary entry, at the supplied position size. */
export function calculateDaySummaryPnl(
  day: Pick<DayEntry, 'eurusdPips' | 'gbpusdPips' | 'xauusdMove' | 'fees' | 'commission' | 'swap'>,
  size: PositionSize,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): DayPnlBreakdown {
  const eurusd = calculateFxPnl(day.eurusdPips, size.fxLots, settings.fxPipValuePerLot)
  const gbpusd = calculateFxPnl(day.gbpusdPips, size.fxLots, settings.fxPipValuePerLot)
  const xauusd = calculateGoldPnl(day.xauusdMove, size.goldLots, settings.goldContractSize)
  const gross = eurusd + gbpusd + xauusd
  const fees = day.fees + day.commission + day.swap
  return { eurusd, gbpusd, xauusd, gross, fees, net: gross - fees }
}

/**
 * Theoretical P&L of a single trade, from its own recorded lot size.
 * `actualPnl`, when present, is what statistics use instead.
 */
export function calculateTradePnl(
  trade: Pick<Trade, 'instrument' | 'result' | 'lots'>,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): number {
  if (trade.instrument === 'XAUUSD') {
    return calculateGoldPnl(trade.result, trade.lots, settings.goldContractSize)
  }
  return calculateFxPnl(trade.result, trade.lots, settings.fxPipValuePerLot)
}

/** Realized P&L of a trade: actual when supplied, theoretical otherwise. Fees deducted. */
export function realizedTradePnl(
  trade: Trade,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): number {
  const gross = trade.actualPnl ?? calculateTradePnl(trade, settings)
  return gross - trade.fees
}

export function grossTradePnl(
  trade: Trade,
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): number {
  return trade.actualPnl ?? calculateTradePnl(trade, settings)
}

/** P&L of a day's detailed trades. */
export function calculateTradesPnl(
  trades: Trade[],
  settings: Pick<Settings, 'fxPipValuePerLot' | 'goldContractSize'>,
): DayPnlBreakdown {
  let eurusd = 0
  let gbpusd = 0
  let xauusd = 0
  let fees = 0
  for (const t of trades) {
    const gross = grossTradePnl(t, settings)
    if (t.instrument === 'EURUSD') eurusd += gross
    else if (t.instrument === 'GBPUSD') gbpusd += gross
    else xauusd += gross
    fees += t.fees
  }
  const gross = eurusd + gbpusd + xauusd
  return { eurusd, gbpusd, xauusd, gross, fees, net: gross - fees }
}

/**
 * Pips required to produce `amount` at the given FX size.
 * Returns `Infinity` when the size is zero (nothing can be earned).
 */
export function calculateRequiredPips(
  amount: number,
  lots: number,
  pipValuePerLot: number,
): number {
  const perPip = fxValuePerPip(lots, pipValuePerLot)
  if (perPip === 0) return Infinity
  return amount / perPip
}

/** Dollars of Gold price movement required to produce `amount`. */
export function calculateRequiredGoldMove(
  amount: number,
  lots: number,
  goldContractSize: number,
): number {
  const perDollar = goldValuePerDollar(lots, goldContractSize)
  if (perDollar === 0) return Infinity
  return amount / perDollar
}

/**
 * "Full Position Equivalent": expresses a realized P&L as the pip (or Gold $)
 * result a full reference-size position would have produced. Makes scaled-out
 * results comparable with full-position ones.
 */
export function fullPositionEquivalentPips(
  pnl: number,
  referenceLots: number,
  pipValuePerLot: number,
): number {
  return calculateRequiredPips(pnl, referenceLots, pipValuePerLot)
}

export function fullPositionEquivalentGoldMove(
  pnl: number,
  referenceGoldLots: number,
  goldContractSize: number,
): number {
  return calculateRequiredGoldMove(pnl, referenceGoldLots, goldContractSize)
}
