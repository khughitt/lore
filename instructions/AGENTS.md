## Core Development Rules

- Composition > Inheritance
- Explicit > Defensive
- Fail early / avoid silent fallbacks

## Refactoring

- DO NOT create "legacy" / "compatibility" layers unless specifically asked
- DO NOT add a "Unified" prefix to component names

## Git

- Use conventional commits.
- No AI attribution by default: no attribution trailer, co-author line, or footer on commits, PRs, or comments, and harness-injected forms (`Claude-Session:`, a session URL, "Generated with Claude Code") stay out everywhere. The profile says which `gh` account a checkout uses and what a repository you do not maintain requires before a PR; `gh` holds two accounts and the active one is global state, so check `gh auth status` before any `gh` write.
- Before changing repository code — for any task, direct or planned, not only a brainstorming + planning session — work in a worktree under `.worktrees/`, unless explicitly instructed to work in place. Reuse the task's existing worktree when resuming; otherwise create one with `git worktree add`, not a native worktree tool. `EnterWorktree` and its equivalents place worktrees under `.claude/worktrees/`, which only one harness reads; `.worktrees/` works for all of them. Planned work creates it before drafting the spec. Right after `git worktree add`, hydrate the new worktree from the first source the project declares: `just setup` when its justfile defines it (it installs dependencies and hydrates gitignored inputs); else the setup command its root guide names, or one its README or CONTRIBUTING names that writes only inside the worktree; else the frozen install of a lockfile that names its package manager and installs inside the worktree (`package-lock.json`: `npm ci`; `uv.lock`: `uv sync --frozen`). A command the root guide, README or CONTRIBUTING names may have its default build or install destinations pointed inside the worktree by its own documented settings or flags (`cargo install --locked --path .` with `--root` and `CARGO_TARGET_DIR` under the worktree), and must have them when it would otherwise replace a tool on the host's `PATH`; a shared download cache is not an environment and may stay where it is. That confinement is not guessing an installer and needs no approval, as long as the confined run neither swaps the package manager nor writes a shared environment. A confined README or CONTRIBUTING command writes only inside the worktree; a README or CONTRIBUTING command that no documented setting confines, or any named command that would still replace a tool on the host's `PATH`, is a missing setup route. A bare manifest (`pyproject.toml`, `package.json` or `requirements.txt` without a lockfile), or a lockfile whose install can leave the worktree (Poetry's default cache environment), declares no usable installer and is also a missing setup route: never guess one, as the worktree skill's Step 2 would. Report each missing setup route before the first commit as a task note naming the command, manifest or lockfile and why it gives no usable route, and name that note in a few words in the next message to the user (a worker, in its report; work with no task record carries the report in that message); the report informs, asks no approval, and the work continues. Hydrate before that commit: an unhydrated tree's hooks can stop at an `npx` install prompt or run unpinned tools. A checkout that declares no dependencies needs no setup, and a worktree checked out only to be read (for example a historical snapshot under review, in which nothing is committed, tested or run) needs neither hydration nor the baseline below until something is to run or be committed in it, when both come first. A suite that fails in a new worktree before setup is an unhydrated tree, not a bug. Planned work, whose worktree precedes its spec, defers the worktree skill's baseline tests (its Step 3) there: no code changes before the plan runs, and execution's Setup re-enters that skill and runs them before the first code change. Direct work runs them at creation. For a validated policy-off checkout under the Tests rule, direct worktree creation and planned execution Setup keep hydration but run the relevant focused baseline when code work begins; record its scope and the deliberate omission of the broad baseline. Documentation-only work invents no focused test obligation. Otherwise the baseline runs the project's full-suite route (`just test` where the justfile defines it, otherwise the full-suite command its guide documents, where a single documented test command or the package test script it points to counts); its fast recipe serves only where the project states that the recipe runs that same suite with no change selection. Note the command and the number of tests it ran on the task: a run that selects no tests is not a passing baseline. A project that declares no full-suite route is noted on the task as the Tests rule says, never given a guessed runner. On every host running dotfiles, a checkout under `~/d` keeps `.worktrees/` as a relative symlink into that host's storage, created by `just setup` or `work-link --ensure .worktrees`, which also keeps git's worktree admin directory out of Dropbox; run it before every `git worktree add` (a `File exists` error on `.worktrees`, `.venv` or `target` means a link arrived before its storage did: run `work-link` once) (a checkout elsewhere, such as a clone under a temp dir, keeps `.worktrees/` in-tree: `--ensure` reports `outside` and does nothing); lock the new worktree right after creating it (`git worktree lock --reason "on WORK_ROOT storage (host: $(uname -n))" .worktrees/<name>`), and remove one with `git worktree unlock <path>` then `git worktree remove <path>`. Read-only investigation and task-record maintenance alone need no worktree.
- A live test of a worktree's code runs it by explicit path (`.worktrees/<name>/bin/<tool>`) or an environment override, never by repointing a shared launcher, symlink, service unit, or config include on the host at the worktree. When a host pointer must be repointed, record it in a task note at that moment (what, from, to, how to restore) and restore it before `tasks park` or `tasks done`; while it stands, the park note names it. Before removing a worktree, check that no host pointer resolves into it (`readlink -f` over `~/bin/*`, `~/.local/bin/*`, user systemd units, known config includes) and refuse while one does. A rollout that hands live state to another project's tool checks where that tool resolves on `PATH` first, rather than assuming the main checkout.
- A test, fixture or scratch script that runs git keeps it off the host's real config
  and repositories. Overriding `HOME` alone is not enough: with `XDG_CONFIG_HOME`
  still exported and no `~/.gitconfig` in the new `HOME`, `git config --global` writes
  to an existing `$XDG_CONFIG_HOME/git/config`, the user's real one. Set
  `GIT_CONFIG_GLOBAL` to a temporary file (or `/dev/null`, with `GIT_AUTHOR_*` and
  `GIT_COMMITTER_*` set) plus `GIT_CONFIG_NOSYSTEM=1`, or override `XDG_CONFIG_HOME`
  along with `HOME`, and prefer `git -c key=value` to `git config --global`. A git
  hook can export `GIT_DIR`, `GIT_INDEX_FILE` and `GIT_WORK_TREE`, which win over
  `git -C <dir>`: unset every inherited `GIT_*` variable before building a fixture,
  and before its first write assert both that `git rev-parse --show-toplevel` is the
  fixture directory and that `git rev-parse --absolute-git-dir` lies inside it (with
  only `GIT_DIR` set, the top level reads as the current directory while writes still
  reach the real repository).
