# What to save, park or skip

Use this to sort each candidate. A candidate is anything the scan or the sources show: a value, a rule, a component, a piece of copy, a behaviour, a file.

## Save

Save when at least one is true:
1. **A person decided it.** They said it, chose between options, or approved it. ("Option D, but make the curve more S." "The website stays white.") Save the decision and who made it.
2. **The product does it consistently.** A value or pattern used many times, in more than one place, with no competing version. The scan count helps: 20 uses of 18px for field corners is a standard.
3. **Breaking it causes a visible problem.** Contrast, a minimum tap size, a rule an audit found broken. Save the rule and the measured reason.
4. **It is exact wording** the person fixed ("You're invited. Let's get on the road."). Copy is a design decision.
5. **It is an asset** that stands for the brand (logo, favicon, a chosen share image) and its approved version.
6. **It is a condition** (what changes for whom): organizer or member, phone or website, loading or offline. Save it with who decided it.

For every saved rule, write: the rule, the reason, an example of good, and the condition where it applies.

## Park (an open question, not a rule)

Park when:
- It is **undecided**: two options were shown and no choice was made.
- **Two sources disagree**: the written rule says one thing and the code does another, or two documents conflict. Record both and mark a conflict.
- It was used **once or twice** and nobody confirmed it. It may be a mistake.
- It needs **a person's call**: a naming choice, a behaviour with a trade-off, something with legal or privacy impact.
- It is **proposed**: you suggested it, they did not answer. Mark it "proposed", never as decided.

Every parked item gets: the question in one line, the options, your recommendation, where it came from, and who decides.

## Skip

Skip, with a one-line reason, when it is:
- The **prototype's own frame** (the page chrome around a prototype, stepper buttons, viewer styling), not the product.
- A **temporary label** or placeholder ("Coming soon" on a feature that will ship, test names).
- **Test data or fixtures** (sample trip names, fake people).
- A **throwaway experiment** the person rejected.
- **Private**: keys, tokens, real people's names, emails or data. Never write these into a design system.
- A **near-duplicate caused by a typo** (a colour one shade off a token used 40 times). Flag it as a probable error, do not make it a token.

## Hard cases

- **Code differs from the stated decision.** Save the decision. Park the difference as a conflict: "The code uses 14px; the decision says 12 or 18."
- **A value is used a lot but nobody chose it.** Save it as "as built", say so, and recommend folding it into the nearest standard step. Do not call it a standard.
- **Something worked and was then removed.** Keep it as "retired on <date>, because <reason>". The reason is the lesson.
- **An audit found a bug.** The rule that would have prevented it is worth saving. The bug itself is not.
- **The person is frustrated or terse.** Their wording still carries a decision. "I don't like this at the top" means the top needs another design; park it as a request with the picture, do not guess silently.

## Worked example (from a real project, Trinner)

| Candidate | Pile | Why |
|---|---|---|
| "One red action per screen" | Save | Stated by the person; reason: the main action should be unmistakable |
| "The website stays white; the phone uses colour" | Save | Stated; becomes a condition (phone vs website) |
| 14px and 16px corner radii (used 23 and 8 times) | Save as built, flag | Used a lot, never chosen; recommend folding into 12 or 18 |
| #1A1A19 and #262624 dark colours | Skip | They belong to the prototype's own page frame, not the app |
| "Coming soon" on Leave the trip | Park | A temporary label; the real behaviour is undecided |
| Whether the organizer is told when a member leaves | Park | Proposed, not answered; needs the person |
| "You're invited. Let's get on the road." | Save | Exact copy, fixed by the person |
| A one-off 61px margin | Skip, flag | Used twice, looks like a mistake |
