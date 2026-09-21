import { useMemo, useState } from 'react'
import { useApp } from '@/app/store'
import { LogDaySheet } from '@/features/journal/LogDaySheet'
import { Button, Card, CardTitle, ProgressBar, Row, Stat, cx, signTone } from '@/components/ui'
import {
  calculateBalancedScenario,
  calculateEquivalents,
} from '@/domain/calculations/weekly'
import { getNextTier, getSizingTier, tierProgress } from '@/domain/sizing/sizing'
import {
  formatGoldMove,
  formatLots,
  formatPct,
  formatPips,
  formatUsd,
  formatUsdCompact,
  formatUsdSigned,
} from '@/utils/format'
import { formatDayLabel, weekDates, weekdayShort } from '@/utils/date'

export function HomeScreen({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const { settings, derived } = useApp()
  const { ledger, weekly, challenge, size, today } = derived
  const [logOpen, setLogOpen] = useState(false)

  const todayRecord = ledger.byDate.get(today)
  const todayPnl = todayRecord?.tradingNet ?? 0
  const losses = todayRecord?.losses ?? 0
  const limitReached = losses >= settings.dailyLossLimit

  const equivalents = useMemo(
    () => calculateEquivalents(weekly.remaining, size, settings),
    [weekly.remaining, size, settings],
  )
  const balanced = useMemo(
    () => calculateBalancedScenario(weekly.remaining, size, settings),
    [weekly.remaining, size, settings],
  )

  const currentTier = getSizingTier(ledger.currentEquity, settings.tiers)
  const nextTier = getNextTier(ledger.currentEquity, settings.tiers)
  const tierRatio = tierProgress(ledger.currentEquity, settings.tiers)

  const recentDays = useMemo(
    () =>
      ledger.days
        .filter((d) => d.hasActivity)
        .slice(-5)
        .reverse(),
    [ledger.days],
  )

  const weekRecords = weekDates(today, settings.weekStart).map((date) => ({
    date,
    record: ledger.byDate.get(date),
  }))

  return (
    <div className="space-y-4">
      {/* Equity headline */}
      <section className="animate-fade-up pt-1">
        <div className="text-[11px] font-semibold tracking-[0.14em] text-[var(--color-muted)] uppercase">
          Current equity
        </div>
        <div className="tabular mt-1 text-5xl font-bold">
          {formatUsdCompact(ledger.currentEquity)}
        </div>
        <div className="mt-1.5 flex items-center gap-2 text-sm">
          <span className={cx('tabular font-semibold', signTone(ledger.totalTradingPnl) === 'pos' ? 'text-[var(--color-pos)]' : signTone(ledger.totalTradingPnl) === 'neg' ? 'text-[var(--color-neg)]' : '')}>
            {formatUsdSigned(ledger.totalTradingPnl, 0)}
          </span>
          <span className="text-[var(--color-dim)]">trading P&L since start</span>
        </div>
      </section>

      {/* Road to 500K */}
      <Card>
        <CardTitle
          right={
            <button
              type="button"
              onClick={() => onNavigate('road')}
              className="text-xs font-semibold text-[var(--color-accent)]"
            >
              Details →
            </button>
          }
        >
          Road to {formatUsdCompact(settings.targetCapital)}
        </CardTitle>
        <div className="flex items-end justify-between gap-4">
          <div className="tabular text-3xl font-bold">
            {formatPct(Math.max(0, challenge.progressRatio))}
          </div>
          <div className="text-right text-xs text-[var(--color-dim)]">
            <div>{challenge.daysRemaining} days left</div>
            <div>
              needs {formatPct(challenge.requiredWeeklyRate)}
              <span className="text-[var(--color-dim)]">/week</span>
            </div>
          </div>
        </div>
        <div className="mt-3">
          <ProgressBar ratio={challenge.progressRatio} label="Challenge progress" />
        </div>
        <div className="mt-2 flex items-center justify-between text-xs">
          <span className="text-[var(--color-dim)]">
            Trajectory today {formatUsd(challenge.trajectoryEquity, 0)}
          </span>
          <span
            className={cx(
              'tabular font-semibold',
              challenge.aheadBy >= 0 ? 'text-[var(--color-pos)]' : 'text-[var(--color-neg)]',
            )}
          >
            {challenge.aheadBy >= 0 ? '▲ ahead ' : '▼ behind '}
            {formatUsd(Math.abs(challenge.aheadBy), 0)}
          </span>
        </div>
      </Card>

      {/* Weekly target */}
      <Card>
        <CardTitle
          right={
            <span className="text-xs text-[var(--color-dim)]">
              {settings.weeklyTargetMode === 'fixedRate' ? 'fixed' : 'compound'}{' '}
              {formatPct(weekly.rate)}
            </span>
          }
        >
          Weekly target
        </CardTitle>
        <div className="grid grid-cols-3 gap-2">
          <Stat label="Target" value={formatUsdSigned(weekly.targetAmount, 0)} />
          <Stat
            label="Done"
            value={formatUsdSigned(weekly.done, 0)}
            tone={signTone(weekly.done)}
          />
          <Stat label="Remaining" value={formatUsd(weekly.remaining, 0)} tone="accent" />
        </div>
        <div className="mt-3">
          <ProgressBar
            ratio={weekly.progressRatio}
            tone={weekly.progressRatio >= 1 ? 'pos' : 'accent'}
            label="Weekly target progress"
            height="h-2.5"
          />
          <div className="mt-1.5 flex justify-between text-xs text-[var(--color-dim)]">
            <span className="tabular">{formatPct(weekly.progressRatio)}</span>
            <span>week ends at {formatUsd(weekly.targetEquity, 0)}</span>
          </div>
        </div>

        {weekly.remaining > 0 ? (
          <div className="mt-4">
            <div className="mb-2 text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
              Equivalent — at {formatLots(size.fxLots)} FX / {formatLots(size.goldLots)} Gold
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <Equivalent label="EU only" value={`${formatPips(equivalents.eurusdPips)} pips`} />
              <Equivalent label="GU only" value={`${formatPips(equivalents.gbpusdPips)} pips`} />
              <Equivalent label="Gold only" value={formatGoldMove(equivalents.goldMove, 1)} />
            </div>
          </div>
        ) : (
          <p className="mt-4 rounded-xl bg-[var(--color-pos)]/10 px-3 py-2 text-sm font-semibold text-[var(--color-pos)]">
            ✓ Weekly target reached. Process over pressure.
          </p>
        )}
      </Card>

      {/* Quick scenarios */}
      {weekly.remaining > 0 ? (
        <Card>
          <CardTitle>How can I finish the week?</CardTitle>
          <div className="space-y-0">
            <Row
              label="EU only"
              value={`${formatPips(equivalents.eurusdPips)} pips`}
              tone="accent"
            />
            <Row
              label="GU only"
              value={`${formatPips(equivalents.gbpusdPips)} pips`}
              tone="accent"
            />
            <Row
              label="Gold only"
              value={formatGoldMove(equivalents.goldMove, 1)}
              tone="accent"
            />
            <Row
              label="Balanced — equal $ contribution"
              value={
                <span className="tabular">
                  {formatPips(balanced.eurusdPips)} / {formatPips(balanced.gbpusdPips)} pips ·{' '}
                  {formatGoldMove(balanced.goldMove, 1)}
                </span>
              }
            />
          </div>
          <Button full className="mt-3" onClick={() => onNavigate('calculator')}>
            Open calculator
          </Button>
        </Card>
      ) : null}

      {/* Today */}
      <Card className={limitReached ? 'border-[var(--color-neg)]/50' : undefined}>
        <CardTitle right={<span className="text-xs text-[var(--color-dim)]">{formatDayLabel(today)}</span>}>
          Today
        </CardTitle>
        <div className="flex items-end justify-between gap-4">
          <Stat
            label="P&L"
            value={formatUsdSigned(todayPnl, 0)}
            tone={signTone(todayPnl)}
            size="lg"
          />
          <div className="text-right">
            <div className="text-[10px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
              Losses
            </div>
            <div
              className={cx(
                'tabular mt-0.5 text-xl font-semibold',
                limitReached ? 'text-[var(--color-neg)]' : 'text-[var(--color-text)]',
              )}
            >
              {limitReached ? `${losses}/${settings.dailyLossLimit} STOP` : `${losses}/${settings.dailyLossLimit}`}
            </div>
          </div>
        </div>

        <div className="mt-3 flex gap-1.5">
          {Array.from({ length: settings.dailyLossLimit }, (_, i) => (
            <span
              key={i}
              aria-hidden="true"
              className={cx(
                'h-1.5 flex-1 rounded-full',
                i < losses ? 'bg-[var(--color-neg)]' : 'bg-[var(--color-surface-2)]',
              )}
            />
          ))}
        </div>

        {limitReached ? (
          <p className="mt-3 rounded-xl border border-[var(--color-neg)]/40 bg-[var(--color-neg)]/10 px-3 py-2.5 text-sm font-semibold text-[var(--color-neg)]">
            Daily loss limit reached. The day is done — the weekly target waits for tomorrow.
          </p>
        ) : null}

        {todayRecord && todayRecord.tradesAfterLimit.length > 0 ? (
          <p className="mt-2 rounded-xl border border-[var(--color-warn)]/40 bg-[var(--color-warn)]/10 px-3 py-2 text-xs font-semibold text-[var(--color-warn)]">
            {todayRecord.tradesAfterLimit.length} trade(s) taken after the daily limit ·{' '}
            {formatUsdSigned(todayRecord.pnlAfterLimit, 0)}
          </p>
        ) : null}

        <div className="mt-3 grid grid-cols-2 gap-2 border-t border-[var(--color-line)] pt-3">
          <Stat label="EU / GU sizing" value={`${formatLots(size.fxLots)} lots`} size="sm" />
          <Stat label="Gold sizing" value={`${formatLots(size.goldLots)} lots`} size="sm" />
        </div>
      </Card>

      <Button full size="lg" variant="primary" onClick={() => setLogOpen(true)}>
        + LOG TODAY
      </Button>

      {/* Tier progress */}
      {nextTier ? (
        <Card>
          <CardTitle right={<span className="text-xs text-[var(--color-dim)]">next palier</span>}>
            {currentTier ? formatUsdCompact(currentTier.minEquity) : '—'} →{' '}
            {formatUsdCompact(nextTier.minEquity)}
          </CardTitle>
          <ProgressBar ratio={tierRatio} label="Progress to next sizing tier" />
          <div className="mt-2 flex justify-between text-xs text-[var(--color-dim)]">
            <span>
              now {formatLots(currentTier?.fxLots ?? 0)} FX / {formatLots(currentTier?.goldLots ?? 0)}{' '}
              Gold
            </span>
            <span>
              then {formatLots(nextTier.fxLots)} FX / {formatLots(nextTier.goldLots)} Gold
            </span>
          </div>
        </Card>
      ) : null}

      {/* Week strip */}
      <Card>
        <CardTitle>This week</CardTitle>
        <div className="grid grid-cols-7 gap-1">
          {weekRecords.map(({ date, record }) => {
            const pnl = record?.tradingNet ?? 0
            const active = Boolean(record?.hasActivity)
            return (
              <div key={date} className="text-center">
                <div className="text-[10px] font-semibold text-[var(--color-dim)]">
                  {weekdayShort(date).slice(0, 3)}
                </div>
                <div
                  className={cx(
                    'mt-1 rounded-lg py-2 text-[10px] font-semibold',
                    !active
                      ? 'bg-[var(--color-surface-2)] text-[var(--color-dim)]'
                      : pnl > 0
                        ? 'bg-[var(--color-pos)]/15 text-[var(--color-pos)]'
                        : pnl < 0
                          ? 'bg-[var(--color-neg)]/15 text-[var(--color-neg)]'
                          : 'bg-[var(--color-surface-2)] text-[var(--color-muted)]',
                  )}
                >
                  {active ? formatUsdSigned(pnl, 0).replace('$', '') : '–'}
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Recent days */}
      <Card>
        <CardTitle
          right={
            <button
              type="button"
              onClick={() => onNavigate('journal')}
              className="text-xs font-semibold text-[var(--color-accent)]"
            >
              All days →
            </button>
          }
        >
          Recent
        </CardTitle>
        {recentDays.length === 0 ? (
          <p className="py-4 text-center text-sm text-[var(--color-dim)]">
            No day logged yet. Tap “+ LOG TODAY”.
          </p>
        ) : (
          <div>
            {recentDays.map((d) => (
              <Row
                key={d.date}
                label={
                  <span>
                    <span className="font-semibold text-[var(--color-text)]">
                      {weekdayShort(d.date)}
                    </span>{' '}
                    <span className="text-[var(--color-dim)]">{formatDayLabel(d.date)}</span>
                  </span>
                }
                value={formatUsdSigned(d.tradingNet, 0)}
                tone={signTone(d.tradingNet)}
              />
            ))}
          </div>
        )}
      </Card>

      <LogDaySheet open={logOpen} onClose={() => setLogOpen(false)} date={today} />
    </div>
  )
}

function Equivalent({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] px-2 py-2.5">
      <div className="text-[10px] font-semibold text-[var(--color-dim)] uppercase">{label}</div>
      <div className="tabular mt-0.5 text-sm font-semibold">{value}</div>
    </div>
  )
}