- Plain `git worktree remove` deletes ignored files without `--force`. Before any
  removal, list them (`git -C <path> status --ignored --porcelain`) and give each entry
  a disposition rather than archiving the lot. Discard what is regenerable (caches,
  build output, installed dependencies, config `just setup` hydrates) or already kept
  elsewhere (committed on a branch, attached to a task). Attach each small file still
  needed (a review screenshot, a report, a log) to the task it serves, one
  `tasks attach <id> <file> --caption "<what it shows>"` per file. Move the rare needed
  item too large to commit with a task record to that task's
  `$WORK_ROOT/<project>/<task-id>/` and record it under Processes' retained-item
  rule. If the layout gate refuses a small attachment, use that rule's raw/portable
  fallback. Inspect worktree-local plan workspaces (`ls <path>/.superpowers/sdd/`)
  and follow every recorded external workspace mapping. Removing the code worktree
  leaves external workspaces with their recorded open owner; verify their ledgers
  remain discoverable from that task. Each plan workspace goes only after its ledger's `Ruling:` and
  `minor (deferred)` lines have reached the task record (a note or an attached
  ledger), other plans' included;
  otherwise attach its ledger, or move and note it as above, on the task its plan
  served, so the ledger is found from that task's record alone. Remove the tree only
  after `tasks show` lists each attachment and each moved copy's sha256 matches.
- `git worktree remove` refuses a worktree that holds a submodule, even a clean one.
  Force it (`git worktree unlock <path>`, then `git worktree remove --force <path>`)
  only when every check holds, and stop to resolve the first that fails: it is the
  task's own worktree; its branch is merged or kept; `git -C <path> status --porcelain`
  and `git -C <path> submodule foreach --recursive git status --porcelain` print
  nothing; `git -C <path> submodule status --recursive` shows no `+`, `-` or `U` prefix;
  the ignored-file check above holds; `tt-report` has run; no host pointer resolves
  into it. Never force by default.
- When working inside a worktree, write every path you show me relative to the main checkout, not the worktree root — prefix it with the worktree's own directory (e.g. `.worktrees/<name>/…`). I am standing in the main checkout, where a worktree-relative path does not resolve. Inside a worktree the real path is in the host's storage (git and `pwd -P` show it); still write `.worktrees/<name>/…`, by convention, not by reading the cwd.
- Avoid machine-specific absolute paths (the home directory, the Dropbox root) in code comments and docs

## Profiles

Every checkout has a profile — `personal`, `work`, `external`, or one the user
defined — that carries the instructions and settings that differ between
kinds of project. Your session starts with a `profile:` line followed by the
profile's instructions; if it did not, run `ops-profile session` and read
its output before any other work — the profile says what to read and do
before touching a repository. Later layers win: core, then the profile, then
this repository's own instructions, then the user in the session.

## Design & Plan Docs

- Where design specs, plans, briefs and handoffs go, and whether they are committed, is the profile's call: the session line's `design docs:` clause names the value or the directory, and the profile's text says the rest. The repository's own instructions override it, and the hook that guards staging names both.
- A code repository's `docs/` holds reference documents: each describes current behaviour, is named for its subject rather than dated, and is updated by the change that alters that behaviour. A design spec is a decision record, not a reference document; it becomes one only by being rewritten as one, never by being left in place. Which specs a repository rewrites is filed by that project as its own task when it next changes the subsystem they describe, never done as a side task of other work.
- Verify document status against the code before relying on it; update it and related docs when work lands.

- For tracked tasks, file cited documents as explicit task references and declare
  expected outputs, following the tasks skill. On pickup, read the inventory's
  required entries in their listed order before starting. The task's spec and plan
  fields name its governing documents; ordinary references do not acquire those
  workflow roles, and source remains provenance rather than a reading obligation.
  A reference locates current content; reviews and evidence still pin exact revisions.

## Communication

