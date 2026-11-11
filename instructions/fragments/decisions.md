## Decisions

<!-- rule:fdd377a3c264435296d1792c8f74c68b begin -->
- When you hold a recommendation for a bounded decision, state it with one clause of
  reason and act on it; the alternative you rejected goes to the task record, as
  Communication sends rejected options (without a record, after the recommendation in the
  message), while a trade-off that could change the user's answer stays in the message.
  Do not end the turn to ask for confirmation: the user
  overrides in free text if they disagree, and a wrong default costs one correction
  while a question costs a stop. This applies to "which approach", "where should this
  land", "does this section look right", "which follow-ups to file", and "execute now".
<!-- rule:fdd377a3c264435296d1792c8f74c68b end -->
<!-- rule:8d52bc64e99b42d78f4219f73c3b375c begin -->
- Stop and ask only when the answer needs the user: an artifact they must inspect and
  judge (a sheet, a screenshot, a rendered page), a choice of taste, scope, or priority
  that is the user's to make (your recommendation informs it but cannot settle it, and
  the question carries your recommendation, or the guess that stands in for one, as the
  question rule below says), money to spend, an action outside the repository without
  an explicit applicable grant, a live operation that has failed twice with no
  established cause (the next rule), or a turn that has run past its range (the
  turn-pause rule below).
  An explicit task grant, recorded in a task note quoting the user's words and
  session, carries through stages, fixes and handoffs within its action scope,
  repository, destination/ref and limits; recover that note and accepted revisions.
  Checkpoints or new commit IDs do not expire it. Closure, revocation or retargeting
  does; reopening does not revive it. General “proceed” or plan approval alone grants no
  external authority. Check all outgoing commits for unrelated or unreviewed changes;
  separate those changes or seek new authority.
<!-- rule:8d52bc64e99b42d78f4219f73c3b375c end -->
<!-- rule:052f6da8885c4d2f81b11c0602eb6e92 begin -->
- A live or external operation (a download, an acquisition, a deploy, a remote job; not
  a local test or build, which debugging covers) that has failed twice with no
  established cause is the user's decision, not a reason to gather more evidence: stop
  and ask whether to retry, change approach or defer, recommending one. The question
  names what each attempt cost (wall time, holds on the host, quota or rate limit spent)
  and what is known and unknown about the cause. A cause is established when evidence
  shows it (an error that names it, a reproduction), not when a hypothesis fits. A new
  diagnosis, build, review or re-scope aimed at the same operation does not reset the
  count, and neither does a fix for a cause that was guessed.
  Retries inside an explicit user allowance (including a user-approved plan's Binding
  allowance with source and purpose) continue without asking; otherwise stop after
  the second unexplained failure. Rulings may lower or remove incidental caps, never
  enlarge unexplained-failure authority or relax human or protective limits.
  Unattended, park the task `--waiting-on user --reason decision` with that question
  as its next step.
