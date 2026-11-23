# Where things go: the design system format

Use this when you write into a design system. It describes the layout the "Design System" artifact type uses, which is also a good plain-folder layout if there is no artifact tool.

## Files

| Path | What goes in it |
|---|---|
| `README.md` | The brand book: voice, visual foundations, iconography, how to use the tokens. Start here. |
| `tokens.json` | Colours (per theme), type, spacing, radius, shadow, z-index. |
| `conditions.md` | The condition tables (see conditions.md in this skill). |
| `spacing-and-layout.md`, `accessibility.md`, `writing-and-copy.md`, `motion.md` | Rules pages, each rule with its reason. |
| `for-ai-agents.md` | The hard rules in one place, why they exist, examples of good, and "when a rule and a request disagree, do what they asked and say which rule it breaks". |
| `decisions-and-open-items.md` | The ledger: decided, found while checking, open, conflicts. Nothing parked is lost. |
| `components/<Name>/README.md` | The guideline: rules, states, when not to use. First sentence is the summary. |
| `components/<Name>/preview.html` | A small live example. Line 1 is `<!-- @dsCard group="Actions" height=200 subtitle="..." -->`. Plain HTML and CSS using the tokens (e.g. `var(--accent)`). Load fonts with a Google Fonts link inside the preview. |
| `components/Cover/preview.html` | The cover picture (palette blocks, one pattern from the brand, the name). |
| `design-system.json` | The index (`title`, `lastChange`). Written last. |

## tokens.json shape (the artifact type reads exactly this)
Every family except `type` is a **list**: `{"tokens":[{"name","value","usage"}, ...]}`. A name-to-value map is valid JSON but the page cannot read it.
- `color`: `{"themes":[{"id":"light"},{"id":"dark"}],"tokens":[{"name":"ink","value":{"light":"#1E1E1B","dark":"#F4F2EC"},"usage":"..."}]}`. Values: hex, `rgb()`, `hsl()` or an alias `"{other-token}"`. No `var()`, no named colours. A plain string is the first theme's value.
- `type`: `{"fonts":[...],"families":{"serif":"\"Instrument Serif\", Georgia, serif"},"groups":[{"name","family","styles":[{"name","fontSize","lineHeight","fontWeight","usage"}]}]}`.
- `spacing`, `radius`, `shadow`, `zindex`: `{"note":"...","tokens":[...]}`. Lengths are `px`, `rem`, `em` or `%`.
- Names: letters, digits, `_ . -`, unique across all families except `type`. Every token gets a `usage` note, written for the person or AI who will apply it.

## Writing to the Design System artifact
1. Read the current `project/design-system.json` and every file you will change, first. People edit the page, so never work from an old copy.
2. Write the files into one folder under `project/<path>`, same layout as above.
3. Publish all changed files in one Artifact call (`url`, `root` = your folder, `file_path` = `project/design-system.json`, `files` = the others). Send the index last, with `lastChange` updated (who, when, a one-line note).
4. If a publish is refused because someone saved meanwhile, read those files again, redo the edit on them, and try once more. If it fails again, tell the person and stop.
5. Test every preview in light and dark before publishing: no overflow, readable text, real fonts.

## If there is no artifact tool
Keep the same folder layout in the project (for example `design-system/`), and tell the person the folder is the system. Do not invent a different layout; the layout is what makes it portable.

## Never
- Invent a value, a name, or a person's decision.
- Put keys, tokens, real emails or real people's data in the system.
- Delete a token or rule. Mark it replaced and keep it.
