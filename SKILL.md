---
name: design-system-keeper
description: Captures a team's design decisions from the real working project into a living design system, decides what to save so nothing is lost, reports what the system contains against a complete one, and delivers it as a PDF, a single page or artifact, or code (CSS variables, Tailwind config, AGENTS.md for AI agents). Use it whenever someone is building or changing screens, components, prototypes or code and mentions a design system, tokens, style guide, "save this", "don't lose this", drift, handoff or consistency, or says "pull my design system", "turn my design into a design system", "export it" or "what does my design system contain", even if they never say "skill". Also use it at the end of a design session, before handing work to developers or an AI agent, or when a design system and the product might disagree. It scans code, prototypes, docs and conversation decisions, compares them with the saved system, then saves real decisions, parks undecided items and skips noise, with a reason for each.
---

# Design system keeper

A design system goes stale because the real decisions are made in the work: in code, in prototypes, in chat ("make the website white", "one red button per screen"), in handoff notes. Nobody copies them back. Your job is to be the person who does, and to decide what is worth keeping, so the system stays true and nothing that was decided is lost.

Two failures to avoid, equally:
- **Losing a decision.** Something a person decided is in a chat or a file, never reaches the system, and the next person (or AI) breaks it.
- **Saving noise.** Every value that appeared once becomes a "rule", and the system fills with contradictions nobody trusts.

So the skill is mostly judgement about what to save. The script only gathers facts.

## The workflow

### 1. Find the sources
Ask the person which of these exist, and look for them yourself first. Check all of them, not just the code:
- The **code and prototypes** (CSS, HTML, components).
- **Written decisions:** handoff notes, instruction files, README files, design docs, review feedback.
- **Decisions made in this conversation** (and any transcript or notes they point to). People state rules in passing. Read back through the conversation for statements like "always", "never", "I don't like", "make it", "keep", and for corrections they made.
- **Assets:** logos, icons, favicons, photos, email templates, exported images.
- The **existing design system**: an artifact URL, a `tokens.json`, a Figma file, a folder. Read it fully before changing anything. If there is none, you are creating a small first one (see `references/design-system-format.md`, and run the scanner with `--draft-tokens`, step 2).
- What a complete system holds is in `references/ideal-system.md` (from Figma's "Design systems 101" and Into Design Systems' "AI design systems"). Use it as the measure of what is missing.

### 2. Gather the facts
Run the scanner on the project folders, comparing with the saved tokens if there are any:

```bash
python <this-skill>/scripts/inventory.py <project-folder> [more folders] --tokens <tokens.json> --out inventory.json
```

It lists the colours, radii, font sizes, spacing, shadows, layers and animations the code really uses, how often, which near-duplicates exist, what is used but not in the tokens, and what is in the tokens but not found in code. Treat the numbers as evidence, not as decisions: a value used 40 times is probably a standard; a value used once may be a mistake or a one-off. The scanner turns `rem` into `px` (so 0.875rem and 14px are the same size) and treats 9999px as the pill radius.

If there is **no design system yet**, add `--draft-tokens draft.json`. It writes a first `tokens.json` from what the code uses (colours, text sizes, spacing, radii, shadows, layers), named after the CSS variables where they exist, every value marked "used N times in the scan, not yet confirmed by a person". Tell the person it is a draft of what the code does, not of what anyone decided, and park every value that needs their call.

### 3. Decide what to save
Sort every candidate into exactly one of three piles, and keep the reason. The full rubric, with examples, is in `references/what-to-save.md`. In short:

- **Save** it when a person decided it (said it, approved it, or the product consistently does it), when it recurs, or when breaking it would cause a visible problem. Rules always get their reason.
- **Park** it (write it down as an open question, do not make it a rule) when it is undecided, when two sources disagree, when it was used once, or when it needs a person's call.
- **Skip** it when it is the prototype's own chrome, a temporary label, a test fixture, a throwaway experiment, or anything private (keys, real people's data).