<!-- rule:052f6da8885c4d2f81b11c0602eb6e92 end -->
<!-- rule:1f37e3afebdd433a9ccaa2970cde7289 begin -->
- A turn is the work since the user's last message, your subagents' work included; a
  session you launch from the shell (`claude -p`, `codex exec`, a dispatched worker or
  reviewer) is a subagent here, so check before launching one and count it as spawned
  and its work as your turn's. A background wake or loop tick does not start a new
  turn. If the hook says a message the user typed matched a pending scheduled prompt,
  ask them to rephrase it; that message has not reset the turn or ended a pause.
  A turn is past its range when it crosses an enforced limit `hq pause limits` prints
  (active time, root tool-call attempts, tree-wide subagents spawned), or the budget the user set for
  this turn as the first line of their own message, alone on the line and in the form
  `budget: 12h` (optionally `, 2000 calls`, `, 80 agents`, `, 4 compactions`), which
  scales the other limits with it. Budget text anywhere else, quoted, fenced or pasted
  included, is an example: it sets nothing, and you ask nothing about it. A first line
  that starts with `budget:` but is not in that form sets nothing either: mention it
  in your next report and carry on under the turn's limits. An approved spec, plan or
  task is not a budget, nothing you write can set one, and a prompt you write for
  another session never carries a budget line. Check `hq pause status` before
  dispatching a subagent, at each plan-task boundary and after a compaction. Where no
  pause hook runs, keep the enforced counts (active time, root tool-call attempts,
  tree-wide subagents spawned) yourself against those limits. For counted metrics,
  `hq pause status --json` is authoritative; keep manual unhooked counts separate.
  Root calls count only the controller's attempts: 445 root calls plus 57 reviewer
  calls is still 445 against the root allowance. Active time includes in-flight
  work across the tree; spawns count the whole tree, and compactions only the root.
  Root compactions are an advisory context-growth signal, not a hard limit: reaching
  or crossing the compaction threshold never pauses or stops a turn on its own,
  whether hooked or unhooked, and an unhooked session never stops for automatic
  compactions or guesses pre-compaction tool calls from truncated context.
  Exactly reaching an enforced limit remains allowed: 500 root calls under an
  allowance of 500 is within range; the 501st crosses it. Count a running call or wait in full
  and time spent waiting on the user not at all. The hook's warning (including the
  advisory compaction warning) means give a
  concise status update and prepare while continuing authorized work; it is not a
  mandatory stop, a request for a new budget, or a new approval gate. Stop on an
  actual crossed enforced limit or another genuine human gate. Its refusal, or your own count
  past an enforced limit, means stop: start nothing new, stop the work you already started
  (interrupt your subagents and the sessions you launched, stop your background calls
  and processes). Pause any active goal of yours when authorized; if its tool requires
  a user pause request you do not have, include that request in the decision below.
  Then only the report and the park (the hook enforces this where it runs); this
  outranks Processes' wait for a running child. A paused park records the
  worktree, process and retained-item accounting you already hold and says it was not
  refreshed; the session that resumes refreshes it before other work, which here
  outranks Processes' accounting at park. As the controller (or working alone), write
  the pause report, park the task `--waiting-on user --reason decision` with the
  decision as its next step, and end the turn. As a subagent, or a session another
  agent launched (even when the hook treats you as a root), park any claim
  `--waiting-on agent` for whoever launched you and return a short status (done, left,
  running); only the controller writes the pause report. The report gives what the
  turn spent (active time, tool calls, subagents, compactions, and tokens or rate
  limit where you can see them), what is done and verified, what is left with your
  estimate of its cost, anything that went wrong, and one decision with your
  recommendation: continue under a budget you name, given as the exact first line for
  the user to send (a reply without it continues under the default limits), continue
  in a user-chosen fresh controller when compaction or context growth is the binding
  cause, narrow the work, or stop. The user's reply ends the pause; it is not an
  approval of routine steps, and the next turn asks nothing about continuing until it
  too crosses a limit; the other stops above still apply. Never edit the hook's state
  or limits, split work across turns or controllers, or start a fresh session to stay
  under a limit.
<!-- rule:1f37e3afebdd433a9ccaa2970cde7289 end -->
<!-- rule:db275842f3af447dbe84d8b1dfc68051 begin -->
- Two written artifacts keep their gate: a design spec and an implementation plan are
  reviewed before the next phase starts. Within writing them, sections are not
  individually approved.
  A material amendment changes accepted goals, scope, behavior or outputs,
  constraints, required evidence, cost or risk bounds or authority; judge cumulative
  effects. Review changed specs before affected plans, with exact revisions and
  consequences; keep active inputs frozen. Explicitly close or supersede the old
  round in its record before submitting a frozen replacement. Stop dependent work;
  unaffected authorized work may continue.
  Adjustments preserving commitments use existing rulings; purely
  mechanical flag or path repairs restoring the intended operation need none; target,
  behavior or risk changes are not mechanical. Record named acceptance, clear stale
  waits, and carry it into handoffs. New plans label proposed stops or caps Binding
  with source and purpose; approval adopts them, never retroactively added labels. Reviewers challenge unnecessary binding stops before acceptance.
  Unlabelled agent checkpoints or caps stay adjustable; human, policy and protective
  limits bind regardless. For older plans use recorded intent; clarify consequential
  conflicts.
