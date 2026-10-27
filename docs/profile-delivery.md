# Profile delivery

Type: protocol, currently unversioned. It describes how the SessionStart hook
`hooks/claude-profile` puts a checkout's profile layer in front of a Claude Code or
Codex session. Changing what it reads, prints or writes changes this protocol for
every harness at once.

## Layers and owners

A session's instructions stack in this order, later layers winning:

1. Core: the assembled global instructions, `instructions/AGENTS.md` (see
   [instruction-assembly.md](instruction-assembly.md)).
2. Profile: the text this protocol delivers.
3. The repository's own instructions (`AGENTS.md`, `CLAUDE.md`).
4. The user in the session.

| Part | Owner |
| --- | --- |
| Profile fragment text, `profiles/<name>.md` | lore |
| The hook, `hooks/claude-profile` | lore |
| Profile selection, keys and homes (`profiles.toml`, `identity-mirror.toml`) and the resolver `bin/ops-profile` | ops |
| Hook wiring in each harness home (Claude Code `settings.json`, Codex `hooks.json`) | hq |
| The registry, `$XDG_CONFIG_HOME/tasks/projects.toml` | tasks |

hq declares the hook as a `SessionStart` command (Claude Code matches `startup` and
`resume`) and runs it through the main lore checkout's path, so a worktree's hook or
fragments are never delivered.

## Exchange

Inputs:

- Standard input: the harness's hook payload, a JSON object. The hook reads `cwd`;
  the resolver reads `transcript_path` to tell which harness home is running. Input
  that is not JSON, or not an object, is treated as no payload.
- Environment: `XDG_CONFIG_HOME` (else `~/.config`) locates the registry; the
  hook reads `CLAUDE_ENV_FILE`; the resolver reads harness variables such as
  `CLAUDE_CONFIG_DIR` and `CODEX_HOME`.
- Working directory: used as the checkout path when the payload has no `cwd`.

Sequence:

1. Read the registry's `[projects] ops` entry and load that checkout's
   `bin/ops-profile` as a module.
2. Call its `resolve(path, env, payload)`. Selection, layout and warnings are the
   resolver's; `ops-profile explain` shows each value's source.
3. Write `session_text(result)` to standard output.
4. If `CLAUDE_ENV_FILE` is set, append `export AGENT_PROFILE=<names>` to it, the
   selected profile names joined by commas.

Standard output, in order:

- One session line: `profile: <names> (<source>); home: <home|unknown>; design docs:
  <clause>; gh: <account>; PRs: <policy> — <precedence note>`.
- `records: …` when the checkout is linked to an overlay project.
- One `warning: …` line per resolver warning (an unexpected home, a missing
  fragment file, lore not registered).
- Each selected profile's fragment, read from the registered lore checkout's
  `profiles/`, after a blank line.
- The linked overlay's notes and any `### Projects under this profile` list, when
  the resolver supplies them.

## Failure behaviour

The hook must never block a session. Its exit status is always 0 and is not
evidence of success; verify a change by the text a fresh session shows.

| Failure | Output |
| --- | --- |
| Registry missing, unparsable, or without an `ops` string entry; resolver fails to load | `profile: unresolved — <reason>; register or repair the ops checkout, then run ops-profile session` |
| Resolver raises its configuration error or a registry `ValueError` | `profile: unresolved — <reason>; run ops-profile session after fixing it` |

Intended invariant: every failure produces exactly one `profile: unresolved` line.
Known gap in the current implementation: any other exception (for example an
unreadable fragment file while composing the text, or a failed append to
`CLAUDE_ENV_FILE`) is caught only at the top level, so the hook exits 0 with no
`unresolved` line, and in the second case after the profile text was already
printed. Treat a session that shows no profile line at all as this case.
