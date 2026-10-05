## Tests

- While changing code: `just test-one <runner args>` for the test you are working on,
  then `just test-fast` before committing. Where a project's justfile has no `test-one`
  yet, use the focused run its AGENTS.md names; if it names none, use `just test-fast`
  until the project adopts `test-one`.
- The full suite runs in CI where CI is configured for it, and otherwise in the pre-push
  hook. Run `just test` yourself only when the hooks are not installed, when the fast
  target does not cover the affected behavior, or when you are asked to.
- In a project with the test front door (a justfile with `test-fast`), never call a test
  runner directly: the recipe is how the run is recorded.
- Before removing a worktree, run `tt-report` so its test timings are harvested.

A project with an open task tagged `halt` takes that task first; `tasks prime` and
the session-start message name it. To start other blocked work, use `tasks start
<id> --force --reason "<why>"` so the override is recorded. Close a latency
incident tagged `test-latency` only after `tt-latency verify <id> --after <remedy
timestamp>` exits 0 for every host named in its breach notes, and include the
verify output in the `tasks done` message.