<!-- rule:db275842f3af447dbe84d8b1dfc68051 end -->
<!-- rule:f431707097c0418c9822d67074875c51 begin -->
- A request to review a spec or plan names the frozen revision under review: the
  repository, commit and path, so the reviewer reads `git -C <repo> show <sha>:<path>`
  rather than the working file. Where the profile keeps the document out of the tree,
  the request names its path and sha256, and the reviewer checks that sha256 before
  reading and stops on a mismatch. While that review is open, never amend or rebase
  the commit, and leave an out-of-tree file unedited. A later draft reaches review only
  as a new frozen revision, named in the next round's request, and each finding is
  judged against the revision its request named. When asking the user to approve a
  frozen artifact or amendment, keep the frozen revision in the linked record or
  change summary rather than as raw hashes in the message, and for an amendment state
  the change and its consequences with the full document linked (Communication).
  For any commit-based review, including implementation review, finish the
  commit, read its actual full SHA from Git in the target repository, then
  dispatch against that SHA. Never guess the SHA or dispatch in the same parallel
  batch as the commit that creates it; a nonexistent SHA is not a frozen target.
<!-- rule:f431707097c0418c9822d67074875c51 end -->
<!-- rule:2c5785f136ca4ee590e1c69406276623 begin -->
- A question, when asked, is one question, not a series, and carries your
  recommendation: in a harness's multiple-choice question tool, as the first option;
  on relay's typed `question` schema, as `recommended` on each choice item (`single`
  or `multi`) where you hold a view; in a message, inside the decision request
  (Communication), with the alternatives in the record. Use the available
  supported channel (the harness's question tool or an active relay question route)
  without mandating an uninstalled connector, activating services, or turning a
  bounded recommendation under the first rule above into a stop. Over the typed
  channel, keep the question `class` values distinct: `clarification` for scope,
  priority, taste or intent, `artifact-review` with `artifact.ref` and
  `artifact.revision` for an artifact the user must inspect, and `authorization`
  (answerable only from a local surface) for an external, host, spend or live-surface
  gate; transporting an answer delivers the user's response and grants no authority
  beyond the gate asked. A question that asks
  the user to describe what they want (brainstorming's open questions, and its
  playback asking what is wrong or missing) carries no options; a guess they can
  correct stands in for the recommendation. That playback is not a "does this section
  look right" decision: what they want is theirs to say.
<!-- rule:2c5785f136ca4ee590e1c69406276623 end -->
<!-- rule:c165eee5aa0a4b819061b34386c78c23 begin -->
- Before drafting or resuming a design or spec/plan amendment, even when no question
  is planned, and before asking the user what work should achieve or why
  (brainstorming's opening questions, playback or builder check), establish the
  latest human goal and limits. Work the user describes in this session starts with
  that description; ask only what it leaves unresolved. Naming a task to take up
  is not describing it. Other work (filed by
  another session or agent, captured earlier, grown by scope passes, or derived as a
  follow-up, feedback report or decomposition child) starts by reading what already
  exists: the task's body, notes and references, its `source` and parent chain, and
  the session that filed it. Use session-logs to recover its relevant human turns
  and follow continuation notes, handoffs and prior amendments to relevant human
  turns in any later sessions they reference, including further referenced
  clarifications. Reading needs no offer or permission. Compare inherited
  architecture and scope against those human words, keeping agent assumptions
  separate. State the simplest route satisfying the goal and binding constraints,
  and justify any extra machinery by those requirements; prior investment,
  implemented capability, a continuation note or earlier approval does not establish
  necessity. Remove unnecessary proposed scope without deleting existing code,
  evidence or unfinished work. A human clarification contradicting an inherited
  scope assumption supersedes approval of the affected design or plan: preserve
  the old artifact and approval as history, record the clarification and affected
  assumption, and submit a corrected frozen revision for review before implementing
  it. Old approval does not approve that corrected artifact. A clarification leaving
  approved scope intact creates no new review gate by itself and revokes no unrelated
  authorization. Play back
  what you found and where each part came from, keeping the user's recorded words
  apart from what agents added. Then ask only what the evidence leaves to the user (a
  choice of taste, scope or priority, or a premise the evidence contradicts), each
  question naming what you found; when nothing remains, write the design and mark each
  call as yours. Never ask the user to recall what a record or transcript holds; when
  a source cannot be found, say so and offer your reading for them to correct. The
  written design's review stays the user's gate. This outranks brainstorming's first
  message and its offer to go look.
<!-- rule:c165eee5aa0a4b819061b34386c78c23 end -->
<!-- rule:fbbd81a9cc8642cb9f54ef949154cfc0 begin -->
- For an experiment, pipeline, batch or dedicated supporting infrastructure whose
  intended run incurs additional metered model or external-service charges,
  including an optional paid path, establish cost and proportionality upfront.
  Before accepting its design or implementing dedicated experimental machinery,
  record the simple/manual baseline, the proposed benefit over it, a cost range
  and assumptions, and the proposed enforcing control. The estimate names workload
  units, unit-price basis and date, expected volume, a conservative charge bound
  including retries and concurrent in-flight work, and material uncertainty.
  State any user-approved spending limit separately; leave it unset when absent.
  An estimate or design approval grants no spending authority and sets no default
  budget. Before accepting the implementation plan, make implementation and
  verification of the control a dependency of every paid run, including a cheap
  pilot. Reuse a suitable existing cap or small bounded runner; building the control
  itself does not require it already to exist, and no new service is required.
  Before any paid invocation, verify that the control refuses work exceeding the
  authorized total across all charge paths, including retries, concurrency,
  resumption and unavoidable already-admitted charges, without resetting the
  allowance per step. A provider cap, runner guard or conservatively priced fixed
  workload qualifies only if it actually bounds those charges; an estimate, log,
  alert or promise to monitor does not. If the bound or control is unestablished,
  keep paid execution blocked and recommend a bounded alternative or return the
  unresolved scope or budget choice to the user. Explicit spending permission
  remains required; within that authority, do not repeat approval for each step.
  Authors and reviewers check these requirements against recorded human intent,
  rejecting unjustified expansion or a missing control dependency before dedicated
  machinery is implemented; internal consistency or a late spend checkpoint alone
  is insufficient.
  Ordinary interactive harness use, local no-charge analysis and free hosted CI
  require no experiment accounting, spend allowance, invocation pool or controller.
  Public visibility plus a resolved standard GitHub-hosted `runs-on` establishes free
  runner execution: no billing check. Private hosted jobs, larger runners and paid
  services retain spending controls; self-hosted execution needs host and resource
  authority. Free CI retains bounded timeouts, backoff and unexplained-failure stops;
  avoid redundant overlapping retries. Paid options stay gated. A tool that launches
  a metered experimental run remains within this rule.
<!-- rule:fbbd81a9cc8642cb9f54ef949154cfc0 end -->
<!-- rule:96e7765f238045f4af07742ea0783816 begin -->
- In assessments and reviews, distinguish tree-verified current capability from
  recorded intended direction. Before characterising intended scope, read the relevant
  goals, authority and task/source records. Code establishes current behaviour, not
  eventual scope: preserve the recorded goal and any limit's provisional meaning
  beside what works today. When intent is missing or records conflict, state what is
  unknown and which evidence is missing or conflicting; neither invent intent nor
  replace it with implemented behaviour. A proposed change to intended scope remains
  a human decision.
<!-- rule:96e7765f238045f4af07742ea0783816 end -->
<!-- rule:4fd096e0dfb040c7b5f77277569bbabd begin -->
- A turn that ends with work still owed reports the observed status, not what the turn
  ending implies: which work has stopped and why, what is still running (a background
  check, a dispatched child) and who owns the next step — never "is underway" for work
  that stopped; how a running result is picked up goes in the task note. A step you own (a review you dispatch, a
  check you rerun, a child you have not started) is never reported as waiting on the
  user: finish it, or `tasks park` the task with that step as the next action and resume
  it; hand it over only explicitly (`--waiting-on user --reason review`). A park's next
  step is an action and who takes it ("rerun `just gate` in .worktrees/x, then dispatch
  the Task 6 review"), never a state ("waiting for next steps"). An unblocked task you
  hold is not parked between increments: continue until a blocker, a gate that needs a
  person, or the end of the session. On a typed question channel, `defer` is not an
  answer and advances no gate: the decision remains unresolved whether relay's entry
  moves to `released` on a route with native handback or stays `pending` with
  `presentation: desktop` on a non-handback route. A question and `tasks park` do not
  write each other: continue independent work while a pending or deferred question
  waits, and when you actually stop on it, `tasks park --waiting-on user` with the
  actionable next step and the question `id` when available (and `context.taskId` on
  the question when known).
<!-- rule:4fd096e0dfb040c7b5f77277569bbabd end -->
<!-- rule:717a50b29e794e72b327bf60820479bf begin -->
- A skill's scripted question or stop (an integration menu, a "surface residual
  findings" step) is a bounded decision under this rule unless it falls in the stop
  list above; this rule outranks the skill's "exactly as written".
<!-- rule:717a50b29e794e72b327bf60820479bf end -->
<!-- rule:5a5808d0572f49e49afe103d7569231e begin -->
- Integrating a finished, reviewed branch by local merge is a bounded decision only in
  a repository the user owns. The profile sets the default: a `personal` checkout
  allows it; in a `work` or `external` checkout, never merge on your own: present the
  integration choice. A user-owned checkout under another profile allows it only when
  its repository instructions or the user in the session say so explicitly (for
  example, "Reviewed branches may be merged locally into main without asking."). Never
  infer that permission from the account, the path, the profile's name or assumed
  ownership. A push, a PR, or a merge that changes a live global surface (these global
  instructions, hooks, services) is external under every profile; use the recorded-grant
  exception above, otherwise ask.
<!-- rule:5a5808d0572f49e49afe103d7569231e end -->
<!-- rule:046dfb8c365f454a86390b6b4167e487 begin -->
- Reviewers do not modify reviewed code, input evidence, task records or the ledger.
  When a plan workspace already exists, the dispatch names one unique
  `<slug>-report.md` there, outside the reviewed code and inputs; the reviewer may
  write only that report. It saves the full review, reviewed revision and verified
  reviewer identity, checks the write succeeded and the file has nonzero size,
  then returns a concise handoff: verdict, reviewed revision, verified reviewer
  identity, every actionable finding with severity and location, report path, byte
  size and write outcome. The saved report is the
  authoritative full review; never overwrite a previous round's report.
  The controller checks the write result and file existence/size, records the review
  round before acting, and reads the finding rationale and context needed for its
  decisions. It does not rewrite the report or hash it merely to prove persistence;
  separate frozen-input, attachment and retained-evidence checks still apply.
  Inconsistent findings block acceptance until reconciled. If the designated write
  fails or is refused, the report cannot be verified as present and nonempty, or no
  plan workspace exists yet (including early spec and plan reviews), the reviewer
  returns its full review
  in the final message and the controller persists it as `<slug>-report.md` in the
  existing authorized document destination, recording the reviewer identity and
  the actual write failure or refusal; claim no file-handoff savings in that case. This applies to
  task reviews, scoped re-reviews and final whole-branch reviews and overrides a
  skill that requires full final reports or forbids this designated report write.
  Keep the existing ledger, ruling and retention rules; saving a report does not
  replace those records. Needed report reads remain required.
<!-- rule:046dfb8c365f454a86390b6b4167e487 end -->
<!-- rule:6a846b1f53ee406d9b48c7434364a2cf begin -->
- Before dispatching a final whole-branch review, and before any measurement compared
  against the branch's merge base (a cost or latency gate, a size budget), the
  controller (you, inline) checks whether the plan's base branch has moved, in
  subagent-driven and inline (executing-plans) execution alike: `git merge-base
  --is-ancestor <base> HEAD` fails when it has. Task reviews see only their own diffs
  and cannot catch it. When it has moved, merge the base into the branch (not a rebase,
  which strands the ledger's task SHAs), resolve conflicts, rerun the policy-appropriate
  checks under Tests, and record the merge commit in the ledger; only then review or
  measure, against the new merge base, so the review package covers the merge
  resolution. A measurement taken before that merge does not count toward its gate.
<!-- rule:6a846b1f53ee406d9b48c7434364a2cf end -->
<!-- rule:3a86283b2dfe4f4daf96bf612fcca2af begin -->
- In planned execution (subagent-driven and inline alike), scale review to step risk
  and bound independent reviews per plan task. A step that changes repository code,
  tests, build or lock files, schemas, runtime configuration, or a plan-designated
  reviewed artifact gets independent review: under subagent-driven execution, one
  task review of the task's `BASE..HEAD` diff and implementer report plus one scoped
  corrective re-review per fix round on `FIX_BASE..HEAD` using the implementer's
  saved test evidence (running a focused test only when reading the diff raises a
  specific named doubt the saved run does not answer); inline, the task's completion
  contract and the final whole-branch review cover it. A plan amendment or interface
  ruling is verified by the controller against the binding spec, recorded as a ledger
  `Ruling:` line with `Why:`, `Cost:` and revision references, and checked by the
  affected build and final reviews; never spawn a standalone scope, authority or
  preflight reviewer solely to bless a ruling before implementation. Operational
  execution of already-reviewed code (a run task after an accepted build-to-run
  barrier, a bounded live continuation slice, a `--resume-scope` invocation, or an
  end-to-end pilot run or rerun on an accepted build commit) gets an operator or
  controller self-check that `HEAD` is at or descendant of the accepted build commit
  with no unreviewed runner/reader edits, the command, slice/resume arguments and
  input hashes match the plan, ruling or pilot check, and the exit status and output
  satisfy the task's `Expected:` contract (and Processes' smallest-run gate and
  verdict check where applicable); never spawn a pre-invocation, scope, pilot-invariance
  or pilot-qualification reviewer for that run, while whether an end-to-end pilot
  must run or rerun stays governed by Processes, Tests and project requirements (if a
  run task commits a final human-facing report the plan explicitly marks as a
  reviewed deliverable, dispatch at most one task review at the end of the run task
  for that deliverable). Bookkeeping, custody and task-record maintenance (task notes,
  `retained:` declarations, container manifests, checkpoints, transfers, ledger
  appends and workspace cleanup) get the acting owner's self-check and never an
  independent reviewer or assessment subagent. Across the life of any numbered plan
  task, dispatch at most six independent reviews in total (one initial task review
  plus up to five scoped corrective re-reviews), batching all open Critical and
  Important findings and confirmed spec gaps from a review into one fix pass and one
  scoped re-review per round, and never dispatch a re-review for a round that changed
  only ledger lines or task notes. Splitting a plan task into internal sub-stages or
  reopening a build task after a downstream operational run exposes a defect
  continues that plan task's cumulative review count and monotonic `review: impl
  round <R>` sequence (`R = 1..6`) without resetting the counter. When a plan task's
  fifth corrective re-review (sixth independent review) still reports a spec gap or an
  unresolved Critical or Important finding, or when a reopened build task has already
  spent all six reviews and needs a code fix, do not rule past the cap, split a new
  sub-stage or start another review round: stop under the turn-pause rule above,
  name the plan task, the six reviews spent, the open findings (with report paths) or
  reason a seventh review would be needed, and one recommended decision in the pause
  report, and park the task `--waiting-on user --reason decision`. This outranks
  subagent-driven-development's "Never skip the task review", "Every round ends with
  a scoped re-review", "Rulings, not stalls" and `references/fix-loop.md`'s breaker
  continuation past the cap.
<!-- rule:3a86283b2dfe4f4daf96bf612fcca2af end -->
<!-- rule:d21e7a02223e4d00adbb602627e441a6 begin -->
- After a final whole-branch review, in subagent-driven and inline (executing-plans)
  execution alike, fix (or rule on, as the skills allow) its Critical and Important
  findings in corrective rounds, up to five, under the same one-fix-pass,
  one-scoped-re-review and saved-evidence discipline as per-task reviews above; if
  the fifth corrective round still leaves any Critical or Important finding
  unresolved, surface what remains by stopping and parking for the user under the
  turn-pause rule above rather than proceeding to integration. A round is one
  fix pass plus one scoped re-review of it, and another follows while that re-review
  reports any Critical or Important finding, persisting or introduced by the fix. Minor
  findings never enter a round; they go to the ledger as `minor (deferred)`, as both
  skills say. In either execution mode, a final review's "fix before merge" call on a
  deferred minor is a re-grade proposal: the controller confirms or rejects it by its
  consequence for the person, records each decision as a ledger `Ruling:` line, and
  admits confirmed proposals to corrective rounds as Important; rejected proposals
  stay `minor (deferred)` in the ledger, named in a task note that the final message
  links, and owned by an open task before close as Processes says. A fix subagent makes the fixes
  under subagent-driven execution; inline,
  you make them yourself, each still proven RED→GREEN with policy-appropriate checks
  under Tests: a green suite when policy is enabled, focused evidence and mandatory
  hygiene when it is off. A skipped suite is never green evidence. A fresh
  reviewer runs the re-review whenever a subagent tool exists, inline too. This outranks
  executing-plans' "do not dispatch a re-review" and "no second fix pass" and
  subagent-driven-development's "exactly one scoped re-review" and "no second fix wave".
  Without a subagent tool, the re-review is a self-review, recorded as such in the
  ledger and the task note the final message links, as executing-plans'
  final-review fallback does. External
  actions stay gated.
<!-- rule:d21e7a02223e4d00adbb602627e441a6 end -->
<!-- rule:e5201d5768794401bf9d88a39b1ee445 begin -->
- A review correction to a task already closed as `done`, before its branch is
  integrated, reopens that record: the agent that makes the fix (the fix subagent, or
  you inline) runs `tasks edit <id> --status todo`, then `tasks start <id>`, since a
  bare `start` refuses a done record. A task still open, parked or not, needs only
  `tasks start <id>`. The fix owner releases it with `tasks done` or `tasks park`
  before reporting. Such a correction stays a review finding; a `concerns:` task is
  filed only for work that fell short after its branch landed.
<!-- rule:e5201d5768794401bf9d88a39b1ee445 end -->
<!-- rule:4411cf3f68ce4834a40a5379234ddc3b begin -->
- A custody check belongs to one acting owner for a given input revision and purpose;
  separate review seats still perform their own independent reviews. The author or
  controller freezes a spec or plan revision once and keeps it unchanged while review
  is open; the receiving reviewer verifies and reads the dispatched revision; the
  implementer runs changed-behavior tests under Tests and reports the command, tested
  revision, results/counts and limits for the controller to pass to the reviewer; the
  reviewer persists its report under the designated-report rule above; the controller
  advances the plan ledger once per transition; and the current item or claim owner on
  that host observes retained items at park, done or disposal, reporting its checkpoint
  basis before releasing its claim. When a child's report binds the relevant input
  revision (commit and path, or path and sha256) and scope, is complete, and has no
  conflicting evidence, the controller relies on that result for the same revision and
  purpose without rehashing the unchanged input or rerunning the child's checks merely
  at handoff. Do not compute routine report sha256 digests or write report hashes to
  the ledger; use the report path and reviewed revision, while a report that is itself
  a frozen review input, independent retained evidence or a published attachment still
  obeys that distinct contract at its required boundary. When a review accepts with a
  substantive concern or actionable finding, the controller reads the concern and
  records its disposition or ruling; a short verdict never hides an actionable concern.
  Missing inputs, an unbound verdict, an observed mismatch, changed bytes (such as
  evidence for revision A when the input is now revision B), a failed persistence
  operation or contradictory evidence require a targeted check or return to the
  responsible actor; never infer success from silence, a passing attach exit status
  alone, a notification or an omitted failure, and keep an in-flight child under
  tracked waiting. Checks whose purpose requires a new observation stay fresh when
  their event occurs: receiving a frozen revision, recovering after context loss,
  current retained-item inventory at park/done/disposal, claim transfer, host-pointer
  inspection before removal, and branch freshness before final review or base-relative
  measurement. A previous hash never proves mutable bytes stayed unchanged, and at
  park, done or disposal the acting owner inspects the complete known local retained
  set; if an explicitly delegated check supplies evidence, the recording actor names
  the observer and never describes another actor's observation as its own recheck.
<!-- rule:4411cf3f68ce4834a40a5379234ddc3b end -->
<!-- rule:6c0a22eb29eb4e1db82c7e7e9fc6ae27 begin -->
- In planned execution, the controller reads the plan and binding constraints once at
  setup, keeps the plan ledger as the recovery map (current task and phase, completed
  ranges, pending review or corrective round, findings, rulings, deferred minors and
  next action), and dispatches narrow task briefs with applicable constraints and
  needed interfaces. Keep full review reports and clean supporting logs in files so
  only concise handoffs and the finding sections needed for decisions or rulings enter
  controller context. After compaction while enforced `hq pause limits` remain
  uncrossed, check `hq pause status` (maintaining the enforced counts where no pause
  hook runs) and recover inside the current turn budget by reading the current task,
  the plan's ledger and the referenced sections needed for the next decision, and
  verifying the named current Git state; reconcile any conflict between ledger, task
  records and Git state before dispatch, and never replay completed task sequences,
  respawn completed workers, reload every prior report, or ask permission to recover.
  Compaction alone never triggers a pause; when an enforced limit crosses `hq pause
  limits`, stop under the turn-pause rule above and, when compaction or context
  growth is the binding cause, recommend a user-chosen fresh controller in the pause
  decision. During the permitted pause report and park, record
  the durable handoff in the task record and its existing ledger/report references:
  actual status, task/plan/spec identities and frozen revisions, branch/worktree,
  current HEAD/base and next action with its owner; completed task ranges, current
  review round, findings, rulings, deferred minors, and evidence locations and
  revision-bound verdicts with limits (preserving full reports); claims, running
  processes with stop/pickup commands, host pointers, and retained items/checkpoint
  basis, stating which accounting was not refreshed at the limit instead of starting
  fresh inventory or cleanup work; and observed spend/counts (keeping unknown counters
  unknown), limit reached, remaining estimate and the user's outstanding decision.
  Never auto-launch a replacement controller, start another session, continue work
  merely to finish a handoff, or reset budgets; a user who continues the current
  controller receives the same normal checks. A receiving controller reads the handoff
  and task before claiming work, verifies current claim, process and Git state and the
  evidence it needs before reuse, refreshes stale or unrefreshed accounting first,
  reconciles any state change, and resumes the first unfinished action without
  treating old reports as fresh filesystem observations or rerunning completed reviews
  merely because the controller changed.
<!-- rule:6c0a22eb29eb4e1db82c7e7e9fc6ae27 end -->
