# Context selection

Type: data model, guide; document types 1. Covers the selection context (schema 1,
`instructions/selection-context.json`), the applicability file
(`instructions/applicability.toml`), the selection record (schema 1) and the `lore context`
commands. Selection runs in shadow only: no session or launcher reads a selection today,
and every session still receives the full `instructions/AGENTS.md`. The package is
`src/lore/context/`; the assembler and the manifest format are in
[instruction-formats.md](instruction-formats.md).

## What selection reads

Three committed files and nothing else: the delivered artifact `instructions/AGENTS.md`,
its manifest `instructions/AGENTS.manifest.json` (version 2) and `instructions/applicability.toml`.
It never reads fragments or the catalog and never calls `tasks`.

Before selecting, the reader verifies that the artifact's sha256 equals the manifest's
`artifact.sha256` ("run just assemble" when it does not), that every rule range starts at
a line start and ends with a newline, and that each range hashes to its manifest sha256.
Any failure refuses the selection.

When any of the three files is staged, the reader takes all three from the index (`git
show :<path>`); a file absent from the index is absent, whatever is on disk. Otherwise it
reads the working tree. Git calls on any repository other than the checkout `bin/lore`
runs from drop the variables `git rev-parse --local-env-vars` names, so a commit hook's
`GIT_DIR` or `GIT_INDEX_FILE` cannot redirect them.

## Selection context

A JSON document, schema 1. `facts` and `duties` may be left out; `{"schema": 1, "name":
"empty"}` is the empty context.

```json
{"schema": 1, "name": "band-worker",
 "assembled": {"by": "lore test fixture", "at": "2026-11-26"},
 "facts": {"actor.harness": {"value": "pi", "source": "band launcher"},
           "actor.shell": {"value": null, "reason": "hq records no shell fact for pi"}},
 "duties": {"held": ["edit-code"],
            "withheld": [{"duty": "worktree-lifecycle", "source": "band brief: \"Never create or remove worktrees.\""}]}}
```

Every fact is `{value, source}` or `{value: null, reason}`. A fact left out is unknown.
A known `false` is a known value. Names, types and values outside the vocabulary are
refused, never read as unknown.

| Fact | Type and values |
| --- | --- |
| `actor.harness` | claude-code, codex, agy, pi, opencode |
| `actor.model` | any name; used by no entry |
| `actor.role` | root, worker, reviewer, search |
| `actor.interactive` | true, false: whether a person reads this actor's messages |
| `actor.shell` | bash, zsh |
| `actor.skills` | native, shell, none: how the harness loads a skill |
| `actor.child_wake` | true, false |
| `target.project` | any prefix |
| `target.stage` | experimental, pre-release, supported |
| `target.profile` | list of names |
| `target.family` | guild, verifiably, none |
| `target.test_policy` | broad, off |
| `target.code_guide` | true, false: the root guide cites a code guide |
| `target.test_front_door` | true, false: the justfile defines `test-fast` |
| `host.host_budget` | true, false: `host-budget` is installed |
| `moment` | launch, session-start |

