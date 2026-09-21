import { useApp } from '@/app/store'
import { Button, Card, CardTitle, Row, Segmented, Toggle } from '@/components/ui'
import { NumberField, TextField } from '@/components/NumberField'
import { TierEditor } from './TierEditor'
import { CashflowSection } from './CashflowSection'
import { DataSection } from './DataSection'
import { DEFAULT_SETTINGS, DISCLAIMER } from '@/domain/models/defaults'
import {
  INSTRUMENTS,
  INSTRUMENT_SHORT,
  type InstrumentId,
  type WeekStartDay,
} from '@/domain/models/types'
import { formatLots, formatPct, formatUsd } from '@/utils/format'

const WEEK_DAYS: Array<{ value: WeekStartDay; label: string }> = [
  { value: 1, label: 'Monday' },
  { value: 0, label: 'Sunday' },
  { value: 6, label: 'Saturday' },
]

export function SettingsScreen() {
  const { settings, updateSettings, derived } = useApp()
  const set = updateSettings

  return (
    <div className="space-y-4">
      <Card>
        <CardTitle>Challenge</CardTitle>
        <div className="space-y-3">
          <NumberField
            label="Starting capital"
            prefix="$"
            value={settings.startingCapital}
            onChange={(v) => void set({ startingCapital: v ?? 0 })}
            allowNegative={false}
          />
          <NumberField
            label="Target capital"
            prefix="$"
            value={settings.targetCapital}
            onChange={(v) => void set({ targetCapital: v ?? 0 })}
            allowNegative={false}
          />
          <div className="grid grid-cols-2 gap-3">
            <TextField
              label="Start date"
              type="date"
              value={settings.startDate}
              onChange={(v) => v && void set({ startDate: v })}
            />
            <TextField
              label="Target date"
              type="date"
              value={settings.targetDate}
              onChange={(v) => v && void set({ targetDate: v })}
            />
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle>Weekly target methodology</CardTitle>
        <Segmented
          ariaLabel="Weekly target methodology"
          value={settings.weeklyTargetMode}
          onChange={(v) => void set({ weeklyTargetMode: v })}
          options={[
            { value: 'compound', label: 'Compound (exact)' },
            { value: 'fixedRate', label: 'Fixed rate' },
          ]}
        />
        <p className="mt-2 text-xs text-[var(--color-dim)]">
          {settings.weeklyTargetMode === 'compound'
            ? 'Recomputed each week from the equity at the week open, the remaining weeks and the target.'
            : 'Constant weekly growth rate, independent of the remaining time.'}
        </p>
        {settings.weeklyTargetMode === 'fixedRate' ? (
          <div className="mt-3">
            <NumberField
              label="Fixed weekly rate"
              suffix="%"
              value={settings.fixedWeeklyRate * 100}
              onChange={(v) => void set({ fixedWeeklyRate: (v ?? 0) / 100 })}
              allowNegative={false}
              quick={[1, 5, -1, -5]}
              clearable={false}
            />
          </div>
        ) : null}
        <div className="mt-3 border-t border-[var(--color-line)] pt-3">
          <Row label="This week's rate" value={formatPct(derived.weekly.rate)} tone="accent" />
          <Row label="This week's target" value={formatUsd(derived.weekly.targetAmount, 2)} />
        </div>
      </Card>

      <Card>
        <CardTitle>Position sizing</CardTitle>
        <Segmented
          ariaLabel="Sizing mode"
          value={settings.sizingMode}
          onChange={(v) => void set({ sizingMode: v })}
          options={[
            { value: 'tiers', label: 'B — tiers' },
            { value: 'continuous', label: 'A — continuous' },
          ]}
        />
        <p className="mt-2 text-xs text-[var(--color-dim)]">
          {settings.sizingMode === 'continuous'
            ? `FX lots = equity / ${settings.fxSizingDivisor}. Gold is interpolated from the tier table below.`
            : 'Lots stay frozen at the active tier until the next one is reached.'}
        </p>

        {settings.sizingMode === 'continuous' ? (
          <div className="mt-3">
            <NumberField
              label="FX sizing divisor"
              value={settings.fxSizingDivisor}
              onChange={(v) => void set({ fxSizingDivisor: v ?? 1 })}
              allowNegative={false}
              hint={`$${settings.fxSizingDivisor} per lot`}
            />
          </div>
        ) : null}

        <div className="mt-4">
          <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
            FX sizing mode
          </span>
          <Segmented
            ariaLabel="FX exposure"
            value={settings.fxSizingExposure}
            onChange={(v) => void set({ fxSizingExposure: v })}
            options={[
              { value: 'perInstrument', label: 'Per instrument' },
              { value: 'sharedTotal', label: 'Shared total' },
            ]}
          />
          <p className="mt-2 text-xs text-[var(--color-dim)]">
            {settings.fxSizingExposure === 'perInstrument'
              ? 'Each FX instrument is valued at the full lot size.'
              : 'The FX lot size is the total exposure, split across the FX instruments.'}
          </p>
        </div>

        <div className="mt-4">
          <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
            Tier change applies
          </span>
          <Segmented
            ariaLabel="Tier apply mode"
            value={settings.tierApplyMode}
            onChange={(v) => void set({ tierApplyMode: v })}
            options={[
              { value: 'immediate', label: 'Immediately' },
              { value: 'nextDay', label: 'Next day' },
              { value: 'nextWeek', label: 'Next week' },
            ]}
          />
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <NumberField
            label="Manual FX lots"
            value={settings.manualFxLots}
            onChange={(v) => void set({ manualFxLots: v })}
            allowNegative={false}
            hint="auto"
          />
          <NumberField
            label="Manual Gold lots"
            value={settings.manualGoldLots}
            onChange={(v) => void set({ manualGoldLots: v })}
            allowNegative={false}
            hint="auto"
          />
        </div>

        <div className="mt-3 border-t border-[var(--color-line)] pt-3">
          <Row label="Current FX size" value={`${formatLots(derived.size.fxLots)} lots`} />
          <Row label="Current Gold size" value={`${formatLots(derived.size.goldLots)} lots`} />
        </div>
      </Card>

      <TierEditor />

      <Card>
        <CardTitle>Contract specifications</CardTitle>
        <div className="space-y-3">
          <NumberField
            label="FX pip value per standard lot"
            prefix="$"
            value={settings.fxPipValuePerLot}
            onChange={(v) => void set({ fxPipValuePerLot: v ?? 0 })}
            allowNegative={false}
            hint="default $10"
          />
          <NumberField
            label="Gold contract size (oz per lot)"
            value={settings.goldContractSize}
            onChange={(v) => void set({ goldContractSize: v ?? 0 })}
            allowNegative={false}
            hint="default 100"
          />
        </div>
        <p className="mt-3 text-xs text-[var(--color-dim)]">
          At the current size: {formatUsd(derived.size.fxLots * settings.fxPipValuePerLot, 2)} per FX
          pip, {formatUsd(derived.size.goldLots * settings.goldContractSize, 2)} per $1 of Gold
          movement.
        </p>
      </Card>

      <Card>
        <CardTitle>Rules</CardTitle>
        <NumberField
          label="Daily loss limit"
          value={settings.dailyLossLimit}
          onChange={(v) => void set({ dailyLossLimit: Math.max(1, Math.round(v ?? 1)) })}
          allowNegative={false}
          quick={[1, -1]}
          clearable={false}
          hint="losses, not trades"
        />
        <p className="mt-2 text-xs text-[var(--color-dim)]">
          The limit counts losing trades, never the number of trades taken.
        </p>
        <div className="mt-4">
          <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
            Week starts on
          </span>
          <Segmented
            ariaLabel="Week start"
            value={String(settings.weekStart)}
            onChange={(v) => void set({ weekStart: Number(v) as WeekStartDay })}
            options={WEEK_DAYS.map((d) => ({ value: String(d.value), label: d.label }))}
          />
        </div>
        <div className="mt-4">
          <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
            Win-rate convention
          </span>
          <Segmented
            ariaLabel="Win rate convention"
            value={settings.winRateConvention}
            onChange={(v) => void set({ winRateConvention: v })}
            options={[
              { value: 'excludeBE', label: 'BE excluded' },
              { value: 'includeBE', label: 'BE included' },
            ]}
          />
          <p className="mt-2 text-xs text-[var(--color-dim)]">
            {settings.winRateConvention === 'excludeBE'
              ? 'wins / (wins + losses) — break-evens excluded from the denominator.'
              : 'wins / (wins + losses + break-evens).'}
          </p>
        </div>
      </Card>

      <Card>
        <CardTitle>Scale-out</CardTitle>
        <div className="rounded-xl border border-[var(--color-line)] px-3">
          <Toggle
            label="Scale-out enabled"
            description="Reference management plan. Never applied automatically to full-position results."
            checked={settings.scaleOut.enabled}
            onChange={(v) =>
              void set({ scaleOut: { ...settings.scaleOut, enabled: v } })
            }
          />
        </div>
        {settings.scaleOut.enabled ? (
          <div className="mt-3 space-y-4">
            {INSTRUMENTS.map((i: InstrumentId) => {
              const leg = settings.scaleOut.legs[i]
              const patchLeg = (patch: Partial<typeof leg>) =>
                void set({
                  scaleOut: {
                    ...settings.scaleOut,
                    legs: { ...settings.scaleOut.legs, [i]: { ...leg, ...patch } },
                  },
                })
              return (
                <div key={i} className="rounded-xl border border-[var(--color-line)] p-3">
                  <div className="mb-2 text-sm font-semibold">{INSTRUMENT_SHORT[i]}</div>
                  <div className="grid grid-cols-3 gap-2">
                    <NumberField
                      label="First TP"
                      prefix={i === 'XAUUSD' ? '$' : undefined}
                      value={leg.firstTakeProfit}
                      onChange={(v) => patchLeg({ firstTakeProfit: v ?? 0 })}
                      allowNegative={false}
                    />
                    <NumberField
                      label="Closed"
                      suffix="%"
                      value={leg.closedPct}
                      onChange={(v) => patchLeg({ closedPct: v ?? 0, runnerPct: 100 - (v ?? 0) })}
                      allowNegative={false}
                    />
                    <NumberField
                      label="Runner"
                      suffix="%"
                      value={leg.runnerPct}
                      onChange={(v) => patchLeg({ runnerPct: v ?? 0, closedPct: 100 - (v ?? 0) })}
                      allowNegative={false}
                    />
                  </div>
                </div>
              )
            })}
            <p className="text-xs text-[var(--color-dim)]">
              Daily results entered as full-position equivalents stay untouched. Realized P&L and
              full-position equivalents remain two distinct concepts.
            </p>
          </div>
        ) : null}
      </Card>

      <CashflowSection />

      <Card>
        <CardTitle>Appearance</CardTitle>
        <Segmented
          ariaLabel="Theme"
          value={settings.theme}
          onChange={(v) => void set({ theme: v })}
          options={[
            { value: 'dark', label: 'Dark' },
            { value: 'light', label: 'Light' },
          ]}
        />
        <div className="mt-3 rounded-xl border border-[var(--color-line)] px-3">
          <Toggle
            label="Reduce motion"
            description="Also honours the system setting automatically."
            checked={settings.reduceMotion}
            onChange={(v) => void set({ reduceMotion: v })}
          />
        </div>
        <div className="mt-3">
          <TextField
            label="Currency symbol / code"
            value={settings.currency}
            onChange={(v) => void set({ currency: v })}
          />
          <p className="mt-1 text-xs text-[var(--color-dim)]">
            Display label only — every amount is tracked in the account currency.
          </p>
        </div>
      </Card>

      <DataSection />

      <Card>
        <CardTitle>About</CardTitle>
        <p className="text-sm leading-relaxed text-[var(--color-muted)]">{DISCLAIMER}</p>
        <div className="mt-3 border-t border-[var(--color-line)] pt-3">
          <Row label="Schema version" value={String(settings.schemaVersion)} />
          <Row label="Storage" value="IndexedDB (local only)" />
          <Row
            label="Win-rate convention"
            value={
              settings.winRateConvention === 'excludeBE'
                ? 'wins / (wins + losses)'
                : 'wins / (wins + losses + BE)'
            }
          />
        </div>
        <Button
          full
          className="mt-3"
          onClick={() => void set({ ...DEFAULT_SETTINGS, schemaVersion: settings.schemaVersion })}
        >
          Restore default settings
        </Button>
        <p className="mt-2 text-[11px] text-[var(--color-dim)]">
          Restores the configuration only — your days, trades and movements are kept.
        </p>
      </Card>
    </div>
  )
}
