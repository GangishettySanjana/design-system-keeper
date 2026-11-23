# What a complete design system contains

This is the checklist the skill measures a project against. It combines two sources:

- Figma, "Design systems 101": a design system is the top-level container. Inside it sit the **foundations** (colour, type, icons, logos, illustration, spacing, voice and tone), the **component and pattern libraries** (reusable elements and the flows that combine them), and the **guidelines and documentation** (accessibility, brand, usability, coding standards, principles, processes). It is a living product, so it also needs an owner, maintenance time, and people who champion it. A style guide is only the visual subset; a design system also covers code and usability.
- Into Design Systems, "AI design systems": AI agents are a new consumer. They need the team's own decisions written down, tokens they can read by name, one structured description per component (identity, props, variants, sizes, states, usage), usage rules in plain text, always-on rules (for example an AGENTS.md), clean naming, and clear limits on what an agent may do alone.

## The checklist

**Foundations**
- Colour, with themes (at least light and dark) and a usage note for each token.
- Typography: families, a type scale, and where each style is used.
- Spacing scale, corner radius, elevation (shadows), layers (z-index).
- Motion: durations, easing, what may animate, reduced motion.
- Iconography, brand marks (logo, wordmark, favicon), imagery and illustration.

**Token quality**
- Every token has a usage note ("what is this for?").
- Code names are linked to token names, so a developer or agent knows `--bg` is `paper`.
- Names are consistent: lowercase, dash-separated, one meaning each.

**Components**
- Each repeated component is documented: what it is, when to use it, when not to, its variants, sizes and states.
- A live example or preview for each.
- Machine-readable data per component (a small JSON file) so tools and agents can read it.

**Patterns and templates**
- Layouts and flows that combine components (for example sign-in, empty state, error state).

**Guidelines**
- Accessibility: contrast, tap-target size, focus, motion.
- Content and voice: tone, exact wording that was decided, words to avoid.
- Principles and hard rules, each with a reason.
- Conditions: what changes by role, device, theme and state. This is where most real bugs live.

**Documentation**
- An overview (README) that says what the system is and how to use it.
- A decisions ledger: what was decided, what is open, what conflicts. A change log.

**Governance**
- An owner, an update process, and a rule for how the system and the product stay in step.
- Versioning and deprecation (retire things on purpose, never silently).

**AI readiness**
- Machine-readable tokens.
- Machine-readable component data.
- Always-on rules for agents (AGENTS.md or a "for AI" page) that say: use the tokens, never invent a value, ask when unsure.
- Trust levels: what an agent may do alone (suggest only, draft a change, or apply a low-risk fix) and what needs a person.

## How to use this checklist

Run `scripts/coverage.py` to mark each item Found, Partly or Missing, with the evidence. Report it in plain words. Do not fill a Missing item by inventing content: park it as an open question, or, when the project clearly has the answer, save it with its source. A system that honestly says "motion: not decided yet" is better than one that guesses.
