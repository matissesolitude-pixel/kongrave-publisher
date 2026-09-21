import { useRef, useState } from 'react'
import { useApp } from '@/app/store'
import { Button, Card, CardTitle, EmptyState } from '@/components/ui'
import { Sheet, ConfirmDialog } from '@/components/Sheet'
import { useToast } from '@/components/Toast'
import {
  buildBackup,
  cashflowsToCsv,
  daysToCsv,
  tradesToCsv,
  validateBackup,
} from '@/db/backup'
import {
  buildTradesFromCsv,
  guessMapping,
  parseCsv,
  TRADE_IMPORT_FIELDS,
  type ColumnMapping,
  type ParsedCsv,
} from '@/db/csvImport'

function download(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const stamp = (): string => new Date().toISOString().slice(0, 10)

/** Export / import / reset — the whole dataset lives on this device. */
export function DataSection() {
  const { settings, days, trades, cashflows, importBackup, resetAll, addTrades } = useApp()
  const toast = useToast()
  const jsonInput = useRef<HTMLInputElement>(null)
  const csvInput = useRef<HTMLInputElement>(null)

  const [confirmReset, setConfirmReset] = useState(false)
  const [resetText, setResetText] = useState('')
  const [importReport, setImportReport] = useState<string[] | null>(null)

  const [csv, setCsv] = useState<ParsedCsv | null>(null)
  const [mapping, setMapping] = useState<ColumnMapping>({})

  const exportJson = () => {
    download(
      `500k-backup-${stamp()}.json`,
      JSON.stringify(buildBackup({ settings, days, trades, cashflows }), null, 2),
      'application/json',
    )
    toast.show('Backup exported ✓')
  }

  const onJsonFile = async (file: File) => {
    try {
      const text = await file.text()
      const result = validateBackup(JSON.parse(text) as unknown)
      if (!result.ok || !result.payload) {
        setImportReport(result.errors)
        toast.show('Import refused', 'neg')
        return
      }
      await importBackup(result.payload)
      setImportReport([
        `Imported ${result.payload.days.length} days, ${result.payload.trades.length} trades, ${result.payload.cashflows.length} movements.`,
        ...result.warnings,
      ])
      toast.show('Backup imported ✓', 'pos')
    } catch (e) {
      setImportReport([e instanceof Error ? e.message : 'Unreadable file.'])
      toast.show('Import failed', 'neg')
    }
  }

  const onCsvFile = async (file: File) => {
    const text = await file.text()
    const parsed = parseCsv(text)
    setCsv(parsed)
    setMapping(guessMapping(parsed.headers))
  }

  const runCsvImport = async () => {
    if (!csv) return
    const result = buildTradesFromCsv(csv, mapping)
    if (result.trades.length === 0) {
      toast.show('No importable row', 'neg')
      setImportReport(result.errors.slice(0, 10))
      return
    }
    await addTrades(result.trades)
    toast.show(`${result.trades.length} trades imported ✓`, 'pos')
    setImportReport([
      `${result.trades.length} trades imported, ${result.skipped} skipped.`,
      ...result.errors.slice(0, 10),
    ])
    setCsv(null)
  }

  return (
    <>
      <Card>
        <CardTitle>Data</CardTitle>
        <div className="space-y-2">
          <Button full onClick={exportJson}>
            Export backup (JSON)
          </Button>
          <Button full onClick={() => jsonInput.current?.click()}>
            Import backup (JSON)
          </Button>
          <div className="grid grid-cols-3 gap-2">
            <Button size="sm" onClick={() => download(`500k-days-${stamp()}.csv`, daysToCsv(days), 'text/csv')}>
              Days CSV
            </Button>
            <Button size="sm" onClick={() => download(`500k-trades-${stamp()}.csv`, tradesToCsv(trades), 'text/csv')}>
              Trades CSV
            </Button>
            <Button
              size="sm"
              onClick={() => download(`500k-cashflows-${stamp()}.csv`, cashflowsToCsv(cashflows), 'text/csv')}
            >
              Cash CSV
            </Button>
          </div>
          <Button full onClick={() => csvInput.current?.click()}>
            Import trades from CSV
          </Button>
          <Button full variant="danger" onClick={() => setConfirmReset(true)}>
            Reset all data
          </Button>
        </div>

        <input
          ref={jsonInput}
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) void onJsonFile(file)
            e.target.value = ''
          }}
        />
        <input
          ref={csvInput}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) void onCsvFile(file)
            e.target.value = ''
          }}
        />

        {importReport ? (
          <div className="mt-3 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface-2)] p-3">
            <ul className="space-y-1 text-xs text-[var(--color-muted)]">
              {importReport.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
            <Button size="sm" variant="ghost" className="mt-2" onClick={() => setImportReport(null)}>
              Dismiss
            </Button>
          </div>
        ) : null}

        <p className="mt-3 text-[11px] text-[var(--color-dim)]">
          Everything is stored in IndexedDB on this device. Nothing leaves it. Export regularly.
        </p>
      </Card>

      {/* CSV column mapping */}
      <Sheet
        open={Boolean(csv)}
        title="Map CSV columns"
        onClose={() => setCsv(null)}
        footer={
          <Button full size="lg" variant="primary" onClick={() => void runCsvImport()}>
            Import trades
          </Button>
        }
      >
        {!csv ? (
          <EmptyState title="No file" />
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-[var(--color-dim)]">
              {csv.rows.length} rows detected. Map each field onto one of your columns — the
              importer stays broker-agnostic on purpose.
            </p>
            {TRADE_IMPORT_FIELDS.map((f) => (
              <div key={f.field} className="flex items-center justify-between gap-3">
                <span className="text-sm">
                  {f.label}
                  {f.required ? <span className="text-[var(--color-neg)]"> *</span> : null}
                  <span className="block text-[11px] text-[var(--color-dim)]">{f.hint}</span>
                </span>
                <select
                  aria-label={`Column for ${f.label}`}
                  value={mapping[f.field] ?? -1}
                  onChange={(e) =>
                    setMapping((m) => ({ ...m, [f.field]: Number(e.target.value) }))
                  }
                  className="min-h-10 min-w-32 rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-2)] px-2 text-sm"
                >
                  <option value={-1}>— none —</option>
                  {csv.headers.map((h, i) => (
                    <option key={`${h}-${i}`} value={i}>
                      {h || `col ${i + 1}`}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        )}
      </Sheet>

      <ConfirmDialog
        open={confirmReset}
        destructive
        title="Reset all data?"
        message='This permanently deletes every day, trade, movement and setting on this device. Type "RESET" to confirm.'
        confirmLabel="Erase everything"
        onCancel={() => {
          setConfirmReset(false)
          setResetText('')
        }}
        onConfirm={() => {
          if (resetText.trim().toUpperCase() !== 'RESET') {
            toast.show('Type RESET to confirm', 'neg')
            return
          }
          void resetAll().then(() => {
            toast.show('All data erased', 'neg')
            setConfirmReset(false)
            setResetText('')
          })
        }}
      >
        <input
          value={resetText}
          onChange={(e) => setResetText(e.target.value)}
          placeholder="RESET"
          aria-label="Type RESET to confirm"
          className="mt-4 min-h-12 w-full rounded-xl border border-[var(--color-neg)]/40 bg-[var(--color-surface-2)] px-3 text-sm outline-none"
        />
      </ConfirmDialog>
    </>
  )
}
