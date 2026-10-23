# Profile: personal

A repository the user maintains for themself. Design specs, implementation plans,
briefs and handoffs go where the session line's `design docs:` clause says. Under
the records root, write them in the `docs/` directory that clause names, at the
paths the skills use (`specs/`, `plans/`, `notes/`), and commit them in the records
repository, which keeps one branch and no worktrees; `--spec` and `--plan` take the
path relative to the project's records directory (`docs/specs/<name>.md`). While a project's records are still in
the tree, or the value is `commit`, commit them in the code repository under the
convention it documents (`docs/specs/` and `docs/plans/` unless its own instructions
name another place). The `docs/superpowers/` default of the brainstorming and
writing-plans skills is never the right directory here. The code repository's
`docs/` keeps reference documents, which the change that alters their behaviour
updates in the same commit. Pull requests, where the repository uses them, need no
draft. GitHub writes use the `khughitt` account, named per command:
`GH_TOKEN=$(gh auth token --user khughitt) gh …` touches no global state. The
fallback is `gh auth switch --user khughitt` when `gh auth status` shows another
account, but the active account is global state, often the other one, and a
concurrent session can switch it back before the write.
