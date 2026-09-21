/**
 * Presentation-only rounding.
 *
 * Calculations never round intermediate values — formatting happens once,
 * at the edge, right before a number is rendered.
 */

export function formatUsd(value: number, decimals = 2): string {
  if (!Number.isFinite(value)) return '—'
  const abs = Math.abs(value)
  const body = abs.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
  return `${value < 0 ? '-' : ''}$${body}`
}

/** Large headline figures: no decimals. */
export function formatUsdCompact(value: number): string {
  return formatUsd(value, 0)
}

/** `+$1,850.00` / `-$420.00` — sign is always explicit. */
export function formatUsdSigned(value: number, decimals = 2): string {
  if (!Number.isFinite(value)) return '—'
  const sign = value > 0 ? '+' : value < 0 ? '-' : ''
  const abs = Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
  return `${sign}$${abs}`
}

/** Pips: 1 decimal. */
export function formatPips(value: number, decimals = 1): string {
  if (!Number.isFinite(value)) return '—'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function formatPipsSigned(value: number, decimals = 1): string {
  if (!Number.isFinite(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${formatPips(value, decimals)}`
}

/** Gold price movement, in dollars: 2 decimals. */
export function formatGoldMove(value: number, decimals = 2): string {
  if (!Number.isFinite(value)) return '—'
  const sign = value < 0 ? '-' : ''
  return `${sign}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`
}

export function formatGoldMoveSigned(value: number, decimals = 2): string {
  if (!Number.isFinite(value)) return '—'
  const sign = value > 0 ? '+' : value < 0 ? '-' : ''
  return `${sign}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`
}

/** Lots: up to 2 decimals, trailing zeros trimmed. */
export function formatLots(value: number): string {
  if (!Number.isFinite(value)) return '—'
  return Number(value.toFixed(2)).toString()
}

/** Percentage from a ratio (0.665 -> `66.5%`). */
export function formatPct(ratio: number, decimals = 1): string {
  if (!Number.isFinite(ratio)) return '—'
  return `${(ratio * 100).toFixed(decimals)}%`
}

export function formatPctSigned(ratio: number, decimals = 1): string {
  if (!Number.isFinite(ratio)) return '—'
  const sign = ratio > 0 ? '+' : ''
  return `${sign}${(ratio * 100).toFixed(decimals)}%`
}

/** Percentage from an already-scaled value (66.5 -> `66.5%`). */
export function formatPctValue(value: number, decimals = 1): string {
  if (!Number.isFinite(value)) return '—'
  return `${value.toFixed(decimals)}%`
}

export function formatNumber(value: number, decimals = 2): string {
  if (!Number.isFinite(value)) return '—'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/** Short money label for chart axes: `$7k`, `$500k`. */
export function formatUsdAxis(value: number): string {
  const abs = Math.abs(value)
  const sign = value < 0 ? '-' : ''
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000) return `${sign}$${Math.round(abs / 1_000)}k`
  return `${sign}$${Math.round(abs)}`
}

export function formatR(value: number): string {
  if (!Number.isFinite(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}R`
}
