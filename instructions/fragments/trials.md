## Trials

<!-- rule:b2d5d7b434c74989a11e2b7a88dcd829 begin -->
After `tasks start`, run `~/.agents/bin/trial-arm <id>` and follow what it prints.
`flow on` runs the task under the flow skill; `flow off` runs it without flow,
whatever else would choose it; `not enrolled` changes nothing. Every task in a unit
has the unit's arm, and the task's `process` is unchanged in both arms. Only the user
overrides an arm: record it with `tasks note <id> "arm: <trial> — override: <why>"`.
If it exits non-zero, show the user its error and do not choose flow on or off until they answer.
<!-- rule:b2d5d7b434c74989a11e2b7a88dcd829 end -->

<!-- rule:00bc708d91bf4a1b80ce498d206479e4 begin -->
Reviewer effort is a separate policy, applied equally to flow-on and flow-off work.
For an independent model review, choose the harness/model and rubric before drawing.
Run the stable installed flows helper
`~/.agents/bin/review-effort <task-id> --harness H --model M` for the reviewed task,
require exit 0 and parse its JSON. With `status: assigned`, set its `assigned`
medium/high through the native child setting before launch: Codex's explicit `model`
and `reasoning_effort` with an isolated fork, or Claude Code Agent's per-child
`effort` on a supporting non-fork interface (Claude forks ignore it).
Prompt wording and shared host settings do not
deliver the assignment. Keep other routing, rubrics and review-count rules.
`inactive`, `excluded` and `unsupported` retain the ordinary review policy;
exit 1 or 2, a missing helper or invalid JSON is an error to resolve, never permission
to choose an arm. Human, human-relayed and builder checks are not randomized.

Keep the original task assignment across spec, plan, implementation and corrective
reviews, retries and reopening, including moves/renames; never overwrite its note.
Only exceptions or overrides need an ordinary explanatory note identifying the
affected review and reason. Ask for the reviewer's own observed identity/effort;
missing observation stays unknown and does not by itself exclude supported delivery.

obs identifies eligible supported reviews independently of assignment-note compliance,
applies the same exclusion for any `review:` note timestamped before activation,
and recomputes arms with `~/.agents/bin/review-effort compute <original-task-id>`.
Matching assignment duplicates count once; contradictory identity/hash/history is
an error. A late synchronized earlier review note excludes without deleting the
old assignment; a note timestamped after activation does not prove a later dispatch.
Controllers need no dispatch-timestamp archaeology.
<!-- rule:00bc708d91bf4a1b80ce498d206479e4 end -->
