# Realism checklist: <method and machine class>, Slice <letter>

Copy this file for a new demo, fill every field, and review it before the demo is published (realism rule 6 in the
[ROADMAP](../ROADMAP.md#realism-rules-apply-to-every-phase)). Keep the six rule names exactly as below, so the
checklists can be read side by side.

- **Demo:** [`web/<demo>/`](../../web/<demo>/) (add the query string if it opens a variant)
- **Class preset:** `<preset id>` in [machine-classes.json](../../models/presets/machine-classes.json), or "none" with the reason
- **Method card:** [<method>](../research/methods-reference.md#<anchor>)
- **Rules:** [ROADMAP realism rules](../ROADMAP.md#realism-rules-apply-to-every-phase)
- **Models:** links to the model sections in [MODELS.md](../MODELS.md)
- **Validation:** links to the pages in [validation/](../validation/) that check this demo, or "none yet"

Reviewed <date>. Status: ✅ meets the rule · ⚠️ partly, gap listed · ❌ not yet.

| # | Rule | Status | Evidence | Known gaps |
|---|---|---|---|---|
| 1 | One method, one machine class, one ground | | Method, class preset and ground, with the source that pairs them | |
| 2 | Right support and lining for the method | | What is built behind the face, with sources | |
| 3 | Right layout and muck path | | Front to back, with sources | |
| 4 | Right cycle and utilisation | | The cycle steps, their times and the downtime model, with sources | |
| 5 | Every number in a cited range | | Inputs, limits and outputs against reference machines or projects; best day, week and month against the records | |
| 6 | Honest labels | | Badge and Model limits panel wording | |

Evidence names its source (a link, or a key from a Sources list below). A value without a source goes under Assumed
values, never in the Evidence column.

## Sources (optional)

Short keys for sources cited many times in the table, each with its link.

## Assumed values (optional)

Every value the demo uses that no open source gives, grouped by part, each marked assumed or illustrative.

## Behaviour checked in the browser (optional)

What was clicked or changed in the running demo and what it showed.

## Before the next publish

- [ ] Open items, each tied to a rule number or a gap in the [validation report](../validation/REPORT.md).
