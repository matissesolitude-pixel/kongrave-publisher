import { useEffect, useRef, useState } from 'react'
import { useApp } from '@/app/store'
import { getSizingTier } from '@/domain/sizing/sizing'
import { formatLots, formatUsdCompact } from '@/utils/format'

const STORAGE_KEY = '500k.lastTier'

/**
 * Discreet "LEVEL UP" acknowledgement when equity unlocks a new sizing tier.
 * Rewards progress, never prompts another trade.
 */
export function LevelUpBanner() {
  const { settings, derived, ready } = useApp()
  const [visible, setVisible] = useState(false)
  const [tierEquity, setTierEquity] = useState(0)
  const seen = useRef<number | null>(null)

  const tier = getSizingTier(derived.ledger.currentEquity, settings.tiers)

  useEffect(() => {
    if (!ready || !tier) return
    if (seen.current === null) {
      const stored = Number(window.localStorage.getItem(STORAGE_KEY) ?? NaN)
      seen.current = Number.isFinite(stored) ? stored : tier.minEquity
      window.localStorage.setItem(STORAGE_KEY, String(seen.current))
      return
    }
    if (tier.minEquity > seen.current) {
      seen.current = tier.minEquity
      window.localStorage.setItem(STORAGE_KEY, String(tier.minEquity))
      setTierEquity(tier.minEquity)
      setVisible(true)
      const id = window.setTimeout(() => setVisible(false), 6000)
      return () => window.clearTimeout(id)
    }
  }, [ready, tier])

  if (!visible || !tier) return null

  return (
    <div className="animate-pop-in mx-4 mt-3 rounded-2xl border border-[var(--color-pos)]/40 bg-[var(--color-pos)]/10 px-4 py-3">
      <div className="text-[10px] font-bold tracking-[0.2em] text-[var(--color-pos)] uppercase">
        Level up
      </div>
      <div className="mt-0.5 text-lg font-bold">
        {formatUsdCompact(tierEquity)} palier unlocked
      </div>
      <div className="mt-1 text-xs text-[var(--color-muted)]">
        New FX size {formatLots(tier.fxLots)} lots · New Gold size {formatLots(tier.goldLots)} lots
        {settings.tierApplyMode === 'immediate'
          ? ' — applied immediately.'
          : settings.tierApplyMode === 'nextDay'
            ? ' — applied next trading day.'
            : ' — applied next week.'}
      </div>
      <button
        type="button"
        onClick={() => setVisible(false)}
        className="mt-2 text-xs font-semibold text-[var(--color-pos)]"
      >
        Dismiss
      </button>
    </div>
  )
}