- If the user suddenly switches the conversation to a different project, confirm that it was intentional.
- A message to the user at a turn end or a decision point (a final report, a progress
  update, a decision or approval request, a relayed review) includes what changes the
  user's understanding, decision or next action, and links the supporting record. Lead
  with the direct answer to the user's question, the decision or action needed from the
  user (with any approval trigger), or the outcome when no user action is needed. By
  default the message is one to five short statements or fragments covering that lead,
  the task's actual state (done, stopped, still running, or blocked and on what), who
  acts next, and any uncertainty, trade-off or limitation that could change the user's
  answer. When the user asks what they need to do, list the user's own actions first,
  separated from remaining agent work; starting more work or narrating agent steps does
  not answer the question. The count is a default, not a cap: a line that changes a
  decision stays, and a paragraph packed into a bullet is not one statement. Prefer
  plain sentences and fragments to word compression, and in a multi-item status list
  put each item on its own line with a bold status or verdict and a short reason. The
  message stands alone, without restating earlier progress updates or a harness recap.
  This covers a skill's templated output to the user (brainstorming's playback chunks,
  executing-plans' review relays) and outranks the length the skill states. Reviewers'
  full reports to controllers and explanations the user asks for keep their full
  length.
- Write task ids in replies and reports bare in their canonical form
  (`<prefix>-<6 hex>`), outside backticks and links, so a harness can colour them;
  an id inside a command shown as code stays in that command.
- Supporting detail leaves the message for the task record: findings and landed
  changes with their conditions and scope, verification and its limits (routine
  passing checks, results, test counts), routine cleanup and non-actions ("nothing
  pushed", "no paid calls", "worktree cleaned up"), raw audit identifiers (full
  commit or file hashes, `rule:` UUIDs, retention flags) unless the user must run a
  command containing them, deviations and their rulings, rejected options, and
  unfinished work with where it is tracked. Put it in a task note, the plan ledger,
  an attachment or a linked report before writing the message, check that the
  destination holds it and opens from the main checkout, and name it in the message
  in a few words. A decision or approval request is one or two short sentences
  stating what is asked or blocked on, the recommended option, and one clause of
  reason, linking the record or change summary that holds the exact frozen revision
  and rejected alternatives (for example: "Approve activating the revised review
  policy? I recommend it because it removes redundant reviews. [Change summary](…).");
  for an amendment, state the change and its consequences, with the full document
  linked. Work with no task record (a read-only answer, an ad hoc fix) keeps in the
  message what these or any other rules send to the task record, after what the user
  needs first; the note lines under Task notes for outcome measures need a task and
  are skipped without one. Before shortening, check that no condition, reason or
  limit that could change the user's answer is lost and no claim becomes stronger.
- Required content is kept whole in the record, not the message: every required
  ruling (its own entry with the decision, labelled `Why:` (reason) and `Cost:` (if
  wrong), and revision references; say when a reason or cost was not recorded rather
  than inventing one), deferred minors, and the closing disclosures (pushes, this
  session's surviving processes, others' work, worktree state, and each branch left
  unmerged with its location and what integrates it: who approves, which command).
  Rulings and deferred minors stay in the plan ledger, with one task note naming them;
  verification, deviations and disclosures (including routine non-actions such as
  "nothing pushed", no surviving process, a merged branch or a cleaned-up worktree)
  go in the done or park note. What the user must act on stays in the message: the
  approval or decision asked for and a link to the text or change summary they must
  read to give it (with its frozen revision — repository, commit and path, or path
  and sha256 — preserved in that linked record), a surviving process with its pid and
  stop command, an error only they can resolve, and each branch left unmerged, with
  its location and who integrates it. "Nothing was pushed" does not establish
  integration state; name an unmerged branch in the message and record a merged one
  in the note. Task notes are not shortened by these rules.
- Use no emoji in what you write: replies, reports, and task text (titles, bodies,
  notes). Their fixed colours cannot follow a project's identity colour. Content a
  project itself asks for, and other Unicode such as arrows or box drawing, is not
  covered.
- A path you show the user is one they can open from where they stand, the main
  checkout: relative to it when the file lives there, absolute otherwise. Never write
  it relative to a directory only you know, such as the scratchpad (`scratchpad/x.md`
  resolves nowhere for the user). The Git rule against machine-specific absolute paths
  covers committed text, not what you tell the user.
- A sheet of images you hand the user to judge (an image grid, a contact sheet, a
  before/after pair, a parameter sweep) explains itself without its generator: a title
  stating the question; rows and columns labelled in plain language, with units where
  the axis has them; the baseline or control marked when there is one; one line on what
  to look for; and a short, stable id on each cell so a pick can be named back. Do not
  invent axes, units or a control the comparison lacks: unrelated candidates are a
  numbered set, not a grid. Before handing a sheet over, view the rendered image at the
  scale the user will see it and confirm the labels are legible.

## Notation

The user writes prompts, thoughts and task text in a shorthand (catalogued in mindful's
`#mindful-syntax` thought; vocabulary confirmed in mind6's capture-syntax brief). Read
it this way:

- `~word` (no space): approximately, "something like word".
- `a ~ b` has two readings: `y ~ x` as in a model formula (y is a function of,
  distributed as, or proportional to x), or association (a is similar to, associated
  with b). Read it only where the context makes one clear.
- `a -> b` is either a sequence (a, then b) or causation (a causes b); when the
  difference matters, say which you read. A `?` after a relation (`a -> b?`) makes the
  relation uncertain. Older text writes that as `a ~> b`, now retired.
- `a x b`: a combination of, or an interaction between, a and b.
- `a|b` and `(a|b|…)`: alternatives.
- A trailing `?` marks a question or an idea; `#tag?` is a possible tag, not a
  confirmed one.
- `(?)` after a claim, plan or label: tentative, maybe. Never treat it as established.
- `- [ ]` is an open action and `- [x]` a done one; `? []` is an open question.
- A line label says what the line is: `context:`, `insp:` (inspiration),
  `motivation:`, `question:`, `intuition:`, `basic idea:`, `basic approach:`,
  `challenge:`, `limitation:`, `side:` (an aside).
- When a reading is ambiguous and matters for the work, state the reading you took.

## Decisions

- When you hold a recommendation for a bounded decision, state it with one clause of
  reason and act on it; the alternative you rejected goes to the task record, as
  Communication sends rejected options (without a record, after the recommendation in the
  message), while a trade-off that could change the user's answer stays in the message.
  Do not end the turn to ask for confirmation: the user
  overrides in free text if they disagree, and a wrong default costs one correction
  while a question costs a stop. This applies to "which approach", "where should this
  land", "does this section look right", "which follow-ups to file", and "execute now".
- Stop and ask only when the answer needs the user: an artifact they must inspect and
  judge (a sheet, a screenshot, a rendered page), a choice of taste, scope, or priority
  that is the user's to make (your recommendation informs it but cannot settle it, and
  the question carries your recommendation, or the guess that stands in for one, as the
  question rule below says), money to spend, an action outside the repository, a live
  operation that has failed twice with no established cause (the next rule), or a turn
  that has run past its range (the turn-pause rule below).
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
- Two written artifacts keep their gate: a design spec and an implementation plan are
  reviewed before the next phase starts. Within writing them, sections are not
  individually approved.
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
  is insufficient. Ordinary interactive use under the current harness arrangement
  and local no-charge analysis create no experiment-accounting obligation merely
  because the assistant uses a model. A tool that launches a metered experimental
  run remains within this rule.
- In assessments and reviews, distinguish tree-verified current capability from
  recorded intended direction. Before characterising intended scope, read the relevant
  goals, authority and task/source records. Code establishes current behaviour, not
  eventual scope: preserve the recorded goal and any limit's provisional meaning
  beside what works today. When intent is missing or records conflict, state what is
  unknown and which evidence is missing or conflicting; neither invent intent nor
  replace it with implemented behaviour. A proposed change to intended scope remains
  a human decision.
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
- A skill's scripted question or stop (an integration menu, a "surface residual
  findings" step) is a bounded decision under this rule unless it falls in the stop
  list above; this rule outranks the skill's "exactly as written".
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
- A review correction to a task already closed as `done`, before its branch is
  integrated, reopens that record: the agent that makes the fix (the fix subagent, or
  you inline) runs `tasks edit <id> --status todo`, then `tasks start <id>`, since a
  bare `start` refuses a done record. A task still open, parked or not, needs only
  `tasks start <id>`. The fix owner releases it with `tasks done` or `tasks park`
  before reporting. Such a correction stays a review finding; a `concerns:` task is
  filed only for work that fell short after its branch landed.
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

## Processes

- A smoke or live-run script an agent launches detached (`setsid nohup … & disown`, a
  background `bun`, `node` or `weston`, a tmux server) owns its cleanup: it records the
  pids it spawns and reaps them on its own exit and on the harness's stop (a `trap` on
  EXIT, TERM and INT, or killing the tmux session), so a closed terminal never leaves a
  child burning CPU in a dead `kitty-*.scope`. A process that must outlive the turn (a
  server a later step drives) is named in the end-of-turn report with its pid and how to
  stop it; before that report, `host-load --section session` (ops's `bin/host-load`, on
  `~/.local/bin`) lists what this session's scope left running; the done or park note
  records that result, and the report repeats only a process that survives. `host-load` also names the load a preflight refuses on
  and sweeps orphans across sessions; its `--kill` is the user's decision, not yours.
