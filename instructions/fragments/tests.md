## Tests

<!-- rule:c6567204f9e443b68cb95a08c8264b3f begin -->
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
  A policy skip is not a pass, a test sample or proof of correctness. Report the actual
  focused scope, mandatory checks, skipped broad work and any remote evidence separately.
- The protected focused route is `just test-one <runner args>` when declared, otherwise
  the project's documented focused route. If none exists, report the gap and use the
  documented route; never invent a runner or disguise a full suite as focused work.
  Adoption must settle this gap before switching off. Documentation-only work creates
  no test obligation. Known correctness failures still need a fix or explicit disposition.
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
  - Neither a recipe nor a documented command: say in your report that the project
    declares no test route. Do not guess a runner, skip the check silently, or add
    recipes to the project to fill the gap.
<!-- rule:c6567204f9e443b68cb95a08c8264b3f end -->
<!-- rule:48ef50fb32d24e7fa13b92a69affc29b begin -->
- With policy enabled or absent, the full suite runs in CI where CI is configured for
  it, and otherwise in the pre-push
  hook. Run it yourself (`just test`, or the guide's documented full-suite command where
  there is no recipe) only when the hooks are not installed, when the fast check does
  not cover the affected behavior, or when you are asked to. The baseline the Git rule
  requires (at a new worktree's creation, or at execution's Setup for planned work) is
  a scheduled exception and runs the full suite.
<!-- rule:48ef50fb32d24e7fa13b92a69affc29b end -->
<!-- rule:da431a1b3ac14c21800cb5488031d7e8 begin -->
- In a project with the test front door (a justfile with `test-fast`), never call a test
  runner directly: the recipe is how the run is recorded.
<!-- rule:da431a1b3ac14c21800cb5488031d7e8 end -->
<!-- rule:ca536e7c8ef24f09a49bd0c598972ef5 begin -->
- A test that starts a subprocess passes it an environment built key by key: `PATH`,
  `HOME` pointed at a temporary directory the test owns, and each other variable the
  process reads (such as `USER`), with a fake value for any credential. It never passes
  the inherited environment, a copy of it, or one edited from it (`os.environ.copy()`,
  `{**os.environ, …}`, a denylist filter), so a failing case's traceback, captured
  output or log cannot print a credential held in the environment or under `HOME`.
  Build that environment before the first run, the RED run included: an expected
  failure is exactly where a credential gets printed.
<!-- rule:ca536e7c8ef24f09a49bd0c598972ef5 end -->
<!-- rule:4402e5c1ec654514a43ca011c2800ba6 begin -->
- Before removing a worktree, run `tt-report` so its test timings are harvested.
<!-- rule:4402e5c1ec654514a43ca011c2800ba6 end -->

<!-- rule:13f54add0c144229bf870b4b39835acf begin -->
A project with an open task tagged `halt` takes that task first; `tasks prime` and
the session-start message name it. To start other blocked work, use `tasks start
<id> --force --reason "<why>"` so the override is recorded.
<!-- rule:13f54add0c144229bf870b4b39835acf end -->

<!-- rule:b6576b5590d4430da697c160e083b10c begin -->
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
<!-- rule:b6576b5590d4430da697c160e083b10c end -->
