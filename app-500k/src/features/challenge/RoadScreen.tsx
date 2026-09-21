import { useMemo } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useApp } from '@/app/store'
import { Button, Card, CardTitle, ProgressBar, Row, Stat, cx } from '@/components/ui'
import { generateCheckpoints, trajectoryEquityAt } from '@/domain/calculations/challenge'
import { DISCLAIMER } from '@/domain/models/defaults'
import { formatDayLabel } from '@/utils/date'
import { formatPct, formatUsd, formatUsdAxis, formatUsdSigned } from '@/utils/format'

interface Point {
  date: string
  label: string
  trajectory: number
  actual: number | null
}

export function RoadScreen({ onBack }: { onBack: () => void }) {
  const { settings, derived } = useApp()
  const { ledger, challenge, today } = derived

  const checkpoints = useMemo(
    () => generateCheckpoints(settings, ledger, today),
    [settings, ledger, today],
  )

  const chartData = useMemo<Point[]>(() => {
    const points: Point[] = [
      {
        date: settings.startDate,
        label: formatDayLabel(settings.startDate),
        trajectory: settings.startingCapital,
        actual: settings.startingCapital,
      },
    ]
    for (const c of checkpoints) {
      points.push({
        date: c.date,
        label: formatDayLabel(c.date),
        trajectory: c.equity,
        actual: c.actual,
      })
    }
    // Always show today's real equity, even between two checkpoints.
    if (today > settings.startDate && today < settings.targetDate) {
      points.push({
        date: today,
        label: formatDayLabel(today),
        trajectory: trajectoryEquityAt(settings, today),
        actual: ledger.currentEquity,
      })
    }
    return points.sort((a, b) => (a.date < b.date ? -1 : 1))
  }, [checkpoints, settings, today, ledger.currentEquity])

  const ahead = challenge.aheadBy >= 0

  return (
    <div className="space-y-4">
      <Button variant="ghost" onClick={onBack} className="-ml-2">
        ← Back
      </Button>

      <Card>
        <CardTitle>Road to {formatUsd(settings.targetCapital, 0)}</CardTitle>
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Starting equity" value={formatUsd(challenge.startingCapital, 0)} />
          <Stat label="Current equity" value={formatUsd(challenge.currentEquity, 0)} />
          <Stat label="Target" value={formatUsd(challenge.targetCapital, 0)} size="sm" />
          <Stat label="Days remaining" value={String(challenge.daysRemaining)} size="sm" />
        </div>
        <div className="mt-3">
          <ProgressBar ratio={challenge.progressRatio} label="Challenge progress" />
          <div className="mt-1.5 flex justify-between text-xs text-[var(--color-dim)]">
            <span className="tabular">{formatPct(Math.max(0, challenge.progressRatio))}</span>
            <span>
              {formatDayLabel(settings.startDate)} → {formatDayLabel(settings.targetDate)}
            </span>
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle>Rates</CardTitle>
        <Row
          label="Required compound weekly return"
          value={
            Number.isFinite(challenge.requiredWeeklyRate)
              ? formatPct(challenge.requiredWeeklyRate)
              : 'n/a'
          }
          tone="accent"
        />
        <Row label="Planned rate (start → target)" value={formatPct(challenge.plannedWeeklyRate)} />
        <Row
          label="Actual average weekly return"
          value={
            challenge.actualWeeklyRate === null ? '—' : formatPct(challenge.actualWeeklyRate)
          }
          tone={
            challenge.actualWeeklyRate === null
              ? 'neutral'
              : challenge.actualWeeklyRate >= challenge.plannedWeeklyRate
                ? 'pos'
                : 'neg'
          }
        />
        <Row
          label="Trajectory today"
          value={formatUsd(challenge.trajectoryEquity, 0)}
        />
        <Row
          label={ahead ? '▲ Ahead of trajectory' : '▼ Behind trajectory'}
          value={`${formatUsdSigned(challenge.aheadBy, 0)} · ${formatPct(challenge.aheadRatio)}`}
          tone={ahead ? 'pos' : 'neg'}
        />
      </Card>

      <Card>
        <CardTitle>Required trajectory vs. actual equity</CardTitle>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
              <CartesianGrid stroke="var(--color-line)" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: 'var(--color-dim)', fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                minTickGap={24}
              />
              <YAxis
                scale="log"
                domain={['auto', 'auto']}
                tickFormatter={formatUsdAxis}
                tick={{ fill: 'var(--color-dim)', fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                width={48}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-line)',
                  borderRadius: 12,
                  fontSize: 12,
                }}
                labelStyle={{ color: 'var(--color-muted)' }}
                formatter={(value, name) => [
                  formatUsd(Number(value ?? 0), 0),
                  String(name) === 'trajectory' ? 'Required' : 'Actual',
                ]}
              />
              <Line
                type="monotone"
                dataKey="trajectory"
                stroke="var(--color-accent)"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="var(--color-pos)"
                strokeWidth={2.5}
                dot={false}
                connectNulls
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex justify-center gap-4 text-[11px] text-[var(--color-dim)]">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 bg-[var(--color-accent)]" aria-hidden="true" />
            Required (dashed)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 bg-[var(--color-pos)]" aria-hidden="true" />
            Actual
          </span>
        </div>
        <p className="mt-1 text-center text-[10px] text-[var(--color-dim)]">Logarithmic scale.</p>
      </Card>

      <Card>
        <CardTitle>Checkpoints</CardTitle>
        <p className="mb-2 text-xs text-[var(--color-dim)]">
          Generated from the exact compound rate between {formatDayLabel(settings.startDate)} and{' '}
          {formatDayLabel(settings.targetDate)}.
        </p>
        <div className="divide-y divide-[var(--color-line)]">
          {checkpoints.map((c) => {
            const delta = c.actual === null ? null : c.actual - c.equity
            return (
              <div key={c.date} className="flex items-center justify-between gap-3 py-2.5">
                <span className="text-sm text-[var(--color-muted)]">{formatDayLabel(c.date)}</span>
                <span className="text-right">
                  <span className="tabular block text-sm font-semibold">
                    {formatUsd(c.equity, 0)}
                  </span>
                  {delta !== null ? (
                    <span
                      className={cx(
                        'tabular block text-xs font-semibold',
                        delta >= 0 ? 'text-[var(--color-pos)]' : 'text-[var(--color-neg)]',
                      )}
                    >
                      {delta >= 0 ? '▲' : '▼'} {formatUsdSigned(delta, 0)}
                    </span>
                  ) : null}
                </span>
              </div>
            )
          })}
        </div>
      </Card>

      <p className="px-1 pb-2 text-[11px] leading-relaxed text-[var(--color-dim)]">{DISCLAIMER}</p>
    </div>
  )
}
