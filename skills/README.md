# skills

hq's `links.toml` declares `~/.agents/skills` as a real directory of individual links
into this repository, into the tasks, ops, flows, hq and quarry checkouts, and into
the superpowers submodule here;
it is the skill directory for every harness other
than Claude Code, which reads skills from `~/.claude/skills` and plugins from its own
cache. Its readers are Codex (shown as root `r0`), OpenCode (a recursive `**/SKILL.md`
scan) and Crush (dotfiles' `crush/patch_skills_user_invocable.py` patches the
directory for its command palette).

Upstream revisions are pinned by the Git submodules; hq's `links.toml` records
which skills are served. There is no separate installer lock inventory.

The layout is flat: every skill is served at `~/.agents/skills/<name>/SKILL.md`,
from a directory here or in its owner's checkout. Codex shows each as `r0/<name>/SKILL.md`, and a flat path
is the one an agent guesses; nested skill directories were read back with a level
dropped or added. Keep new skills at this depth.

- `curate-docs/` — the documentation-review rubric (ops
  `docs/project-guides.md` and `docs/operations.md`), shaped like `curate`.
  Served by a `lore:skills/curate-docs` declaration in hq's `links.toml` for each home
  surface.
- `tasks`, `curate`, `scope`, `quick-add` — served from the tasks and ops checkouts by
  declarations in hq's `links.toml`, so the skills those repositories ship are always
  the checked-out version. A new skill is a declaration there for each home surface;
  `just link --apply` creates the links.
- `flow` and `session-logs` — served from the flows and hq checkouts, declared the same way.
- `quarry` and `quarry-biology` — served from the quarry checkout's `skills/`, declared
  the same way.
- `references/retained-item-records.md` — lore-authored closeout record guidance,
  read on demand from the global Processes rule. The existing hq directory link
  serves it at `~/.agents/skills/references/retained-item-records.md`, beside the
  retention-v1 schemas; it is not a skill.
- Nine addyosmani/agent-skills skills (`api-and-interface-design`,
  `code-simplification`, `context-engineering`, `documentation-and-adrs`,
  `frontend-ui-engineering`, `observability-and-instrumentation`,
  `performance-optimization`, `security-and-hardening`, `source-driven-development`) —
  served from `vendor/agent-skills/skills/` here, a git submodule of
  addyosmani/agent-skills pinned at a release tag (`0.6.15`), by one hq `links.toml`
  declaration per skill in `[required]` (`~/.agents/skills/<name>`) and in
  `[harness.claude.links]` (`skills/<name>`), so every harness sees the same set.
  Upstream skills cite their shared checklists as `../../references/<file>.md`; hq
  links `~/.agents/references` and `~/.claude/references` to
  `lore:vendor/agent-skills/references` so that path resolves from either skill
  directory. The other 16 upstream skills are not served: several duplicate or collide
  with superpowers skills, and the rest conflict with the global instructions or need
  tooling not set up here (lore-1be62d records each reason). In Claude Code, overlap
  with the `code-simplifier`, `security-guidance` and `frontend-design` plugins is
  accepted. Lore carries no patches to upstream text. Bump with
  `git -C vendor/agent-skills checkout <tag>` and commit the pointer; a change to the
  selected set needs the matching hq declarations on both surfaces in the same change
  set.
- The superpowers skills (`brainstorming`, `writing-plans`, … one declaration per skill) —
  served from `vendor/superpowers/skills/` here, a git submodule of obra/superpowers
  pinned at a release tag. This is the only superpowers copy the non-Claude harnesses
  see: the Codex remote plugin `superpowers@openai-curated-remote` is uninstalled
  (`codex plugin remove`). A `[plugins.…] enabled = false` entry does not hide a remote
  plugin, whose install state syncs from the account; if it returns, remove it again.
  Claude Code loads superpowers as the `superpowers@superpowers-marketplace` plugin
  (obra's marketplace, auto-update off in hq's Claude settings; the official
  `superpowers@claude-plugins-official` entry is disabled because it lagged 7.0.1), so
  keep the submodule on the same commit as the installed plugin (`gitCommitSha` in
  `~/.claude/plugins/installed_plugins.json`) or the two harnesses run different skills.
  That marketplace entry pins no commit, so install or update the plugin only while
  upstream's default branch is at the release tag. Bump with
  `git -C vendor/superpowers checkout <tag>` and commit the pointer; when the
  release adds or removes a skill, add or remove its declaration in hq's `links.toml`
  (`lore:vendor/superpowers/skills/<name>`), in the commit after the bump here.
  Move a removed home link's declaration to `[retired]`, keeping its
  former target so `just link --apply` can safely remove it. On a fresh clone,
  `git submodule update --init`.

Profile fragments — the instructions that differ between kinds of project —
live in `profiles/` here, one file per profile. ops
`profiles.toml` names them and `ops-profile session` prints the ones a
checkout selects; the delivery contract is [`../docs/profile-delivery.md`](../docs/profile-delivery.md).
