# skills

hq's `links.toml` declares `~/.agents/skills` as a real directory of individual links
into this repository, into tasks and ops, and into the superpowers submodule here;
it is the skill directory for every harness other
than Claude Code, which reads skills from `~/.claude/skills` and plugins from its own
cache. Its readers are Codex (shown as root `r0`), OpenCode (a recursive `**/SKILL.md`
scan) and Crush (dotfiles' `crush/patch_skills_user_invocable.py` patches the
directory for its command palette).

The layout is flat: every skill is served at `~/.agents/skills/<name>/SKILL.md`,
from a directory here or in its owner's checkout. Codex shows each as `r0/<name>/SKILL.md`, and a flat path
is the one an agent guesses; nested skill directories were read back with a level
dropped or added. Keep new skills at this depth.

- `curate-docs/` — the documentation-review rubric (ops
  `docs/specs/2026-09-22-project-guides-design.md` §8, extended), shaped like `curate`.
  Served by a `lore:skills/curate-docs` declaration in hq's `links.toml` for each home
  surface.
- `tasks`, `curate`, `scope`, `quick-add` — served from the tasks and ops checkouts by
  declarations in hq's `links.toml`, so the skills those repositories ship are always
  the checked-out version. A new skill is a declaration there for each home surface;
  `just link --apply` creates the links.
- `flow` and `session-logs` — served from the flows and hq checkouts, declared the same way.
- `references/retained-item-records.md` — lore-authored closeout record guidance,
  read on demand from the global Processes rule. The existing hq directory link
  serves it at `~/.agents/skills/references/retained-item-records.md`; it is separate
  from the vendored checklists below and is not a skill.
- `api-and-interface-design/`, `code-simplification/`, `context-engineering/`,
  `documentation-and-adrs/`, `observability-and-instrumentation/`,
  `performance-optimization/`, `security-and-hardening/` — vendored copies from
  addyosmani/agent-skills. Their shared checklists live in `references/` (not a skill;
  `references/source.md` names the origin), cited from a skill as `../references/<file>.md`.
- The superpowers skills (`brainstorming`, `writing-plans`, … one declaration per skill) —
  served from `vendor/superpowers/skills/` here, a git submodule of obra/superpowers
  pinned at a release tag. This is the only superpowers copy the non-Claude harnesses
  see: the Codex remote plugin `superpowers@openai-curated-remote` is uninstalled
  (`codex plugin remove`). A `[plugins.…] enabled = false` entry does not hide a remote
  plugin, whose install state syncs from the account; if it returns, remove it again.
  Claude Code loads superpowers as the `superpowers@claude-plugins-official` plugin, so
  keep the submodule on the same version as the installed plugin (`~/.claude/plugins/installed_plugins.json`)
  or the two harnesses run different skills. Bump with
  `git -C vendor/superpowers checkout <tag>` and commit the pointer; when the
  release adds or removes a skill, add or remove its declaration in hq's `links.toml`
  (`lore:vendor/superpowers/skills/<name>`), in the commit after the bump here.
  Move a removed home link's declaration to `[retired]`, keeping its
  former target so `just link --apply` can safely remove it. On a fresh clone,
  `git submodule update --init`.

Profile fragments — the instructions that differ between kinds of project —
live in `profiles/` here, one file per profile. ops
`profiles.toml` names them and `ops-profile session` prints the ones a
checkout selects; the design is `docs/specs/2026-09-19-project-profiles-design.md`.
