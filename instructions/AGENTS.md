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
- Before changing repository code — for any task, direct or planned, not only a brainstorming + planning session — work in a worktree under `.worktrees/`, unless explicitly instructed to work in place. Reuse the task's existing worktree when resuming; otherwise create one with `git worktree add`, not a native worktree tool. `EnterWorktree` and its equivalents place worktrees under `.claude/worktrees/`, which only one harness reads; `.worktrees/` works for all of them. Planned work creates it before drafting the spec. Right after `git worktree add`, hydrate the new worktree from the first source the project declares: `just setup` when its justfile defines it (it installs dependencies and hydrates gitignored inputs); else the setup command its root guide names, or one its README or CONTRIBUTING names that writes only inside the worktree; else the frozen install of a lockfile that names its package manager and installs inside the worktree (`package-lock.json`: `npm ci`; `uv.lock`: `uv sync --frozen`). A bare manifest (`pyproject.toml`, `package.json` or `requirements.txt` without a lockfile), or a lockfile whose install can leave the worktree (Poetry's default cache environment), declares no usable installer: never guess one, as the worktree skill's Step 2 would, and report the missing setup route before the first commit. Hydrate before that commit: an unhydrated tree's hooks can stop at an `npx` install prompt or run unpinned tools. A checkout that declares no dependencies needs no setup. A suite that fails in a new worktree before setup is an unhydrated tree, not a bug. Planned work, whose worktree precedes its spec, defers the worktree skill's baseline tests (its Step 3) there: no code changes before the plan runs, and execution's Setup re-enters that skill and runs them before the first code change. Direct work runs them at creation. On every host running dotfiles, a checkout under `~/d` keeps `.worktrees/` as a relative symlink into that host's storage, created by `just setup` or `work-link --ensure .worktrees`, which also keeps git's worktree admin directory out of Dropbox; run it before every `git worktree add` (a `File exists` error on `.worktrees`, `.venv` or `target` means a link arrived before its storage did: run `work-link` once) (a checkout elsewhere, such as a clone under a temp dir, keeps `.worktrees/` in-tree: `--ensure` reports `outside` and does nothing); lock the new worktree right after creating it (`git worktree lock --reason "on WORK_ROOT storage (host: $(uname -n))" .worktrees/<name>`), and remove one with `git worktree unlock <path>` then `git worktree remove <path>`. Read-only investigation and task-record maintenance alone need no worktree.
- A live test of a worktree's code runs it by explicit path (`.worktrees/<name>/bin/<tool>`) or an environment override, never by repointing a shared launcher, symlink, service unit, or config include on the host at the worktree. When a host pointer must be repointed, record it in a task note at that moment (what, from, to, how to restore) and restore it before `tasks park` or `tasks done`; while it stands, the park note names it. Before removing a worktree, check that no host pointer resolves into it (`readlink -f` over `~/bin/*`, `~/.local/bin/*`, user systemd units, known config includes) and refuse while one does. A rollout that hands live state to another project's tool checks where that tool resolves on `PATH` first, rather than assuming the main checkout.
- Plain `git worktree remove` deletes ignored files without `--force`. Before any
  removal, list them (`git -C <path> status --ignored --porcelain`) and copy out what is
  still needed. Each plan workspace (`ls <path>/.superpowers/sdd/`) goes only after its
  ledger's `Ruling:` and `minor (deferred)` lines have reached a final message, other
  plans' included; otherwise copy its ledger out first.
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

- Whether design specs and plans are committed is the profile's call; the repository's own instructions override it, and the hook that guards staging names both.
- Verify document status against the code before relying on it; update it and related docs when work lands.

## Communication

- If the user suddenly switches the conversation to a different project, confirm that it was intentional.
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

- When you hold a recommendation for a bounded decision, state it with the alternative
  you rejected and act on it. Do not end the turn to ask for confirmation: the user
  overrides in free text if they disagree, and a wrong default costs one correction
  while a question costs a stop. This applies to "which approach", "where should this
  land", "does this section look right", "which follow-ups to file", and "execute now".
- Stop and ask only when the answer needs the user: an artifact they must inspect and
  judge (a sheet, a screenshot, a rendered page), a choice of taste, scope, or priority
  that no recommendation can settle, money to spend, or an action outside the repository.
- Two written artifacts keep their gate: a design spec and an implementation plan are
  reviewed before the next phase starts. Within writing them, sections are not
  individually approved.
