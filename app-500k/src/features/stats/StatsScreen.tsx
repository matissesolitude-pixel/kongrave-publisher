import { useMemo } from 'react'
import { useApp } from '@/app/store'
import { Card, CardTitle, EmptyState, Row, Stat, cx, signTone } from '@/components/ui'
import {
  calculateDisciplineStats,
  calculateEmotionStats,
  calculateLedgerStats,
  calculateTradeStats,
} from '@/domain/calculations/stats'
import { EMOTION_LABEL, INSTRUMENT_SHORT } from '@/domain/models/types'
import { formatDayLabel } from '@/utils/date'
import {
  formatNumber,
  formatPct,
  formatR,
  formatUsd,
  formatUsdSigned,
} from '@/utils/format'

/** A drawdown of zero reads as "0.0%", never as "-0.0%". */
function ddLabel(pct: number): string {
  return pct > 0 ? `-${formatPct(pct)}` : '0.0%'
}

export function StatsScreen() {
  const { settings, derived } = useApp()
  const { ledger, weeks, drawdown } = derived

  const tradeStats = useMemo(() => calculateTradeStats(ledger, settings), [ledger, settings])
  const ledgerStats = useMemo(() => calculateLedgerStats(ledger, weeks), [ledger, weeks])
  const emotions = useMemo(() => calculateEmotionStats(ledger, EMOTION_LABEL), [ledger])
  const discipline = useMemo(() => calculateDisciplineStats(ledger), [ledger])

  const activeWeeks = weeks.filter((w) => w.loggedDays > 0)
  const wrConvention =
    settings.winRateConvention === 'includeBE'
      ? 'wins / (wins + losses + BE)'
      : 'wins / (wins + losses) — BE excluded'

  return (
    <div className="space-y-4">
      <Card>
        <CardTitle>Account</CardTitle>
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Current equity" value={formatUsd(ledger.currentEquity, 0)} />
          <Stat
            label="Trading P&L"
            value={formatUsdSigned(ledger.totalTradingPnl, 0)}
            tone={signTone(ledger.totalTradingPnl)}
          />
          <Stat label="Deposits" value={formatUsd(ledger.totalDeposits, 0)} size="sm" />
          <Stat label="Withdrawals" value={formatUsd(ledger.totalWithdrawals, 0)} size="sm" />
          <Stat label="Fees" value={formatUsd(ledger.totalFees, 0)} size="sm" />
          <Stat label="Days logged" value={String(ledgerStats.loggedDays)} size="sm" />
        </div>
      </Card>

      <Card>
        <CardTitle>Drawdown</CardTitle>
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Peak equity" value={formatUsd(drawdown.peakEquity, 0)} />
          <Stat
            label="Current DD"
            value={ddLabel(drawdown.currentDrawdownPct)}
            tone={drawdown.currentDrawdownPct > 0 ? 'neg' : 'neutral'}
            hint={formatUsd(drawdown.currentDrawdown, 0)}
          />
          <Stat
            label="Max DD"
            value={ddLabel(drawdown.maxDrawdownPct)}
            tone={drawdown.maxDrawdownPct > 0 ? 'neg' : 'neutral'}
            size="sm"
            hint={
              drawdown.maxDrawdownDate ? formatDayLabel(drawdown.maxDrawdownDate) : 'never'
            }
          />
          <Stat
            label="Daily DD"
            value={ddLabel(drawdown.dailyDrawdownPct)}
            size="sm"
            tone={drawdown.dailyDrawdownPct > 0 ? 'neg' : 'neutral'}
          />
          <Stat
            label="Weekly DD"
            value={ddLabel(drawdown.weeklyDrawdownPct)}
            size="sm"
            tone={drawdown.weeklyDrawdownPct > 0 ? 'neg' : 'neutral'}
          />
        </div>
      </Card>

      <Card>
        <CardTitle right={<span className="text-[10px] text-[var(--color-dim)]">detailed trades</span>}>
          Trade statistics
        </CardTitle>
        {tradeStats.totalTrades === 0 ? (
          <EmptyState
            title="N/A — detailed trades required."
            body="Quick daily entries never invent a win rate. Add individual trades to unlock these metrics."
          />
        ) : (
          <>
            <div className="grid grid-cols-3 gap-3">
              <Stat label="Trades" value={String(tradeStats.totalTrades)} />
              <Stat
                label="Win rate"
                value={tradeStats.winRate === null ? 'N/A' : formatPct(tradeStats.winRate)}
              />
              <Stat
                label="Trades P&L"
                value={formatUsdSigned(tradeStats.netPnl, 0)}
                tone={signTone(tradeStats.netPnl)}
              />
            </div>
            <div className="mt-3">
              <Row label="Wins / Losses / BE" value={`${tradeStats.wins} / ${tradeStats.losses} / ${tradeStats.breakEvens}`} />
              <Row
                label="Average winner"
                value={tradeStats.averageWinner === null ? '—' : formatUsdSigned(tradeStats.averageWinner, 2)}
                tone="pos"
              />
              <Row
                label="Average loser"
                value={tradeStats.averageLoser === null ? '—' : formatUsdSigned(tradeStats.averageLoser, 2)}
                tone="neg"
              />
              <Row
                label="Profit factor"
                value={
                  tradeStats.profitFactor === null
                    ? '—'
                    : Number.isFinite(tradeStats.profitFactor)
                      ? formatNumber(tradeStats.profitFactor, 2)
                      : '∞'
                }
              />
              <Row
                label="Expectancy / trade"
                value={tradeStats.expectancy === null ? '—' : formatUsdSigned(tradeStats.expectancy, 2)}
                tone={tradeStats.expectancy !== null ? signTone(tradeStats.expectancy) : 'neutral'}
              />
              <Row
                label="Average R"
                value={tradeStats.averageR === null ? '—' : formatR(tradeStats.averageR)}
              />
              <Row
                label="Streak now"
                value={
                  tradeStats.currentWinStreak > 0
                    ? `${tradeStats.currentWinStreak}W`
                    : tradeStats.currentLossStreak > 0
                      ? `${tradeStats.currentLossStreak}L`
                      : '—'
                }
                tone={tradeStats.currentWinStreak > 0 ? 'pos' : tradeStats.currentLossStreak > 0 ? 'neg' : 'neutral'}
              />
              <Row label="Max win streak" value={String(tradeStats.maxWinStreak)} />
              <Row label="Max losing streak" value={String(tradeStats.maxLossStreak)} tone="neg" />
            </div>
            <p className="mt-3 text-[11px] text-[var(--color-dim)]">
              Win rate convention: {wrConvention}. “Trades P&amp;L” sums the detailed trades only —
              days whose source is the manual daily P&amp;L keep their own result in the account
              totals above, and the two are never added together.
            </p>
          </>
        )}
      </Card>

      <Card>
        <CardTitle>Rule compliance</CardTitle>
        <Row
          label={`Trades after the ${settings.dailyLossLimit}-loss limit`}
          value={String(tradeStats.tradesAfterLossLimit)}
          tone={tradeStats.tradesAfterLossLimit > 0 ? 'warn' : 'pos'}
        />
        <Row
          label="P&L after the limit"
          value={formatUsdSigned(tradeStats.pnlAfterLossLimit, 2)}
          tone={signTone(tradeStats.pnlAfterLossLimit)}
        />
        <Row
          label="Days respecting the limit"
          value={
            ledgerStats.complianceRatio === null
              ? '—'
              : `${ledgerStats.compliantDays}/${ledgerStats.loggedDays} · ${formatPct(ledgerStats.complianceRatio)}`
          }
          tone={ledgerStats.complianceRatio === 1 ? 'pos' : 'neutral'}
        />
        <Row
          label="Checklist compliance"
          value={
            ledgerStats.checklistCompliance === null
              ? '—'
              : formatPct(ledgerStats.checklistCompliance)
          }
        />
        <p className="mt-3 text-[11px] text-[var(--color-dim)]">
          Discipline is scored on process, never blended with P&L.
        </p>
      </Card>

      <Card>
        <CardTitle>By instrument</CardTitle>
        {tradeStats.totalTrades === 0 ? (
          <EmptyState title="N/A — detailed trades required." />
        ) : (
          <div className="space-y-3">
            {tradeStats.byInstrument.map((s) => (
              <div key={s.instrument} className="rounded-xl border border-[var(--color-line)] p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">{INSTRUMENT_SHORT[s.instrument]}</span>
                  <span
                    className={cx(
                      'tabular text-sm font-semibold',
                      signTone(s.pnl) === 'pos'
                        ? 'text-[var(--color-pos)]'
                        : signTone(s.pnl) === 'neg'
                          ? 'text-[var(--color-neg)]'
                          : '',
                    )}
                  >
                    {formatUsdSigned(s.pnl, 0)}
                  </span>
                </div>
                <div className="tabular mt-1 grid grid-cols-4 gap-2 text-xs text-[var(--color-dim)]">
                  <span>{s.trades} trades</span>
                  <span>WR {s.winRate === null ? 'N/A' : formatPct(s.winRate)}</span>
                  <span>avg {s.averageResult === null ? '—' : formatUsdSigned(s.averageResult, 0)}</span>
                  <span>{formatPct(s.contribution)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <CardTitle>Weekly win rate</CardTitle>
        {activeWeeks.length === 0 ? (
          <EmptyState title="No week logged yet." />
        ) : (
          <div className="divide-y divide-[var(--color-line)]">
            {activeWeeks.map((w) => (
              <div key={w.weekStart} className="flex items-center justify-between gap-3 py-2.5">
                <div>
                  <div className="text-sm font-semibold">Week {w.index}</div>
                  <div className="text-xs text-[var(--color-dim)]">
                    {formatDayLabel(w.weekStart)} → {formatDayLabel(w.weekEnd)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="tabular text-sm font-semibold">
                    {w.winRate === null ? (
                      <span className="text-[var(--color-dim)]">N/A</span>
                    ) : (
                      `${w.wins}W / ${w.losses}L · ${formatPct(w.winRate)}`
                    )}
                  </div>
                  <div
                    className={cx(
                      'tabular text-xs font-semibold',
                      signTone(w.tradingNet) === 'pos'
                        ? 'text-[var(--color-pos)]'
                        : signTone(w.tradingNet) === 'neg'
                          ? 'text-[var(--color-neg)]'
                          : 'text-[var(--color-dim)]',
                    )}
                  >
                    {formatUsdSigned(w.tradingNet, 0)} · {formatPct(w.returnRatio)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        <p className="mt-3 text-[11px] text-[var(--color-dim)]">
          Weeks without detailed trades show “N/A — detailed trades required.”
        </p>
      </Card>

      <Card>
        <CardTitle>Extremes</CardTitle>
        <Row
          label="Best day"
          value={
            ledgerStats.bestDay
              ? `${formatDayLabel(ledgerStats.bestDay.date)} · ${formatUsdSigned(ledgerStats.bestDay.value, 0)}`
              : '—'
          }
          tone={ledgerStats.bestDay ? signTone(ledgerStats.bestDay.value) : 'neutral'}
        />
        <Row
          label="Worst day"
          value={
            ledgerStats.worstDay
              ? `${formatDayLabel(ledgerStats.worstDay.date)} · ${formatUsdSigned(ledgerStats.worstDay.value, 0)}`
              : '—'
          }
          tone={ledgerStats.worstDay ? signTone(ledgerStats.worstDay.value) : 'neutral'}
        />
        <Row
          label="Best week"
          value={
            ledgerStats.bestWeek
              ? `${formatDayLabel(ledgerStats.bestWeek.weekStart)} · ${formatUsdSigned(ledgerStats.bestWeek.value, 0)}`
              : '—'
          }
          tone={ledgerStats.bestWeek ? signTone(ledgerStats.bestWeek.value) : 'neutral'}
        />
        <Row
          label="Worst week"
          value={
            ledgerStats.worstWeek
              ? `${formatDayLabel(ledgerStats.worstWeek.weekStart)} · ${formatUsdSigned(ledgerStats.worstWeek.value, 0)}`
              : '—'
          }
          tone={ledgerStats.worstWeek ? signTone(ledgerStats.worstWeek.value) : 'neutral'}
        />
        <Row label="Green / red / flat days" value={`${ledgerStats.greenDays} / ${ledgerStats.redDays} / ${ledgerStats.flatDays}`} />
      </Card>

      {emotions.length > 0 || discipline.length > 0 ? (
        <Card>
          <CardTitle>Psychology</CardTitle>
          {emotions.map((b) => (
            <Row
              key={b.key}
              label={`${b.label} (${b.days}d)`}
              value={formatUsdSigned(b.averagePnl, 0)}
              tone={signTone(b.averagePnl)}
            />
          ))}
          {discipline.map((b) => (
            <Row
              key={b.key}
              label={`${b.label} (${b.days}d)`}
              value={formatUsdSigned(b.averagePnl, 0)}
              tone={signTone(b.averagePnl)}
            />
          ))}
          <p className="mt-3 text-[11px] text-[var(--color-dim)]">Average day P&L per bucket.</p>
        </Card>
      ) : null}
    </div>
  )
}
