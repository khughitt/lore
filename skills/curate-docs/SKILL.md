---
name: curate-docs
description: Use when asked to review, curate or audit a project's documentation (README, AGENTS.md, subsystem guides, docs/ reference documents) for drift, completeness or clarity (`/curate-docs`), or when a documentation-review task names the rubric; never part of the session protocol.
---

# curate-docs

**Rubric version 1.** The note names it, so a later pass can tell which criteria a
project was last judged against.

One pass judges one project's documents against the rubric below and records what it
found. It edits prose only to shorten or correct; every structural change, deletion of
a section, or addition of content is a proposal. It creates at most one task during
the review, the project's documentation review task, and never closes one. Invoke
deliberately:

    /curate-docs [--project <prefix>]

Default: the current project. The mechanical checks (`ops-docs check`, `ops-check`)
judge shape, regions, budgets and paths; this pass judges what they cannot: whether
the prose is true, complete for its reader, and earning its lines. A pass is
curation, not a review round of an artifact under approval: it writes no `review:`
outcome-measure note.

## 1. Root, revision, mechanical

1. **Root.** `--project` given: the root is the last column of that project's row in
   `tasks projects --paths --pretty`. Otherwise: the nearest ancestor of the current
   directory holding `tasks/.config.toml`. Every `tasks`, `git` and `grep` below runs
   in that root (`tasks -C <root> …`, `git -C <root> …`).
2. **Revision.** `git -C <root> rev-parse --short HEAD`; `git -C <root> status
   --porcelain`. The note records the commit and, when the tree has changes, `dirty:`
   with the covered documents among them or `none covered`. The pass judges the
   working tree.
3. **Mechanical first.** Run the project's vendored `python3 tools/ops-docs check`
   (ops itself: `python3 bin/ops-docs check`) and `python3 tools/ops-check`. Record
   each exit status and, when non-zero, one phrase per finding. A mechanical finding is
   not a rubric finding: it is fixed by `just docs` or by editing `identity.toml`,
   named in the note's `mechanical:` segment, and never hand-edited by the pass.

## 2. Documents covered

Read these whole, in this order; the note lists exactly what was read.

- **Root guides:** `identity.toml`, `README.md`, `AGENTS.md`.
- **Declared subsystem guides:** for each directory in `identity.toml`'s
  `subsystems`, its `identity.toml`, `README.md` and `AGENTS.md`.
- **Undeclared guides:** `git ls-files '*/README.md'` outside the excluded trees
  below (a README inside an excluded tree is not a candidate). One that is not a
  declared subsystem and reads as a guide (a layout, setup or usage section, not a
  pointer to the root guide) is covered under criteria 8 and 9, listed as `<path>
  (undeclared)`, and raises criterion 11.
- **Reference documents and user guides:** files under `docs/` that describe current
  behaviour and are not dated decision records. Excluded by directory, each named in
  the note with its reason: `docs/specs/`, `docs/plans/`, `docs/designs/`,
  `docs/notes/`, `docs/archive/`, `docs/superpowers/`, any dated filename (`2026-…`),
  and vendored trees (`tools/`, `vendor/`, submodules); an exclusion wins over a link
  from the README. Of what remains, read first the documents the root README links,
  then the rest by path, whole documents only, until 800 lines of reference documents
  have been read; list the rest under `excluded: unread` so the next pass starts there.
  Root and subsystem guides are always read whole and count against no budget.
  Criterion 10's git check is cheap and runs over every reference document, read or
  unread.
- **Authority documents:** each `identity.toml` `authority` path is read under
  criterion 2 alone, whatever directory holds it, including an excluded one: its head
  and status lines, not the body. Listed as `<path> (authority)`.

The global-layer project (lore, whose `instructions/AGENTS.md` is the file every
session loads) is read under every criterion for its README and under criterion 5
only for that generated file.

Drift is judged by reading the tree: `ls`, `git ls-files`, the justfile, the package
manifest, the module list. The pass runs nothing the judged documents describe: no
example, no test, no tool of the project beyond the mechanical checks in §1.

## 3. The rubric

Each criterion names its evidence and the verdicts it can produce. Verdicts are the
ones `curate` uses: `keep` (nothing to change), `refined` (edited in the pass; meaning
unchanged or a fact corrected), `stale` (the text contradicts the tree or its own
authority; proposal in the note), `decision` (a choice the human owns; proposal in the
note). A `refined` edit the pass may not make (§4) is recorded as `proposed` with the
edit. A pass that reaches no verdict on a criterion writes `not judged: <why>`.

