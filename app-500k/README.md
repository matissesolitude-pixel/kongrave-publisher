# 500K — Trading Challenge

A personal, offline-first PWA to track a trading challenge: daily journal, P&L
calculator, position sizing, weekly objective and equity trajectory.

> 500K is a personal tracking and calculation tool. Targets are mathematical
> tracking goals, not predictions or guarantees of future trading performance.

Everything is stored locally in IndexedDB. There is no backend, no account, no
network call at runtime.

---

## Quick start

```bash
cd app-500k
npm install
npm run dev          # http://localhost:5173
```

Other commands:

```bash
npm run typecheck    # tsc -b, strict mode
npm run lint         # eslint (flat config)
npm run test         # vitest — business logic unit tests
npm run build        # tsc -b && vite build  -> dist/
npm run preview      # serve dist/ locally
npm run check        # typecheck + lint + test + build
npm run icons        # regenerate the PWA icons from the SVG source
```

To test the PWA (service worker + install prompt) you must serve the **build**,
not the dev server:

```bash
npm run build && npm run preview -- --host
```

---

## Business rules encoded in the app

| Rule | Where it lives |
| --- | --- |
| FX P&L = `pips × lots × pipValuePerLot` (default $10/lot) | `domain/calculations/pnl.ts` |
| Gold P&L = `$ of price movement × lots × contractSize` (default 100 oz) | `domain/calculations/pnl.ts` |
| Sizing mode A (`equity / 2000`) and mode B (frozen tiers) | `domain/sizing/sizing.ts` |
| Ledger replay, equity curve, daily loss limit | `domain/calculations/ledger.ts` |
| Required compound rate, trajectory, checkpoints, drawdown | `domain/calculations/challenge.ts` |
| Weekly target, remaining amount, equivalents, scenarios | `domain/calculations/weekly.ts` |
| Win rate, profit factor, expectancy, streaks, per instrument | `domain/calculations/stats.ts` |
| Mix planner (weights = **dollar contribution**, not raw pips) | `domain/calculations/mix.ts` |

Every financial assumption — pip value, contract size, tier table, sizing mode,
week start, loss limit, win-rate convention, scale-out plan — is a **setting**,
editable in the app. Nothing is hidden in a component.

Key invariants:

- **No double counting.** A day draws its P&L from exactly one source: the
  manual daily summary *or* its detailed trades. Never both.
- **Full replay.** Editing or deleting a past day rebuilds the whole equity
  curve from that date. The current balance is never patched in isolation.
- **Losses, not trades.** The daily limit counts losing trades. Trades taken
  after the limit are recorded, flagged, and measured (`P&L after the limit`)
  rather than blocked.
- **No invented win rate.** Days logged through the quick path show
  `N/A — detailed trades required.`
- **Full Position Equivalent.** A scaled-out result is also expressed as the pip
  (or Gold $) result a full reference-size position would have produced, so
  results stay comparable. Realized P&L and full-position equivalent are two
  distinct concepts, never merged.
- **Local calendar dates.** Days are stored as `YYYY-MM-DD` local dates, so a
  UTC offset can never shift a day to its neighbour.

Default configuration: $7,000 → $500,000, 2026-09-21 → 2027-01-01, 3.5 FX lots,
0.30 Gold lots, 3 losses/day, week starting Monday. The weekly target is the
exact compound rate required from the current equity — the +35 % figure is only
available as an explicit "fixed rate" mode.

---

## Project structure

```
app-500k/
├── index.html                  iOS meta tags, viewport-fit=cover
├── vite.config.ts              Vite + Tailwind + PWA (Workbox) + Vitest
├── public/icons/               app icons (generated)
├── scripts/generate-icons.mjs  SVG -> PNG icon pipeline
└── src/
    ├── app/                    App shell, routing, global store
    ├── components/             UI primitives, sheets, toasts, error boundary
    ├── db/                     persistence interface, Dexie adapter, backup, CSV
    ├── domain/
    │   ├── models/             types, defaults, factories
    │   ├── calculations/       pnl, ledger, challenge, weekly, stats, mix
    │   └── sizing/             tier ladder and lot resolution
    ├── features/
    │   ├── dashboard/          Home, level-up banner
    │   ├── journal/            calendar, day detail, quick log, trade form
    │   ├── calculator/         gauges + mix planner
    │   ├── stats/              statistics
    │   ├── challenge/          Road to 500K (lazy-loaded chart)
    │   └── settings/           settings, tiers, cash movements, data
    ├── utils/                  date, formatting and id helpers
    └── tests/                  unit tests for the business logic
```

The persistence layer is behind `db/persistence.ts`. Swapping IndexedDB for a
remote backend means writing one more adapter — no feature code changes.

---

## Data

- **Export backup (JSON)** — full snapshot: settings, days, trades, cash
  movements, plus `schemaVersion`.
- **Import backup (JSON)** — validated against the schema *before* anything is
  written; malformed rows are skipped and reported, never imported silently.
- **CSV export** — days, trades and cash movements, one file each.
- **CSV import** — broker-agnostic, with explicit column mapping (headers are
  fuzzy-matched to pre-fill it). Ready for a MetaTrader history later without
  pretending to parse every MetaTrader dialect today.
- **Reset all data** — requires typing `RESET`.

---

## Deployment

The app is a static bundle (`dist/`). `base` is `./`, so it works from a domain
root or a sub-path.

**Requirement: HTTPS.** Service workers, and therefore offline mode and "Add to
Home Screen", only work over HTTPS (or `localhost`).

Any static host works:

```bash
npm run build          # produces dist/

# Netlify
npx netlify deploy --prod --dir dist

# Vercel
npx vercel deploy --prod dist

# Cloudflare Pages
npx wrangler pages deploy dist

# GitHub Pages — push dist/ to the gh-pages branch, or add a workflow that
# runs `npm ci && npm run build` in app-500k/ and publishes app-500k/dist
```

Because the app is a single-page app, configure the host to rewrite unknown
paths to `index.html` (Netlify: `/* /index.html 200`, Vercel: a catch-all
rewrite). The service worker already registers `index.html` as the navigation
fallback for offline navigation.

There is no environment variable, no API key, no secret of any kind.

---

## Install on iPhone

1. Deploy the build to an **HTTPS** URL (see above).
2. Open that URL in **Safari** on the iPhone. Chrome/Firefox on iOS cannot add
   to the Home Screen.
3. Tap the **Share** button (square with an arrow).
4. Scroll down and tap **Add to Home Screen**.
5. Confirm the name (`500K`) and tap **Add**.

The app then launches full-screen without the Safari chrome, with the dark
status bar and the iOS safe areas respected.

**Offline:** after the first load, the service worker caches the whole app.
Turn on Airplane Mode and the app still opens with all your data — it lives in
IndexedDB on the device.

**Updating:** the service worker auto-updates. Reopen the app twice after a new
deployment to be sure the new version is active.

**Important:** iOS clears the storage of web apps that go unused for a long
time. Export a JSON backup regularly (Settings → Data).

---

## Accessibility

- Colour is never the only signal: arrows (`▲ ▼`), explicit `+/-` signs and
  text labels double every green/red cue.
- Numeric inputs use `inputMode="decimal"` for the iOS numeric keypad.
- Touch targets are at least 36–44 px tall.
- `prefers-reduced-motion` is honoured, with a manual override in Settings.
- Progress bars, switches and tabs carry the matching ARIA roles and values.
