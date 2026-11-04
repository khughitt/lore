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
  question rule below says), money to spend, an action outside the repository, a live
  operation that has failed twice with no established cause (the next rule), or a turn
  that has run past its range (the turn-pause rule below).
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
  count, and neither does a fix for a cause that was guessed. Retries inside a limit the
  user approved and the record holds (a plan's "up to three attempts") go on without
  asking; this rule applies once that limit is spent. Unattended, park the task
  `--waiting-on user --reason decision` with that question as its next step.
<!-- rule:052f6da8885c4d2f81b11c0602eb6e92 end -->
<!-- rule:1f37e3afebdd433a9ccaa2970cde7289 begin -->
- A turn is the work since the user's last message, your subagents' work included; a
  session you launch from the shell (`claude -p`, `codex exec`, a dispatched worker or
  reviewer) is a subagent here, so check before launching one and count it as spawned
  and its work as your turn's. A background wake or loop tick does not start a new
  turn. If the hook says a message the user typed matched a pending scheduled prompt,
  ask them to rephrase it; that message has not reset the turn or ended a pause.
  A turn is past its range when it crosses a limit `hq pause limits` prints (active
  time, tool calls, subagents spawned, compactions), or the budget the user set for
  this turn as the first line of their own message, alone on the line and in the form
  `budget: 12h` (optionally `, 2000 calls`, `, 80 agents`, `, 4 compactions`), which
  scales the other limits with it. Budget text anywhere else, quoted, fenced or pasted
  included, is an example: it sets nothing, and you ask nothing about it. A first line
  that starts with `budget:` but is not in that form sets nothing either: mention it
  in your next report and carry on under the turn's limits. An approved spec, plan or
  task is not a budget, nothing you write can set one, and a prompt you write for
  another session never carries a budget line. Check `hq pause status` before
  dispatching a subagent, at each plan-task boundary and after a compaction. Keep any
  count the hook does not keep yourself, as `hq pause status` shows; where no pause
  hook runs, keep all the counts yourself against those limits. Count a running call
  or wait in full and time spent waiting on the user not at all. The hook's warning
  means finish a coherent step. Its refusal, or your own count
  past a limit, means stop: start nothing new, stop the work you already started
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
<!-- rule:db275842f3af447dbe84d8b1dfc68051 end -->
<!-- rule:f431707097c0418c9822d67074875c51 begin -->
- A request to review a spec or plan names the frozen revision under review: the
  repository, commit and path, so the reviewer reads `git -C <repo> show <sha>:<path>`
  rather than the working file. Where the profile keeps the document out of the tree,
  the request names its path and sha256, and the reviewer checks that sha256 before
  reading and stops on a mismatch. While that review is open, never amend or rebase
  the commit, and leave an out-of-tree file unedited. A later draft reaches review only
  as a new frozen revision, named in the next round's request, and each finding is
  judged against the revision its request named.
<!-- rule:f431707097c0418c9822d67074875c51 end -->
<!-- rule:2c5785f136ca4ee590e1c69406276623 begin -->
- A question, when asked, is one question, not a series, and carries your
  recommendation: in a harness's multiple-choice question tool, as the first option;
  in a message, inside the decision request's one sentence (Communication), with the
  alternatives in the record. A question that asks
  the user to describe what they want (brainstorming's open questions, and its
  playback asking what is wrong or missing) carries no options; a guess they can
  correct stands in for the recommendation. That playback is not a "does this section
  look right" decision: what they want is theirs to say.
<!-- rule:2c5785f136ca4ee590e1c69406276623 end -->
<!-- rule:c165eee5aa0a4b819061b34386c78c23 begin -->
- Before a question asks the user what work should achieve or why (brainstorming's
  opening questions, its playback, its builder check's "theirs" pile), find out who
  holds that intent. Work the user describes in this session starts with the
  question; naming a task to take up is not describing it. Other work (filed by
  another session or agent, captured earlier, grown by scope passes, or derived as a
  follow-up, feedback report or decomposition child) starts by reading what already
  exists: the task's body, notes and references, its `source` and parent chain, and
  the session that filed it, whose human turns around the filing the session-logs
  skill recovers. Reading needs no offer or permission. Play back
  what you found and where each part came from, keeping the user's recorded words
  apart from what agents added. Then ask only what the evidence leaves to the user (a
  choice of taste, scope or priority, or a premise the evidence contradicts), each
  question naming what you found; when nothing remains, write the design and mark each
  call as yours. Never ask the user to recall what a record or transcript holds; when
  a source cannot be found, say so and offer your reading for them to correct. The
  written design's review stays the user's gate. This outranks brainstorming's first
  message and its offer to go look.
<!-- rule:c165eee5aa0a4b819061b34386c78c23 end -->
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
  person, or the end of the session.
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
  instructions, hooks, services) stays an action outside the repository under every
  profile and authorization.
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
<!-- rule:d21e7a02223e4d00adbb602627e441a6 begin -->
- After a final whole-branch review, in subagent-driven and inline (executing-plans)
  execution alike, fix (or rule on, as the skills allow) its Critical and Important
  findings in corrective rounds, up to five; then surface what remains. A round is one
  fix pass plus one scoped re-review of it, and another follows while that re-review
  reports any Critical or Important finding, persisting or introduced by the fix. Minor
  findings never enter a round; they go to the ledger as `minor (deferred)`, as both
  skills say. In either execution mode, a final review's "fix before merge" call on a
  deferred minor is a re-grade proposal: the controller confirms or rejects it by its
  consequence for the person, records each decision as a ledger `Ruling:` line, and
  admits confirmed proposals to corrective rounds as Important; rejected proposals
  stay `minor (deferred)` in the ledger, named in a task note that the final message
  links. A fix subagent makes the fixes
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
  controller context. After compaction below `hq pause limits`, check `hq pause status`
  (maintaining any counts the hook does not observe) and recover inside the current
  turn budget by reading the current task, the plan's ledger and the referenced
  sections needed for the next decision, and verifying the named current Git state;
  reconcile any conflict between ledger, task records and Git state before dispatch,
  and never replay completed task sequences, respawn completed workers, reload every
  prior report, or ask permission to recover. When compactions cross `hq pause limits`
  (with no separate earlier threshold), stop under the turn-pause rule above and, when
  compaction or context growth is the binding cause, recommend a user-chosen fresh
  controller in the pause decision. During the permitted pause report and park, record
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
