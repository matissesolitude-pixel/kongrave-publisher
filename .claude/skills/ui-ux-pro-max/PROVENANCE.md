# Provenance

This skill is vendored from an upstream open-source project.

- **Upstream**: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **Upstream version**: 2.11.0
- **Vendored at commit**: `4d140cf8ff6842de13213c7214eff3810371beb2` (2026-08-03)
- **Source path in upstream**: `.claude/skills/ui-ux-pro-max/`
- **License**: MIT (see `LICENSE`)

## Local modifications

Only one change was made to the upstream payload:

- `SKILL.md` — the 11 example commands used `${CLAUDE_PLUGIN_ROOT}/...`, a variable
  that is only set when the skill is installed as a Claude *plugin*. Since this is
  vendored as a *project* skill, those paths were rewritten to be relative to the
  repo root (`.claude/skills/ui-ux-pro-max/scripts/search.py`), and the surrounding
  paragraph was updated to match.

Data files (`data/`), scripts (`scripts/`) and references (`references/`) are
byte-identical to upstream.

## Updating

    git clone --depth 1 https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git /tmp/uipm
    rm -rf .claude/skills/ui-ux-pro-max
    cp -r /tmp/uipm/.claude/skills/ui-ux-pro-max .claude/skills/ui-ux-pro-max
    cp /tmp/uipm/LICENSE .claude/skills/ui-ux-pro-max/LICENSE

Then re-apply the `${CLAUDE_PLUGIN_ROOT}` path rewrite above and restore this file.

## Sibling skills not vendored

Upstream also ships 6 other skills under `.claude/skills/` that were **not** installed
here: `banner-design`, `brand`, `design`, `design-system`, `slides`, `ui-styling`
(the last bundles ~5.8 MB of TTF fonts). Add them from the same upstream clone if needed.