- A request to review a spec or plan names the frozen revision under review: the
  repository, commit and path, so the reviewer reads `git -C <repo> show <sha>:<path>`
  rather than the working file, or, where the profile keeps the document out of the
  tree, its path and sha256. While that review is open, never amend or rebase the
  commit, and leave an out-of-tree file unedited. A later draft reaches review only as
  a new frozen revision, named in the next round's request, and each finding is judged
  against the revision it reviewed.
- A question, when asked, carries your recommendation as the first option and is one
  question, not a series. A question that asks the user to describe what they want
  (brainstorming's open questions, and its playback asking what is wrong or missing)
  carries no options; a guess they can correct stands in for the recommendation. That
  playback is not a "does this section look right" decision: what they want is theirs
  to say.
- A turn that ends with work still owed reports the observed status, not what the turn
  ending implies: which work has stopped and why, what is still running (a background
  check, a dispatched child) and how its result is picked up, and who owns the next step
  — never "is underway" for work that stopped. A step you own (a review you dispatch, a
  check you rerun, a child you have not started) is never reported as waiting on the
  user: finish it, or `tasks park` the task with that step as the next action and resume
  it; hand it over only explicitly (`--waiting-on user --reason review`). A park's next
  step is an action and who takes it ("rerun `just gate` in .worktrees/x, then dispatch
  the Task 6 review"), never a state ("waiting for next steps"). An unblocked task you
  hold is not parked between increments: continue until a blocker, a gate that needs a
  person, or the end of the session.
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
- Reviewers stay read-only and return their full review in their final message;
  dispatches must not ask them to write report files. When persistence is needed,
  the controller saves the full returned text in the plan workspace as
  `<slug>-report.md`, with the reviewer identity recorded alongside it. This applies
  to initial task reviews, scoped re-reviews and final whole-branch reviews. Keep
  the existing ledger, ruling and retention rules; saving a report does not replace
  those records.
- After a final whole-branch review, in subagent-driven and inline (executing-plans)
  execution alike, fix (or rule on, as the skills allow) its Critical and Important
  findings in corrective rounds, up to five; then surface what remains. A round is one
  fix pass plus one scoped re-review of it, and another follows while that re-review
  reports any Critical or Important finding, persisting or introduced by the fix. Minor
  findings never enter a round; they go to the ledger as `minor (deferred)`, as both
  skills say. A fix subagent makes the fixes under subagent-driven execution; inline,
  you make them yourself, each still proven RED→GREEN with a green suite. A fresh
  reviewer runs the re-review whenever a subagent tool exists, inline too. This outranks
  executing-plans' "do not dispatch a re-review" and "no second fix pass" and
  subagent-driven-development's "exactly one scoped re-review" and "no second fix wave".
  Without a subagent tool, the re-review is a self-review, recorded as such in the
  ledger and the final message, as executing-plans' final-review fallback does. External
  actions stay gated.

## Processes

- A smoke or live-run script an agent launches detached (`setsid nohup … & disown`, a
  background `bun`, `node` or `weston`, a tmux server) owns its cleanup: it records the
  pids it spawns and reaps them on its own exit and on the harness's stop (a `trap` on
  EXIT, TERM and INT, or killing the tmux session), so a closed terminal never leaves a
  child burning CPU in a dead `kitty-*.scope`. A process that must outlive the turn (a
  server a later step drives) is named in the end-of-turn report with its pid and how to
  stop it; before that report, `host-load --section session` (ops's `bin/host-load`, on
  `~/.local/bin`) lists what this session's scope left running, and the report repeats
  it or says nothing was left. `host-load` also names the load a preflight refuses on
  and sweeps orphans across sessions; its `--kill` is the user's decision, not yours.
- A launcher that leaves a process running behind a tracked channel (the harness's
  shell tool, `ssh host cmd`, a hook) redirects all three of that process's standard
  streams (`</dev/null >log 2>&1`): a child that inherits stdout or stderr holds the
  call open after the launcher returns, and `&`, `nohup` and `setsid` close nothing.
- A process the user has authorized to outlive the session starts as a transient user
  service: `systemd-run --user --unit=<name> --service-type=exec
  --working-directory=<dir> [-E VAR=value] <cmd>`, once `systemctl --user` answers and,
  for a launch over ssh, lingering is on (`loginctl show-user <user> -p Linger`;
  enabling it is the user's decision). Its return means started, not ready, so a
  bounded readiness check (its port, a health command) follows, and the report names
  the unit, `journalctl --user -u <name>` and `systemctl --user stop <name>`. `setsid`
  and `systemd-run --scope` leave the process in the terminal's scope and are not
  service launches. A server that a later step of this session drives stays under the
  cleanup bullet above.
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
  retrying. When asking for the machine, name the pilot and what it showed.
- A task that spans sessions keeps its inputs where a reboot cannot take them. Its
  scratch lives in a per-task directory on persistent host-local storage off the synced
  tree, `$WORK_ROOT/<project>/<task-id>/` (on a host without `WORK_ROOT`, ask the user
  where rather than inventing a path). tmpfs (`/dev/shm`, `/tmp`, `/run`) holds only
  per-run copies made from that persistent canonical copy, and a park names the
  canonical copy's path and sha256. A resume checks that its inputs exist and match the
  recorded hash before it claims an idle-host window or the user's machine.
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

## Tests

- While changing code, run the test you are working on, then a fast check before
  committing, by the first route the project defines:
  - A justfile with `test-fast` (the test front door): `just test-one <runner args>`;
    where there is no `test-one` yet, the focused run its AGENTS.md names, or
    `just test-fast` if it names none. Then `just test-fast` before committing.
  - No `test-fast` recipe: `just test-one` when the justfile has it, otherwise the test
    command the project's guide documents (or the package test script or README command
    it points to); before committing, that documented command.
  - Neither a recipe nor a documented command: say in your report that the project
    declares no test route. Do not guess a runner, skip the check silently, or add
    recipes to the project to fill the gap.
- The full suite runs in CI where CI is configured for it, and otherwise in the pre-push
  hook. Run it yourself (`just test`, or the guide's documented full-suite command where
  there is no recipe) only when the hooks are not installed, when the fast check does
  not cover the affected behavior, or when you are asked to.
- In a project with the test front door (a justfile with `test-fast`), never call a test
  runner directly: the recipe is how the run is recorded.
- A test that starts a subprocess passes it an environment built key by key: `PATH`,
  `HOME` pointed at a temporary directory the test owns, and each other variable the
  process reads (such as `USER`), with a fake value for any credential. It never passes
  the inherited environment, a copy of it, or one edited from it (`os.environ.copy()`,
  `{**os.environ, …}`, a denylist filter), so a failing case's traceback, captured
  output or log cannot print a credential. Build that environment before the first run,
  the RED run included: an expected failure is exactly where it gets printed.
- Before removing a worktree, run `tt-report` so its test timings are harvested.

A project with an open task tagged `halt` takes that task first; `tasks prime` and
the session-start message name it. To start other blocked work, use `tasks start
<id> --force --reason "<why>"` so the override is recorded. Close a latency
incident tagged `test-latency` only after `tt-latency verify <id> --after <remedy
timestamp>` exits 0 for every host named in its breach notes, and include the
verify output in the `tasks done` message.

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
  reviews labelled `human`. A Codex session that performed a review reads its identity,
  never another session's, in the turn that performed it with a fresh command (never a
  terminal left from an earlier turn): `timeout 2 relay model --harness codex --pretty`
  prints `codex/<model>` when verified and `codex` otherwise. Copy the printed value;
  when the command exits non-zero or times out, the value is `codex`. Whenever it is
  bare `codex`, name the stderr reason or the exit status in your report. A reviewer
  writes no note: it states that value in its review for the note writer to record.
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
- File from where you stand. A project checkout (one with `tasks/.config.toml`) or a
  linked checkout reports under its project's prefix; outside every project the report
  is tagged `from:unregistered`. Never borrow another checkout with `-C`, which would
  misstate the source. If filing fails (a broken config, `tasks` missing), name the
  tool, its owner, and the error in your end-of-turn report, and the user decides.
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
- `beliefs` — beliefs — The epistemic kernel of verifiably: recording scientific belief
- `crew` — crew — An agent harness on pi: runs work from tasks and science on their own terms
- `dots` — dotfiles — The dotfiles: shell, editor, desktop, and terminal configuration
- `fam` — familiar — Agent pets and the session hook bus
- `flows` — flows — Agent flows: task states, gates, evidence, and the tools that judge them
- `forge` — familiar-forge — Generative art CAS behind familiar's pet themes
- `glean` — glean — Finds and retrieves the Google Photos a local photo collection is missing
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
- `prism` — prism — Resolves appearance definitions and applies them to their targets
- `quarry` — quarry — One CLI and skills over scientific resources, with domains as lenses
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
