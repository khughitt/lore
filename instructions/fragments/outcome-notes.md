## Task notes for outcome measures

Two note shapes are read by obs's outcome measures; write them as plain
`tasks note` lines, exactly in this form.

- When a review of your spec, plan, or implementation arrives, before acting on
  it, note it on the task: `review: <spec|plan|impl> round <n> — verdict: <revise|accept>; findings: <label> <count>, … | none; reviewer: <harness/model | human>`
  (`review: plan round 2 — verdict: revise; findings: P1 1, P2 3; reviewer: codex/gpt-6.1-sol`).
  Use the actual reviewer's exact model identity when supplied by the reviewer or
  verified dispatch/runtime metadata. Do not substitute the controller's model,
  a generic model family, or a configuration default. When the reviewer's model
  cannot be verified, record the harness alone without guessing; keep human
  reviews labelled `human`. A Codex session that performed a review reads its own
  identity (never on another session's behalf), in the turn that performed it with a
  fresh command (never a terminal left from an earlier turn):
  `timeout 2 relay model --harness codex --pretty` prints `codex/<model>` when
  verified and `codex` otherwise. Copy the printed value; when the command exits
  non-zero or times out, the value is `codex`. Whenever it is bare `codex`, name the
  stderr reason or the exit status in the review, or in the final message for a
  self-review, never in the note. A reviewer writes no note: it states that value in
  its review for the note writer to record.
  Only a session noting its own self-review records it directly.
  `n` counts from 1 per task and artifact; a re-review after a revision is the next
  round; a short acceptance is still a round. The flow `verified` gate stays a
  disposition record, not a round.
  One agent writes each round's note, once, before handing the findings on: the
  controller when there is one, otherwise the agent the review arrives to. A worker
  handed review findings (resumed or freshly dispatched) checks that the round's note
  exists and writes none; if it is missing, the worker says so in its report for the
  controller to add.
- When you file a task because work closed as `done` fell short, changed, or grew,
  note it on the new task at filing: `concerns: <task-id> <defect|change|extension> — <one line>`.
  `defect`: the closed work did not do what its task asked or broke something that
  worked; `change`: it did what was asked and something different is now wanted;
  `extension`: new scope built on it. A finding before close is a review finding,
  not a concern.