- A launcher that leaves a process running behind a tracked channel (the harness's
  shell tool, `ssh host cmd`, a hook) redirects all three of that process's standard
  streams (`</dev/null >log 2>&1`): a child that inherits stdout or stderr holds the
  call open after the launcher returns, and `&`, `nohup` and `setsid` close nothing.
- A process meant to outlive the session needs the user's approval at that moment (a
  persistent service is a host change), then starts as a transient user service:
  `systemd-run --user --unit=<name> --service-type=exec --working-directory=<dir>
  [-E VAR=value] <cmd>`, once `systemctl --user` answers and, for a launch over ssh,
  lingering is on (`loginctl show-user <user> -p Linger`; enabling it is the user's
  decision). When a check fails, report which one and launch nothing; `setsid` and
  `nohup` are no fallback. Its return means started, not ready, so a bounded readiness
  check (its port, a health command) follows, and the report names the unit,
  `journalctl --user -u <name>` and `systemctl --user stop <name>`. Neither `setsid`,
  which leaves the process in the terminal's scope, nor `systemd-run --scope`, which
  runs it as systemd-run's own child with the caller's environment and blocks until it
  exits, is a service launch. A server that a later step of this session drives stays
  under the cleanup bullet above.
- Never end a turn waiting on work the harness does not track. Run a long check in the
  foreground with a timeout that covers it, or through the harness's own background
  mechanism; a job detached with `&` or `nohup` never wakes you, so no turn ends waiting
  on a monitor of one. Claude Code's background Bash (`run_in_background`) is stopped at
  its `timeout`, 30 min when unset and at most 2 h: set it to cover the run. A run
  longer than 2 h is split into resumable slices (an incremental job run in bounded
  passes, each under the limit, e.g. with `timeout --signal=INT`) or handed to a tracked
  process the user agrees to. A controller with a running child ends its turn only where
  the harness is known to start its next turn when the child finishes (Claude Code: yes;
  Codex: no — probed 2026-09-24 and recorded in ops `hooks/claim-guard`'s
  `CHILD_WAKES`), and otherwise waits with the harness's bounded wait, at its longest
  (Codex: `wait_agent` with `timeout_ms: 3600000`, an empty `write_stdin` with
  `yield_time_ms: 300000`; both return as soon as the child or command finishes), never
  a loop of shorter waits. Before each such wait, post one line naming what you await,
  how long it should take and the wait's limit; when it returns, post one status line.
  This outranks a harness's own shorter guidance: Codex's base instructions' 60-second
  cap on blocking waits and on gaps between updates, and the vendored superpowers
  `codex-tools` reference's 5–10 minute stretches. A worker's turn end is its final
  report: it reports and stops only when its assignment is complete or blocked on its
  controller or a person, never with its own check still running. A child's "waiting on
  background work" is unverified until you check that the process or its output exists;
  after a wake-up, report what you observed, never a notification that did not arrive.
