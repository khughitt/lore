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

### Review briefs and regime

<!-- rule:6e47fe41e61e4fa4a39e084d05e7a8a1 begin -->
Every brief includes the affected projects' stages, the effective process,
the applicable safeguards and the named consumer obligations. Confirm the
review is needed and choose the rubric before the effort draw. A cross-project
review grades each affected part using that project's obligations.

- `rubric: early-1`. Grade a defect or a missed explicit obligation. In
  experimental work, missing compatibility code, a speculative migration or
  broad tests alone do not count as findings. A missing named consumer update
  can be Important for pre-release. Updating the consumers together fulfills
  their compatibility obligation.
- `rubric: supported-1`. Use the supported grading criteria and existing evidence
  and review workflow. Use this marker for a retained flow-trial unit or a
  combined review that includes supported work. Name the
  user-facing consequence of each finding and check the applicable explicit
  contracts.

Copy the marker from the applicable grading text into the brief. Bump its
number only when the corresponding grading criteria change.

If these rubrics are active before the reviewer-effort trial begins on
2026-11-30 UTC, apply them starting with the first eligible review. If activated
after the trial begins, keep the same rubric in both arms, preserve assignments,
and record one matching companion beside each applicable review note:

```text
review regime: <spec|plan|impl> round <n> — stages: <prefix>=<stage>[,<prefix>=<stage>...]; process: <direct|planned>; rubric: <early|supported>-<positive revision>
```

Use the effective process and the marker copied into the brief. List distinct
prefixes in sorted order. Match the task, artifact and round of the existing
`review:` note. Apply the paired write and controller fallback under Task notes
for outcome measures. Preserve original eligibility, assignments and review counts.
<!-- rule:6e47fe41e61e4fa4a39e084d05e7a8a1 end -->
