import type { ButtonHTMLAttributes, ReactNode } from 'react'

/** Small, composable primitives shared by every feature screen. */

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

export function Card({
  children,
  className,
  as: As = 'section',
}: {
  children: ReactNode
  className?: string
  as?: 'section' | 'div' | 'article'
}) {
  return (
    <As
      className={cx(
        'rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-4',
        className,
      )}
    >
      {children}
    </As>
  )
}

export function CardTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-baseline justify-between gap-3">
      <h2 className="text-[11px] font-semibold tracking-[0.14em] text-[var(--color-muted)] uppercase">
        {children}
      </h2>
      {right}
    </div>
  )
}

export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase"
    >
      {children}
    </label>
  )
}

export function Stat({
  label,
  value,
  hint,
  tone = 'neutral',
  size = 'md',
}: {
  label: string
  value: ReactNode
  hint?: ReactNode
  tone?: Tone
  size?: 'sm' | 'md' | 'lg'
}) {
  const sizeClass =
    size === 'lg' ? 'text-3xl' : size === 'sm' ? 'text-base' : 'text-xl'
  return (
    <div>
      <div className="text-[10px] font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase">
        {label}
      </div>
      <div className={cx('tabular mt-0.5 font-semibold', sizeClass, toneClass(tone))}>{value}</div>
      {hint ? <div className="mt-0.5 text-xs text-[var(--color-dim)]">{hint}</div> : null}
    </div>
  )
}

export type Tone = 'neutral' | 'pos' | 'neg' | 'accent' | 'muted' | 'warn'

export function toneClass(tone: Tone): string {
  switch (tone) {
    case 'pos':
      return 'text-[var(--color-pos)]'
    case 'neg':
      return 'text-[var(--color-neg)]'
    case 'accent':
      return 'text-[var(--color-accent)]'
    case 'muted':
      return 'text-[var(--color-muted)]'
    case 'warn':
      return 'text-[var(--color-warn)]'
    default:
      return 'text-[var(--color-text)]'
  }
}

/** Tone derived from a signed number. */
export function signTone(value: number): Tone {
  if (value > 0) return 'pos'
  if (value < 0) return 'neg'
  return 'neutral'
}

/**
 * Colour is never the only carrier of meaning: an arrow glyph doubles the
 * green/red signal for colour-blind users and greyscale screenshots.
 */
export function TrendGlyph({ value }: { value: number }) {
  if (value === 0) return <span aria-hidden="true">–</span>
  return <span aria-hidden="true">{value > 0 ? '▲' : '▼'}</span>
}

export function ProgressBar({
  ratio,
  tone = 'accent',
  label,
  height = 'h-2',
}: {
  ratio: number
  tone?: Tone
  label?: string
  height?: string
}) {
  const clamped = Math.max(0, Math.min(1, Number.isFinite(ratio) ? ratio : 0))
  const bg =
    tone === 'pos'
      ? 'bg-[var(--color-pos)]'
      : tone === 'neg'
        ? 'bg-[var(--color-neg)]'
        : 'bg-[var(--color-accent)]'
  return (
    <div
      className={cx('w-full overflow-hidden rounded-full bg-[var(--color-surface-2)]', height)}
      role="progressbar"
      aria-valuenow={Math.round(clamped * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label ?? 'Progress'}
    >
      <div
        className={cx('h-full rounded-full transition-[width] duration-500 ease-out', bg)}
        style={{ width: `${clamped * 100}%` }}
      />
    </div>
  )
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  full?: boolean
}

export function Button({
  variant = 'secondary',
  size = 'md',
  full,
  className,
  ...rest
}: ButtonProps) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition active:scale-[0.98] disabled:opacity-40 disabled:active:scale-100'
  const sizes = {
    sm: 'min-h-9 px-3 text-sm',
    md: 'min-h-11 px-4 text-sm',
    lg: 'min-h-14 px-5 text-base',
  }
  const variants = {
    primary: 'bg-[var(--color-accent)] text-white',
    secondary:
      'border border-[var(--color-line)] bg-[var(--color-surface-2)] text-[var(--color-text)]',
    ghost: 'text-[var(--color-muted)]',
    danger: 'border border-[var(--color-neg)]/40 bg-[var(--color-neg)]/10 text-[var(--color-neg)]',
  }
  return (
    <button
      type="button"
      className={cx(base, sizes[size], variants[variant], full && 'w-full', className)}
      {...rest}
    />
  )
}

export function Chip({
  active,
  children,
  onClick,
  tone = 'neutral',
}: {
  active?: boolean
  children: ReactNode
  onClick?: () => void
  tone?: Tone
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cx(
        'min-h-9 rounded-full border px-3 text-xs font-semibold whitespace-nowrap transition active:scale-[0.97]',
        active
          ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/15 text-[var(--color-accent)]'
          : 'border-[var(--color-line)] bg-[var(--color-surface-2)]',
        !active && toneClass(tone),
      )}
    >
      {children}
    </button>
  )
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: Array<{ value: T; label: string }>
  value: T
  onChange: (value: T) => void
  ariaLabel: string
}) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className="flex gap-1 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-1"
    >
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="tab"
          aria-selected={value === o.value}
          onClick={() => onChange(o.value)}
          className={cx(
            'min-h-9 flex-1 rounded-lg px-2 text-xs font-semibold transition',
            value === o.value
              ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-muted)]',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function Toggle({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean
  onChange: (next: boolean) => void
  label: string
  description?: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex w-full items-center justify-between gap-4 py-2 text-left"
    >
      <span>
        <span className="block text-sm font-medium">{label}</span>
        {description ? (
          <span className="mt-0.5 block text-xs text-[var(--color-dim)]">{description}</span>
        ) : null}
      </span>
      <span
        className={cx(
          'relative h-7 w-12 shrink-0 rounded-full transition',
          checked ? 'bg-[var(--color-accent)]' : 'bg-[var(--color-surface-2)]',
        )}
      >
        <span
          className={cx(
            'absolute top-1 h-5 w-5 rounded-full bg-white transition-all',
            checked ? 'left-6' : 'left-1',
          )}
        />
      </span>
    </button>
  )
}

export function EmptyState({ title, body }: { title: string; body?: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-[var(--color-line)] px-4 py-8 text-center">
      <p className="text-sm font-medium text-[var(--color-muted)]">{title}</p>
      {body ? <p className="mt-1 text-xs text-[var(--color-dim)]">{body}</p> : null}
    </div>
  )
}

export function Row({
  label,
  value,
  tone = 'neutral',
}: {
  label: ReactNode
  value: ReactNode
  tone?: Tone
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[var(--color-line)] py-2.5 last:border-0">
      <span className="text-sm text-[var(--color-muted)]">{label}</span>
      <span className={cx('tabular text-sm font-semibold', toneClass(tone))}>{value}</span>
    </div>
  )
}
