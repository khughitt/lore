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