A **finding** is one defect with one fix. Several documents sharing a defect and its
fix (six pages whose `updated` date lags, one check that would catch all six) are one
finding; two defects in one document are two; every `proposed` edit to one document is
one finding, since one docs commit makes them all. A finding may surface under more
than one criterion (a claim that is criterion 9 in the README and criterion 10 in a
runbook): each criterion's line in §6 names it, the note and the resolution carry it
once.

**Root guides (project-guides design §8):**

1. **Identity fits.** The purpose says what the thing is; the abstract says what it
   does and for whom; neither restates the other. Evidence: the two strings in
   `identity.toml`. `refined` with the rewrite, or `keep`.
2. **Authority is named and current.** Each `authority` path is the document that
   decides what is built, and its status line is not older than the last landed goal.
   The status line is the document's newest dated line of its own: a front-matter
   `updated` or `status` date, or the dated heading of its current-state section; a
   document with none is `not judged` here. The last landed goal is the newest `done`
   task whose record links the document (`tasks -C <root> list --status done --sort
   updated --plan <path>`, then `--ref <path>`); when none links it, the newest `done`
   task, and the verdict says so. `stale` naming the goal and the newer entry, `keep`,
   or `not judged` when the pass cannot tell whether the document was meant to record
   that goal.
3. **No status prose.** The root guides make no claim of the form "X is implemented",
   "as of <date>", "in progress", and carry no dated measurements that are history
   rather than guidance; in the README the rendered `ops:status` region is exempt. A
   failure a rule cites (a commit, task or cut id) is guidance, not status. Evidence:
   the text. `refined` when deleting a word or clause leaves true guidance; otherwise
   `stale` with the proposal: delete the claim and, when it says something the tracker
   or a dated note does not, file or move it there.
4. **Nothing the global layer already says.** No section restates the tasks skill, the
   worktree rule, the commit conventions, or a profile's instructions. Evidence: the
   text against the global `AGENTS.md` the session loaded and the tasks skill.
   `refined` with the section deleted and the line count saved. Text that fails here
   is not judged again under criterion 5.
5. **Every rule has a failure.** Each rule (a sentence under Rules) names, or the pass
   finds in `git log`, a retro note, or a task (`tasks -C <root> search "<phrase>"`,
   `grep -ril <word> tasks/`), the failure it prevents. A rule that states a boundary
   its authority document draws is `keep` when it cites that document. Evidence: the
   search. `decision`: the rule is a removal candidate for the human, never deleted by
   the pass.
6. **Budget earned.** A project over the default `AGENTS.md` budget with a declared
   raise still has every section pulling weight. Evidence: line counts by section.
   `decision` naming the sections a reader could lose, or `keep`.
7. **Projections agree.** README and `AGENTS.md` do not contradict each other on
   setup, gates, or layout. Evidence: the two texts. `refined` with the correction, or
   `stale` when the tree disagrees with both.

**Completeness and facts, every covered document:**

8. **Complete for its reader.** Four questions, answered from the document and what
   it links: can a reader tell what the project (or subsystem) is; get started; perform
   its main workflows; find the deeper reference for each? Evidence: the answers, with
   the link followed. `stale` or `refined` naming the missing orientation. Completeness
   is judged by these needs, not by enumeration: a README need not list sixty modules,
   and an unlisted directory is a finding only when a reader needs it for one of the
   four. A layout table that names one module of sixty misleads and is `stale`.
9. **Facts match the tree.** Every named path, command, recipe, module, package name
   and primary-implementation claim exists or holds in the tree. Evidence: `ls`,
   `git ls-files`, the justfile, the manifest. A contradiction is a defect: `refined`
   when one word corrects it (`npm install` where the lockfile and justfile say `npm
   ci`), `stale` when the claim needs rewriting. Wording the pass would merely prefer is
   never `stale`: it is `refined` when shortened in place, otherwise `keep`.

**Reference documents and user guides:**

10. **Updated by the change that altered its behaviour.** For each document: the last
    commit touching it (`git -C <root> log -1 --full-history --format=%h -- <doc>`,
    so a merge that resolved a conflict in it counts), then the commits since that
    touch the paths, commands or modules the document names (`git -C <root> log
    <that>..HEAD --stat -- <paths>`). Read each such diff. `stale` naming the
    commit when behaviour the document describes changed. A document whose own
    `updated` or status line is older than its last content change is `stale` under
    its own rule; an edit that only retargets a link or anchor is not a content
    change. `keep` otherwise.

**Coverage:**

11. **Guides are declared where they exist.** An undeclared guide (§2) means the
    mechanical checks never read it; that is how a stale subsystem README passes every
    gate. Evidence: `identity.toml` `subsystems` against the undeclared guides found.
    `decision`: declare the subsystem (its own `identity.toml`, `README.md`,
    `AGENTS.md`) or reduce the file to a pointer.