Never silently drop something. Never overwrite a person's decision with what the code happens to do: when code and a stated decision disagree, record both and mark it as a conflict for the person to settle. Decisions belong to the people; your job is to make them visible.

### 4. Write it into the system
Update only what changed, keeping everything else. Add:
- **Tokens** with a usage note each. New values only if they are used or decided; never invent values.
- **Components** that appear repeatedly, with a short guideline (rules, states, when not to use) and a live example where the format supports one.
- **Conditions:** what changes by role, device, theme and state (organizer or member, phone or website, loading or offline, locked or not). This is where most real bugs live, and the part most systems forget. See `references/conditions.md`.
- **Content:** exact wording that was decided, and the words to avoid.
- **Accessibility and spacing rules** that were decided or measured.
- **A decisions and open items page:** the ledger. Every parked item and every conflict goes here, with where it came from.
- **A change note** (who, when, what).

Deprecate instead of deleting: mark a token or rule "replaced by X on <date>" and keep it. If the format has no place for something, put it in the decisions page rather than dropping it. For where each kind of thing goes, and the exact file format when the target is a design system artifact, read `references/design-system-format.md`.

### 5. Check and report
Before saying you are done, check your own work: every new token has a usage note, no value was invented, nothing conflicts silently, and text colours still pass contrast (4.5:1 for normal text, in every theme). Then report to the person in plain words, in this shape:

- **Saved** (count): each item and where it came from.
- **Parked** (count): each open question and who needs to decide.
- **Skipped** (count): what and why, in one line each.
- **Conflicts:** where the product and a stated decision disagree.
- **Not checked:** anything you could not reach (a source, a file you could not read).
- **What the system contains:** first write the component records into the docs folder (`python <this-skill>/scripts/export_system.py <tokens.json> --docs <docs> --format components --out <docs>/components.json`) so the check can see them, then run `python <this-skill>/scripts/coverage.py <tokens.json> --docs <docs folder>` and report the result: what is Found, Partly there and Missing against the complete checklist, in plain words. Do not fill a Missing item by inventing content; park it.

Ask the person only about decisions that are theirs. Do not ask permission for the routine act of recording what was clearly decided.

### 6. Offer the delivery
When the design system is saved and checked, ask how they want it, in one short question with these choices (they may pick more than one):

1. **A PDF**: a flippable document of the whole system (colour in light and dark, type, spacing, radius, shadows, every guideline page). Run `python <this-skill>/scripts/export_system.py <tokens.json> --docs <docs folder> --format pdf --out <name>.pdf --title "<Name>"` (needs Google Chrome; otherwise use `--format html` and print to PDF from a browser).
2. **A page or artifact**: one self-contained page to read, share and keep. Use `--format html`. If they use Claude artifacts, follow `references/design-system-format.md` to publish it as a design system artifact.
3. **Put it into the code**: tokens as CSS variables (`--format css`), a Tailwind config (`--format tailwind`), and an `AGENTS.md` of always-on rules so AI agents use the real tokens (`--format agents`). Say where each file should go in their project, and let them place it. Never overwrite their existing files without asking.

3b. **If the project already has its own variable names** (most do), do not ask the developer to rename anything. Run `check_drift.py ... --write-names linked-tokens.json`, then `export_system.py linked-tokens.json --format bridge --source <label>`. It writes a small CSS file that points the app's own names at the tokens (only for variables that share a token's name and already hold its value, so nothing changes visually). Add `--prefix ds-` to the CSS, Tailwind and bridge exports so token names never clash with the app's. For rules that belong only to this project, put them in a markdown file and pass `--rules rules.md` to the agents export, so the generated AGENTS.md does not say things that are untrue for the project (the 44px tap-target line appears only when the system has a 44px token).
4. **For engineers**: `--format components` writes `components.json`, one structured record per component (summary, use, rules, states, tokens used) read from the component pages, so tools and AI agents can read what each component is. `--format style-dictionary` writes `tokens.dtcg.json`, the Design Tokens (DTCG) format that Style Dictionary and Figma token tools read, with dark values under `$extensions.mode.dark`.