Duties say what the actor may do: `edit-code`, `commit`, `run-tests`,
`worktree-lifecycle`, `task-records`, `integrate` (push, merge, PR), `file-feedback`,
`trials`, `ask-user`, `dispatch` (launch child agents), `run-reviews` (request or run
review rounds), `host-services` (start persistent or detached processes), `desktop`,
`spend`. A duty is held, withheld (with the launcher's words that withhold it) or, in
neither list, unknown. A duty is never inferred from a role.

Two readings the entries rely on:

- `actor.interactive` is about who reads the actor's messages. A rule that also says what
  an unread actor writes in a task record, a ledger or a report to its controller is not
  covered by that test alone; such entries carry the governing duty as a second
  alternative.
- `worktree-lifecycle` covers creating a worktree, hydrating it, reporting a missing setup
  route, preparing its baseline and removing it, not only `git worktree add` and `remove`.

## Applicability file

One TOML table per rule: `[rule.<32 hex>]` names `rule:<32 hex>`. A rule with no entry is
always selected.

```toml
[rule.5b1c2e9a734c498fb8285b1eb1cba9cf]  # Shell syntax boundaries
when = [{ fact = "actor.shell", in = ["zsh"] }]
note = "Under zsh"
rule_sha256 = "d920966d…"

[rule.046dfb8c365f454a86390b6b4167e487]  # Read-only reviewers and saved reports
any = [
  { when = [{ fact = "actor.role", in = ["reviewer"] }] },
  { governs = ["run-reviews"] },
]
rule_sha256 = "1496d212…"
```

| Field | Meaning |
| --- | --- |
| `when` | Tests, all of which must hold. A test is `{ fact, eq = v }`, `{ fact, in = [...] }` or `{ fact, not_in = [...] }`. |
| `governs` | Duties the rule is about; holds when the actor holds at least one. |
| `any` | Alternatives, each with `when`, `governs` or both; holds when one holds. Not combined with top-level `when` or `governs`. |
| `accompanies` | For a lead-in: selected only with at least one listed rule. Carries no tests and lists no other lead-in. |
| `requires` | Rules selected whenever this one is. |
| `by` | The earliest decision the rule can change: launch, session-start or first-edit. Recorded; nothing uses it yet. |
| `note` | Why, for the reviewer. |
| `rule_sha256` | Required: the manifest hash of the rule text the entry was written against. |
| `reviewed` | The entry's review digest, present only once the user approved it. |

`eq` takes a scalar fact; `in` and `not_in` take a list. On a list fact (`target.profile`),
`in` holds when any element is in the set and `not_in` when none is.

## Evaluation

Per entry: if any fact a test names is unknown, or any governed duty is unknown, the rule
is selected (reason `unknown-fact`), whatever the other tests say. Otherwise the entry
holds when an alternative has all its `when` tests true and, if it has `governs`, one of
those duties held.

Over the corpus, in order:

1. P: every rule with no effective entry, every rule whose entry holds, and every lead-in.
2. C: P closed under `requires`, read from every entry in every review state. A rule
   restored this way has reason `required-by`.
3. A lead-in leaves when none of its companions is in C and no other rule in C requires
   it (`no-companion`). A rule required only by a removed lead-in stays.

Reasons in the record: `no-entry`, `stale`, `proposed`, `unknown-fact`, `entry-holds`,
`no-tests`, `required-by`, `test-false`, `no-companion`.

## Review state

An entry is `stale` when its `rule_sha256` no longer equals the manifest hash: the rule's
text changed. A stale entry omits nothing in any mode, and `check` reports it as a
warning, not a failure.

Otherwise it is `reviewed` when `reviewed` equals the digest of its canonical content:
every field but `reviewed`, `rule_sha256` included, plus the sorted list of rules whose
entries require it. Anything else is `proposed`. Live selection applies only reviewed
entries; shadow selection (`--shadow`) applies proposed ones too.

Because the digest covers incoming requirements, an approved requirement cannot be
dropped by an unapproved edit, in either direction:

- Removing `requires` from an approved entry, or removing that entry, returns the
  required rule to proposed, so it stays selected in live mode until reviewed again.
- Adding a new entry that requires an already reviewed rule also returns that rule to
  proposed until it is approved again.

`lore context approve RULE_ID...` writes the `reviewed` digests, directly after each
named table's header, and is the only command that writes. It refuses, writing nothing,
when `check` reports a problem, a named rule has no entry or its entry is stale. It runs
only for entries the user approved, in a change that cites the approval.

## Cutting

An omitted rule's lines are removed from the artifact. Everything else is kept, with two
exceptions next to a removal: a heading whose section lost rule text and keeps no rule
and no generated block is removed with that section's connective text, and a blank-line
run that a removal touched collapses to one blank line (none at the file's edges).
Headings and fences follow the assembler's patterns. With nothing omitted the output is
the artifact byte for byte, which `check` verifies for the empty context in both modes.

## Commands

All run against the checkout `bin/lore` runs from.

- `lore context select --context FILE [--shadow] [--json] [--record FILE]`: the selected
  text; `--json` prints the record instead; `--record` writes the record and prints the
  text.
- `lore context explain --context FILE [--shadow]`: one line per rule with decision,
  reason, rule id, bytes and the facts used, then the selected and artifact byte counts.
- `lore context check`: problems on stderr with exit 1; stale-entry warnings on stderr
  with exit 0. `just check` and the documentation-only pre-commit check run it.
- `lore context approve RULE_ID...`: see Review state.
- `lore context shadow-band --attempts DIR --fixture FILE [--json]`: the shadow selection
  for each recorded band attempt, with the fixture context plus target facts read at
  the attempt's branch point (`git show <branchPoint>:<path>`); unrecoverable facts are
  unknown. Markdown by default, JSON with `--json`.

Any refusal prints `lore context: <message>` and exits 1.

## Selection record

Schema 1, keys exactly:

| Key | Content |
| --- | --- |
| `schema` | 1 |
| `mode` | `live` or `shadow`; no live delivery may use a shadow record |
| `context` | the context as supplied |
| `corpus` | `artifact_sha256`, `manifest_sha256`, `applicability_sha256` (null when absent), as read |
| `selector` | `sha256` over the package's `src/lore/context/*.py` (relative path and file hash), `commit` (`git rev-parse HEAD` or null), `clean` (no change to the package or the three inputs) |
| `replayable` | true only when `selector.clean` and a commit is known |
| `rules` | per rule in artifact order: `id`, `decision` (`include` or `omit`), `reason`, `detail` (facts and duties used, unknown names, requiring rules), `bytes` |
| `output` | `sha256` and `bytes` of the selected text, `artifact_bytes` |
| `delivery` | null; filled by whoever delivers |

The record says what was selected and from what. It is not evidence that a session
received or followed the text.

## Checks

`lore context check` fails when a table key is not a live rule; a fact, duty, operator or
`by` value is outside the vocabulary; `eq` is used on a list fact or `in`/`not_in` without
a list; a test value is outside the fact's values; an entry mixes top-level tests with
`any`; a lead-in carries tests or lists another lead-in; `requires` or `accompanies`
names a rule that is not live; `requires` has a cycle; `rule_sha256` is missing; or the
empty-context selection differs from the artifact in either mode.

## Not built

No session, subagent or launcher receives selected text: delivery stays the full
artifact. Nothing is deferred to a later moment, `by` is recorded only, and no rule is
split. The selector reads no live state: every fact comes from the supplied context.
