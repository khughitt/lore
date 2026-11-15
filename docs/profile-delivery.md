# Profile delivery

Type: protocol; document types 1. Currently unversioned. The SessionStart hook
`hooks/claude-profile` delivers the checkout's profile layer to Claude Code or Codex.
Changing its inputs, text or export changes this protocol on both surfaces.

## Ownership and invocation

Instructions apply in order: assembled core, profile, repository instructions,
then the user. Lore owns the resolver in `src/lore/`, the thin `bin/lore` launcher,
the hook and the prose in `profiles/`. Tasks owns assignment/placement metadata and
its resolver. hq owns hook wiring and continues invoking main's hook; a worktree's
hook is used only by explicit path during preparation.

There is no PATH install. From this checkout, use `./bin/lore profile` with one of:

| Subcommand | Result |
| --- | --- |
| `resolve [PATH] [--json]` | Effective values and sources, optionally JSON |
| `explain [PATH]` | Human-readable values with provenance |
| `session [PATH]` | Complete delivered profile text |
| `check` | Configuration/catalogue diagnostics; nonzero for problems |
| `audit [PATH]` | Existing design documents hidden by excludes or retained in code |

From elsewhere, run `tasks resolve lore --json`, require a successful single result,
and read `results[0].root`. Invoke that root's `bin/lore` by explicit path, safely
quoting the executable path. Delivered explain/recovery advice prints the actual
quoted launcher from the executing source tree. Missing or invalid resolution is
an error, not a reason to guess an installation path.

## Configuration and selection

`profiles/profiles.toml` is public. The private file is `profiles.toml` under the
lore records directory returned as `entry.records` by `tasks resolve lore --json`.
The production resolver never reads ops's profile config or identity mirror.

| TOML section | Content |
| --- | --- |
| `[profile.<name>]` | `fragment`, `home`, `design_docs`, `pr_draft`, `private`; private-only `gh_account`, `git_identity`, `overlay` |
| `[home.<name>]` | `claude`, `codex`, `agy` paths; home detection is advisory |
| `[[family]]` | Absolute or home-relative `path`, nonempty `profiles` list; longest real prefix wins |
| `[default]` | Nonempty `profiles` list, declared by exactly one file |

Private values include accounts, commit identities, overlays and employer-specific
path rules. Public and private files may extend profiles/homes with disjoint keys;
a duplicate scalar is an error. Path arrays concatenate but duplicate real prefixes
are errors. Unknown fields/names, invalid types, missing files and ambiguous
ownership fail explicitly. Names use lowercase letters, digits, underscores and
hyphens, starting with a letter. Each selected typed key has exactly one owner;
composable profiles may contribute disjoint keys and prose.

Selection is clone `agent.profile` (comma-separated names), records `entry.profile`
(one name), longest path default, then default profiles. Missing assignment advances
through that declared order; broken metadata or unknown assignments do not. Worktrees
classify through their main checkout, while repository placement overrides are read
from the invoking worktree. Existing `ops.designDocs=commit` and explicit instruction
references to docs/superpowers subdirectories remain supported.

## Exchange

Inputs are the JSON hook payload (`cwd`, `transcript_path`), process cwd, and the
caller's environment. Non-object/invalid JSON means no payload. A transcript path
identifies its configured harness home before environment hints. The hook reads
`CLAUDE_ENV_FILE` for the optional selected-name export.

1. Load the executing tree's package without writing bytecode.
2. Resolve configuration and checkout through bounded config-only tasks queries.
   No task-body scan, freshness repair, registry parsing, lock acquisition or write.
3. Construct the complete session text before exporting or printing success.
4. If `CLAUDE_ENV_FILE` is set, append `export AGENT_PROFILE=<comma-joined names>`.
5. Print the prepared text only after both rendering and export succeed.

The package exposes `resolve(path, env, payload=None)` and `session_text(result)`,
plus `ProfileError`. Ordinary results retain checkout/path/worktree/project, records,
layout, notes, profiles, home, keys, fragments, private_projects and warnings.
`kind` is `checkout` or `records-store`; `records_store` is the store root or null.
Each effective key has a value and source. JSON omits internal otherwise explanations.

Ordinary stdout starts with one `profile:` line naming profile, source, home,
design-document destination, account and PR policy. Warnings, selected corpus
fragments, linked notes and private project listings follow as applicable. A
missing fragment remains a visible warning; an unreadable selected fragment fails
rendering without a successful export.

## Records store

Canonicalize to the main Git checkout first. Only `status: unregistered` with
`records_store` equal to that canonical root identifies the shared records store.
This also handles store subdirectories and linked Git worktrees. A distinct nested
code repository with a parent-store marker, or ordinary in-tree tracker, keeps
checkout behavior; no extra `tasks where` classification query is needed.

Store results have null project and design_docs value `not-applicable`, sourced
from `tasks records store`; this sentinel cannot be configured on a profile.
Account/identity and selected-name export still come from ordinary profile selection.
Store sessions begin `profile: records-store` and load `profiles/records-store.md`,
including core attribution/task-id rules and the one-branch/no-worktrees/locked
`tasks commit` rule. Code-placement prose, linked notes and private listings are
not delivered there. Policy enforcement remains a separate consumer's responsibility.

## Failures and verification

CLI errors are nonzero. Every handled hook failure is exactly one flattened
`profile: unresolved` line with explicit-path recovery advice, and exit 0.
Rendering/export failures emit no successful profile text. Exit 0 therefore proves
nothing: activation requires comparing a fresh session's actual profile, home,
account, PR policy, placement prose and launcher advice against recorded expectations.
The existing exception boundary does not catch SystemExit or KeyboardInterrupt.

Self-contained tests run on CI without private ops. `just test-live` runs
`tests/test_profile_tasks_live.py` against installed tasks and fails if it is absent;
its temporary registry, records and Git config are isolated. Hosted suites declare
`LORE_TEST_LIVE_TASKS=unavailable`, printing the explicit integration skip reason;
any other marker value errors, and test-live unsets it.

The explicit local acceptance command is `scripts/profile-parity.py --ops-root PATH`,
where PATH is the registered ops root. It checks every registered checkout present
on the host, lists unavailable ones, rejects present-resolution failures and
unexplained differences, and compares effective definitions. Ops and lore's private
copies can diverge after acceptance until program piece 1.5 retires the old copy;
check does not promise synchronization. Live hook/global-instruction activation and
bounded rollback require a separate concrete user grant. See the task's frozen plan
and activation packet for exact revision/rollback evidence.