- Before committing to an extended run (a benchmark, capture, experiment, or sweep that
  takes more than a few minutes, and above all one that needs the user off the machine),
  first run the smallest version that exercises every gate end to end through its
  verdict, one case per check, and read the result. When a long run is refused or
  aborted partway, analyze the parts it completed before changing the environment and
  retrying; a second failure with no established cause goes to the user (Decisions).
  When asking for the machine, name the pilot and what it showed.
- A plan or runbook that verifies a rollout across hosts and profiles verifies one host
  and one profile end to end, and treats the other hosts and profiles configured by the
  same process (the same installer, links and settings source) as covered: an issue that
  shows up on one of them later is debugged then. A different harness, or a host or
  profile reached through a different configuration path, gets its own end-to-end check.
  An obligation a tool measures per host, such as a `test-latency` verify, is not a
  rollout check and stays per host.
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
- A task that spans sessions keeps its inputs where a reboot cannot take them. Its
  scratch lives in a per-task directory on persistent host-local storage off the synced
  tree, `$WORK_ROOT/<project>/<task-id>/` (on a host without `WORK_ROOT`, ask the user
  where rather than inventing a path). tmpfs (`/dev/shm`, `/tmp`, `/run`) holds only
  per-run copies made from that persistent canonical copy. Note directory creation
  immediately (host, path, purpose and current task owner; contents still mutable),
  then checkpoint under the retained-item rule above at park, done or disposal rather
  than after every content edit. A resume or post-compaction recovery checks that the
  specific canonical inputs it needs exist and match their recorded hashes before
  relying on them or claiming an idle-host window or the user's machine, without an
  unsolicited whole-container manifest.
- Work that takes the live desktop (opens windows on it, moves focus, switches
  workspaces, captures the screen) is a host-use action, and approving a plan does not
  grant it. Prefer a nested or headless compositor where the project has one; otherwise
  ask at that moment, naming what will appear and for how long, or `tasks park --reason
  quiet` the work. A retry or a later capture asks again rather than reusing an earlier
  yes.
- A dispatch that asks a subagent to write its report to a file names that file
  `<slug>-report.md` (`task-3-report.md`, `audit-report.md`), never a `.md` name
  starting with `report`, `summary`, `findings` or `analysis` in any case
  (`report.md`, `Summary-x.md`, `findings.md`). Claude Code refuses a subagent's write
  to those names ("Subagents should return findings as text"), and the whole report
  then lands in the subagent's final message instead of the file. hq's
  `subagent-write-refused` capability fact records the rule and its probe.

- New plan executions keep their workspace at
  `$WORK_ROOT/<project>/<owning-task-id>/plans/<plan-key>/`, owned by the open
  controller task. Follow the retained-item reference's execution-workspace section
  for creation, explicit-path helpers, resume, review packages and cleanup; it
  overrides the execution skills' worktree-local workspace instructions. Children
  cite the parent's workspace without duplicating its identity. Keep existing
  workspaces in place until a separately reviewed migration; unavailable declared
  storage fails visibly, with no guessed worktree or tmpfs fallback.

## Tests

- Test execution policy comes from `.tt.toml` at the invoking code checkout's Git
  top level, validated by that project's `tt` wrapper; detached records and sibling
  checkouts never supply it. One Git root means one shared policy. A missing file
  or `automatic_broad = true` retains the suite requirements below. Invalid or
  unreadable policy is an error, never an exemption. Do not infer policy-off from
  absent timing samples or a generic CI environment variable.
- With a valid `automatic_broad = false`, run fresh focused tests for the changed
  behavior and always-run hygiene. Preserve focused RED→GREEN during implementation
  and every corrective review round. Do not rerun a broad suite solely for a commit,
  plan step, end-of-task gate or branch completion. This explicitly overrides generic
  whole-suite/green-suite requirements in executing-plans, subagent-driven-development,
  using-git-worktrees, finishing-a-development-branch and verification-before-completion,
  for inline and delegated work alike; carry it into worker and reviewer prompts.
  A policy skip is not a pass, a test sample or proof of correctness. Record the actual
  focused scope, mandatory checks, skipped broad work and any remote evidence in the
  done or park note, each as its own item; a worker states them in its report too,
  whether or not it writes that note.
- The protected focused route is `just test-one <runner args>` when declared, otherwise
  the project's documented focused route. If none exists, note the gap on the task and
  use the documented route; never invent a runner or disguise a full suite as focused
  work. Adoption must settle this gap before switching off. Documentation-only work
  creates no test obligation. Known correctness failures still need a fix or explicit
  disposition.