If they do not say, recommend the PDF or page first (it is safe and changes nothing), then offer the code export. Tell them what you produced and where it is saved.

### 7. Keep it in step
A design system goes stale the day after it is written, so offer the drift check and say what it does: `python <this-skill>/scripts/check_drift.py <tokens.json> <label=folder> [more sources] --ignore <colours that are not the app's> --write-names linked-tokens.json`. For each source (for example the prototype and the real app) it lists the values used in the code but missing from the tokens, the variables that share a token's name but hold a different value, and which code variable holds each token. The threshold is automatic (a small project checks every value; a larger one ignores values used fewer than 3 times, and the report says how many rarer values it skipped), and `--min-uses N` overrides it. `--ignore` takes the exact hex values of the prototype's own frame colours, which belong in the skipped pile. Without `--fail` the exit code is always 0; add `--fail` to exit with an error when there is drift, so a developer can run it before each release. Report the result in plain words, park each difference for the person, and never change the code or the tokens by yourself.

## Judgement calls that come up every time

These were found by testing the skill on a small project. Decide them this way so different people get the same result.

- **Linking code names to token names.** Put the code name in the token's usage note ("Code: `--bg`"). That is how the next scan, and a developer, know they are the same thing. The scanner matches variables to tokens by value and flags any with no match. To link a prototype and the real app at once, use `check_drift.py ... --write-names linked-tokens.json`; it stores each token's code variable per source in a `code` field and prefers a variable with the token's own name.
- **A value used once that nobody confirmed.** Park it. Save an as-built value only when it recurs, or a person confirmed it. Never promote a one-off just because it exists.
- **Who decided it.** Name the person only if they said it. If a note records a decision with no speaker, attribute it to the document and date ("decided in the review notes, 21 Nov"). Never guess a name.
- **Retiring a token or rule.** Do not add custom fields to a format. Begin the usage note with "Deprecated, replaced by X on <date>." and add a line to the decisions page. The token stays.
- **Only one theme in the sources.** Save the theme that exists. Park the other ("dark values not decided") instead of inventing them.
- **Conditions the sources do not state.** Write only the rows the sources support. A blank row is better than a guessed one; park the question instead.
- **Reports and recommendations.** A review, report or handoff note often holds a recommendation ("recommended: delete for good"), or an answer written by someone's tool. Record it as proposed, not decided, until the person has said yes in their own words. Read the person's own answers and replies first, then the reports. When the two disagree (for example the person said "keep the blue ring" and a report says there is no blue ring), do not pick one: record both as a conflict for the person to settle.
- **The scanner's limits.** It counts occurrences, so on a tiny project the counts mean little. It cannot read everything (unusual shorthand, styles built in code). Read the CSS yourself for what it misses, and say in the report what you read by hand.

## Principles behind the choices

- **A rule without a reason gets broken.** Write why, because the next person, or an AI agent, has to handle cases the rule did not foresee. A system that carries its reasoning can be followed in new situations; a list of values cannot.
- **Examples beat adjectives.** "Calm" means nothing; a screenshot or exact copy of a good case does.
- **Write it so an AI can follow it.** AI has no memory of the conversation where a decision was made. If it is not written down with its reason and an example, it does not exist for the next build.
- **One source of truth.** If the tokens exist in code and in the system, say which wins and how they stay in step. Two copies drift.
- **The system follows the product, and the product follows the system.** When they disagree, either the product is fixed or the system is changed on purpose, and the change is written down. Never leave both and hope.

## When something is missing
No existing system: create a small first one and say it is small (6 to 10 colours, a handful of type styles, a spacing scale, radii, a README, and the decisions page). No code, only conversation: save the decisions and mark every value as "stated, not yet seen in code". No tokens file: build one from the inventory and mark each value's source.
