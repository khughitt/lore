# Retained item records

Type: guide, data model; document types 1. The record fields are currently
unversioned: they are lore-authored guidance, not a parser's format or a new tasks
CLI interface. Read this when creating, refreshing or releasing a task's
retained-item record. Existing process/service, Git removal and publication rules
still apply.

## Record an item

Use `tasks note <id>` with `retained: ` followed by one JSON object per item.
At park and before done, account for every known worktree, task scratch directory
and off-tree evidence copy left on a host. Inspect the current host; explicitly
carry other hosts' unverified observations forward. Refresh resource and wait
descriptions from observations. If nothing remains, a plain closeout note suffices.

| Field | Meaning |
| --- | --- |
| `host` | Host name observed when recording the item. |
| `kind` | `worktree`, `scratch` or `evidence`. |
| `path` | Same-project worktree: main-checkout-relative, including `.worktrees/`. Foreign-project worktree: absolute on the named host. Scratch/evidence under storage: prefer literal `$WORK_ROOT/…`; otherwise absolute on that host. |
| `state` | `kept` or `released`. |
| `verification` | `verified` after current inspection; otherwise `unknown`. |
| `purpose` | Concrete remaining use, or the verified disposition for a released item. |
| `next_owner` | `task:<full-id>` of an open task; `session:<stamped-identity>` only within the integration window below; or `user` with `handoff`. Released items use `none`. |
| `cleanup_trigger` | Observable event after which the owner rechecks disposition, never “later” or “when safe”. Released items use `none`. |

For `next_owner: "user"`, add `handoff`: identify the existing agreement by
task-note timestamp or another durable reference and state the next user action.
Keep purpose separate; never invent the user's agreement.

For a verified kept evidence file, add `sha256` for its exact bytes. For a
verified kept scratch or evidence directory, add `manifest` (the manifest-file
path) and `sha256` (that file's hash). The manifest lists relative file paths
and their SHA-256 hashes, includes hidden files, excludes itself and records
symlink targets without following them. Unreadable contents prevent a complete
checkpoint. A live worktree has no content hash; Git state and ignored-file
inspection remain separate removal requirements.

`$WORK_ROOT` is a literal token, resolved only against the named host's declared
storage root, never arbitrary shell text to evaluate. The same path form applies
to `manifest`. Do not guess another host's root. Keep the recorded path spelling
stable: `(host, kind, path)` is the identity within the task record. Later notes
for that identity supersede earlier notes without editing history. For an old
absolute path converted to a token spelling, first verify both locate the same
item, write the new kept identity, then release the old as an alias replacement.

An absent, malformed, conflicting or stale record means unknown, not permission
to delete. No bulk backfill or host audit is required. A future inventory must
keep observations separate from retention intent; merge ancestry alone cannot
prove an item disposable.

## Unknown checkpoints

For inaccessible items, remote observations not verified now, missing hashes
or mismatches, use `state: "kept", verification: "unknown"`. Include
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

Use one retained record per item, without a mandatory directory migration.
The task directory is a scratch container; each retained evidence file or
subdirectory inside it has its own `evidence` record, purpose, owner, trigger and
hash. The scratch manifest covers all contents, including separately recorded
evidence, and is refreshed after changes at each checkpoint.

Evidence can outlive the experiment or task. Never remove a container while it
holds an unreleased item: first verify preservation and record its destination
or attachment. Keeping the whole container solely for evidence is valid when
its purpose and trigger say so. Do not discard the only needed raw evidence
copy or unfinished work. Give each item a disposition under the existing rules:
authorized discard, verified attachment or retention with a current record.

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

Only a verified disposition may have `state: "released"`. Retain the identity,
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
