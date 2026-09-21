import { useApp } from '@/app/store'
import { Button, Card, CardTitle } from '@/components/ui'
import { DEFAULT_TIERS } from '@/domain/models/defaults'
import type { SizingTier } from '@/domain/models/types'
import { sortTiers } from '@/domain/sizing/sizing'

/** The sizing ladder is data, not a constant — every row is editable. */
export function TierEditor() {
  const { settings, updateSettings } = useApp()

  const update = (index: number, patch: Partial<SizingTier>) => {
    const next = settings.tiers.map((t, i) => (i === index ? { ...t, ...patch } : t))
    void updateSettings({ tiers: next })
  }

  const remove = (index: number) => {
    void updateSettings({ tiers: settings.tiers.filter((_, i) => i !== index) })
  }

  const add = () => {
    const last = sortTiers(settings.tiers).at(-1)
    void updateSettings({
      tiers: [
        ...settings.tiers,
        {
          minEquity: (last?.minEquity ?? 0) * 2 || 1000,
          fxLots: (last?.fxLots ?? 0) * 2 || 1,
          goldLots: (last?.goldLots ?? 0) * 2 || 0.1,
        },
      ],
    })
  }

  return (
    <Card>
      <CardTitle
        right={
          <button
            type="button"
            className="text-xs font-semibold text-[var(--color-accent)]"
            onClick={() => void updateSettings({ tiers: DEFAULT_TIERS })}
          >
            Reset table
          </button>
        }
      >
        Sizing tiers
      </CardTitle>

      <div className="grid grid-cols-[1.2fr_1fr_1fr_auto] gap-2 pb-1 text-[10px] font-semibold tracking-[0.1em] text-[var(--color-dim)] uppercase">
        <span>Equity</span>
        <span>FX lots</span>
        <span>Gold</span>
        <span />
      </div>

      <div className="space-y-1.5">
        {settings.tiers.map((tier, index) => (
          <div key={index} className="grid grid-cols-[1.2fr_1fr_1fr_auto] items-center gap-2">
            <TierInput
              value={tier.minEquity}
              onChange={(v) => update(index, { minEquity: v })}
              label={`Tier ${index + 1} equity`}
            />
            <TierInput
              value={tier.fxLots}
              onChange={(v) => update(index, { fxLots: v })}
              label={`Tier ${index + 1} FX lots`}
            />
            <TierInput
              value={tier.goldLots}
              onChange={(v) => update(index, { goldLots: v })}
              label={`Tier ${index + 1} Gold lots`}
            />
            <button
              type="button"
              aria-label={`Remove tier ${index + 1}`}
              onClick={() => remove(index)}
              className="min-h-10 px-2 text-sm text-[var(--color-neg)]"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <Button full className="mt-3" onClick={add}>
        + Add tier
      </Button>
    </Card>
  )
}

function TierInput({
  value,
  onChange,
  label,
}: {
  value: number
  onChange: (next: number) => void
  label: string
}) {
  return (
    <input
      type="number"
      inputMode="decimal"
      aria-label={label}
      value={value}
      onChange={(e) => onChange(Number(e.target.value) || 0)}
      className="tabular min-h-10 w-full rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-2)] px-2 text-sm outline-none"
    />
  )
}
