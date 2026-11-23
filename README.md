# design-system-keeper

A Claude skill that pulls a design system out of a real project, decides what is worth saving so nothing is lost, tells you what the system contains, and hands it back as a PDF, a single page, or code.

## What it does

1. **Finds the sources.** Code and prototypes, written decisions (handoff notes, READMEs), decisions made in the conversation, assets, and any existing design system.
2. **Scans the code** (`scripts/inventory.py`) for the colours, type sizes, spacing, radii, shadows and layers actually used. It reads CSS and Tailwind classes, converts `rem` to `px`, and links code variables to saved tokens. With `--draft-tokens` it drafts a first `tokens.json` when no design system exists.
3. **Sorts every finding** into save, park (an open question) or skip, with a reason. It never overwrites a person's decision with what the code happens to do: conflicts are recorded for a person to settle. A report's recommendation is a proposal, not a decision: it reads the person's own answers first.
4. **Checks what the system contains** (`scripts/coverage.py`) against a complete one (`references/ideal-system.md`, drawn from Figma's "Design systems 101" and Into Design Systems' "AI design systems"): foundations, token quality, components, patterns, guidelines, documentation, governance, and AI readiness.
5. **Offers the delivery** (`scripts/export_system.py`):
   - a PDF or a single print-ready HTML page,
   - CSS variables and a Tailwind config,
   - an `AGENTS.md` of always-on rules for AI agents.
   - for engineers, `components.json` (one structured record per component) and `tokens.dtcg.json` (Design Tokens format for Style Dictionary and Figma token tools).
   - for a project that already has its own variable names, a **bridge file** (`--format bridge`) that points the app's names at the tokens without renaming anything, a `--prefix` so token names never clash, and `--rules` to add project-specific rules to the `AGENTS.md`.
6. **Keeps it in step** (`scripts/check_drift.py`). Compare the saved tokens with the code of several sources (a prototype and the real app), list the differences, link each token to the code variable that holds it, and exit with an error on drift (`--fail`) so it can run before a release.

## Install

Upload `design-system-keeper.skill` to Claude (Settings, Skills), or copy this folder into your skills directory. Then ask: "pull my design system", "turn my design into a design system", or "what does my design system contain?".

## What it needs

- Read access to your project folders (code, prototypes, docs). In Claude Code or the desktop app it can read them directly; in a chat you upload them.
- Python 3 (standard library only). Google Chrome is needed only to print the PDF.
- Your existing design system, if you have one (a `tokens.json`; see `references/design-system-format.md`).
- You, for the decisions that are yours. It parks them instead of guessing.

## Honest limits

- The coverage score is keyword-based. Treat it as a guide, not a grade. A scan-only draft is flagged as a draft.
- Colours written as Tailwind classes (for example `bg-emerald-600`) are not read. Dark values in a draft are listed separately, not paired with light ones.
- `components.json` is read from component pages written as a title, a summary and labelled paragraphs (`**Use.**`, `**Rules.**`). Pages written another way give thinner data.
- The draft pairs light and dark values only when the CSS declares both (`:root` and a `.dark`, `[data-theme=dark]` or `prefers-color-scheme: dark` block).
- The drift check compares colours by name and value. It does not yet compare shadows, spacing names or component code.
- Tested on three projects (a design system with 17 components, a portfolio site and a Next.js app) and in two fresh sessions, and the tests found errors that were fixed. It is not tested on every setup.
