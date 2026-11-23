# Conditions: the part most systems forget

A component is rarely wrong by itself. It is wrong in the wrong condition: a Delete button shown to a member, a red toggle on the website, a "No account needed" line when accounts are needed. Record the conditions.

## How to find them
Read the sources for: roles (who sees what), devices (phone, tablet, desktop), themes (light, dark), states (empty, loading, slow, offline, error, locked, disabled), stages of a flow (draft, review, locked, done), flags (feature on or off, beta), and sizes (narrow screens, long text). Every "only when", "never for", "except", "unless" in the chat, notes or code points to one.

## The format
One table per kind of condition, each row: the condition, what shows, what never shows.

| Condition | What shows | What never shows |
|---|---|---|
| Organizer | Delete trip, Lock the plan | Leave the trip |
| Member | Leave the trip | Delete trip, Lock the plan |

Kinds worth a table: **who is looking**, **device**, **theme**, **state of the screen**, **stage of the flow**, **settings and flags**, **size and input** (narrow screens, long names, touch, keyboard).

## Rules
- Add a row the moment a decision creates a condition. Put the source and date in the decisions page if it matters.
- If a condition exists in the product but nobody ever decided it, add it as "as built" and park the question.
- Keep each row to one sentence. If it needs a paragraph, it is a rule and belongs in the rules pages with its reason.
