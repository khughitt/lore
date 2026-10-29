# Instruction assembly

Type: operations guide; document types 1. How to build, check and diagnose the
delivered global instructions. Field definitions for the catalog and manifest are
in [instruction-formats.md](instruction-formats.md); this guide does not repeat them.

## What it produces

`bin/assemble-instructions` is the only writer of the delivered pair:

- `instructions/AGENTS.md`: the fragments named by `instructions/assembly.toml`,
  in catalog order, joined by one newline. hq links it into every harness home.
- `instructions/AGENTS.manifest.json`: which source produced which bytes, with
  hashes and the evidence behind each fragment. Provenance stays out of the
  delivered text.

Lore owns the policy fragments in `instructions/fragments/`. Ops owns the
Projects/Feedback-owners fragment (`instructions/fragments/projects.md` in the ops
checkout), generated there by `just projects`. Never hand-edit either output.

## Commands

| Command | Effect |
| --- | --- |
| `just assemble` | `bin/assemble-instructions write`: render both files and replace them atomically. Refuses a symlinked or non-regular output. |
| `bin/assemble-instructions render` | Print the artifact; `render --manifest` prints the manifest. Writes nothing. |
| `bin/assemble-instructions check` | Read-only verification; `just check` runs it. |
| `check --working-tree` | The same check against files on disk, whatever is staged. |
| `--owner-root PREFIX=PATH` | Read one external owner from another checkout, such as a prepared ops worktree. |

Typical change: edit a fragment or the catalog, run `just assemble`, then stage the
artifact, the manifest and the source change together. An edit to the assembler
itself also changes the manifest's `assembler` entry, so assemble and stage the
manifest in the same commit.

After an ops change to project identity: run `just projects` in ops, then
`just assemble` here.

## Owner roots

`lore` is always the checkout running the assembler. Every other owner a fragment
or evidence pointer names, `lore:records` included, is looked up in the tasks
registry. An `--owner-root` override must name an external owner the catalog
declares, once; `lore` cannot be overridden. For `write` and `check` the override
must be a checkout of the registered repository (same Git common directory), and
`check` announces each override on standard error. Repository-local Git variables
a hook exports are stripped before reading any other owner's repository.

## What check verifies

In order: the catalog's format; every evidence pointer resolves at its full commit
to a file blob; every source reads; the committed mandatory set is preserved and
each source has the required shape; the ops Projects input equals what `ops-projects render`
prints on this host (skip with `--skip-projects-render`); the selected artifact and
manifest equal a fresh rendering.

Which view is checked: when the staged changes include the catalog, artifact,
manifest, assembler, anything under `instructions/fragments/`, or a lore-owned
source the staged catalog names, the whole prospective index is checked; otherwise
the working tree. In the index view, the executing assembler must be byte-identical
to its staged copy, so a pre-commit check cannot pass with an unstaged assembler
edit. External owners are always read from their checkouts.

## Historical proofs

Two read-only proofs show that the assembler reproduced, byte for byte, the global
instructions as they stood before assembly existed (`verify-baseline`) and the
first assembled artifact (`verify-initial`). Each loads the assembler and proof
driver from the recorded lore revision, renders that revision's catalog and
sources, and compares the result with an independent pinned Git blob. They run
during acceptance and audits, not in `just check`; current policy edits do not
affect them.

| Input | Value |
| --- | --- |
| Lore proof revision | `f6d5acc2bc88523e4ac9ff18a5bfd6ea42f396b4` |
| Ops revision (initial proof) | `3c176f25455291abb1eaf2d0fe917f16b7be797d` |
| Extraction revision (baseline reference) | `49568066eeb8a6b4a09e453a10e81fade87919e7` |
| Baseline reference | blob `5297be329c58bc758b20c48a504a87887be5470a`, SHA-256 `66f5ae3d32e218ac3688969171179501ecdcc253e4d9a01f48c05ddb04350642` |
| Initial reference | blob `08bd5862dcd0fa47000dac7f13e8617875f99586`, SHA-256 `2729ca9ae116c50501a65764af73b4729498df283407f8b6a5a5e98e15cc2760` |

Prerequisites: a lore checkout whose history contains the proof revision, and a
registered ops checkout (tasks registry) whose history contains the ops revision.
From the lore checkout:

```sh
python3 bin/assemble-instructions verify-baseline --revision f6d5acc2bc88523e4ac9ff18a5bfd6ea42f396b4
python3 bin/assemble-instructions verify-initial --revision f6d5acc2bc88523e4ac9ff18a5bfd6ea42f396b4 \
  --projects-revision 3c176f25455291abb1eaf2d0fe917f16b7be797d
git merge-base --is-ancestor f6d5acc2bc88523e4ac9ff18a5bfd6ea42f396b4 HEAD
git merge-base --is-ancestor 49568066eeb8a6b4a09e453a10e81fade87919e7 HEAD
```

