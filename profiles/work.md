# Profile: work

A repository worked under the work account. Design specs and plans stay out of
the tree unless the repository's own instructions ask for them. In a linked
checkout (`tasks where` says `"linked": true`), write them under `docs/specs/`
and `docs/plans/` in the project's `root` that `tasks where` names, where
`--spec` and `--plan` resolve, and commit them in the overlay repository.
Elsewhere, write the doc at the skill's path, add that path to
`.git/info/exclude`, and copy it out before removing a worktree. GitHub writes use the work account the session's
`profile:` line names after `gh:`, named per command:
`GH_TOKEN=$(gh auth token --user <that account>) gh …` touches no global state.
The fallback is `gh auth switch --user <that account>` when `gh auth status`
shows another account; the active account is global state, and a concurrent
session can switch it back before the write. The repository's own guidelines decide
branch, commit, and review conventions.
