# Records store

This repository holds task records and working documents. Code-checkout design-document
placement rules do not apply here. Core attribution and task-id rules still apply.

Keep this repository on its one branch, with no worktrees. Commit records and working
documents through `tasks commit` under its records lock, never raw `git add` or
`git commit`. From the store root, select the project explicitly:
`tasks commit --project <prefix> <path>... -m "<message>"`. Paths are relative to
that project's records directory. Replace these placeholders before running the
command; commit only the intended project's paths. The from-project-checkout form
of `tasks commit` remains valid too.
