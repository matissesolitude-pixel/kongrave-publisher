import { useMemo, useState } from 'react'
import { useApp } from '@/app/store'
import { Button, Card, CardTitle, EmptyState, Segmented, cx, signTone } from '@/components/ui'
import { DayDetailSheet } from './DayDetailSheet'
import { LogDaySheet } from './LogDaySheet'
import type { IsoDate } from '@/domain/models/types'
import {
  addMonths,
  formatDayLabel,
  monthGrid,
  monthLabel,
  sameMonth,
  todayIso,
  weekdayShort,
} from '@/utils/date'
import { formatUsdSigned } from '@/utils/format'

type View = 'calendar' | 'list'

const WEEKDAY_ORDER = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'] as const

export function JournalScreen() {
  const { settings, derived } = useApp()
  const [view, setView] = useState<View>('calendar')
  const [month, setMonth] = useState<IsoDate>(() => todayIso())
  const [selected, setSelected] = useState<IsoDate | null>(null)
  const [logOpen, setLogOpen] = useState(false)

  const grid = useMemo(() => monthGrid(month, settings.weekStart), [month, settings.weekStart])

  const headers = useMemo(() => {
    const order: string[] = []
    for (let i = 0; i < 7; i += 1) {
      order.push(WEEKDAY_ORDER[(settings.weekStart + i) % 7] ?? '')
    }
    return order
  }, [settings.weekStart])

  const loggedDays = useMemo(
    () => derived.ledger.days.filter((d) => d.hasActivity).slice().reverse(),
    [derived.ledger.days],
  )

  return (
    <div className="space-y-4">
      <Segmented
        ariaLabel="Journal view"
        value={view}
        onChange={setView}
        options={[
          { value: 'calendar', label: 'Calendar' },
          { value: 'list', label: 'List' },
        ]}
      />

      {view === 'calendar' ? (
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <Button size="sm" onClick={() => setMonth((m) => addMonths(m, -1))} aria-label="Previous month">
              ←
            </Button>
            <h2 className="text-sm font-semibold capitalize">{monthLabel(month)}</h2>
            <Button size="sm" onClick={() => setMonth((m) => addMonths(m, 1))} aria-label="Next month">
              →
            </Button>
          </div>

          <div className="mb-1 grid grid-cols-7 gap-1 text-center text-[10px] font-semibold text-[var(--color-dim)]">
            {headers.map((h) => (
              <div key={h}>{h.slice(0, 1)}</div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {grid.map((date) => {
              const record = derived.ledger.byDate.get(date)
              const active = Boolean(record?.hasActivity)
              const pnl = record?.tradingNet ?? 0
              const inMonth = sameMonth(date, month)
              const isToday = date === derived.today
              return (
                <button
                  key={date}
                  type="button"
                  onClick={() => setSelected(date)}
                  aria-label={`${date}${active ? `, ${formatUsdSigned(pnl, 0)}` : ', no trade'}`}
                  className={cx(
                    'relative aspect-square rounded-lg border text-[11px] font-semibold transition active:scale-[0.96]',
                    inMonth ? 'opacity-100' : 'opacity-30',
                    isToday ? 'border-[var(--color-accent)]' : 'border-transparent',
                    !active
                      ? 'bg-[var(--color-surface-2)] text-[var(--color-dim)]'
                      : pnl > 0
                        ? 'bg-[var(--color-pos)]/15 text-[var(--color-pos)]'
                        : pnl < 0
                          ? 'bg-[var(--color-neg)]/15 text-[var(--color-neg)]'
                          : 'bg-[var(--color-surface-2)] text-[var(--color-muted)]',
                  )}
                >
                  <span className="absolute top-1 left-1.5 text-[10px] opacity-70">
                    {Number(date.slice(8, 10))}
                  </span>
                  {active ? (
                    <span className="tabular absolute inset-x-0 bottom-1 text-[9px]">
                      {pnl > 0 ? '▲' : pnl < 0 ? '▼' : '–'}
                    </span>
                  ) : null}
                </button>
              )
            })}
          </div>

          <div className="mt-3 flex justify-center gap-4 text-[10px] text-[var(--color-dim)]">
            <Legend className="bg-[var(--color-pos)]/40" label="▲ positive" />
            <Legend className="bg-[var(--color-neg)]/40" label="▼ negative" />
            <Legend className="bg-[var(--color-surface-2)]" label="– flat / no trade" />
          </div>
        </Card>
      ) : (
        <Card>
          <CardTitle>{loggedDays.length} logged days</CardTitle>
          {loggedDays.length === 0 ? (
            <EmptyState title="Nothing logged yet" body="Log a day to start the equity curve." />
          ) : (
            <ul className="divide-y divide-[var(--color-line)]">
              {loggedDays.map((d) => (
                <li key={d.date}>
                  <button
                    type="button"
                    onClick={() => setSelected(d.date)}
                    className="flex w-full items-center justify-between gap-3 py-3 text-left"
                  >
                    <span>
                      <span className="block text-sm font-semibold">
                        {weekdayShort(d.date)} {formatDayLabel(d.date)}
                      </span>
                      <span className="tabular block text-xs text-[var(--color-dim)]">
                        {d.tradeCount > 0
                          ? `${d.tradeCount} trades · ${d.wins}W / ${d.losses}L`
                          : d.entry
                            ? `EU ${d.entry.eurusdPips} · GU ${d.entry.gbpusdPips} · Gold ${d.entry.xauusdMove}`
                            : 'cash movement'}
                      </span>
                    </span>
                    <span
                      className={cx(
                        'tabular text-sm font-semibold',
                        signTone(d.tradingNet) === 'pos'
                          ? 'text-[var(--color-pos)]'
                          : signTone(d.tradingNet) === 'neg'
                            ? 'text-[var(--color-neg)]'
                            : '',
                      )}
                    >
                      {formatUsdSigned(d.tradingNet, 0)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <Button full size="lg" variant="primary" onClick={() => setLogOpen(true)}>
        + LOG A DAY
      </Button>

      <DayDetailSheet date={selected} onClose={() => setSelected(null)} />
      <LogDaySheet open={logOpen} onClose={() => setLogOpen(false)} />
    </div>
  )
}

function Legend({ className, label }: { className: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className={cx('inline-block h-2 w-2 rounded-sm', className)} aria-hidden="true" />
      {label}
    </span>
  )
}
