# Retained item records

Type: guide, data model; document types 1. The current writer version is retention 1.
Every new retained object includes integer `version: 1`; historical unversioned
notes and examples remain historical. Tasks ships `tasks retained state`,
`checkpoint`, `transfer` and `reconcile` under this same writer version.
Obs explicitly recognizes v1 and historical input; recorded assertions remain
separate from current filesystem inspection. A `retention checkpoint:` is opaque dated evidence unless
a consumer validates its exact basis. Read this when creating, refreshing or
releasing records. Existing process/service, Git removal, privacy and publication
rules still apply. No history rewrite, bulk backfill or migration is authorized.

Tasks owns the command, request and receipt contracts: read `docs/retention.md`
(Query state; Requests and checkpoints; Transfers and reconciliation; Phase and
checkpoint envelopes; Failure, retry and result interpretation), linked from its
README, and the installed tasks skill's Retained-state queries section. Resolve
the owning checkout through `tasks projects`. This reference owns retention
semantics and the manual/recovery obligations below; it is not a second CLI spec.

## Record an item

Use `tasks retained checkpoint` for supported automated host accounting; it
publishes new or changed item records after inspection. For manual recording, use
`tasks note <id>` with `retained: ` followed by one complete JSON object for
a new item or changed fields. At park and before done, inspect and account for all
known kept worktrees, task scratch directories and off-tree evidence on this host.
Compare parsed fields with the immediate effective predecessor; do not repeat an
unchanged object. Use the host checkpoint below to date fresh inspection.

| Field | Meaning |
| --- | --- |
| `host` | Host name observed when recording the item. |
| `kind` | `worktree`, `scratch` or `evidence`. |
| `path` | Same-project worktree: main-checkout-relative, including `.worktrees/`. Foreign-project worktree: absolute on the named host. Scratch/evidence under storage: prefer literal `$WORK_ROOT/…`; otherwise absolute on that host. |
| `state` | `kept` or `released`. |
| `verification` | `verified` describes the last recorded observation; otherwise `unknown`. Never timeless or current proof. |
| `purpose` | Concrete remaining use, or the verified disposition for a released item. |
| `next_owner` | `task:<full-id>` of an open task; `session:<stamped-identity>` only within the integration window below; or `user` with `handoff`. Released items use `none`. |
| `cleanup_trigger` | Observable event after which the owner rechecks disposition, never “later” or “when safe”. Released items use `none`. |

For `next_owner: "user"`, add `handoff`: identify the existing agreement by
task-note timestamp or another durable reference and state the next user action.
Keep purpose separate; never invent the user's agreement.