In the ops checkout, `git merge-base --is-ancestor 3c176f25455291abb1eaf2d0fe917f16b7be797d main`
checks the ops revision's ancestry. Each proof prints `<mode> proof passed: lore <revision> … sha256 <hash>` and exits 0.
Add `--owner-root ops=<checkout>` to read a different checkout of the registered
ops repository.

## Diagnosis

| Message | Cause and action |
| --- | --- |
| `artifact Projects block stale: …` | Ops's Projects input changed since the last assembly. Run `just assemble`. |
| `Projects input differs from this host's current project rendering …` | A project was registered, renamed or retired. Run `just projects` in ops, then `just assemble`. |
| `artifact stale; …` / `manifest stale; …` | A lore source, the catalog or the assembler changed. Run `just assemble`. |
| `executing assembler differs from index; …` | Stage the intended assembler or restore the index copy. |
| `missing or downgraded committed mandatory fragments: …` | A mandatory fragment was removed or made adaptable; restore it. |
| `invalid evidence OWNER REVISION:PATH: …` | The pointer's commit or blob cannot be read, or its revision is not a full commit id. Fix the pointer, or fetch the owner's history. |
| `X is not registered in the tasks registry` | Register the owner (`tasks init` in it). `--owner-root` works around it only for `render`; `write` and `check` require every owner, overridden or not, to be registered. |

The SessionStart notice from ops also reports a forgotten assembly after an ops
refresh.

## Creating and refreshing rule records

The authoring commands operate on working files and never stage files or imply
approval. The production coverage/manifest integration is tracked separately.

```
python3 bin/assemble-instructions add-rule git --start-line 3 --end-line 5 --title 'Commit style'
python3 bin/assemble-instructions refresh
python3 bin/assemble-instructions refresh rule:<32-hex-id> --selectors selectors.json
```

`add-rule` takes an inclusive unmarked source range in a local catalog fragment.
It mints an ID, inserts markers and creates a complete unknown record. Optional
`--split-from ID` or `--merged-from ID ...` records predecessor identities without
copying claims; retire replaced rules separately. For multiple ranges, work from
bottom to top so earlier line numbers remain stable.

Creation prints its ID before writes. Until both source and record are complete,
`instructions/rules/pending/<id>.json` retains the exact attempt. Retry with the
same arguments plus `--resume rule:<id>` after an interruption. A conflicting
request refuses; a missing previously committed record is corruption and must be
restored. Do not commit pending authoring files.

`refresh` selects changed marked rules by default. It appends revisions and moves
a clause only when its old exact quote occurs once. A selector JSON file maps a
clause ID to `{"text": "new exact quote", "offset": 10}` (UTF-8 byte offset) or
`{"retire": true}`. Missing or ambiguous quotes refuse before any record writes.
Retained revisions and claims stay intact; a rerun completes interrupted record
writes without duplicating revisions, including when selectors were supplied.

Both commands refuse staged changes to affected files, symlink outputs and invalid
records. Unstage the named files **keeping working edits**, refresh, inspect,
restage and rerun check. After authoring, record available proposal and approval
sources separately; exact-text adoption must bind the hash actually accepted.
Evidence-only changes need no refresh. Command execution is never adoption.

## Reading judgments in a target context

```
python3 bin/assemble-instructions provenance
python3 bin/assemble-instructions provenance --context claude.json --context codex.json --json
python3 bin/assemble-instructions provenance --tier high --warning unknown-origin
```

Context files follow `instructions/schemas/context.json`. Names are unique; model,
harness name/version, ordered instruction references/hashes and named environment
values are supplied explicitly. No shell values are inferred. Omitted context
means unknown runtime comparisons. Relevant staged inputs select the index;
`--working-tree` explicitly selects disk. JSON stdout is a deterministic complete
report; human output names findings, actions, historical gaps and judgments.
Structural errors fail; warnings alone exit successfully.

An assessment's ordered `instruction_dependencies.items` select the comparisons;
its rationale explains the selection (including an empty list). Compare those
items, the subject hash, model, harness and every environment field it names.
Missing values or a snapshot inconsistent with local source are unverifiable.
Other instruction/artifact drift is informational. Matching inputs mean only
that no mismatch is recorded. Approval, applicability and measured effectiveness
remain independent; a negative experiment still counts as tested.

An evidenced human/user adoption of an exact current hash clears the actionable
origin warning for that subject. Historical authorship remains unknown when it
was unknown before. Scope authorization does not count. One review of a set's
exact texts may supply one adoption per hash; container adoption covers clauses
only when `covers_clauses` is true. A new hash needs new affirmation. Unknowns
never authorize removing an obligation.