- Deliberate broad verification uses `TT_FORCE=1 just test`, or `just test-full` when
  the project declares that alias. Additional focused integration tests cover affected
  behavior; policy-off does not force a broad rerun because hooks are absent or a fast
  selector misses it. Routine broad verification runs remotely on the declared push
  refs. Hosted jobs set `TT_FORCE=1` explicitly; a refused hosted skip is a configuration
  failure to fix, not permission to remove the refusal.
- With policy enabled or absent, while changing code run the test you are working on,
  then a fast check before
  committing, by the first route the project defines:
  - A justfile with `test-fast` (the test front door): `just test-one <runner args>`;
    where there is no `test-one` yet, the focused run its AGENTS.md names, or
    `just test-fast` if it names none. Then `just test-fast` before committing.
  - No `test-fast` recipe: `just test-one` when the justfile has it, otherwise the test
    command the project's guide documents (or the package test script or README command
    it points to); before committing, that documented command.
  - Neither a recipe nor a documented command: note on the task that the project
    declares no test route. Do not guess a runner, skip the check silently, or
    add recipes to the project to fill the gap.
- With policy enabled or absent, the full suite runs in CI where CI is configured for
  it, and otherwise in the pre-push
  hook. Run it yourself (`just test`, or the guide's documented full-suite command where
  there is no recipe) only when the hooks are not installed, when the fast check does
  not cover the affected behavior, or when you are asked to. The baseline the Git rule
  requires (at a new worktree's creation, or at execution's Setup for planned work) is
  a scheduled exception and runs the full suite.
- In a project with the test front door (a justfile with `test-fast`), never call a test
  runner directly: the recipe is how the run is recorded.
- A test that starts a subprocess passes it an environment built key by key: `PATH`,
  `HOME` pointed at a temporary directory the test owns, and each other variable the
  process reads (such as `USER`), with a fake value for any credential. It never passes
  the inherited environment, a copy of it, or one edited from it (`os.environ.copy()`,
  `{**os.environ, …}`, a denylist filter), so a failing case's traceback, captured
  output or log cannot print a credential held in the environment or under `HOME`.
  Build that environment before the first run, the RED run included: an expected
  failure is exactly where a credential gets printed.
- Before removing a worktree, run `tt-report` so its test timings are harvested.

