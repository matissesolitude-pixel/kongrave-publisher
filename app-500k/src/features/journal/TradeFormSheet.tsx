import { useMemo, useState } from 'react'
import { Sheet } from '@/components/Sheet'
import { NumberField, TextField } from '@/components/NumberField'
import { Button, Chip, Segmented, Stat, Toggle, signTone } from '@/components/ui'
import { useToast } from '@/components/Toast'
import { useApp } from '@/app/store'
import { createTrade } from '@/domain/models/factories'
import {
  INSTRUMENTS,
  INSTRUMENT_SHORT,
  type InstrumentId,
  type IsoDate,
  type Trade,
  type TradeOutcome,
} from '@/domain/models/types'
import { calculateTradePnl } from '@/domain/calculations/pnl'
import { equityOpenAt } from '@/domain/calculations/ledger'
import { resolveSize } from '@/domain/sizing/sizing'
import { formatUsdSigned } from '@/utils/format'

/**
 * Detailed trade entry — everything optional except instrument, result and lots.
 * Mounted only while open, so the draft starts from the right trade without an
 * effect resynchronising it.
 */
export function TradeFormSheet({
  open,
  onClose,
  date,
  trade,
}: {
  open: boolean
  onClose: () => void
  date: IsoDate
  trade?: Trade | null
}) {
  if (!open) return null
  return (
    <TradeForm key={trade?.id ?? `new-${date}`} date={date} trade={trade} onClose={onClose} />
  )
}

