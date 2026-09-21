import { useState } from 'react'
import { Sheet, ConfirmDialog } from '@/components/Sheet'
import { Button, Card, CardTitle, Row, Stat, cx, signTone } from '@/components/ui'
import { useToast } from '@/components/Toast'
import { useApp } from '@/app/store'
import { LogDaySheet } from './LogDaySheet'
import { TradeFormSheet } from './TradeFormSheet'
import type { IsoDate, Trade } from '@/domain/models/types'
import { EMOTION_LABEL, INSTRUMENT_SHORT } from '@/domain/models/types'
import { grossTradePnl, fullPositionEquivalentGoldMove, fullPositionEquivalentPips } from '@/domain/calculations/pnl'
import { addDays, formatFullDate } from '@/utils/date'
import {
  formatGoldMoveSigned,
  formatLots,
  formatPipsSigned,
  formatUsdSigned,
} from '@/utils/format'

/** Full detail of one day: summary, trades, rules, psychology, actions. */
export function DayDetailSheet({
  date,
  onClose,
}: {
  date: IsoDate | null
  onClose: () => void
}) {
  const { derived, settings, deleteDay, duplicateDay, deleteTrade } = useApp()
  const toast = useToast()
  const [editOpen, setEditOpen] = useState(false)
  const [tradeOpen, setTradeOpen] = useState(false)
  const [editingTrade, setEditingTrade] = useState<Trade | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [confirmTrade, setConfirmTrade] = useState<Trade | null>(null)

  const record = date ? derived.ledger.byDate.get(date) : null

  if (!date) return null

  const net = record?.tradingNet ?? 0
  const limitReached = (record?.losses ?? 0) >= settings.dailyLossLimit

  const onDuplicate = async () => {
    const target = addDays(date, 1)
    await duplicateDay(date, target)
    toast.show(`Duplicated to ${target} ✓`)
  }

  return (
    <>
      <Sheet
        open={Boolean(date) && !editOpen && !tradeOpen}
        title={formatFullDate(date)}
        onClose={onClose}
        footer={
          <div className="grid grid-cols-3 gap-2">
            <Button onClick={() => setEditOpen(true)}>Edit</Button>
            <Button onClick={() => void onDuplicate()}>Duplicate</Button>
            <Button variant="danger" onClick={() => setConfirmDelete(true)}>
              Delete
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Card>
            <div className="flex items-end justify-between">
              <Stat label="Net P&L" value={formatUsdSigned(net, 2)} tone={signTone(net)} size="lg" />
              <div className="text-right text-xs text-[var(--color-dim)]">
                <div>Gross {formatUsdSigned(record?.breakdown.gross ?? 0, 2)}</div>
                <div>Fees {formatUsdSigned(-(record?.fees ?? 0), 2)}</div>
                <div className="mt-1">
                  {formatLots(record?.size.fxLots ?? 0)} FX ·{' '}
                  {formatLots(record?.size.goldLots ?? 0)} Gold
                </div>
              </div>
            </div>
            <div className="mt-3 border-t border-[var(--color-line)] pt-3">
              <Row
                label="P&L source"
                value={record?.source === 'trades' ? 'Detailed trades' : 'Manual daily P&L'}
              />
              <Row
                label="Equity"
                value={`${formatUsdSigned(record?.equityOpen ?? 0, 0)} → ${formatUsdSigned(
                  record?.equityClose ?? 0,
                  0,
                )}`}
              />
              <Row
                label="Losses"
                value={`${record?.losses ?? 0} / ${settings.dailyLossLimit}`}
                tone={limitReached ? 'neg' : 'neutral'}
              />
            </div>
          </Card>

          {record?.entry ? (
            <Card>
              <CardTitle>Daily results</CardTitle>
              <Row
                label="EURUSD"
                value={formatPipsSigned(record.entry.eurusdPips)}
                tone={signTone(record.entry.eurusdPips)}
              />
              <Row
                label="GBPUSD"
                value={formatPipsSigned(record.entry.gbpusdPips)}
                tone={signTone(record.entry.gbpusdPips)}
              />
              <Row
                label="XAUUSD"
                value={formatGoldMoveSigned(record.entry.xauusdMove, 1)}
                tone={signTone(record.entry.xauusdMove)}
              />
              <Row label="Commission" value={formatUsdSigned(-record.entry.commission, 2)} />
              <Row label="Swap" value={formatUsdSigned(-record.entry.swap, 2)} />
              <Row label="Other fees" value={formatUsdSigned(-record.entry.fees, 2)} />
            </Card>
          ) : null}

          <Card>
            <CardTitle
              right={
                <button
                  type="button"
                  className="text-xs font-semibold text-[var(--color-accent)]"
                  onClick={() => {
                    setEditingTrade(null)
                    setTradeOpen(true)
                  }}
                >
                  + Add trade
                </button>
              }
            >
              Trades ({record?.trades.length ?? 0})
            </CardTitle>
            {!record || record.trades.length === 0 ? (
              <p className="py-3 text-center text-sm text-[var(--color-dim)]">
                No detailed trade for this day.
              </p>
            ) : (
              <ul className="space-y-2">
                {record.trades.map((t) => {
                  const pnl = grossTradePnl(t, settings) - t.fees
                  const afterLimit = record.tradesAfterLimit.some((x) => x.id === t.id)
                  const equivalent =
                    t.instrument === 'XAUUSD'
                      ? `${formatGoldMoveSigned(
                          fullPositionEquivalentGoldMove(
                            pnl,
                            record.size.goldLots,
                            settings.goldContractSize,
                          ),
                          1,
                        )} full-size`
                      : `${formatPipsSigned(
                          fullPositionEquivalentPips(
                            pnl,
                            record.size.fxLots,
                            settings.fxPipValuePerLot,
                          ),
                        )} pips full-size`
                  return (
                    <li
                      key={t.id}
                      className={cx(
                        'rounded-xl border p-3',
                        afterLimit
                          ? 'border-[var(--color-warn)]/50 bg-[var(--color-warn)]/5'
                          : 'border-[var(--color-line)]',
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold">
                            {INSTRUMENT_SHORT[t.instrument]} · {t.direction === 'long' ? 'Long' : 'Short'}{' '}
                            · {t.outcome}
                          </div>
                          <div className="tabular mt-0.5 text-xs text-[var(--color-dim)]">
                            {t.instrument === 'XAUUSD'
                              ? formatGoldMoveSigned(t.result, 1)
                              : `${formatPipsSigned(t.result)} pips`}{' '}
                            · {formatLots(t.lots)} lots
                            {t.time ? ` · ${t.time}` : ''}
                          </div>
                          <div className="tabular mt-0.5 text-xs text-[var(--color-dim)]">
                            {equivalent}
                          </div>
                        </div>
                        <div
                          className={cx(
                            'tabular text-sm font-semibold',
                            pnl > 0
                              ? 'text-[var(--color-pos)]'
                              : pnl < 0
                                ? 'text-[var(--color-neg)]'
                                : '',
                          )}
                        >
                          {formatUsdSigned(pnl, 2)}
                        </div>
                      </div>
                      {afterLimit ? (
                        <p className="mt-2 text-xs font-semibold text-[var(--color-warn)]">
                          Trade taken after the daily limit.
                        </p>
                      ) : null}
                      {t.comment ? (
                        <p className="mt-2 text-xs text-[var(--color-muted)]">{t.comment}</p>
                      ) : null}
                      <div className="mt-2 flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => {
                            setEditingTrade(t)
                            setTradeOpen(true)
                          }}
                        >
                          Edit
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => setConfirmTrade(t)}>
                          Delete
                        </Button>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </Card>

          {record?.entry &&
          (record.entry.notes ||
            record.entry.whatHappened ||
            record.entry.emotion ||
            record.entry.executionScore !== null ||
            record.entry.disciplineScore !== null) ? (
            <Card>
              <CardTitle>Notes & psychology</CardTitle>
              {record.entry.executionScore !== null ? (
                <Row label="Execution" value={`${record.entry.executionScore}/5`} />
              ) : null}
              {record.entry.disciplineScore !== null ? (
                <Row label="Discipline" value={`${record.entry.disciplineScore}/5`} />
              ) : null}
              {record.entry.emotion ? (
                <Row label="Emotion" value={EMOTION_LABEL[record.entry.emotion]} />
              ) : null}
              {record.entry.notes ? (
                <p className="mt-3 text-sm text-[var(--color-muted)]">{record.entry.notes}</p>
              ) : null}
              {record.entry.whatHappened ? (
                <p className="mt-2 text-sm text-[var(--color-muted)]">
                  {record.entry.whatHappened}
                </p>
              ) : null}
            </Card>
          ) : null}

          {record && record.cashflows.length > 0 ? (
            <Card>
              <CardTitle>Cash movements</CardTitle>
              {record.cashflows.map((c) => (
                <Row
                  key={c.id}
                  label={`${c.type}${c.note ? ` — ${c.note}` : ''}`}
                  value={formatUsdSigned(
                    c.type === 'withdrawal' || c.type === 'fee' ? -c.amount : c.amount,
                    2,
                  )}
                />
              ))}
            </Card>
          ) : null}
        </div>
      </Sheet>

      <LogDaySheet open={editOpen} onClose={() => setEditOpen(false)} date={date} />
      <TradeFormSheet
        open={tradeOpen}
        onClose={() => {
          setTradeOpen(false)
          setEditingTrade(null)
        }}
        date={date}
        trade={editingTrade}
      />

      <ConfirmDialog
        open={confirmDelete}
        destructive
        title="Delete this day?"
        message="The daily summary and every detailed trade of this day will be removed. The equity curve is recalculated from this date onwards."
        confirmLabel="Delete day"
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => {
          void deleteDay(date, true).then(() => {
            toast.show('Day deleted', 'neg')
            setConfirmDelete(false)
            onClose()
          })
        }}
      />

      <ConfirmDialog
        open={Boolean(confirmTrade)}
        destructive
        title="Delete this trade?"
        message="This trade is removed and every statistic recalculated."
        confirmLabel="Delete trade"
        onCancel={() => setConfirmTrade(null)}
        onConfirm={() => {
          if (!confirmTrade) return
          void deleteTrade(confirmTrade.id).then(() => {
            toast.show('Trade deleted', 'neg')
            setConfirmTrade(null)
          })
        }}
      />
    </>
  )
}
