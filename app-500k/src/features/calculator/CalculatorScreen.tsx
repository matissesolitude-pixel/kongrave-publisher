import { useMemo, useState } from 'react'
import { useApp } from '@/app/store'
import { Button, Card, CardTitle, Chip, ProgressBar, Row, Segmented, Stat, cx, signTone } from '@/components/ui'
import { NumberField } from '@/components/NumberField'
import { evaluateMix, MIX_PRESETS, solveMix, type MixPresetId, type Weights } from '@/domain/calculations/mix'
import { calculateRequiredGoldMove, calculateRequiredPips } from '@/domain/calculations/pnl'
import type { InstrumentId } from '@/domain/models/types'
import {
  formatGoldMove,
  formatLots,
  formatPct,
  formatPips,
  formatUsd,
  formatUsdSigned,
} from '@/utils/format'

type TargetMode = 'weekly' | 'custom'

const DEFAULT_WEIGHTS: Weights = { EURUSD: 1 / 3, GBPUSD: 1 / 3, XAUUSD: 1 / 3 }

export function CalculatorScreen() {
  const { settings, derived } = useApp()
  const { weekly, size } = derived

  const [mode, setMode] = useState<TargetMode>('weekly')
  const [customTarget, setCustomTarget] = useState<number | null>(1000)

  const [eu, setEu] = useState(0)
  const [gu, setGu] = useState(0)
  const [gold, setGold] = useState(0)

  const [preset, setPreset] = useState<MixPresetId>('balanced')
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS)
  const [locked, setLocked] = useState<Partial<Record<InstrumentId, number>>>({})

  const target = mode === 'weekly' ? weekly.remaining : Math.max(0, customTarget ?? 0)

  const live = useMemo(
    () => evaluateMix({ EURUSD: eu, GBPUSD: gu, XAUUSD: gold }, size, settings),
    [eu, gu, gold, size, settings],
  )

  const missing = target - live.total
  const progress = target > 0 ? live.total / target : 0

  const mix = useMemo(
    () => solveMix({ target, size, settings, locked, weights }),
    [target, size, settings, locked, weights],
  )

  const perPip = size.fxLots * settings.fxPipValuePerLot
  const perGoldDollar = size.goldLots * settings.goldContractSize

  const applyPreset = (id: MixPresetId) => {
    setPreset(id)
    const found = MIX_PRESETS.find((p) => p.id === id)
    if (found?.weights) setWeights(found.weights)
  }

  const toggleLock = (instrument: InstrumentId, value: number) => {
    setLocked((l) => {
      const next = { ...l }
      if (next[instrument] === undefined) next[instrument] = value
      else delete next[instrument]
      return next
    })
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardTitle>Target</CardTitle>
        <Segmented
          ariaLabel="Target mode"
          value={mode}
          onChange={setMode}
          options={[
            { value: 'weekly', label: 'Weekly target' },
            { value: 'custom', label: 'Custom target' },
          ]}
        />
        {mode === 'custom' ? (
          <div className="mt-3">
            <NumberField
              label="Custom target"
              prefix="$"
              value={customTarget}
              onChange={setCustomTarget}
              allowNegative={false}
              quick={[100, 500, 1000, -500]}
            />
          </div>
        ) : (
          <div className="mt-3 grid grid-cols-3 gap-2">
            <Stat label="Week target" value={formatUsd(weekly.targetAmount, 0)} size="sm" />
            <Stat
              label="Done"
              value={formatUsdSigned(weekly.done, 0)}
              tone={signTone(weekly.done)}
              size="sm"
            />
            <Stat label="Remaining" value={formatUsd(weekly.remaining, 0)} tone="accent" size="sm" />
          </div>
        )}
        <p className="mt-3 text-xs text-[var(--color-dim)]">
          Sizing: {formatLots(size.fxLots)} FX lots → {formatUsd(perPip, 0)} per pip ·{' '}
          {formatLots(size.goldLots)} Gold lots → {formatUsd(perGoldDollar, 0)} per $1 of movement.
        </p>
      </Card>

      {/* Interactive gauges */}
      <Card>
        <CardTitle>Simulate</CardTitle>
        <div className="space-y-5">
          <Gauge
            label="EURUSD"
            unit="pips"
            value={eu}
            onChange={setEu}
            min={-100}
            max={100}
            step={0.5}
            pnl={live.perInstrument.EURUSD}
          />
          <Gauge
            label="GBPUSD"
            unit="pips"
            value={gu}
            onChange={setGu}
            min={-100}
            max={100}
            step={0.5}
            pnl={live.perInstrument.GBPUSD}
          />
          <Gauge
            label="XAUUSD"
            unit="$ move"
            value={gold}
            onChange={setGold}
            min={-150}
            max={150}
            step={0.5}
            pnl={live.perInstrument.XAUUSD}
          />
        </div>

        <div className="mt-5 rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-3">
          <div className="flex items-end justify-between">
            <Stat
              label="Total P&L"
              value={formatUsdSigned(live.total, 2)}
              tone={signTone(live.total)}
              size="lg"
            />
            <div className="text-right">
              <div className="text-[10px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
                of target
              </div>
              <div className="tabular text-lg font-semibold">{formatPct(progress)}</div>
            </div>
          </div>
          <div className="mt-3">
            <ProgressBar ratio={progress} tone={progress >= 1 ? 'pos' : 'accent'} label="Target progress" />
          </div>
          <p className="mt-2 text-sm">
            {missing > 0 ? (
              <span className="text-[var(--color-muted)]">
                Missing <strong className="tabular text-[var(--color-text)]">{formatUsd(missing, 2)}</strong>
              </span>
            ) : (
              <span className="font-semibold text-[var(--color-pos)]">✓ Target covered</span>
            )}
          </p>
        </div>

        {missing > 0 ? (
          <div className="mt-3">
            <div className="mb-2 text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
              If the rest came from one instrument
            </div>
            <Row
              label="EU only"
              value={`${formatPips(calculateRequiredPips(missing, size.fxLots, settings.fxPipValuePerLot))} pips`}
              tone="accent"
            />
            <Row
              label="GU only"
              value={`${formatPips(calculateRequiredPips(missing, size.fxLots, settings.fxPipValuePerLot))} pips`}
              tone="accent"
            />
            <Row
              label="Gold only"
              value={formatGoldMove(
                calculateRequiredGoldMove(missing, size.goldLots, settings.goldContractSize),
                2,
              )}
              tone="accent"
            />
          </div>
        ) : null}

        <Button full className="mt-3" onClick={() => { setEu(0); setGu(0); setGold(0) }}>
          Reset gauges
        </Button>
      </Card>

      {/* Mix planner */}
      <Card>
        <CardTitle>Mix planner</CardTitle>
        <p className="mb-3 text-xs text-[var(--color-dim)]">
          Weights are shares of the <strong>dollar contribution</strong>, not of raw pips.
        </p>
        <div className="no-scrollbar -mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1">
          {MIX_PRESETS.map((p) => (
            <Chip key={p.id} active={preset === p.id} onClick={() => applyPreset(p.id)}>
              {p.label}
            </Chip>
          ))}
        </div>

        {preset === 'custom' ? (
          <div className="mt-3 space-y-3">
            {(['EURUSD', 'GBPUSD', 'XAUUSD'] as InstrumentId[]).map((i) => (
              <div key={i}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="font-semibold">{i}</span>
                  <span className="tabular text-[var(--color-dim)]">
                    {formatPct(weights[i] / sumWeights(weights))}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={weights[i]}
                  aria-label={`${i} weight`}
                  onChange={(e) =>
                    setWeights((w) => ({ ...w, [i]: Number(e.target.value) }))
                  }
                  className="w-full accent-[var(--color-accent)]"
                />
              </div>
            ))}
          </div>
        ) : null}

        <div className="mt-4 space-y-2">
          {(['EURUSD', 'GBPUSD', 'XAUUSD'] as InstrumentId[]).map((i) => {
            const isLocked = locked[i] !== undefined
            const required = mix.required[i]
            const contribution = mix.contribution[i]
            const display =
              i === 'XAUUSD'
                ? formatGoldMove(required, 2)
                : `${formatPips(required)} pips`
            return (
              <div
                key={i}
                className={cx(
                  'rounded-xl border p-3',
                  isLocked
                    ? 'border-[var(--color-accent)]/50 bg-[var(--color-accent)]/5'
                    : 'border-[var(--color-line)]',
                )}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold">{i}</div>
                    <div className="tabular text-xs text-[var(--color-dim)]">
                      {formatUsdSigned(contribution, 0)} contribution
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="tabular text-lg font-semibold">
                      {Number.isFinite(required) ? display : 'n/a'}
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        toggleLock(i, i === 'XAUUSD' ? gold || 15 : i === 'EURUSD' ? eu || 10 : gu || 12)
                      }
                      className="mt-1 text-xs font-semibold text-[var(--color-accent)]"
                    >
                      {isLocked ? 'Unlock' : 'Lock'}
                    </button>
                  </div>
                </div>
                {isLocked ? (
                  <div className="mt-2">
                    <NumberField
                      label="Locked at"
                      prefix={i === 'XAUUSD' ? '$' : undefined}
                      suffix={i === 'XAUUSD' ? 'move' : 'pips'}
                      value={locked[i] ?? 0}
                      onChange={(v) => setLocked((l) => ({ ...l, [i]: v ?? 0 }))}
                    />
                  </div>
                ) : null}
              </div>
            )
          })}
        </div>

        {mix.unreachable ? (
          <p className="mt-3 rounded-xl border border-[var(--color-warn)]/40 bg-[var(--color-warn)]/10 px-3 py-2 text-xs font-semibold text-[var(--color-warn)]">
            Every unlocked instrument has a zero weight — the remaining{' '}
            {formatUsd(mix.remaining, 2)} cannot be allocated.
          </p>
        ) : null}

        <div className="mt-3 border-t border-[var(--color-line)] pt-3">
          <Row label="Locked contribution" value={formatUsdSigned(mix.lockedPnl, 2)} />
          <Row label="Left to allocate" value={formatUsdSigned(mix.remaining, 2)} tone="accent" />
        </div>
      </Card>
    </div>
  )
}

function sumWeights(w: Weights): number {
  const s = w.EURUSD + w.GBPUSD + w.XAUUSD
  return s > 0 ? s : 1
}

function Gauge({
  label,
  unit,
  value,
  onChange,
  min,
  max,
  step,
  pnl,
}: {
  label: string
  unit: string
  value: number
  onChange: (next: number) => void
  min: number
  max: number
  step: number
  pnl: number
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
          {label}
        </span>
        <span
          className={cx(
            'tabular text-sm font-semibold',
            pnl > 0 ? 'text-[var(--color-pos)]' : pnl < 0 ? 'text-[var(--color-neg)]' : '',
          )}
        >
          {formatUsdSigned(pnl, 0)}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          aria-label={`${label} ${unit}`}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full accent-[var(--color-accent)]"
        />
        <input
          type="number"
          inputMode="decimal"
          value={value}
          aria-label={`${label} ${unit} value`}
          onChange={(e) => onChange(Number(e.target.value) || 0)}
          className="tabular min-h-10 w-20 shrink-0 rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-2)] px-2 text-right text-sm font-semibold outline-none"
        />
      </div>
      <div className="mt-0.5 text-right text-[10px] text-[var(--color-dim)]">{unit}</div>
    </div>
  )
}