For a verified kept evidence file, add `sha256` for its exact bytes. For a
verified kept scratch or evidence directory, add `manifest` (the manifest-file
path) and `sha256` (that file's hash). The manifest lists relative file paths
and their SHA-256 hashes, includes hidden files and records symlink targets
without following them. Keep checkpoint metadata outside the inventoried container. Unreadable contents prevent a complete
checkpoint. A live worktree has no content hash; Git state and ignored-file
inspection remain separate removal requirements.

`$WORK_ROOT` is a literal token, resolved only against the named host's declared
storage root, never arbitrary shell text to evaluate. The same path form applies
to `manifest`. Do not guess another host's root. Keep the recorded path spelling
stable: `(host, kind, path)` is the identity within the task record. Later notes
for that identity supersede earlier notes without editing history. For an old
absolute path converted to a token spelling, first verify both locate the same
item, write the new kept identity, then release the old as an alias replacement.

An absent, malformed or conflicting state means unknown and blocks reliance or
disposal. Never select a convenient valid predecessor to conceal a later conflict.
An old verified record remains a dated observation; freshness is unknown until
inspection. No bulk backfill or host audit is required. Keep observations separate
from retention intent; merge ancestry alone cannot prove an item disposable.

## Artifact placement

The task body holds intent, acceptance, scope and named references. Notes hold
decisions, changed facts, required audit entries, review outcomes and concise
checkpoint/next-action summaries. A short fact can stay inline; inventories,
transcripts, repeated tables and long reports belong outside note text. Do not
replace required review or attachment audit notes with an undocumented link.

| Artifact / descriptive reference kind | Destination and use |
| --- | --- |
| Small immutable evidence: `log`, `trace`, `image`, `dataset`, `manifest`, `review` | `tasks attach`; link useful artifacts with `files:<name>`. Use a new name for a changed version and verify the ledger, bytes and applicable checks. |
| Evolving human document: `brief`, `spec`, `plan`, `report`, `ledger`, `receipt`, `handoff` | Specs/plans follow the profile's established destination. Operational ledgers/receipts/reports use the task's declared records or overlay document home, under `docs/notes/`, only when that repository is an authorized destination for that content; otherwise retain them in persistent task storage. Pin review/checkpoint versions. A ledger/receipt has a short purpose, owner, status and evidence links, with detailed rows in the file. |
| Large, mutable or layout-refused raw evidence | Persistent task storage under the named host's declared `WORK_ROOT`, governed by ordinary retained-item records. Add an accessible summary or derivative, with exact raw location and hash discoverable on the task. |
| Current reusable instruction or contract | The owning project's reference documentation, rewritten as current behavior and typed under its adopted standard. A historical ledger does not become a reference merely by moving it. |

Reference `kind` is descriptive, so `manifest` and `receipt` need no CLI change
and confer no new validation or privacy exemption. The task references the current
working document for navigation; a checkpoint or review pins an exact historical
revision separately. The same artifact is not copied inline just because it has a
named reference. Cross-project task ids identify owners; use their own document
inventory, without inventing cross-project reference syntax.

Permission to commit design documents in a code repository is not permission to
commit operational ledgers there. In personal in-tree repositories, task-owned
operational documents may use the existing records convention. In work/external
repositories, use an authorized private records/overlay destination, or persistent
task storage with a concise permitted pointer; put operational content into the
code repository only when its instructions or the user explicitly authorize that
content. Neither a reference nor an attachment bypasses this destination check.
If no permitted durable pointer exists, resolve placement with the user before
publishing it. An ignored worktree copy alone is not a durable destination.

Choose a separate task when there is an independently actionable outcome, owner,
dependency, approval or retention lifetime. A long log or many rows alone is a
reason for an artifact, not task decomposition. A closed task cannot own retained
items: transfer to an open follow-up or an agreed user handoff as today.

For an over-cap UTF-8 manifest within the project's multipart limits, use the
shipped `tasks attach --multipart` route below. Only that route may split one
document: manual splitting, compression, raised caps and relabelling raw bytes as
records documents to evade checks remain forbidden. If admission or publication
fails, keep the exact source bytes and resolve the stated cause; an eligible
off-tree copy remains governed by the placement rules below. A layout refusal keeps the existing
raw-plus-portable fallback, with the mapping in a task note; only acceptance by the
executing shipped checker retires that fallback. Other refusals retain their own
diagnosis. Normal publication permission still applies in every destination.

## Changed observations

`verification` describes the result of the last recorded
observation of those item fields, not timeless or current verification. A kept
`verified` object may be old. The latest completed checkpoint for that host dates
re-verification of its unchanged fields; a later changed object invalidates that
checkpoint's coverage for that identity until another checkpoint. A record alone
still carries its own dated observation, but cannot assert a completed current
inventory. Release records remain dated verified dispositions, not fresh proof of
absence. Fresh inspection before reuse or disposal remains mandatory.

Read the latest complete valid object for each identity. Missing, malformed or
conflicting state remains unknown and blocks reliance or disposal; never pick a
convenient valid predecessor to conceal a later conflict.

At park/done, inspect all known kept items on the current host. Write a full new
object only for a new item or a change in its retention fields: purpose, owner,
trigger, verification state/action, digest, manifest, path/alias disposition or
release. Compare parsed fields, not JSON whitespace or field order. An unchanged
hash is a result of fresh inspection, not permission to skip reading bytes.
At park, done or disposal, the acting owner inspects the complete known local
retained set; delegated observations do not waive that obligation. An explicitly
delegated check may supply evidence, but the recording actor names the observer
and never describes another actor's observation as its own recheck.

For an inaccessible item within the host being inspected, or an actually observed
missing file/hash mismatch, transition a formerly verified object to kept/unknown,
with null current digest and a verification action. If it was already unknown and
its action and retention terms are unchanged, do not repeat the full object.
Merely working on a different host causes no item rewrite. Other hosts' items keep
their last observations and their own dated checkpoints; this host makes no claim
to have reverified them. A newly learned problem on another host still gets an
explicit unknown object with its evidence and action, rather than hiding behind
host scoping. Preserve last-known hashes in history, never as current proof.

For an intended file replacement, preserve the prior version before editing and
keep both exact versions recoverable through immutable attachments or retained
copies. Inspect the intended replacement bytes, preserve that version, then record
its new verified digest. An unexpected mismatch, unavailable prior evidence or
unverifiable replacement instead stays unknown with a verification action. Merely
knowing that a write occurred does not verify its bytes or preserve its predecessor.

Timestamp and provenance of a legitimate new observation move to the checkpoint
summary below, even when the item's fields did not change. An item that changes
away and later back still gets both transitions; equality to an old historical
record is not grounds to suppress a change from the immediate predecessor.

Existing independently recorded evidence remains independent. This guidance does
not silently fold old identities into a container or mark an existing copy released
because a manifest mentions it. A later explicit migration needs a reviewed
coverage/ownership transfer that preserves old state history; that operation is
outside this guidance delivery and belongs with the supported migration route.

## Unknown observations

For an actually inaccessible item on the inspected host, a newly learned remote
failure, missing hashes or mismatches, use `state: "kept", verification: "unknown"`. Include
`verification_action`: why the observation is uncertain and what its next owner
must check. Set the current `sha256` to JSON `null` for a file/directory and
`manifest` to `null` if none can be located. Preserve the last known path,
expected hash and mismatch diagnostics in earlier notes, or a separate diagnostic
note when newly discovered; never promote an old hash into a current claim.

Missing contents do not release an item. A missing or mismatched checkpoint
blocks use or disposal of that copy, not recording the problem. After verification,
supersede with a verified record and fresh hashes, omitting `verification_action`
once resolved. This exception represents uncertainty; it does not waive checks.

## Creation, scratch and evidence

When creating `$WORK_ROOT/<project>/<task-id>/`, immediately make a plain task
note with host, path, purpose and current task owner, saying contents are mutable
and not yet checkpointed. Do not fabricate a hash. If `WORK_ROOT` is absent,
ask the user where persistent storage belongs rather than inventing a root.
Keep canonical multi-session inputs on that persistent storage; tmpfs holds only
per-run copies. For a changing plan workspace or task scratch/evidence directory,
content additions or edits (new reports, ledger appends, ordinary handoffs) do not
themselves trigger a complete manifest or checkpoint; generate the complete manifest
and checkpoint at real park, done or disposal boundaries. Reuse after interruption
or compaction checks the specific canonical input bytes needed before relying on
them, especially before claiming an idle-host window or the user's machine, without
an unsolicited whole-container manifest.

A scratch/evidence-directory record covers newly retained contained files by
default when they have the same purpose, next owner and cleanup trigger, and the
manifest completely covers them. Hidden files are included; symlink targets are
recorded without traversal. A symlink does not retain or verify its target's bytes.
No mandatory directory migration is introduced.

Give a file/subdirectory an independent evidence record when its purpose, owner,
trigger, lifetime, uncertainty or disposition differs; an independently required
raw copy in the layout fallback is also explicit. Its bytes still appear in the
container manifest, but the specific item's retention intent overrides inherited
container terms. A parent owner cannot release a child owner's evidence.

At a park, done or disposal checkpoint, changed container contents require a fresh
complete manifest and its SHA-256, then a changed container record. During active
work between checkpoints, an in-progress mutable container has changed since its
last checkpoint; that earlier checkpoint is historical and must not be claimed as
current proof. Immediate creation notes and changes of owner, purpose, disposition
or observed uncertainty still get recorded when they occur, and frozen review
inputs, preserved replacement versions, attachment verification and domain-specific
integrity checks still happen at their own required boundaries. A child task's
`done` is a done boundary for the child's own retained set; it does not
automatically checkpoint a container that remains owned by an open parent.
Ownership must be real and recorded, never transferred merely to avoid a required
checkpoint. Incomplete enumeration or a missing/unreadable file makes the
container checkpoint unknown; independently verified files may keep their own
verified records. A container never claims complete verification over an unreadable
exception. Before removal, every manifest member and independently retained item
must have a verified disposition; existing Git/attachment checks still apply.
One container release can record a common verified disposition for all members it
covers, naming the exact manifest version and any exceptions. It does not require
one release note per inherited file. Independently recorded items still need their
own releases; unresolved exceptions block removing the enclosing container.

For new work, prefer a stable evidence subdirectory apart from changing working
files when that matches their retention purpose; do not force an existing directory
migration. This helps only the stable subdirectory's manifest: the parent scratch
record still inventories the complete scratch container, including working files,
and every changed parent checkpoint still incurs a full manifest. This design
accepts that cost instead of introducing incremental manifests or silent exclusions.

Preserve each manifest version used by a checkpoint. Prefer a small immutable
attachment, with its digest in the container record and its actual storage path
as `manifest`. For an over-cap text manifest use the multipart procedure below;
when attachment is unavailable, retain an immutable
off-tree file outside the inventoried container with an explicit evidence record.
This avoids recursively inventorying checkpoint metadata. Reuse the exact version
when contents are unchanged; do not create another manifest attachment at each park.
Keep manifests for as long as their checkpoint evidence is needed. A mutable
`manifest.json` alone cannot substantiate an old checkpoint after it is overwritten.

### Multipart manifests

Tasks owns the command and admission contract: read `docs/attachments.md`
(Multipart text and catalog version 1; Publication, reservations and removal;
Export and current validation; Multipart validators), linked from its README.
Attach one whole UTF-8 source with
`tasks attach <id> <path> --multipart`, or stream it into
`tasks attach <id> - --name <name>.json --multipart`. Use a new logical name for a
changed version. The installed route preserves exact bytes as bounded parts plus a
catalog, each under the ordinary per-file cap; defaults limit one artifact to
16 MiB and 16 parts, not cumulative history. The project must declare
`multipart_validators`: absent refuses admission; `[]` explicitly declares no extra
whole-document gates. Built-in JSON validation is not Manifest 1 schema or complete
filesystem-coverage validation; perform those checks too, and preserve all normal
content/layout and publication-permission requirements.

Inspect the attach result's `publication.state`, not just its exit status:

- `published` binds reconstruction and current validation to `publication.commit`.
  Preserve the task, logical `files:<name>` reference, whole-file byte count and
  SHA-256, full publication commit and returned `validation` object in checkpoint
  evidence. Confirm `tasks show` declares the logical artifact and its digest.
- `local` is an incomplete publication even on exit 0. Resolve its `cause` and
  follow `next`; commit where needed and verify the resulting named commit with
  `tasks export <id> <name> --at <commit> --verify`. Inspect both integrity and
  `validation.passed`, preserving that current-runtime validation result. A local
  save or a working-tree-only export cannot complete the publication requirement.

There is no whole-file storage path: neither a part nor the catalog is the
manifest. Recover exact bytes with
`tasks export <id> <name> --at <commit> -o <destination>`, and compare their hash
with the pinned whole-file SHA-256 before use. Export checks integrity; it does not
run current validators unless `--verify` is requested. Rebuilds and validator input
are in memory; file export writes atomically beside the destination. Keep any
materialized copy outside the inventoried container. A per-run copy may be removed
after its exact bytes and durable publication are verified; preserve the logical
locator and commit so it can be reconstructed before the next inspection.

V1 item records still use an actual inspected file path in `manifest`, with the
whole-file digest. Record the immutable multipart locator and export instruction
separately on the task; do not put `files:<name>` or a catalog path into that field.
Reconstruct the pinned manifest before reusing such a record. Native retained
checkpoint/transfer commands still use ordinary attachment caps and do not
automatically transport oversized manifests. Use the existing manual procedure
only where supported; never bypass a pending operation or publication failure.
Published manifest bytes satisfy preservation, not the remaining item verification,
exact-basis, ownership and complete-checkpoint obligations.

## Exact checkpoint and recovery

When there are no kept items on any host after verified dispositions, retain the
existing plain closeout note; do not add an empty checkpoint. If only another host
has kept items, name that host's last checkpoint and the needed verification in
the park summary; do not create an empty local checkpoint or reset its inventory.

Otherwise `tasks retained checkpoint` publishes a JSON `retention checkpoint:`
envelope for supported automated accounting. The prose procedure below remains
the manual/recovery route: use one concise `retention checkpoint:` note for the
inspected host per completed park/done checkpoint. Historical prose is opaque dated
evidence unless its exact basis is validated. The manual note contains:

- Observation time in UTC and the inspected host.
- A **basis**: task-record repository identity, full commit and repository-relative
  task path, after all changed item records and referenced artifact versions have
  been committed. That exact record prefix defines membership, including unchanged
  items; a count or timestamp alone does not.
- Counts of this host's kept verified, kept unknown and released identities in that basis,
  plus how many objects changed in this pass. Counts refer to explicit identities,
  not each inherited member of a container.
- The statement that all kept/verified identities on the inspected host were
  rechecked, while kept/unknown identities remain unverified with the actions in
  their basis records. Other hosts are outside this observation; retain their own
  dated checkpoint evidence without rewriting their records. State failures/next
  actions briefly; detailed diagnostics are linked.

Example (values are placeholders):

```text
retention checkpoint: observed <UTC> on <host>; basis <task-record repository identity> <full commit>:<task path>; retained by <branch ref>; this host: kept verified 2, kept unknown 1, released 0; changed 1. Rechecked all kept/verified items on this host; unknown items remain unverified with actions in basis. Other hosts retain their own dated observations. Next: verify the inaccessible copy before reuse.
```

The **task-record repository** is the Git repository holding the task file, not
necessarily the code repository or the shared records repository. Its portable
identity consists of the task project prefix, the observed `tasks where` layout
(`in-tree`, `detached` or `linked`), and that project's records-directory path
relative to the containing Git root (`.` for an in-tree project). Resolve through
that project's registry pairing; the full commit and task path must exist in the
resolved repository. In-tree work uses the task's recorded worktree for current
state and `tasks/<id>.md`; detached lore uses `lore/tasks/<id>.md` in the shared
records Git root; a linked project uses its overlay's containing Git repository,
never the foreign code checkout. If a pairing or layout moves, explicitly record
the verified new locator for the same history; do not silently try another repo.

Write the checkpoint with `tasks note <id> "<checkpoint>" --stamp`, then inspect
the resulting note and warnings. Copy resolved session attribution as reported;
if resolution fails or no stamp is present, explicitly record observer attribution
as unknown, never infer it from the branch-valued `by` field or promise a guaranteed
session stamp. The observation and exact basis remain evidence with that stated
attribution limit. A basis commit pins the
inventory without copying it or inventing a canonical JSON hash. Keep it reachable
from a named, retained branch, recorded with the checkpoint. Shared records use
their one branch. For in-tree/overlay feature branches, preserve the branch until
integration keeps the basis in ancestry (a fast-forward or merge commit); verify
ancestry before branch deletion. After verified integration and deletion of the
named feature branch, resolve and check reachability from the repository's default
branch. If integration used a different branch, record that surviving ref explicitly
and retain it until default-branch ancestry is verified; never guess a replacement
ref from a missing name. This changes no integration authorization.

Before rebase, amend, squash or abandonment would remove that reachability, retain
the old basis on a named preservation branch with an open task owner and cleanup
trigger, or preserve an equivalent immutable snapshot and its artifact versions.
Record a preservation branch in a plain task note: task-record repository identity,
full ref, protected basis commit, open task owner and observable cleanup trigger.
Do not invent a `branch` retained-item kind; the existing supported kinds remain
`worktree`, `scratch` and `evidence` unless a separately reviewed consumer change
adds another. The note is discoverable from the checkpoint's owning task.
After rewriting, create a fresh checkpoint at the new basis before relying on it.
A fresh checkpoint alone does not preserve the historical one. Keep the old ref or
snapshot while that history is needed; never rely on a reflog or unreachable Git
object. If unexpectedly lost, report recovery unknown rather than reconstructing
an asserted observation from today's files. No rewriting is authorized here.

If records are not Git-backed, use an immutable attached snapshot of the
inventory with source note order/stamps, snapshot name and SHA-256 instead; obey
caps and normal checks. If neither exact basis can be preserved, record an
incomplete checkpoint and park with a concrete recovery action. Complete and
incomplete checkpoints both begin with the exact lowercase prefix `retention checkpoint:`.
Use this incomplete form (replace each angle-bracketed placeholder with the observed
UTC time, inspected host, reason the basis is unavailable, and concrete recovery action):

```text
retention checkpoint: incomplete; observed <UTC> on <host>; basis unavailable: <reason>; Next: <concrete recovery action>.
```

Obs keeps the entire checkpoint opaque, including any blocker text. Record a cleanup
blocker needing classification in a separate ordinary note. Never claim success
from an unbound count. Records Git history must not be rewritten/discarded while
checkpoints depend on it without preserving an equivalent verifiable snapshot.

Recovery starts at the task: locate the latest checkpoint **for the item's host**,
retrieve its exact basis,
replay retained objects in their original order, and resolve the latest state per
identity. Retrieve pinned manifest/document/attachment versions and verify hashes
before using them. Inherit terms only for eligible container members; preserve
independent exceptions. Apply later changed-item notes in order to obtain current
intent; only a later completed checkpoint for that host establishes another full
observation of that host's set. For hosts without a checkpoint, keep dated item
observations visible and report full-checkpoint freshness unknown.
The prior checkpoint stays a historical observation, never current proof after
intervening changes or an interrupted pass.

For a versioned records document, give repository, commit, path and byte hash;
for an attachment, task, exact name and byte hash. A named reference alone is a
mutable navigation pointer. A missing commit, detached attachment, absent raw copy,
digest mismatch or conflicting evidence is an explicit recovery failure, not
permission to fall back to today's working file or delete anything.

## Writes, interruption and migration boundary

The following manual checkpoint and transfer procedures remain available where
automation is unsupported, including an unsupported-mode refusal before durable
intent. Do not use them to bypass a pending lifecycle reservation or a validation/
publication failure: resolve that failure through the owning contract, recovering
or reconciling a published operation first.

Manual checkpoint order: inspect; preserve changed evidence/manifest versions; write
changed item objects; commit and check the basis; append the checkpoint; then
park/done. With `[git] commit = true`, use the successful auto-commit of the last
item/artifact write, or the existing committed state if nothing changed; do not
manually recommit task notes. Confirm bytes landed when the CLI reports a commit
warning. Without auto-commit, commit the task record through its normal workflow.
Before appending, run `git log <basis>..HEAD -- <task path>` in the task-record
repository, inspect any listed task changes and uncommitted changes to the task
and referenced evidence, and confirm no item-state or evidence-reference change
has occurred since the basis; unrelated task notes do not invalidate it. Respect
the claim and existing Git write coordination. If state changed, inspect that
change and choose a new basis. This guidance provides no atomic filesystem snapshot:
unstable files are unknown and must be settled before a verified checkpoint.

After interruption, reuse a published artifact only after checking its exact bytes
and live ledger; repair an unnoted attach with the supported retry route. Changed
item notes without the final checkpoint remain valid observations but do not imply
the whole set was verified. Resume from them, inspect afresh and finish a new
checkpoint without blindly re-appending unchanged objects. A checkpoint written
before an interrupted park remains historical evidence; retrying park after new
changes requires a new checkpoint.

Move/transfer order is unchanged: preserve and hash destinations, then write all
receiving kept objects with `tasks note <receiver> --stdin < receiving.txt`.
Each input line is one complete `retained: {…}` note for an independent identity.
The CLI validates every line before saving once in input order, with one commit
when record commits are enabled; empty input or any invalid line (including a
blank or whitespace-only line) writes nothing and an invalid-line error names
its line number. Verify all receiving kept records landed, including committed
bytes when required, before writing the sending released objects with
`tasks note <sender> --stdin < released.txt` in the same format. Release only
sending identities whose verified dispositions actually occurred; preserve each
identity and its history. These are two separate writes, not a cross-task
transaction. A partial transfer leaves both copies retained.
Attachment of a derivative never releases raw bytes. A trigger is a recheck event,
not deletion permission. Closed tasks, merged branches and missing files grant none.

History externalization requires a separately supported and authorized route that
preserves exact notes/provenance, protected attachment/lifecycle entries and
checkpoint bases through retries/concurrent writes. This guidance authorizes no
history mutation.

## Who acts after done

At park, the current open task may remain next owner; name its next action.
Keep tasks open across an activation/merge approval gate so they can continue
owning their worktree if approval is delayed or declined.

For immediate integration after approval, the closing session may own only
items it will dispose of before its current turn ends. Use the exact identity
from either the `started`/`resumed` note this session just wrote through
`tasks start`, or a fresh note this session creates:

```sh
tasks note <id> 'Identify the current integration owner' --stamp
tasks show <id>
```

Copy that note's `harness_session` verbatim after `session:`. A stamp
`codex:<thread-id>` becomes `session:codex:<thread-id>`; a stamp
`claude-code:<uuid>` becomes `session:claude-code:<uuid>`. Do not strip or repeat
the existing harness prefix, use a model name, concatenate raw environment
variables or choose a historical note by guesswork. `harness_session_source`
explains where tasks found the identity; it is not another owner string.
If this session's just-written note cannot be identified, emit a fresh stamp.
If no current stamp can be established, use an open follow-up or agreed user
handoff instead of inventing a session identity.

Record session ownership before done, with the trigger authorized integration
and checked removal. Commit done on the branch before merge. Once an authorized
merge brings the closed record into main, run the existing removal checks,
remove the item, then write its verified released note on the task's main-checkout
record. Closed records may receive lifecycle notes without reopening implementation.
This window grants no new merge, activation or removal permission.

Any item still retained before park or the closing session's final report needs
an open follow-up task or an already agreed user handoff. A stopped or blocked
post-done integration ends the window: supersede session ownership before yielding.
When no handoff exists, file the smallest follow-up beside the closing task and
link both records; do not create an open child that prevents completion or silently
assign the user. A closed task cannot be its own actor. If interrupted before
handoff, the session record remains an unresolved blocker, never assumed cleanup.

A cleanup trigger is a reason to reassess, not deletion permission. Done, merged
ancestry, expired dates or missing notes alone prove neither finished work nor
expendable evidence. The next owner refreshes or releases the record when its
trigger occurs, even if the original task is closed.

## Release, move or transfer

Independently recorded items require their own disposition. One common container
release may cover inherited members at its exact pinned manifest, naming exceptions;
unresolved independent items block parent removal. Only a verified disposition may
have `state: "released"`. Retain the identity,
set `verification: "verified"`, describe what actually happened in `purpose`
(removed, attached under a named attachment, transferred to a named task, or
verified alias replacement), and set `next_owner` and `cleanup_trigger` to
`"none"`. No new hash is needed; old evidence remains in history.

A moved item gets a verified kept record at its destination before releasing
the old identity. A transfer releases the sending task's record only after the
receiving task contains the kept record. Attaching a derivative does not release
the raw source, and attaching raw bytes does not mean an off-tree copy was removed.
Release the identity of the copy that actually went away; otherwise it stays kept.

## Attachment layout refusal

Until the project's executing ops-check admits a verified ledger-backed attachment
carrying host values, handle a layout refusal without bypassing any check:

1. Preserve exact raw bytes in the task's persistent directory; verify the copy
   before removing another. Record it as evidence with path, hash, purpose, owner
   and trigger.
2. Make a separate portable derivative, replacing every offending host value
   with a named placeholder. Its caption says it is a derivative and points to
   the raw item record. Write the placeholder-to-original mapping in a task note
   identifying that raw item, never in the portable attachment; task notes are
   exempt from the layout check. Existing privacy/publication permission still applies.
3. Attach normally, verify `tasks show` lists it and run the existing checks.
   Do not disable checks, broaden exemptions, overwrite the only raw copy or
   call the derivative verbatim evidence. Other refusals need their own resolution.

This fallback ends for a project only when an implemented exemption ships and its
executing checker accepts the original ledger-backed attachment through normal
checks. Completing ops-941e4f's design does not ship the exemption. If rejected,
the fallback remains. Shipping an exemption never deletes old raw copies: their
owner may attach verified raw bytes and then record the ordinary disposition.
Layout acceptance grants no publication permission or privacy exemption.

## Quoting-safe example

Replace the example values with the actual task and item. The prefix is note
text; only the object following it is JSON. The quoted heredoc preserves both
apostrophes and literal `$WORK_ROOT` tokens in zsh/bash, and the outer quotes pass
one complete note argument:

```sh
tasks note lore-b1044d "$(cat <<'EOF'
retained: {"host":"host-a","kind":"worktree","path":".worktrees/example","state":"kept","verification":"verified","purpose":"Await the user's frozen spec review","next_owner":"task:lore-b1044d","cleanup_trigger":"After approved work is integrated, inspect evidence and run the removal checks"}
EOF
)"
```


## Retention 1 contract (active writer version)

This section specifies the active reader and writer contract. Following the
authorized cutover after obs-50bfe3 landed and passed the frozen shared fixtures,
all newly written retained objects use integer `version: 1`, including notes
written by agents by hand. There is one current writer version.
The shipped tasks CLI uses the same version; its delivery causes no second cutover.
Stale sessions must refresh the reference before writing after activation.
Historical notes and the examples above are never rewritten or silently stamped v1.

The structural contracts are [record schema](retention-v1-record.schema.json) and
[manifest schema](retention-v1-manifest.schema.json). Portable positive/negative
examples live in [cases.json](../../tools/fixtures/retention-contract/cases.json).
Each case names its kind, exact raw JSON, structural verdict and separate semantic
expectation. Consumers parse strict JSON, rejecting repeated keys and non-JSON
constants before schema validation. Unknown fields, versions and wrong types
(including boolean/string versions) fail; no unknown version passes as an older
subset. Structural acceptance alone grants no filesystem or cleanup verdict.

### Records and semantic checks

V1 adds only `version` to the eight required item fields above, preserving their
meanings and identity `(host, kind, path)` within a task. Cross-task operations
also identify the task. Conditional fields remain `handoff`, `sha256`, `manifest`
and `verification_action`. Verified worktrees have no content digest; verified
evidence files have their exact digest; scratch/evidence directories require a
complete manifest and its digest. Because `kind: evidence` does not distinguish
files from directories, the consumer must require `manifest` when the observed
item is a directory, and verify the digest against the appropriate bytes.
Unknown data has a null current digest and a concrete verification action; unknown
directories name their last located manifest or explicitly use null if none is
located. An unknown worktree has the action and no content digest. A verified
successor omits the resolved action. User ownership requires a durable agreement
and next action in `handoff`; syntactically nonempty text does not prove agreement.
Task owners must be open; session ownership must meet the integration window.
Released v1 records use verified disposition, owner/trigger `none`, and omit
current digest/manifest, action and handoff; earlier evidence stays in history.

The schemas check field shapes, not agreement, open-task status, host accessibility,
full directory enumeration or verified disposition. Those are consumer obligations.
Recorded path spelling remains stable; tokens are never evaluated as shell text.
Relative worktree paths begin `.worktrees/`; foreign worktrees are absolute;
data and manifest locations are absolute or begin literal `$WORK_ROOT/`.
Converting an alias requires the explicit verified transition described above.

A malformed later note blocks reliance on the predecessor it could supersede.
When identity is unavailable, mark the affected host scope incomplete, or the
whole task if the host is unavailable. A correction cites the bad source note;
diagnostics remain visible. Historical unversioned records retain their provenance
and original interpretation under an explicitly supported historical reader.
Unsupported historical forms fail visibly, never acquire v1 authority by inference.

### Manifest 1 and exact retrieval

A v1 manifest is `{ "version": 1, "entries": [...] }`. Each entry has a unique,
normalized relative `path` and a `type`: `file` with `sha256`, `directory`, or
`symlink` with literal `target`. Include hidden entries and empty directories.
Paths have no absolute/drive prefix, backslashes, empty components or `.`/`..`
components. Symlink targets may contain traversal text because they are recorded,
never followed. A symlink does not retain target bytes. Reject duplicate member
paths, unsupported special files, unreadable or unstable entries, and incomplete
enumeration. Duplicate paths and complete filesystem coverage are semantic checks,
not enforced by these structural schemas. Serialize entries in path order; hash
the exact saved UTF-8 bytes, without treating formatting as a digest substitute.

Keep every checkpoint's manifest version outside its inventoried container, with
locators for every exact payload version. Each reviewed report version uses a
distinct immutable member path; the ledger binds it to review round, reviewer and
reviewed input revision. Before replacing/deleting members, preserve needed old
bytes in immutable attachments or retained copies. A manifest cannot recover lost
payloads. Retrieve pinned history, manifest and member bytes; any missing version
or mismatched digest is a recovery failure, never permission to use the latest file.
Existing independent identities remain exceptions with their own disposition,
even while their bytes occur in the complete enclosing manifest.

If the entire task directory already has a scratch identity, no descendant path
can hold its off-container manifest. Use a verified attachment outside that
container; for an over-cap manifest within admission limits, use the explicit
multipart route above. Generate it as a stream or a per-run copy outside the
container, require publication at a named commit and pin its whole-file digest
and validation evidence before completing the manual checkpoint. Recover the
pinned bytes outside the container before inspection; no new persistent storage
root or metadata exclusion is needed. An admission, layout or unresolved
publication refusal keeps evidence retained and the checkpoint incomplete; it
does not authorize another storage root or excluding metadata from the manifest.
Full hashing of all parent members remains
required at each changed checkpoint, including reports; fewer records save no bytes
hashed by themselves.

### Derived history and shipped operations

A current-state query is derived from complete logical note history, including
verified archive segments, at an immutable published basis. Name contract version,
repository/layout, full commit and task path (or the supported immutable non-Git
snapshot), host filter, completeness and diagnostics. Locate source notes by ordinal
within that pinned history, not timestamp alone. Dirty/unstable history cannot
claim a committed basis. Expose recorded intent and dated observations separately
from fresh filesystem inspection. A history query makes no implicit current or
remote verification claim. Caches are disposable and revision-keyed, never a second
editable ledger. Unaffected rows may be exposed with diagnostics; incomplete scope
never supports successful verification or cleanup.

The shipped state query requires a Git basis. Lifecycle mutations require
Git-backed auto-commit records (`[git] commit = true`), a named retained branch,
normal owned claims and exact current input bases. They support in-tree, detached
and linked records, including transfers between records repositories, and inspect
only the executing host. Use one coordinated writer host for every participating
task; prevent other-host writes until completion or reconciliation has committed
and records have synchronized. Claims and locks are host-local, not cross-host
coordination. Non-Git queries and non-Git/manual-commit mutations refuse explicitly;
the manual snapshot and publication procedures above remain their recovery route.

Tasks owns the shipped operation envelopes and implementation.
The CLI validates claims and committed bases and publishes durable intent before
mutation. An operation ID binds its parsed request, input revisions, selected
identities and requested terms; reuse with different inputs refuses. Retry the
original immutable request after interruption. Durable receipts live in history
or referenced immutable evidence; losing a local journal cannot erase transitions.
Keep receipts and exact referenced payload/manifest versions while needed.

Checkpoint order remains inspection, payload/manifest preservation, changed objects,
published exact basis, complete checkpoint, then park/done. The shipped machine
checkpoint preserves time, host, observer
(or explicit unknown attribution), exact basis, scope, counts, changed count,
unresolved actions and operation ID, discoverable by `retention checkpoint:`.
Only the lifecycle command publishes machine operation/checkpoint notes; do not
forge them through `tasks note`. Historical prose checkpoints stay opaque unless
their exact basis is validated. Complete accounting with unknown observations is
`accounted_unknown`, not verification of those items. The command never parks or
closes the task.
A retry inspects published history and bytes, completes missing phases and never
repeats a committed transition merely because its reply was lost. Reinspect for
a new observation; interrupted inspection is not a complete checkpoint. A completed
retry returns historical publication references without inspecting current bytes;
later accounting needs a fresh operation and input bases.

Ownership transfer and physical relocation are distinct. Verify and durably
publish the receiver's kept identities plus exact payload/manifest references
before releasing the sender; ownership-only transfer never implies moving or
deleting bytes. Receiver-only progress remains visible and resumable. Conflicting
receiver state refuses release. Select independent exceptions explicitly.
Serialize competing operations, check intervening changes before publication,
and refuse stale bases, competing intents, uncertain durability or synced-write
conflicts. A claim is neither a filesystem snapshot nor a cross-host lock.
Pending operations reserve task/evidence mutation while allowing reads, unrelated
appended notes, normal claim refresh/start and park. Finish the original operation
or explicitly reconcile it before closure or competing changes. Reconciliation
keeps custody, records unknown observations and verifies all participant ready
commits before ending the reservation through the coordinator terminal. It never
completes the requested checkpoint/transfer or releases bytes. A committed sender
release requires finishing the original transfer's receipts; reconciliation refuses.
Malformed history stays blocked for explicit repair. Unsupported cases and uncertain
publication fail visibly; normal permission, attachment and hygiene gates remain.

Full byte verification remains required at checkpoint, transfer, canonical reuse,
frozen-input validation and disposal. Metadata change detection is not integrity
verification. No incremental hashing or relaxed scrub policy is introduced.


## Execution workspaces (active placement)

This override of superpowers execution setup, task loop, resume, review packaging
and cleanup is active following the approved lore delivery. Existing workspaces
are not moved or folded. For new executions, create
one workspace at `$WORK_ROOT/<project>/<owning-task-id>/plans/<plan-key>/` on the
current host's declared persistent storage. Specs/plans stay in their profile's
authorized destination. Missing or inaccessible storage requires resolution, never
a guessed alternate root. Record host, literal path, owning task, plan repository
and path, and initial frozen revision in a task creation note immediately. A basename
collision needs a deliberately distinct key; resume reads the existing mapping.
Plan revisions do not silently change the key or workspace.

The open controller/standalone task owns the container. Children cite it without
copying its retained identity; independently owned outputs remain explicit exceptions.
Group only matching purpose, owner and cleanup trigger. Complete manifests include
all members and exceptions; directory membership grants no disposal authority.
A containing task directory is a namespace unless already independently recorded
as scratch, in which case its complete-manifest duties and nonrecursive metadata
placement still apply. Keep the owner open across review and activation gates.

Resolve lore's registered checkout once through `tasks projects`; use its explicit
`bin/plan-task-start` and `bin/plan-task-done` paths. They are lore-owned scripts,
not installed plugin modifications. Call from the implementing code worktree:

```sh
"$LORE_ROOT/bin/plan-task-start" "$WORKSPACE" "$PLAN" "$N"
# Read the printed brief and preserve the printed BASE before changing code.
"$LORE_ROOT/bin/plan-task-done" "$WORKSPACE" "$PLAN" "$N" "$BASE" -- just test-one <focused arguments>
```

Here LORE_ROOT is the resolved checkout, WORKSPACE is the exact recorded per-plan
directory, PLAN is the frozen plan file, and N is its positive task number. Create
and record the empty workspace before starting. Start binds the canonical `PLAN`
path in `$WORKSPACE/plan-path` and the ledger header, checks ledger identity,
captures BASE once and extracts a digest-named brief via the pinned `task-brief`
script's explicit OUTFILE. `PLAN` remains bound to that canonical path recorded at
start: when resuming or calling `plan-task-done` from another checkout (such as
`main` after integrating a worktree branch that started with a relative in-tree
plan path), verify the plan bytes match and pass the recorded `$WORKSPACE/plan-path`
value rather than a relative path that resolves to the new checkout. Resume reuses
BASE and preserves old briefs when a reviewed plan revision changes. Read the new
brief; a hash-shaped name is not permission to skip frozen-input verification.
Start fails for an unmarked occupied directory, another plan's ledger, or BASE
outside HEAD ancestry.

Completion runs the required command in the implementing worktree and preserves
its actual status and full output in a new attempt log. Failure appends an attempt,
never a completion. Success adds the task completion at BASE..HEAD; repeated
success at that HEAD keeps fresh attempt evidence without duplicating completion.
A correction at a new HEAD is checked again. The caller must first satisfy the
rest of the execution skill's completion contract: all expected results, meaningful
focused tests under the invoking checkout's policy, mandatory hygiene and committed
implementation. A zero exit from a policy skip is not test evidence; pass the
protected focused route, never a disabled broad target. Inspect the attempt log
and ledger on resume; a leftover log or lost tool reply alone proves nothing.
These local scripts assume one acting controller, not a distributed writer lock.

Do not invoke the pinned `sdd-workspace`, `task-start` or `task-done` for an external
workspace, and do not symlink its old worktree path. For subagent task briefs and
all task/corrective/final review packages, pass the external OUTFILE explicitly to
`task-brief` / `review-package`. This includes calls shown in execution references
and reviewer prompts. Give every review version a distinct report/package name,
then bind reviewed input, round, reviewer and member locator in the ledger. Keep
existing reviewer ownership and report-handoff rules; this changes no review gate.

Worktree removal follows the recorded external mapping, verifies the owner's
ledger is still reachable, and leaves that workspace retained. Workspace disposal
is separate: preserve required ledger rulings/deferred minors on the owner task,
resolve every manifest member and independent exception, and perform ordinary
verification and disposition checks. Neither a clean review nor a code-worktree
removal authorizes deletion of the external evidence.

Retire this interim route only after the installed and pinned upstream release
supports the generic root setting and its returned path matches the recorded
workspace. Upstream issues #1991/#2398 and closed PR #1999 are prior art; neither
the proposed variable name nor its `/sdd` suffix is promised here. A different
resolved path needs a separate migration decision, not a second ledger. No vendor,
plugin cache, shared launcher or host configuration is changed by these scripts.
