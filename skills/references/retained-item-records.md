# Retained item records

Type: guide, data model; document types 1. These unversioned fields are
lore-authored guidance, not a new tasks CLI or parser interface. Obs already
consumes the eight item fields; its recorded assertions are separate from current
filesystem inspection. A `retention checkpoint:` is opaque dated evidence unless
a consumer validates its exact basis. Read this when creating, refreshing or
releasing records. Existing process/service, Git removal, privacy and publication
rules still apply. No history rewrite, bulk backfill or migration is authorized.

## Record an item

Use `tasks note <id>` with `retained: ` followed by one complete JSON object for
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

An over-cap manifest stays losslessly retained off-tree pending tasks-b81063's
supported transport decision. Do not split, compress, raise caps or relabel a raw
blob as a records document to evade checks. A layout refusal keeps the existing
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

For an inaccessible item within the host being inspected, or an actually observed
missing file/hash mismatch, transition a formerly verified object to kept/unknown,
with null current digest and a verification action. If it was already unknown and
its action and retention terms are unchanged, do not repeat the full object.
Merely working on a different host causes no item rewrite. Other hosts' items keep
their last observations and their own dated checkpoints; this host makes no claim
to have reverified them. A newly learned problem on another host still gets an
explicit unknown object with its evidence and action, rather than hiding behind
host scoping. Preserve last-known hashes in history, never as current proof.

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
per-run copies. Checkpoint at park/done and verify recorded hashes before reuse,
especially before claiming an idle-host window or the user's machine.

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

Changed contents require a fresh complete manifest and its SHA-256, then a changed
container record. Incomplete enumeration or a missing/unreadable file makes the
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
as `manifest`; when this cannot pass size/layout checks, retain an immutable
off-tree file outside the inventoried container with an explicit evidence record.
This avoids recursively inventorying checkpoint metadata. Reuse the exact version
when contents are unchanged; do not create another manifest attachment at each park.
Keep manifests for as long as their checkpoint evidence is needed. A mutable
`manifest.json` alone cannot substantiate an old checkpoint after it is overwritten.

## Exact checkpoint and recovery

When there are no kept items on any host after verified dispositions, retain the
existing plain closeout note; do not add an empty checkpoint. If only another host
has kept items, name that host's last checkpoint and the needed verification in
the park summary; do not create an empty local checkpoint or reset its inventory.

Otherwise use one concise `retention checkpoint:` note for the inspected host per
completed park/done checkpoint. This is a fixed prose convention, not a new tasks
command; obs may expose it as opaque dated evidence, not infer freshness from it
without validating its basis. It contains:

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
incomplete checkpoint and park with a concrete recovery action. Never claim success
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

Checkpoint order: inspect; preserve changed evidence/manifest versions; write
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

Move/transfer order is unchanged: preserve and hash destination, record the
receiving kept identity, then release only the sending identity whose verified
disposition actually occurred. A partial transfer leaves both copies retained.
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
