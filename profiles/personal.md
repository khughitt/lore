# Profile: personal

A repository the user maintains for themself. New design specs, implementation
plans, briefs and handoffs go where the session line's `design docs:` clause says.
Under the records root, write them in the `docs/` directory that clause names
(`specs/`, `plans/`, and `notes/` for briefs and handoffs) and commit them in place
on the records repository's one branch: it keeps no worktrees. `--spec` and `--plan`
take the path relative to the project's records directory (`docs/specs/<name>.md`);
a review request names the records repository and the path from its top
(`<prefix>/docs/specs/<name>.md`). While a project's records are still in the tree,
or the value is `commit`, commit them in the code repository under the convention it
documents (`docs/specs/`, `docs/plans/` and `docs/notes/` unless its own instructions
name another place). A document the code tree already tracks stays there and is
revised in place until the project rewrites it as a reference document. The
`docs/superpowers/` default of the brainstorming and writing-plans skills is never
the right directory here. A reference document in the code repository's `docs/` is
updated by the change that alters the behaviour it describes. Pull requests, where
the repository uses them, need no draft. GitHub writes use the `khughitt` account,
named per command: `GH_TOKEN=$(gh auth token --user khughitt) gh …` touches no
global state. The fallback is `gh auth switch --user khughitt` when `gh auth status`
shows another account, but the active account is global state, often the other
one, and a concurrent session can switch it back before the write.
