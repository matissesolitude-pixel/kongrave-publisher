import { useId } from 'react'
import { Button, cx } from './ui'

/**
 * Numeric input tuned for one-handed iPhone entry.
 *
 * `inputMode="decimal"` opens the iOS numeric keypad, and the quick buttons make
 * a typical day loggable without ever using the keyboard.
 */
export function NumberField({
  label,
  value,
  onChange,
  quick,
  suffix,
  prefix,
  placeholder = '0',
  allowNegative = true,
  hint,
  tone,
  step,
  clearable = true,
}: {
  label: string
  value: number | null
  onChange: (next: number | null) => void
  quick?: number[]
  suffix?: string
  prefix?: string
  placeholder?: string
  allowNegative?: boolean
  hint?: string
  tone?: 'pos' | 'neg' | 'neutral'
  step?: number
  /** `false` for settings that must always carry a value. */
  clearable?: boolean
}) {
  const id = useId()
  const text = value === null ? '' : String(value)

  const parse = (raw: string): number | null => {
    const cleaned = raw.replace(',', '.').trim()
    if (cleaned === '' || cleaned === '-' || cleaned === '.') return null
    const n = Number(cleaned)
    if (!Number.isFinite(n)) return null
    return allowNegative ? n : Math.abs(n)
  }

  const bump = (delta: number) => {
    const next = Number(((value ?? 0) + delta).toFixed(6))
    onChange(next)
  }

  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-2">
        <label
          htmlFor={id}
          className="text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase"
        >
          {label}
        </label>
        <span className="flex items-baseline gap-2">
          {hint ? <span className="text-[11px] text-[var(--color-dim)]">{hint}</span> : null}
          {clearable && quick && quick.length > 0 && value !== null ? (
            <button
              type="button"
              onClick={() => onChange(null)}
              className="text-[11px] font-semibold text-[var(--color-accent)]"
            >
              Clear
            </button>
          ) : null}
        </span>
      </div>
      <div
        className={cx(
          'flex items-center gap-1 rounded-xl border bg-[var(--color-surface-2)] px-3',
          tone === 'pos'
            ? 'border-[var(--color-pos)]/50'
            : tone === 'neg'
              ? 'border-[var(--color-neg)]/50'
              : 'border-[var(--color-line)]',
        )}
      >
        {prefix ? <span className="text-sm text-[var(--color-muted)]">{prefix}</span> : null}
        <input
          id={id}
          className="tabular min-h-13 w-full bg-transparent text-2xl font-semibold outline-none"
          inputMode="decimal"
          enterKeyHint="done"
          autoComplete="off"
          step={step}
          value={text}
          placeholder={placeholder}
          onChange={(e) => onChange(parse(e.target.value))}
        />
        {suffix ? (
          <span className="text-xs font-semibold tracking-wide text-[var(--color-muted)] uppercase">
            {suffix}
          </span>
        ) : null}
      </div>
      {quick && quick.length > 0 ? (
        <div className="mt-2 flex gap-1.5">
          {quick.map((q) => (
            <Button
              key={q}
              size="sm"
              onClick={() => bump(q)}
              aria-label={`${q > 0 ? 'Add' : 'Subtract'} ${Math.abs(q)} to ${label}`}
              className="flex-1 px-1"
            >
              {q > 0 ? `+${q}` : q}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  multiline,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (next: string) => void
  placeholder?: string
  multiline?: boolean
  type?: 'text' | 'date' | 'time'
}) {
  const id = useId()
  const className =
    'min-h-12 w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 py-2.5 text-sm outline-none'
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase"
      >
        {label}
      </label>
      {multiline ? (
        <textarea
          id={id}
          className={cx(className, 'min-h-20 resize-y')}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          id={id}
          type={type}
          className={className}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  )
}

export function ScoreField({
  label,
  value,
  onChange,
}: {
  label: string
  value: number | null
  onChange: (next: number | null) => void
}) {
  return (
    <div>
      <span className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
        {label}
      </span>
      <div className="flex gap-1.5">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            aria-pressed={value === n}
            onClick={() => onChange(value === n ? null : n)}
            className={cx(
              'tabular min-h-11 flex-1 rounded-xl border text-sm font-semibold transition active:scale-[0.97]',
              value === n
                ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/15 text-[var(--color-accent)]'
                : 'border-[var(--color-line)] bg-[var(--color-surface-2)] text-[var(--color-muted)]',
            )}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  )
}
