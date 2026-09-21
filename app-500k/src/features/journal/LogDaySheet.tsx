import { useMemo, useState } from 'react'
import { Sheet } from '@/components/Sheet'
import { NumberField, ScoreField, TextField } from '@/components/NumberField'
import { Button, Chip, Row, Segmented, Stat, signTone } from '@/components/ui'
import { useToast } from '@/components/Toast'
import { useApp } from '@/app/store'
import { createDayEntry } from '@/domain/models/factories'
import {
  CHECKLIST_LABEL,
  EMOTIONS,
  EMOTION_LABEL,
  type DayEntry,
  type Emotion,
  type IsoDate,
  type RuleChecklist,
} from '@/domain/models/types'
import { calculateDaySummaryPnl } from '@/domain/calculations/pnl'
import { resolveSize } from '@/domain/sizing/sizing'
import { equityOpenAt } from '@/domain/calculations/ledger'
import { formatFullDate, todayIso } from '@/utils/date'
import { formatLots, formatUsdSigned } from '@/utils/format'

const PIP_QUICK = [5, 10, -5, -10]
const GOLD_QUICK = [5, 10, 15, 20, -5, -10]

const EMPTY_CHECKLIST: RuleChecklist = {
  planFollowed: false,
  maxLossesRespected: false,
  noRevengeTrade: false,
  correctSizing: false,
  onlyValidSetups: false,
}

/**
 * The 15-second logging path: date, three results, fees, notes, save.
 * Everything else lives behind "More".
 *
 * The form is mounted only while the sheet is open, so its draft state is
 * initialised from the store on open instead of being resynchronised by an
 * effect.
 */
export function LogDaySheet({
  open,
  onClose,
  date,
}: {
  open: boolean
  onClose: () => void
  date?: IsoDate
}) {
  if (!open) return null
  return <LogDayForm key={date ?? 'today'} initialDate={date} onClose={onClose} />
}