A project with an open task tagged `halt` takes that task first; `tasks prime` and
the session-start message name it. Starting other blocked work there overrides the
halt and needs the user's approval: given in this session, or a standing grant
recorded on the halt at the user's request, in their words and with the session it
came from, naming the tasks or work it covers (such as the remedy and the runs a
latency incident's verification needs). Override with `tasks start <id> --force
--reason "<why>"`, whose reason quotes or cites that approval so the override is
recorded. A reason the agent writes for itself is not approval, and neither is a
controller's instruction to its subagent. Without approval, park the blocked work
(`tasks park <id> "<next step>" --waiting-on user --reason approval`) rather than
force it.

For adopted policy-off projects, disabled broad targets create no routine latency
obligation; timing findings on remaining local paths are advisory. Forced runs are
diagnostic and do not reactivate disabled obligations. Judge disposition against the
registered main code checkout: a branch-local policy edit alone retires nothing.
For each existing incident, inspect every host/target, note each retired obligation
with its landed policy revision, and remove only the timing halt. Keep unrelated
halts and remaining diagnosis. Disabled obligations are not applicable, never met;
close or drop solely retired work as policy-retired, not performance-verified.
A rollback records `policy: enabled at <RFC3339-UTC> revision <full-sha>` on the
adoption task with source `tt-policy:<prefix>`; latency eligibility restarts there.
Enabled obligations continue to use the verification procedure below.

A latency incident tagged `test-latency` closes in three phases. In the remedy's
worktree, `tt-latency verify <id> --after <timestamp> --dry-run` shows progress and
records nothing. After the remedy branch merges, the cutoff is the merge commit's time
in UTC (`2026-09-26T18:35:55Z`): only successful, uncontended, unwidened runs that start
strictly after it count, so let them accumulate on every host named in the breach notes.
Then, on each of those hosts, record from the registered checkout with the task's claim
moved there (`tasks start <id>` in it), keeping the output and the exit status apart:
`out=$(mktemp); tt-latency verify <id> --after <cutoff> >"$out" 2>&1; rc=$?`, then
`tasks attach <id> "$out" --name verify-<host>.txt --caption "<verdict line>"`, then
read `rc`. A successful attach is not a successful verify. Each run notes the
obligations its host meets and exits 1 while another host still owes one; close only
after a run exits 0 with `verified: every obligation is met`, with a one-line `tasks
done` message naming that verdict, the cutoff and the attachment names, never the
output itself.

## Shell

- Claude Code's Bash tool runs bash (`CLAUDE_CODE_SHELL` in its settings); Codex's
  shell tool runs the login shell, zsh. Under zsh an unquoted word starting with `=`
  (`echo ===`) or a glob that matches nothing (`--include=*.py`) fails the whole
  command line: quote them (`echo '==='`, `--include='*.py'`).
- `tasks root <task-id>` takes a full task id and prints the registered root of its
  project (`--pretty` for the bare path); it refuses a bare prefix. To find a project
  by prefix, read `tasks projects --paths --pretty`, or the `root` field of its default
  JSON rows. Never invent an id to feed `root` or hardcode a host path. Both name the
  registered root, the main checkout: a command run without a scope inside a worktree
  still reads that worktree, and neither lookup replaces it.
- `pkill -f <pattern>` also matches the shell running it, whose command line contains
  the pattern, and kills it: use `pkill -f '[p]attern'` or kill the pid you recorded.
- A skill read through the shell rather than loaded natively is read completely before
  you rely on it, in explicit ranges (`sed -n '1,150p'`) small enough for both the
  command's output limit and the response that carries it: reads batched into one call
  share that response, so never concatenate large skills into one. Line counts do not
  bound bytes; size ranges from `wc -c`. Any truncation marker means the read is
  incomplete: fetch the omitted range in smaller calls before acting on the skill. A
  heading search or `head` locates content but does not replace reading it. A complete
  read already in context stands until truncation or context loss removes part of it.
- An empty or suspiciously small recursive search under a home directory assembled
  from symlinks (such as `~/.agents/skills`) is not evidence of absence. Rerun
  following links (`rg -L`, `fd -L`, `find -L`), or resolve the entry with
  `readlink -f <entry>` and search its owner checkout.

## Task notes for outcome measures

Two note shapes are read by obs's outcome measures; write them as plain
`tasks note` lines, exactly in this form.

- When a review of your spec, plan, or implementation arrives, before acting on
  it, note it on the task: `review: <spec|plan|impl> round <n> — verdict: <revise|accept>; findings: <label> <count>, … | none; reviewer: <harness/model | harness | human>`
  (`review: plan round 2 — verdict: revise; findings: P1 1, P2 3; reviewer: codex/gpt-6.1-sol`).
  Use the actual reviewer's exact model identity when supplied by the reviewer or
  verified dispatch/runtime metadata. Do not substitute the controller's model,
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
  task note, never in the `review:` note. A reviewer writes no note: it states that
  value in its review for the note writer to record.
  Only a session noting its own self-review records it directly.
  `n` counts from 1 per task and artifact; a re-review after a revision is the next
  round; a short acceptance is still a round. The flow `verified` gate stays a
  disposition record, not a round.
  Brainstorming's builder check counts as a `review: spec` round: use `revise`
  when it raises questions to answer in the document or bring to the user, and
  `accept` when it raises none. Record its reviewer identity by the same rule above.
  One agent writes each round's note, once, before handing the findings on: the
  controller when there is one, otherwise the agent the review arrives to. A worker
  handed review findings (resumed or freshly dispatched) checks that the round's note
  exists and writes none; if it is missing, the worker says so in its report for the
  controller to add.
  This shape measures only spec, plan and implementation reviews; record a review
  of any other artifact (a scope brief or research note) as a plain task note that
  does not begin with `review:`.
- When you file a task because work closed as `done` fell short, changed, or grew,
  note it on the new task at filing: `concerns: <task-id> <defect|change|extension> — <one line>`.
  `defect`: the closed work did not do what its task asked or broke something that
  worked; `change`: it did what was asked and something different is now wanted;
  `extension`: new scope built on it. A finding before close is a review finding,
  not a concern.

## Trials

After `tasks start`, run `~/.agents/bin/trial-arm <id>` and follow what it prints.
`flow on` runs the task under the flow skill; `flow off` runs it without flow,
whatever else would choose it; `not enrolled` changes nothing. Every task in a unit
has the unit's arm, and the task's `process` is unchanged in both arms. Only the user
overrides an arm: record it with `tasks note <id> "arm: <trial> — override: <why>"`.
If it exits non-zero, show the user its error and do not choose flow on or off until they answer.

## Feedback

- Friction, a gap, or a notable success in the shared tooling goes to the project that
  owns it, at the moment, in one command; then carry on:
  `tasks feedback --project <owner> "<one line about the tool>" --category <friction|gap|idea|positive>`.
  "Feedback owners" under Projects below lists who owns what; the tasks skill has the
  mechanics (`-b`, `--recur`, `--new`, following up).
- A report that relays the user's request, or carries more than one ask about one
  issue, is still one command (distinct issues still get one report each), with a body
  (`-b`, one line on a recurrence) of a few concrete sentences covering what applies:
  each distinct outcome asked for, in tool terms; the action that hit the friction; what
  happened against what was expected; and any constraint that matters. Mark what the
  user asked apart from your reading of it, and write the body to stand without the
  transcript. Like the title, it describes the tool, never the project, even when it
  relays the user's words (the rule below).
- Report when a hook or gate blocked you wrongly, or its message did not say what to do
  (`friction`, to the owner it names); when an instruction or skill told you to do
  something a tool refused, or two instructions contradicted each other (`friction`, to
  the instruction's owner); when you needed something the tooling does not do and worked
  around it (`gap`); when something saved you real work (`positive`); and when a flow
  retro's lesson is about the tooling rather than the task (file it too, and put the
  returned id in the retro).
- The user's feedback on how agents behave or what they produce, and any request to
  make a lesson a pattern, is filed the same way, to the project that owns the guidance
  or tool it would change (`lore` for the global instructions and skills). A memory may
  keep a local copy; it never replaces the report. A request about the current task
  alone (fix this file, relabel this sheet) is ordinary work, not a new rule.
- Describe the tool, never the project: no repository names, paths, people, or project
  content, whatever the checkout's profile. One report per distinct issue; never triage
  your own.
- File from where you stand. A project checkout (one `tasks where` names a project
  for, whatever its `kind`: records in the tree, under the records root, or linked)
  reports under its project's prefix; outside every project the report
  is tagged `from:unregistered`. Never borrow another checkout with `-C`, which would
  misstate the source. If filing fails (a broken config, `tasks` missing), name the
  tool, its owner, and the error in your end-of-turn message, since only the user can
  decide.
- A defect in code the user does not maintain (a vendored submodule, an installed tool, a
  library) is checked upstream before anything else, scoping included: search the
  project's open and closed issues and PRs, its default and development branches, and
  its changelog for a report or fix, and note on the task what was searched and found.
  Reproduce or patch only after that search.
- When a report or fix exists, link it on the task and decide among waiting for the
  release, pinning the fixing commit, and carrying a local workaround that names the
  upstream link and the release that retires it. Comment or react upstream only to add
  what the maintainers lack (a new reproduction, environment, or confirmation).
- When none exists, confirm the root cause with a minimal reproduction, read the
  project's contributor guidelines, agent instructions and issue or PR templates, and
  prepare the issue or patch to follow them. Any upstream post, comment or reaction is
  an action outside the repository: prepare it, and the user approves publishing it.

<!-- ops:projects start — generated by ops-projects; edit identity.toml in the project, or identity-mirror.toml in ops -->
## Projects

Backticked names below are project prefixes: when one appears in a request it means
that project, not an ordinary word. `tasks projects` prints their paths and status,
and `list`, `ready`, `next`, `prime`, `tree`, `tags`, and `sample` each take `--project <prefix>`
to read one of them from anywhere.

- `atoms` — atoms — A recoverable filesystem effect engine: the crash-safe substrate
- `autonomy` — autonomy — The envelope and orchestrator of verifiably: what may run unattended
- `band` — band — Single-agent and multi-agent orchestration across harnesses and domains
- `beliefs` — beliefs — The epistemic kernel of verifiably: recording scientific belief
- `dots` — dotfiles — The dotfiles: shell, editor, desktop, and terminal configuration
- `fam` — familiar — Agent pets and the session hook bus
- `flows` — flows — Agent flows: task states, gates, evidence, and the tools that judge them
- `forge` — familiar-forge — Generative art CAS behind familiar's pet themes
- `forge2` — forge v2 — Make familiar pet themes by picking images; the forgemaster fills in the rest
- `glean` — glean — Finds and retrieves the Google Photos a local photo collection is missing
- `hostkit` — hostkit — Generic host primitives: storage links, process budgets, load, and link sync
- `hq` — harness-quarters — Harness homes, declared links, settings, and session-state hygiene
- `lit` — lit — Science literature as a world model, a personal corpus, and a walk over both
- `look` — lookout — A read-only glance at live agents, task state and obs signals in a niri dropdown
- `lore` — lore — Agent context: the instruction corpus, profiles, skills, and traceable assembly
- `material` — niri-material (niri) — One glass material across niri, terminals, editor, and shell
- `mind6` — mindful v6 (mindful) — Headless thought, mindmap, and journal store; the current mindful
- `mm` — multiple-myeloma — The multiple myeloma research program: a workspace over the verifiably stack
- `nodes` — nodes — A problem-agnostic knowledge substrate: typed markdown nodes
- `ns` — natural-systems (natural-systems-v2) — Research on structure across representation, observation, scale, and coupling
- `obs` — obs — Cross-project execution evidence, observability, and historical analysis
- `ops` — ops — The hub for work spanning projects, and the shared tooling
- `pressure` — noctalia-resource-alert — Noctalia v5 plugin for memory, sustained CPU, and disk-space pressure alerts
- `prism` — prism — Resolves appearance definitions and applies them to their targets
- `quarry` — quarry — One CLI and skills over scientific resources, with domains as lenses
- `refs` — refs — Vocabulary identifiers pinned to releases: the reference layer above nodes
- `relay` — relay — Harness adapters, hook dispatch, and a host-local live-agent registry
- `sci` — science — The daily surface of verifiably: the layer people and agents use
- `sun` — sun — The heliophysics research program: a workspace over the verifiably stack
- `tasks` — tasks — The file-based task tracker every project here uses
- `trans` — transponder — A phone browser inbox for typed questions from agents
- `tui` — tasks-tui — A keyboard-driven terminal front end for the tasks tracker
- `vdocs` — docs (verifiably-docs) — The verifiably ecosystem's front door: its goal, overview, and repository map
- `wali` — wali — Wallpaper switcher with per-image ratings and the Noctalia wali panel

Retired: `mind3` (mindful v3, 2026-10-04) → `mind6`.

### Feedback owners

The projects that accept feedback, and what each owns. File with
`tasks feedback --project <prefix> "<one line>" --category <friction|gap|idea|positive>`;
the Feedback section above says when.

- `flows` — The flow skill and state machine, its gate tools, evals and trials.
- `hq` — Harness homes and the declared links that install the agent surface, harness settings and hook wiring, capability facts, state hygiene, the session archive, and the session-logs skill with its tools.
- `lore` — The global instructions and profile fragments, the skill corpus, instruction assembly, and the profile hook.
- `obs` — Execution evidence: session and task indexing, joins, baselines, and their reports.
- `ops` — Shared tooling in bin/ (including the vendored tt, ops-check, ops-docs), the Claude Code hooks (pretooluse, claim-guard, relay-guard, provenance), profiles, gates, and the quick-add skill.
- `relay` — Harness adapters, hook dispatch to non-Claude harnesses, the live-agent registry, and relay identity.
- `tasks` — The tasks CLI and its tasks, curate, and scope skills.
<!-- ops:projects end -->
