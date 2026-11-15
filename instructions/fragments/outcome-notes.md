## Task notes for outcome measures

<!-- rule:986dd690d14b42a1a7ca315e475ff7c2 begin -->
Two note shapes are read by obs's outcome measures; write them as plain
`tasks note` lines, exactly in this form.
<!-- rule:986dd690d14b42a1a7ca315e475ff7c2 end -->

<!-- rule:96745a06cd69497b8ffe0511c66bda2f begin -->
- Each review of a spec, plan, or implementation is noted on its task once, before
  anyone acts on it: `review: <spec|plan|impl> round <n> — verdict: <revise|accept>; findings: <label> <count>, … | none; reviewer: <harness/model@effort | harness/model | harness | human>`
  (`review: plan round 2 — verdict: revise; findings: P1 1, P2 3; reviewer: codex/gpt-6.1-sol`).
  Use the actual reviewer's exact model identity when supplied by the reviewer or
  verified dispatch/runtime metadata. Request the reviewer's own observed effort
  from a supported runtime source; retain `@effort` only when observed. Missing
  effort stays unknown, with the reason in the review report; never copy assigned
  or requested effort into observed identity. A Claude reviewer writing its own
  note has no supported source for its own sent effort, so it omits `@effort`.
  A controller writing a Claude child's note observes sent
  effort from the child transcript's `api-request` `params.output_config.effort`,
  corroborated by its metadata; a model's self-report is not evidence. This records
  what the harness sent, not model-internal compliance. Do not substitute the controller's model,
  a generic model family, or a configuration default. When the reviewer's model
  cannot be verified, record the harness alone without guessing; keep human
  reviews labelled `human`. Use the harness id (`codex`, `claude-code`), never
  placeholders such as `unknown`, `unverified` or `unrecorded`, as a reviewer value.
  A Codex session that performed a review reads its own
  identity (never on another session's behalf), in the turn that performed it with a
  fresh command (never a terminal left from an earlier turn):
  `timeout 2 relay model --harness codex --pretty` prints `codex/<model>` when
  verified and `codex` otherwise. Copy the printed value; when the command exits
  non-zero or times out, the value is `codex`. Whenever it is bare `codex`, name the
  stderr reason or the exit status in the review, or for a self-review in a separate
  task note, never in the `review:` note. A reviewer copies that value into the
  `review:` note it writes and states it in its review.
  `n` counts from 1 per task and artifact; a re-review after a revision is the next
  round; a short acceptance is still a round. The flow `verified` gate stays a
  disposition record, not a round.
  Brainstorming's builder check counts as a `review: spec` round: use `revise`
  when it raises questions to answer in the document or bring to the user, and
  `accept` when it raises none. Record its reviewer identity by the same rule above.
  The reviewer writes the round's note. A reviewer whose request names a task id
  appends that round's single `review:` note to that task itself
  (`tasks note <id> "<note>"`) as its last step before returning its review,
  computing `n` from the task's existing `review:` notes for that artifact, and
  changes nothing else on the task: no other note, status, claim or field. Its
  review states the note it wrote, or why it wrote none (no task id named, the
  write refused). The agent the review arrives to (controller, author or worker)
  checks that the round's note exists and writes no second one. Only when the
  reviewer could not write it does that agent write the note, before acting on the
  findings, and say why in its report: the controller when there is one, otherwise
  the agent the review arrives to. A worker handed review findings (resumed or
  freshly dispatched) writes none; if the note is missing, it says so in its report
  for the controller to add. A session noting its own self-review writes it directly.
  This shape measures only spec, plan and implementation reviews; record a review
  of any other artifact (a scope brief or research note) as a plain task note that
  does not begin with `review:`.
<!-- rule:96745a06cd69497b8ffe0511c66bda2f end -->
<!-- rule:86172e9df3bc47369bde0a298b8a292a begin -->
- When you file a task because work closed as `done` fell short, changed, or grew,
  note it on the new task at filing: `concerns: <task-id> <defect|change|extension> — <one line>`.
  `defect`: the closed work did not do what its task asked or broke something that
  worked; `change`: it did what was asked and something different is now wanted;
  `extension`: new scope built on it. A finding before close is a review finding,
  not a concern.
<!-- rule:86172e9df3bc47369bde0a298b8a292a end -->