function TradeForm({
  date,
  trade,
  onClose,
}: {
  date: IsoDate
  trade?: Trade | null
  onClose: () => void
}) {
  const { settings, saveTrade, derived } = useApp()
  const toast = useToast()
  const [showMore, setShowMore] = useState(false)

  const defaultLots = useMemo(() => {
    const equity = equityOpenAt(derived.ledger, date)
    return resolveSize(equity, settings)
  }, [derived.ledger, date, settings])

  const [draft, setDraft] = useState<Trade>(
    () => trade ?? createTrade(date, 'EURUSD', { lots: defaultLots.fxLots }),
  )

  const patch = (next: Partial<Trade>) => setDraft((d) => ({ ...d, ...next }))

  const onInstrument = (instrument: InstrumentId) => {
    const lots = instrument === 'XAUUSD' ? defaultLots.goldLots : defaultLots.fxLots
    patch({ instrument, lots: draft.lots === 0 ? lots : draft.lots })
  }

  const computed = calculateTradePnl(draft, settings)
  const effective = (draft.actualPnl ?? computed) - draft.fees
  const isGold = draft.instrument === 'XAUUSD'

  const onSave = async () => {
    await saveTrade({ ...draft, date })
    toast.show(trade ? 'Trade updated ✓' : 'Trade added ✓', effective >= 0 ? 'pos' : 'neg')
    onClose()
  }

  return (
    <Sheet
      open
      title={trade ? 'Edit trade' : 'Add trade'}
      onClose={onClose}
      footer={
        <Button full size="lg" variant="primary" onClick={() => void onSave()}>
          Save trade
        </Button>
      }
    >
      <div className="space-y-4">
        <div>
          <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
            Instrument
          </span>
          <div className="flex gap-1.5">
            {INSTRUMENTS.map((i) => (
              <Chip key={i} active={draft.instrument === i} onClick={() => onInstrument(i)}>
                {INSTRUMENT_SHORT[i]}
              </Chip>
            ))}
          </div>
        </div>

        <Segmented
          ariaLabel="Direction"
          value={draft.direction}
          onChange={(v) => patch({ direction: v })}
          options={[
            { value: 'long', label: 'Long' },
            { value: 'short', label: 'Short' },
          ]}
        />

        <NumberField
          label={isGold ? 'Result — $ of Gold movement' : 'Result — pips'}
          prefix={isGold ? '$' : undefined}
          value={draft.result === 0 ? null : draft.result}
          onChange={(v) => patch({ result: v ?? 0 })}
          quick={isGold ? [5, 10, 15, -5, -10] : [5, 10, -5, -10]}
          tone={draft.result > 0 ? 'pos' : draft.result < 0 ? 'neg' : 'neutral'}
        />

        <NumberField
          label="Lots"
          value={draft.lots === 0 ? null : draft.lots}
          onChange={(v) => patch({ lots: v ?? 0 })}
          allowNegative={false}
          hint={`auto ${isGold ? defaultLots.goldLots : defaultLots.fxLots}`}
        />

        <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-3">
          <div className="flex items-end justify-between">
            <Stat
              label="Net P&L"
              value={formatUsdSigned(effective, 2)}
              tone={signTone(effective)}
              size="lg"
            />
            <div className="text-right text-xs text-[var(--color-dim)]">
              <div>Computed {formatUsdSigned(computed, 2)}</div>
              {draft.actualPnl !== null ? <div>Actual overrides it</div> : null}
            </div>
          </div>
        </div>

        <div>
          <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
            Outcome
          </span>
          <div className="flex gap-1.5">
            {(['W', 'L', 'BE'] as TradeOutcome[]).map((o) => (
              <Chip key={o} active={draft.outcome === o} onClick={() => patch({ outcome: o })}>
                {o === 'W' ? 'Win' : o === 'L' ? 'Loss' : 'Break-even'}
              </Chip>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <TextField
            label="Time"
            type="time"
            value={draft.time ?? ''}
            onChange={(v) => patch({ time: v || null })}
          />
          <NumberField
            label="Fees"
            prefix="$"
            value={draft.fees === 0 ? null : draft.fees}
            onChange={(v) => patch({ fees: v ?? 0 })}
            allowNegative={false}
          />
        </div>

        <Button full variant="ghost" onClick={() => setShowMore((s) => !s)}>
          {showMore ? 'Hide extras' : 'More — R, targets, context'}
        </Button>

        {showMore ? (
          <div className="space-y-4 border-t border-[var(--color-line)] pt-4">
            <NumberField
              label="Actual realized P&L"
              prefix="$"
              value={draft.actualPnl}
              onChange={(v) => patch({ actualPnl: v })}
              hint="overrides the computed P&L"
            />
            <div className="grid grid-cols-2 gap-3">
              <NumberField
                label="R realized"
                value={draft.rMultiple}
                onChange={(v) => patch({ rMultiple: v })}
              />
              <NumberField
                label={isGold ? 'Stop ($ move)' : 'Stop (pips)'}
                value={draft.stopLoss}
                onChange={(v) => patch({ stopLoss: v })}
                allowNegative={false}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <NumberField
                label="Planned target"
                value={draft.plannedTarget}
                onChange={(v) => patch({ plannedTarget: v })}
              />
              <NumberField
                label="Initial risk ($)"
                prefix="$"
                value={draft.initialRisk}
                onChange={(v) => patch({ initialRisk: v })}
                allowNegative={false}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="MFE" value={draft.mfe} onChange={(v) => patch({ mfe: v })} />
              <NumberField label="MAE" value={draft.mae} onChange={(v) => patch({ mae: v })} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <TextField
                label="Setup"
                value={draft.setup}
                onChange={(v) => patch({ setup: v })}
                placeholder="e.g. FVG london"
              />
              <TextField
                label="Session"
                value={draft.session}
                onChange={(v) => patch({ session: v })}
                placeholder="e.g. London"
              />
            </div>
            <TextField
              label="Exit reason"
              value={draft.exitReason}
              onChange={(v) => patch({ exitReason: v })}
            />
            <TextField
              label="Comment"
              value={draft.comment}
              onChange={(v) => patch({ comment: v })}
              multiline
            />
            <div className="rounded-2xl border border-[var(--color-line)] px-3">
              <Toggle
                label="Target hit"
                checked={draft.targetHit === true}
                onChange={(v) => patch({ targetHit: v })}
              />
              <Toggle
                label="Trading error"
                description="Flag this trade as a process mistake"
                checked={draft.tradingError}
                onChange={(v) => patch({ tradingError: v })}
              />
            </div>
            <ScreenshotField
              value={draft.screenshot}
              onChange={(v) => patch({ screenshot: v })}
            />
          </div>
        ) : null}
      </div>
    </Sheet>
  )
}

function ScreenshotField({
  value,
  onChange,
}: {
  value: string | null
  onChange: (next: string | null) => void
}) {
  const toast = useToast()
  return (
    <div>
      <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
        Screenshot
      </span>
      {value ? (
        <div className="space-y-2">
          <img
            src={value}
            alt="Trade screenshot"
            className="max-h-48 w-full rounded-xl border border-[var(--color-line)] object-contain"
          />
          <Button size="sm" variant="danger" onClick={() => onChange(null)}>
            Remove
          </Button>
        </div>
      ) : (
        <input
          type="file"
          accept="image/*"
          className="w-full text-xs text-[var(--color-muted)]"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (!file) return
            if (file.size > 1_500_000) {
              toast.show('Image too large (max 1.5 MB)', 'neg')
              return
            }
            const reader = new FileReader()
            reader.onload = () => onChange(typeof reader.result === 'string' ? reader.result : null)
            reader.readAsDataURL(file)
          }}
        />
      )}
    </div>
  )
}
