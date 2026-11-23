# Profile delivery

Type: protocol; document types 1. Currently unversioned. The SessionStart hook
`hooks/claude-profile` delivers the checkout's profile layer to Claude Code or Codex,
and the relay notice subscriber `lore hook profile-notice` delivers the same text
through relay. Changing its inputs, text or export changes this protocol on every
surface.

## Ownership and invocation

Instructions apply in order: assembled core, profile, repository instructions,
then the user. Lore owns the resolver in `src/lore/`, the thin `bin/lore` launcher,
the hook and the prose in `profiles/`. Tasks owns assignment/placement metadata and
its resolver. hq owns hook wiring and continues invoking main's hook; a worktree's
hook is used only by explicit path during preparation.

`lore` has no PATH install. From this checkout, use `./bin/lore profile` with one of:

| Subcommand | Result |
| --- | --- |
| `resolve [PATH] [--json]` | Effective values and sources, optionally JSON |
| `explain [PATH]` | Human-readable values with provenance |
| `session [PATH]` | Complete delivered profile text |
| `check` | Configuration/catalogue diagnostics; nonzero for problems |
| `list [--json]` | Every profile name the public and private definitions declare, sorted, one per line; `--json` prints `{"profiles": [<name>, ...]}`. A configuration lore cannot load (unparseable or invalid definitions, lore unregistered, a tasks failure) exits 2 with one `lore profile:` error on stderr |
| `audit [PATH]` | Existing design documents hidden by excludes or retained in code |

`./bin/lore hook profile-notice` and `./bin/lore hook stale-notice` are relay notice
subscribers ([Relay subscribers](#relay-subscribers)), not commands for people.
`git-identity-check` is the one command installed on `PATH`
([Commit identity check](#commit-identity-check)).

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

Profile output also shows the starting checkout's stage and its records source.
Absent or invalid stages remain unresolved. Dispatchers resolve the projects
whose files will change and put those stages in the review brief. A session
reads the supported workflow reference on demand according to its target stage,
trial assignment and scoped safeguards.

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

## Relay subscribers

Relay's notice role (relay `docs/adapters.md`, Notice protocol) runs a subscriber
named by a command basename on `PATH`; relay owns native decoding and reply encoding.
lore provides two SessionStart notices through its launcher, with argv
`["lore", "hook", "profile-notice"]` and `["lore", "hook", "stale-notice"]`. Each
reads one relay schema-2 `SubscriberEnvelope` on stdin (strict UTF-8 JSON object, at
most 4 MiB, no duplicate keys, `type: "event"`, a schema-2 `session-start` event with
an absolute `cwd`) and writes exactly `{}` or `{"context": TEXT}`. The launcher
resolves its own tree, so a host symlink to a checkout's `bin/lore` runs that checkout.
Installing `lore` on `PATH` and listing the subscribers in relay's configuration are
host and harness-settings changes: hq generates the settings, and each activation
needs the user's go-ahead at that moment.

| Command | Input used | Reply |
| --- | --- | --- |
| `profile-notice` | `event.cwd`, the valid `event.private.transcriptPath` fact, the environment | the hook's stdout above as `context`, byte for byte, with the same export |
| `stale-notice` | none beyond validation | `{}`, or the stale-instructions report as one line ([instruction assembly](instruction-assembly.md#diagnosis)) |

The profile notice maps `transcriptPath` to the hook's `transcript_path`; a missing
or invalid fact means no transcript. It never exits nonzero: an invalid envelope, a
resolution or export failure, a package that cannot load, and text over relay's
10,000 UTF-16-unit context limit each become one `profile: unresolved` context line,
so the session sees the failure instead of a dropped notice.

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

Live hook/global-instruction activation and bounded rollback require a separate
concrete user grant.

## Commit identity check

`git-identity-check [PATH]` (launcher `bin/git-identity-check`, package module
`lore._identity_check`) refuses a commit whose author or committer is not the selected
profile's `git_identity`. The global git config declares it as the hook
`hook.identity-check` on the `pre-commit` and `pre-merge-commit` events and calls it by
name, so `just install`, run in the main checkout, links it into `~/.local/bin`; the
recipe refuses a linked worktree. Repointing that link is a host change made only with
the user's go-ahead at that moment.

Without PATH it judges the repository git resolves from the environment, an inherited
`GIT_DIR` included, which inside a hook is the one being committed to. With PATH it
judges that checkout, whatever repository the environment names. It resolves the
profile in-process through `resolve()`, never by spawning `lore`, and the resolver never
sees a repository-local git variable. The expected identity never comes from git config.

| Exit | Meaning |
| --- | --- |
| 0 | Both identities match, or the repository is not judged |
| 1 | One stderr finding per mismatched role, naming where git took each wrong field (a config file and scope, the environment, `--author`, `EMAIL`, or git's system default) |
| 2 | It cannot judge: an unresolvable profile, a tasks failure, an unreadable registry, a package that cannot load. Never a pass and never a traceback |

Git refuses the commit on 1 and 2. A repository is not judged when its profile comes
from lore's default (`profile default`: scratch repositories, test fixtures, and the
records store, which no path rule covers), or when `tasks resolve lore` reports lore unregistered: a sandboxed
`XDG_CONFIG_HOME` whose registry lacks lore prints one `not judged` notice and passes.
A registry tasks cannot read is never a sandbox. `OPS_IDENTITY_AUTHOR=allow` lets a
deliberately foreign author through; any other non-empty value cannot judge, and the
committer is always judged. The variable keeps its earlier name, from when ops owned the
check, so existing runbooks and habits still apply. To commit past the guard once:
`git -c hook.identity-check.enabled=false commit …`.
