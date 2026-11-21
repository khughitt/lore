# Supported workflow and safeguards

Read the entire reference for supported work and enrolled flow-trial units that
retain their rules. At other stages, read the applicable safeguard section when
the scoped action calls for it.

## Safeguards for specific actions

### Writes to irreplaceable persistent data

Use this safeguard for a change that can alter stored bytes, including a
writer, read-modify-write path, migration or format change. Back up the data
before the changed writer touches real data. Prove a round trip on
representative data. If two hosts share the format, confirm that both
installed versions can read the new representation before the first live
write. A display-only read or read-only report follows the project's stage.

### Activation of a live global surface

For a change to installed shared instructions, hooks, services or binaries that
agent sessions use, keep the earlier installed version or artifact and record
the rollback command. Obtain live-change approval where today's rules require it.
Ask before a use of the live desktop when the core requires it. After activation,
smoke-test what is actually installed. Candidate development follows the stage.

### External publication

Keep the existing approval and review the exact material going out. Ordinary
development branch pushes for hosted CI keep their existing push authorization
and remote checks. Apply the publication safeguard when publishing externally.

## Supported rules

### Spec and plan review

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

- In plan writing and execution, inline or subagent-driven, the frozen spec is the
  authority for normative formulas, schemas and interface definitions. When a plan
  needs to repeat one, quote it verbatim with its spec clause reference; avoid copying
  the whole spec. The plan author's self-review compares every repeated definition,
  including those in task steps, tests and Interfaces blocks, against that clause.
  The controller's preflight compares those definitions against the applicable
  binding spec clauses, and each implementer handoff includes its applicable clauses
  and the frozen spec and plan identities. Implementers surface any mismatch; the
  controller resolves it through an explicit recorded `Ruling:` with the spec as
  authority, never by silently adding aliases, extra columns or a second interface.
  A material spec or plan change keeps the existing human amendment-review gate
  before dependent work resumes. The existing final whole-branch reviewer receives
  both frozen spec and plan identities and checks the implemented normative clauses
  directly against the spec and its accepted amendments and recorded rulings. This
  supplements the existing review; it adds no reviewer or dispatch.

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

### Implementation review and controller duties

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

### Retained items and plan workspaces

- At park and before `tasks done`, inspect and account on the task for the complete
  retained set on the current host: worktrees, task scratch and off-tree evidence.
  Read `~/.agents/skills/references/retained-item-records.md` when creating,
  refreshing or releasing records; follow its changed-item and exact host-checkpoint
  procedure. For a changing plan workspace or task scratch/evidence directory, content
  additions or edits (reports, ledger appends, ordinary handoffs) do not trigger a
  complete manifest or checkpoint per edit: generate complete manifests and checkpoints
  at real `park`, `done` or disposal boundaries, while recording immediate creation
  notes and changes of owner, purpose, disposition or uncertainty when they occur and
  keeping frozen-input, replacement-preservation, attachment, recovery and integrity
  checks at their own boundaries. A child task's `done` accounts for the child's own
  retained set and does not automatically checkpoint a container that remains owned by
  an open parent; ownership must be real and recorded, never transferred to avoid a
  checkpoint. Between checkpoints an earlier checkpoint on a mutating container is
  historical, not current proof; at `park`, `done` or disposal the acting owner
  inspects the complete known local retained set (naming the observer when an
  explicitly delegated check supplied evidence, never calling another actor's
  observation its own recheck). Accounting does not require restating unchanged
  inventories. Keep uncertainty explicit and refresh resource/wait descriptions from
  observations. An open task owns items across activation review; only a closing
  session disposing of them in the same turn may temporarily own integration. Anything
  kept longer needs an open follow-up or agreed user handoff. A trigger, merge or done
  grants no deletion permission; preserve unfinished work and the only needed raw copy.
  For layout refusal, keep hashed raw bytes and attach a labelled portable derivative
  under the reference's fallback until the executing checker accepts shipped support;
  design completion alone never retires that fallback or authorizes raw deletion.

- New plan executions keep their workspace at
  `$WORK_ROOT/<project>/<owning-task-id>/plans/<plan-key>/`, owned by the open
  controller task. Follow the retained-item reference's execution-workspace section
  for creation, explicit-path helpers, resume, review packages and cleanup; it
  overrides the execution skills' worktree-local workspace instructions. Children
  cite the parent's workspace without duplicating its identity. Keep existing
  workspaces in place until a separately reviewed migration; unavailable declared
  storage fails visibly, with no guessed worktree or tmpfs fallback.
