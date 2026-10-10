# Profile: personal

A repository the user maintains for themself. Design specs and implementation
plans are committed by default, under the convention the repository documents
(`docs/specs/` and `docs/plans/` unless its own instructions name another
place); the `docs/superpowers/` default of the brainstorming and writing-plans
skills is never the right directory here. Pull requests, where the repository
uses them, need no draft. GitHub writes use the `khughitt` account, named per
command: `GH_TOKEN=$(gh auth token --user khughitt) gh …` touches no global
state. The fallback is `gh auth switch --user khughitt` when `gh auth status`
shows another account, but the active account is global state, often the other
one, and a concurrent session can switch it back before the write.
