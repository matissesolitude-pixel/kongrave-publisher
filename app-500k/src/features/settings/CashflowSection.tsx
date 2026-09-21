import { useState } from 'react'
import { useApp } from '@/app/store'
import { Button, Card, CardTitle, Chip, EmptyState, Row, signTone } from '@/components/ui'
import { NumberField, TextField } from '@/components/NumberField'
import { Sheet, ConfirmDialog } from '@/components/Sheet'
import { useToast } from '@/components/Toast'
import { createCashflow } from '@/domain/models/factories'
import { CASHFLOW_LABEL, type Cashflow, type CashflowType } from '@/domain/models/types'
import { formatDayLabel, todayIso } from '@/utils/date'
import { formatUsdSigned } from '@/utils/format'

const TYPES: CashflowType[] = ['deposit', 'withdrawal', 'fee', 'manual_adjustment']

/** Capital movements — never mixed with trading P&L. */
export function CashflowSection() {
  const { cashflows, saveCashflow, deleteCashflow, derived } = useApp()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [confirm, setConfirm] = useState<Cashflow | null>(null)

  const [type, setType] = useState<CashflowType>('deposit')
  const [date, setDate] = useState(todayIso())
  const [amount, setAmount] = useState<number | null>(null)
  const [note, setNote] = useState('')

  const sorted = [...cashflows].sort((a, b) => (a.date < b.date ? 1 : -1))

  const save = async () => {
    if (amount === null || amount === 0) {
      toast.show('Enter an amount', 'neg')
      return
    }
    await saveCashflow(createCashflow(date, type, amount, note))
    toast.show('Movement saved ✓')
    setAmount(null)
    setNote('')
    setOpen(false)
  }

  const effect = (c: Cashflow): number =>
    c.type === 'withdrawal' || c.type === 'fee' ? -c.amount : c.amount

  return (
    <>
      <Card>
        <CardTitle
          right={
            <button
              type="button"
              className="text-xs font-semibold text-[var(--color-accent)]"
              onClick={() => setOpen(true)}
            >
              + Add
            </button>
          }
        >
          Capital movements
        </CardTitle>
        <Row label="Trading P&L" value={formatUsdSigned(derived.ledger.totalTradingPnl, 2)} tone={signTone(derived.ledger.totalTradingPnl)} />
        <Row label="Deposits" value={formatUsdSigned(derived.ledger.totalDeposits, 2)} />
        <Row label="Withdrawals" value={formatUsdSigned(-derived.ledger.totalWithdrawals, 2)} />
        <Row label="Fees" value={formatUsdSigned(-derived.ledger.totalFees, 2)} />
        <Row label="Current equity" value={formatUsdSigned(derived.ledger.currentEquity, 2)} />

        <div className="mt-3 border-t border-[var(--color-line)] pt-3">
          {sorted.length === 0 ? (
            <EmptyState title="No capital movement recorded." />
          ) : (
            sorted.map((c) => (
              <div key={c.id} className="flex items-center justify-between gap-3 py-2">
                <div>
                  <div className="text-sm font-medium">
                    {CASHFLOW_LABEL[c.type]}
                    {c.note ? ` — ${c.note}` : ''}
                  </div>
                  <div className="text-xs text-[var(--color-dim)]">{formatDayLabel(c.date)}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="tabular text-sm font-semibold">
                    {formatUsdSigned(effect(c), 2)}
                  </span>
                  <button
                    type="button"
                    aria-label="Delete movement"
                    onClick={() => setConfirm(c)}
                    className="px-2 text-sm text-[var(--color-neg)]"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      <Sheet
        open={open}
        title="Capital movement"
        onClose={() => setOpen(false)}
        footer={
          <Button full size="lg" variant="primary" onClick={() => void save()}>
            Save
          </Button>
        }
      >
        <div className="space-y-4">
          <div className="flex flex-wrap gap-1.5">
            {TYPES.map((t) => (
              <Chip key={t} active={type === t} onClick={() => setType(t)}>
                {CASHFLOW_LABEL[t]}
              </Chip>
            ))}
          </div>
          <TextField label="Date" type="date" value={date} onChange={setDate} />
          <NumberField
            label="Amount"
            prefix="$"
            value={amount}
            onChange={setAmount}
            allowNegative={type === 'manual_adjustment'}
            hint={type === 'manual_adjustment' ? 'can be negative' : undefined}
          />
          <TextField label="Note" value={note} onChange={setNote} placeholder="optional" />
        </div>
      </Sheet>

      <ConfirmDialog
        open={Boolean(confirm)}
        destructive
        title="Delete this movement?"
        message="The equity curve is recalculated from this date onwards."
        confirmLabel="Delete"
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          if (!confirm) return
          void deleteCashflow(confirm.id).then(() => {
            toast.show('Movement deleted', 'neg')
            setConfirm(null)
          })
        }}
      />
    </>
  )
}
