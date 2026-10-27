# Instruction assembly

Type: operations guide. How to build, check and diagnose the delivered global
instructions. Field definitions for the catalog and manifest are in
[instruction-formats.md](instruction-formats.md); this guide does not repeat them.

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

## Diagnosis

| Message | Cause and action |
| --- | --- |
| `artifact Projects block stale: …` | Ops's Projects input changed since the last assembly. Run `just assemble`. |
| `Projects input differs from this host's current project rendering …` | A project was registered, renamed or retired. Run `just projects` in ops, then `just assemble`. |
| `artifact stale; …` / `manifest stale; …` | A lore source, the catalog or the assembler changed. Run `just assemble`. |
| `executing assembler differs from index; …` | Stage the intended assembler or restore the index copy. |
| `missing or downgraded committed mandatory fragments: …` | A mandatory fragment was removed or made adaptable; restore it. |
| `invalid evidence OWNER REVISION:PATH: …` | The pointer's commit or blob cannot be read, or its revision is not a full commit id. Fix the pointer, or fetch the owner's history. |
| `X is not registered in the tasks registry` | Register the owner (`tasks init` in it) or pass `--owner-root`. |

The SessionStart notice from ops also reports a forgotten assembly after an ops
refresh.