## 4. Edits

`refined` edits happen only when the pass runs in the project's own checkout, on the
branch the session works on, and land as one `docs:` commit through the project's own
gates. From another project (`--project`), the edit is recorded as `proposed` and
resolved like a `stale` finding (§5): the owning project edits its own tree. An edit
shortens or corrects; it never adds a section, reorders, or deletes a rule. A README
some test reads as input (grep `tests/` for its name) gets that test run before the
commit.

## 5. The review task and its notes

The project's documentation review task is the record every pass reuses. File or
find it with one idempotent command (same `--source` and title return the existing id
as `action: "reused"`):

    tasks -C <root> add "Documentation review" --source curate-docs --tag docs \
      -p 3 --size s --complexity low --process direct \
      -b "The reusable record of curate-docs passes over this project: one note per pass naming the rubric version, commit, documents covered, exclusions and findings by verdict; resolution of findings is recorded apart from the review. Never closed by a pass; ops owns its lifecycle."

It is the only task the review creates. Change nothing else on it: not status,
priority, or body. Then exactly one review note, one line, segments in this order. An
empty segment is omitted. `keep:` lists the criteria whose verdict was `keep` on every
document they judged; a criterion with mixed verdicts appears only under the others.
`unresolved` counts the `stale`, `proposed` and mechanical findings; decisions wait on
the human and are not counted.

    tasks -C <root> note <review-id> "curate-docs: rubric v1; commit <sha>[ dirty: <covered paths|none covered>]; mechanical: ops-docs <rc>, ops-check <rc>[: <finding>, …]; covered: <path>[ (undeclared|authority)], …; excluded: <dir>: <reason>, …[, unread: <paths>]; keep: <criterion numbers>; not judged: <criterion>: <why>, …; refined: <doc>: <what>, …; proposed: <doc>: <edit>, …; stale: <doc>: <what>, …; decision: <doc>: <proposal>, …; unresolved: <n>"

Review completion and finding resolution are separate states. After the review note,
for each `stale`, `proposed` and mechanical finding: reuse the open task that owns it
(`tasks -C <root> search "<distinctive phrase>"`, `tasks -C <root> list --tag docs`),
adding one note on it (`curate-docs: <review-id> at <sha> confirms: <what>`), or file
one in the owning project with `--source <review-id> --tag docs -p 3 --size xs
--complexity low --process direct`, sized up when the fix is larger. A closed owner is
not reused; when the finding shows that closed work fell short, the new task's first
note is the `concerns:` line the global instructions define. One task per finding as
§3 defines it; unrelated findings are never bundled. Then one resolution note on the
review task:

    tasks -C <root> note <review-id> "curate-docs: resolution; <doc>: <what> -> <task-id> (reused|filed); …; decision: <n> awaiting the human"

A `decision` finding is filed as a task only after the human rules on it; until then
it lives in the review note.

## 6. Summary to the human

One line per criterion: its number, verdict, and one phrase (or `not judged: <why>`).
Then the review task id and the commit judged. Then the decisions that are the human's,
grouped, omitting empty groups:

- **removal candidates** (criteria 5, 6): the rule or section, and what was searched;
- **declarations** (criterion 11): the directory, and the two options;
- **stale text** (criteria 2, 3, 7, 8, 9, 10): the document, the claim, the evidence,
  and the task that now owns it;
- **proposed edits** (from another project; criteria 1, 3, 4, 7, 8, 9): the document,
  the edit, and the task that now owns it;
- **questions**: anything the pass could not judge.

Nothing else. A pass with nothing in those groups says so in one line.

## Bounds

- The review creates one task at most, the review task. Findings become tasks in the
  resolution step, after the review note, one per finding.
- Read-only on the host: nothing from the judged documents is executed.
- Only covered documents are judged; a defect noticed in a decision record or a
  vendored file is named in `excluded:`, not judged. An authority document is the one
  exception, under criterion 2 alone.
- Prefer shorter. An edit that grows a document is a proposal.
- Keep defects apart from preference: `stale` is reserved for text the tree or its own
  authority contradicts.

## Rubric history

- **v1** (2026-10-23): criteria 1–7 from ops
  `docs/specs/2026-09-22-project-guides-design.md` §8, with criterion 3 widened from
  `AGENTS.md` to both root guides; 8–11 added for completeness by reader needs, factual
  drift kept apart from preference, reference documents, and undeclared guides. The
  ops documentation-review pilot applies v1 by hand; criteria that produce no
  actionable finding, or many false positives, are revised into v2 on its report.