function LogDayForm({
  initialDate,
  onClose,
}: {
  initialDate?: IsoDate
  onClose: () => void
}) {
  const { days, settings, saveDay, derived } = useApp()
  const toast = useToast()

  const startDate = initialDate ?? todayIso()
  const [date, setDate] = useState<IsoDate>(startDate)
  const [draft, setDraft] = useState<DayEntry>(
    () => days.find((d) => d.date === startDate) ?? createDayEntry(startDate),
  )
  const [showMore, setShowMore] = useState(false)

  const existing = useMemo(() => days.find((d) => d.date === date) ?? null, [days, date])

  /** Switching date loads that day's entry — handled here, not in an effect. */
  const onDateChange = (next: string) => {
    if (!next) return
    setDate(next)
    const found = days.find((d) => d.date === next)
    setDraft(found ? { ...found } : createDayEntry(next))
  }

  // Size the preview with the same equity the ledger would use for this day.
  const size = useMemo(() => {
    const equityOpen = equityOpenAt(derived.ledger, date)
    const resolved = resolveSize(equityOpen, settings)
    return {
      fxLots: draft.fxLotsUsed ?? resolved.fxLots,
      goldLots: draft.goldLotsUsed ?? resolved.goldLots,
    }
  }, [derived.ledger, date, settings, draft.fxLotsUsed, draft.goldLotsUsed])

  const preview = useMemo(
    () => calculateDaySummaryPnl(draft, size, settings),
    [draft, size, settings],
  )

  const patch = (next: Partial<DayEntry>) => setDraft((d) => ({ ...d, ...next }))

  const onSave = async () => {
    await saveDay({ ...draft, date })
    toast.show('Day logged ✓', preview.net >= 0 ? 'pos' : 'neg')
    onClose()
  }

  const checklist = draft.checklist ?? EMPTY_CHECKLIST
  const toggleChecklist = (key: keyof RuleChecklist) =>
    patch({ checklist: { ...checklist, [key]: !checklist[key] } })

  return (
    <Sheet
      open
      title={existing ? 'Edit day' : 'Log day'}
      onClose={onClose}
      footer={
        <Button full size="lg" variant="primary" onClick={() => void onSave()}>
          Save
        </Button>
      }
    >
      <div className="space-y-4">
        <div>
          <TextField label="Date" type="date" value={date} onChange={onDateChange} />
          <p className="mt-1 text-xs text-[var(--color-dim)]">{formatFullDate(date)}</p>
        </div>

        <NumberField
          label="EURUSD"
          suffix="pips"
          value={draft.eurusdPips === 0 ? null : draft.eurusdPips}
          onChange={(v) => patch({ eurusdPips: v ?? 0 })}
          quick={PIP_QUICK}
          tone={draft.eurusdPips > 0 ? 'pos' : draft.eurusdPips < 0 ? 'neg' : 'neutral'}
          hint={formatUsdSigned(preview.eurusd, 0)}
        />
        <NumberField
          label="GBPUSD"
          suffix="pips"
          value={draft.gbpusdPips === 0 ? null : draft.gbpusdPips}
          onChange={(v) => patch({ gbpusdPips: v ?? 0 })}
          quick={PIP_QUICK}
          tone={draft.gbpusdPips > 0 ? 'pos' : draft.gbpusdPips < 0 ? 'neg' : 'neutral'}
          hint={formatUsdSigned(preview.gbpusd, 0)}
        />
        <NumberField
          label="XAUUSD"
          prefix="$"
          suffix="move"
          value={draft.xauusdMove === 0 ? null : draft.xauusdMove}
          onChange={(v) => patch({ xauusdMove: v ?? 0 })}
          quick={GOLD_QUICK}
          tone={draft.xauusdMove > 0 ? 'pos' : draft.xauusdMove < 0 ? 'neg' : 'neutral'}
          hint={formatUsdSigned(preview.xauusd, 0)}
        />

        <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-3">
          <div className="flex items-end justify-between">
            <Stat
              label="Net P&L"
              value={formatUsdSigned(preview.net, 2)}
              tone={signTone(preview.net)}
              size="lg"
            />
            <div className="text-right text-xs text-[var(--color-dim)]">
              <div>Gross {formatUsdSigned(preview.gross, 2)}</div>
              <div>Fees {formatUsdSigned(-preview.fees, 2)}</div>
              <div className="mt-1">
                {formatLots(size.fxLots)} FX · {formatLots(size.goldLots)} Gold
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <NumberField
            label="Commission"
            prefix="$"
            value={draft.commission === 0 ? null : draft.commission}
            onChange={(v) => patch({ commission: v ?? 0 })}
            allowNegative={false}
          />
          <NumberField
            label="Swap"
            prefix="$"
            value={draft.swap === 0 ? null : draft.swap}
            onChange={(v) => patch({ swap: v ?? 0 })}
            allowNegative={false}
          />
        </div>

        <TextField
          label="Notes"
          value={draft.notes}
          onChange={(v) => patch({ notes: v })}
          placeholder="What mattered today?"
          multiline
        />

        <Button full variant="ghost" onClick={() => setShowMore((s) => !s)}>
          {showMore ? 'Hide extras' : 'More — losses, psychology, rules'}
        </Button>

        {showMore ? (
          <div className="space-y-4 border-t border-[var(--color-line)] pt-4">
            <div className="grid grid-cols-2 gap-3">
              <NumberField
                label="Wins today"
                value={draft.manualWins}
                onChange={(v) => patch({ manualWins: v })}
                allowNegative={false}
                quick={[1, -1]}
                hint="optional"
              />
              <NumberField
                label="Losses today"
                value={draft.manualLosses}
                onChange={(v) => patch({ manualLosses: v })}
                allowNegative={false}
                quick={[1, -1]}
                hint={`limit ${settings.dailyLossLimit}`}
              />
            </div>
            <p className="text-xs text-[var(--color-dim)]">
              These counters only feed the daily loss-limit display. Win rate is computed from
              detailed trades only.
            </p>

            <div>
              <Segmented
                ariaLabel="P&L source for this day"
                value={draft.pnlSource}
                onChange={(v) => patch({ pnlSource: v })}
                options={[
                  { value: 'daily', label: 'Manual daily P&L' },
                  { value: 'trades', label: 'Detailed trades' },
                ]}
              />
              <p className="mt-1.5 text-xs text-[var(--color-dim)]">
                One source per day — the two are never added together.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <NumberField
                label="FX lots used"
                value={draft.fxLotsUsed}
                onChange={(v) => patch({ fxLotsUsed: v })}
                allowNegative={false}
                hint="auto"
              />
              <NumberField
                label="Gold lots used"
                value={draft.goldLotsUsed}
                onChange={(v) => patch({ goldLotsUsed: v })}
                allowNegative={false}
                hint="auto"
              />
            </div>

            <ScoreField
              label="Execution 1–5"
              value={draft.executionScore}
              onChange={(v) => patch({ executionScore: v })}
            />
            <ScoreField
              label="Discipline 1–5"
              value={draft.disciplineScore}
              onChange={(v) => patch({ disciplineScore: v })}
            />

            <div>
              <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
                Emotion
              </span>
              <div className="flex flex-wrap gap-1.5">
                {EMOTIONS.map((e: Emotion) => (
                  <Chip
                    key={e}
                    active={draft.emotion === e}
                    onClick={() => patch({ emotion: draft.emotion === e ? null : e })}
                  >
                    {EMOTION_LABEL[e]}
                  </Chip>
                ))}
              </div>
            </div>

            <TextField
              label="What happened?"
              value={draft.whatHappened}
              onChange={(v) => patch({ whatHappened: v })}
              multiline
            />

            <div>
              <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
                Rule compliance
              </span>
              <div className="rounded-2xl border border-[var(--color-line)] px-3">
                {(Object.keys(CHECKLIST_LABEL) as Array<keyof RuleChecklist>).map((key) => (
                  <Row
                    key={key}
                    label={CHECKLIST_LABEL[key]}
                    value={
                      <button
                        type="button"
                        role="switch"
                        aria-checked={checklist[key]}
                        aria-label={CHECKLIST_LABEL[key]}
                        onClick={() => toggleChecklist(key)}
                        className={`min-h-8 rounded-lg border px-3 text-xs font-semibold ${
                          checklist[key]
                            ? 'border-[var(--color-pos)]/50 bg-[var(--color-pos)]/10 text-[var(--color-pos)]'
                            : 'border-[var(--color-line)] text-[var(--color-muted)]'
                        }`}
                      >
                        {checklist[key] ? '✓ Yes' : 'No'}
                      </button>
                    }
                  />
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </Sheet>
  )
}
