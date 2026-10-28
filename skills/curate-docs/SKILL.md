---
name: curate-docs
description: Use when asked to review, curate or audit a project's documentation (README, AGENTS.md, subsystem guides, docs/ reference documents) for drift, completeness or clarity (`/curate-docs`), or when a documentation-review task names the rubric; never part of the session protocol.
---

# curate-docs

**Rubric version 4.** The note names it, so a later pass can tell which criteria a
project was last judged against.

One pass judges one project's documents against the rubric below and records what it
found. It edits prose only to shorten or correct; every structural change, deletion of
a section (except one criterion 4 finds restated from the global layer), or addition
of content is a proposal. It creates at most one task during the review, the project's
documentation review task, and never closes one. Invoke deliberately:

    /curate-docs [--project <prefix>]

Default: the current project. The mechanical checks (`ops-docs check`, `ops-check`)
judge shape, regions, budgets and paths; this pass judges what they cannot: whether
the prose is true, complete for its reader, and earning its lines. A pass is
curation, not a review round of an artifact under approval: it writes no `review:`
outcome-measure note.

## 1. Root, revision, mechanical

1. **Where.** Resolve the project through the tracker, never by walking the tree.
   `--project` given: that project's row in `tasks projects` (JSON) carries `checkout`,
   the code checkout, and `records`, where its task records live. Otherwise `tasks
   where` prints the same two fields for the project the current directory belongs to.
   They differ for a linked project, whose registered root is a records overlay. Every
   `git`, `ls` and `grep` over code and guides, and every mechanical check, runs in the
   checkout (`git -C <checkout> …`); every `tasks` command runs from it too (`tasks -C
   <checkout> …`, which opens the linked project where there is one); a read of record
   files uses `<records>/tasks/*.md`.
2. **Revision.** `git -C <checkout> rev-parse --short HEAD`; `git -C <checkout> status
   --porcelain`. The note records the commit and, when the tree has changes, `dirty:`
   with the covered documents among them or `none covered`. The pass judges the
   working tree.
3. **Mechanical first.** Run the project's vendored `python3 tools/ops-docs check`
   (ops itself: `python3 bin/ops-docs check`) and `python3 tools/ops-check`. Record
   each exit status and, when non-zero, one phrase per finding. A mechanical finding is
   not a rubric finding: it is fixed by `just docs` or by editing `identity.toml`,
   named in the note's `mechanical:` segment, and never hand-edited by the pass.

## 2. Documents covered

Read these in order; the note lists exactly what was read. Root and subsystem
guides are read whole; reference-document sampling is defined below.

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
  then the rest by path, with an 800-line reading budget for reference documents.
  Read documents of at most 300 lines whole when they fit the remaining budget. For
  longer documents, read complete sections in document order while they fit; record
  the headings and line ranges actually read under `covered:` and the remaining
  ranges under `excluded: unread`. If the next document or section cannot fit, stop
  reference reading and leave the rest unread. The next pass reads previously unread
  material before resuming the README-first order. A section over 800 lines stays
  unread and is named under questions as needing a separately scoped read. For every covered
  document over 300 lines, name the sections read, even when all were read.
  Root and subsystem guides count against no budget. Criteria 8–10 judge only read
  sections; an unread portion receives only criterion 10's self-date check (last
  content change against its own `updated` or status line), not a behaviour judgment.
  A partial read never establishes that the whole document is complete or current.
- **Authority documents:** each `identity.toml` `authority` path is judged under
  criterion 2 alone, whatever directory holds it, including an excluded one: its head
  and status lines, not the body. Listed as `<path> (authority)`.
  For criterion 3, consult relevant intent passages in linked authority and task/source
  records as evidence; that read does not add excluded documents to the judged coverage.

The global-layer project (lore, whose `instructions/AGENTS.md` is the file every
session loads) is read like any project for its root guides, and under criterion 5
only for that generated file. Its provenance audit is `docs/instruction-provenance.md`
in lore's records directory (`tasks where` in lore names it); use it as evidence,
checking the current rule.
A finding names the owner and source in `instructions/AGENTS.manifest.json`:
lore-owned rules resolve to their `instructions/fragments/` source; the Projects /
Feedback owners fragment resolves to ops, whose identity declarations and renderer
own it. A rendered copy in lore does not make lore its owner.

Drift is judged by reading the tree: `ls`, `git ls-files`, the justfile, the package
manifest, the module list. The pass runs nothing the judged documents describe: no
example, no test, no tool of the project beyond the mechanical checks in §1 and
the tracker and acknowledgment commands in §5.

## 3. The rubric

Each criterion names its evidence and the verdicts it can produce. Verdicts are the ones
`curate` uses: `keep` (nothing to change), `refined` (edited in the pass; meaning
unchanged or a fact corrected), `stale` (the text contradicts the tree or its own
authority, or omits an orientation its reader needs, criterion 8; proposal in the note),
`decision` (a choice the human owns; proposal in the note). A `refined` edit the pass may
not make (§4) is recorded as `proposed` with the edit. A pass that reaches no verdict on
a criterion writes `not judged: <why>`.

A **finding** is one defect with one fix. Several documents sharing a defect and its
fix (six pages whose `updated` date lags, one check that would catch all six) are one
finding; two defects in one document are two, `proposed` edits included, though several
findings may land in one commit. A finding may surface under more than one criterion
(a claim that is criterion 9 in the README and criterion 10 in a runbook): each
criterion's line in §6 names it, the note and the resolution carry it once.

**Removal provenance.** Every removal a pass proposes or considers, under any criterion
(a deleted sentence or section, a removal candidate), states three things apart: the
text's origin (`user statement`, `agent proposal` or `unknown`, with what was searched),
its current purpose (the failure, preference, boundary or intent it serves, and whether
that still holds), and the pass's judgment of its merit. Origin does not settle merit,
and merit does not erase or reassign origin. Trace origin through the guide's git
history, the task and source records it cites or that name it, and the filing session
where a record carries a session stamp. Missing origin, incident or effectiveness
evidence is recorded as such and is never part of a removal's rationale; neither is a
shorter document or a simpler rule set. A removal's rationale names, with its
evidence, what makes the text wrong or unneeded now: for example, it contradicts the
tree or its authority, restates the global layer, is progress prose with no guidance,
or serves a purpose that has lapsed. The note's entry for the removal carries
`[origin <value>, purpose <…>]`, with no `;` inside; what was searched goes to §6.
Whatever criterion finds it, a proposal to delete a rule (a sentence under Rules, or
any rule in lore's generated file) takes criterion 5's route: a `decision` removal
candidate, or a question when its origin or purpose is unknown, and never a `stale`
or `proposed` finding filed as a task before the human rules. A correction that keeps
the rule (a renamed path, a fixed command) keeps its own criterion's route, and so
does criterion 4's deletion of text the global layer already carries.

**Root and declared subsystem guides (project-guides design §8), judged once per guide
set, the root's and each declared subsystem's own `identity.toml`, `README.md` and
`AGENTS.md`:**

1. **Identity fits.** The purpose says what the thing is; the abstract says what it does
   and for whom; neither restates the other. Evidence: the two strings in
   `identity.toml`. `refined` with the rewrite, or `keep`.
2. **Authority is named and current.** Each `authority` path is the document that decides
   what is built, and its status line is not older than the last landed goal. The status
   line is the document's newest dated line of its own: a front-matter `updated` or
   `status` date, or the dated heading of its current-state section; a document with none
   is `not judged` here. The last landed goal is the newest `done` task whose record
   names the document (`tasks -C <checkout> list --status done --sort updated --plan
   <path>`, then `--ref <path>`; a spec link has no list filter, so `grep -l '<path>'
   <records>/tasks/*.md`
   finds those records, read with `tasks show`); when none names it, the newest `done`
   task, and the verdict says so. `stale` naming the goal and the newer entry, `keep`, or
   `not judged` when the pass cannot tell whether the document was meant to record that
   goal.
3. **Intent and capability stay distinct from progress.** When a passage describes an
   initial slice, provisional limit or future direction, read its linked authority and
   relevant task/source records for intended scope before proposing a rewrite. Keep the
   intended direction and the limit's provisional meaning beside tree-verified current
   capabilities. Such a constraint grounded in recorded intent is guidance (`keep`);
   a shorter rewrite is `refined` only when it preserves both meanings (§4 still applies).
   The code establishes current capability under 9, not the project's eventual scope.
   When intent is unavailable or records conflict, record `not judged` on intent with
   the missing or conflicting evidence under questions; continue capability checks.
   A proposed change to intended scope is a `decision` for the human.

   Pure progress/history prose ("X is implemented", "as of <date>", "in progress",
   dated measurements) is removed when it supplies no operating guidance or intent
   distinction. In the README the rendered `ops:status` region is exempt. A failure a
   rule cites (a commit, task or cut id) is guidance, not status. Evidence: the text,
   recorded intent and tree. `refined` when deleting a word or clause leaves true
   guidance and preserves the scope/capability distinction; otherwise `stale` with
   the proposal: delete the pure progress claim and, when it says something the tracker
   or a dated note does not, file or move it there. Either deletion follows the
   removal-provenance clause.
4. **Nothing the global layer already says.** No section restates the tasks skill, the
   worktree rule, the commit conventions, or a profile's instructions. Evidence: the text
   against the global `AGENTS.md` the session loaded and the tasks skill. `refined` with
   the section deleted, the line count saved and the global section that carries its
   purpose (removal-provenance clause). Text that fails here is not judged again
   under criterion 5.
5. **Every rule has a failure — baseline and Rules changes.** Run this on a guide
   set's first review and when its Rules text changed since the last completed review.
   Read that review's commit from the reusable review task and compare the Rules text
   with the working tree; for lore's generated global file, compare the whole file.
   If the earlier revision or coverage cannot establish a baseline, run it now.
   When the baseline is established and Rules are unchanged, record
   `not judged: Rules unchanged since <sha>`. When running it, each rule (a sentence
   under Rules) names, or the pass
   finds in `git log`, a retro note, or a task (`tasks -C <checkout> search "<phrase>"`,
   `grep -ril <word> <records>/tasks/`), the failure it prevents. Trace each rule's
   origin and purpose (removal-provenance clause). A rule is `keep` whatever its
   origin unless the pass finds an evidenced reason against it under that clause. A
   rule with no found failure has `no incident recorded`, which is never such a
   reason; nor is an unrecorded purpose (purpose `unknown`). A fixed incident does not
   end a purpose; a purpose lapses only when what the rule governs (a component, tool,
   path or condition) no longer exists in the tree or its authority. A purpose that
   still holds does not cancel a reason against the means the rule prescribes (its
   check never sees what the step changes; it costs more than it catches): merit is
   judged apart from purpose and origin. With such a reason, a rule whose origin and
   purpose the pass can state is a removal candidate carrying both; when either is
   unknown, the rule is `not judged: origin unknown` or `not judged: purpose unknown`
   and goes to §6's questions with the reason and what was searched. Rules kept with
   `no incident recorded` are listed by short name, grouped by origin with `|`
   between groups and no `;`, in the note's `keep:` segment even when criterion 5 has
   other verdicts, and on its §6 line with what was searched; this is the one
   exception to §6's one phrase. Evidence: the search and the trace.
   `decision`: the rule is a removal candidate for the human, never deleted by the pass.
6. **Budget — mechanical only.** Record `not judged: retired in v2; budget checked
   mechanically`. §1 records `ops-docs check`'s line-limit findings. It does not judge
   whether sections earn a declared raise; v2 retires that separate prose judgment.
7. **Projections agree.** README and `AGENTS.md` do not contradict each other on setup,
   gates, or layout. Evidence: the two texts. `refined` with the correction, or `stale`
   when the tree disagrees with both.

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
   `git ls-files`, the justfile, the manifest. Compare documented tables and command
   lists directly with their tracked source (key definitions, CLI-help source, justfile
   `*_cmd` values); read the source rather than executing the CLI. Check each named
   path, recipe and package against the tree. A contradiction is a defect: `refined`
   when one word corrects it (`npm install` where the lockfile and justfile say `npm
   ci`), `stale` when the claim needs rewriting. Wording the pass would merely prefer is
   never `stale`: it is `refined` when shortened in place, otherwise `keep`. A fix
   that would delete a rule takes the removal-provenance clause's rule-removal route.

**Reference documents and user guides:**

10. **Updated by the change that altered its behaviour.** For each document: the last
    commit touching it (`git -C <checkout> log -1 --full-history --format=%h -- <doc>`,
    so a merge that resolved a conflict in it counts), then the commits since that
    touch the paths, commands or modules the document names (`git -C <checkout> log
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
shortens or corrects; it never adds a section, reorders, or deletes a rule, except
text criterion 4 finds restated from the global layer. A README some test reads as
input (grep `tests/` for its name) gets that test run before the commit.

## 5. The review task and its notes

The project's documentation review task is the record every pass reuses. File or
find it with one idempotent command (same `--source` and title return the existing id
as `action: "reused"`):

    tasks -C <checkout> add "Documentation review" --source curate-docs --tag docs \
      -p 3 --size s --complexity low --process direct \
      -b "The reusable record of curate-docs passes over this project: one note per pass naming the rubric version, commit, documents covered, exclusions and findings by verdict; resolution of findings is recorded apart from the review. Never closed by a pass; ops owns its lifecycle."

It is the only task the review creates. Record the pass without claiming it. If this
pass started it, run `tasks -C <checkout> edit <review-id> --status todo` before
closeout, and check `tasks -C <checkout> show <review-id>` confirms the claim was
released. Never take over another session's claim. Leave its priority and body to
ops, which owns its lifecycle. Then exactly one review note, one line, segments in
this order. An empty segment is omitted. `keep:` lists the criteria whose verdict was `keep` on every
document they judged; a criterion with mixed verdicts appears only under the others,
except criterion 5's `no incident recorded` list.
`unresolved` counts the `stale`, `proposed` and mechanical findings; decisions wait on
the human and are not counted.

    tasks -C <checkout> note <review-id> "curate-docs: rubric v4; commit <sha>[ dirty: <covered paths|none covered>]; mechanical: ops-docs <rc>, ops-check <rc>[: <finding>, …]; covered: <path>[ (undeclared|authority)][ sections: <headings and line ranges>], …; excluded: <dir>: <reason>, …[, unread: <paths>]; keep: <criterion numbers>[ 5 (no incident recorded, origin <value>: <names> | …)]; not judged: <criterion>: <why>, …; refined: <doc>: <what>, …; proposed: <doc>: <edit>, …; stale: <doc>: <what>, …; decision: <doc>: <proposal>, …; unresolved: <n>"

Review completion and finding resolution are separate states, so a pass writes two
notes: the review note above, then the resolution note below. After the review note,
for each `stale`, `proposed` and mechanical finding: reuse the open task that owns it
(`tasks -C <checkout> search "<literal path or distinctive phrase>"`, `tasks -C <checkout> list --tag
docs`; avoid broad terms such as `AGENTS.md` alone), adding one note on it
(`curate-docs: <review-id> at <sha> confirms: <what>`), or file
one in the owning project with `--source <review-id> --tag docs -p 3 --size xs
--complexity low --process direct`, sized up when the fix is larger. A closed owner is
not reused; when the finding shows that closed work fell short, the new task's first
note is the `concerns:` line the global instructions define. One task per finding as
§3 defines it; unrelated findings are never bundled. Then one resolution note on the
review task:

    tasks -C <checkout> note <review-id> "curate-docs: resolution; <doc>: <what> -> <task-id> (reused|filed); …; decision: <n> awaiting the human"

A `decision` finding is filed as a task only after the human rules on it; until then
it lives in the review note.

After both notes and the finding-owner handoffs, acknowledge every completed pass,
including a direct invocation outside the weekly generator. Open finding tasks and
human decisions keep their recorded owners; acknowledgment records the pass, not
their resolution. First confirm the review record has no live claim as above.

Resolve the reachable `ops` row's `checkout` through `tasks projects` (JSON). From
that registered checkout, using its configuration, run:

    python3 bin/doc-review --acknowledge-only --project <prefix> --dry-run

Inspect the exit status, the reviewed project's row and proposed writes: only that
project may receive acknowledgment writes, with no replacement selections. If the
preview succeeds and acknowledges this pass, run the same command without `--dry-run`.
Inspect its exit status and actual result, then `tasks -C <checkout> show <review-id>`.
A successful acknowledgment leaves the reusable record P3/todo; a future configured
eligibility floor is its defer date. Confirm it is absent from
`tasks -C <checkout> ready` while deferred. The date or a later generator-observed
commit trigger makes it eligible again.

Report command errors, unreachable ops, skipped/in-progress rows, or an unusable
review note as acknowledgment blockers with the next action and owner; a live claim
is not dormancy, and another session's claim stays untouched. If the configured floor
has already expired, acknowledgment leaves the task undeferred: report that it may
remain ready. An already acknowledged pass needs no repeat writes; report the
observed state. Keep the generator's settings and use only acknowledgment mode.

## 6. Summary to the human

One line per criterion: its number, verdict, and one phrase (or `not judged: <why>`).
Then the review task id, the commit judged, and the acknowledgment result (priority,
status and defer date, or blocker with next action and owner). Then the decisions
that are the human's, grouped, omitting empty groups:

- **removal candidates** (criterion 5, or any criterion proposing to delete a rule):
  the rule or section, its origin and current purpose, the reason for removal kept
  apart from them, and what was searched;
- **declarations** (criterion 11): the directory, and the two options;
- **scope decisions** (criterion 3): the passage, recorded intent, proposed scope
  change and evidence; present it for the human's ruling before filing a finding task;
- **stale text** (criteria 2, 3, 7, 8, 9, 10): the document, the claim, the evidence,
  and the task that now owns it;
- **proposed edits** (from another project; criteria 1, 3, 4, 7, 8, 9): the document,
  the edit, and the task that now owns it;
- **questions**: anything the pass could not judge, including a rule with a removal
  reason but unknown origin or purpose, with the reason and what was searched.

Nothing else. A pass with nothing in those groups says so in one line.

## Bounds

- The review creates one task at most, the review task. Findings become tasks in the
  resolution step, after the review note, one per finding.
- Execute only §1's mechanical checks and §5's tracker/acknowledgment commands;
  nothing from the judged documents is executed.
- Only covered documents are judged; a defect noticed in a decision record or a
  vendored file is named in `excluded:`, not judged. Two exceptions: an authority
  document under criterion 2 alone, and an unread reference document under criterion
  10's self-date check alone. Partial reference reads cover only their recorded sections.
- Prefer shorter. An edit that grows a document is a proposal.
- Keep defects apart from preference: `stale` is reserved for text the tree or its own
  authority contradicts, and for an orientation a reader needs and cannot find
  (criterion 8).

## Rubric history

- **v1** (2026-10-23): criteria 1–7 from ops
  `docs/specs/2026-09-22-project-guides-design.md` §8; 8–11 added for completeness by
  reader needs, factual drift kept apart from preference, reference documents, and
  undeclared guides. Deliberate departures from §8's text, each to be confirmed or
  reverted by the pilot: every criterion may return `not judged: <why>`; criteria 1–7 are
  judged per guide set, declared subsystems included; criterion 2 returns `not judged`
  for an undated authority document or an unattributable goal; criterion 2 compares the
  status line with the newest `done` task that names the document before falling back to
  §8's newest `done` task; criterion 3 covers the README as well as `AGENTS.md` (the
  README's rendered status region exempt) and dated measurements, exempts a rule's cited
  failure, allows `refined` where deleting a word or clause leaves true guidance, and
  names a dated note as a destination; text that fails criterion 4 is not judged again
  under criterion 5; criterion 5 reads a rule as a sentence under Rules, not a line,
  returns `keep` for a boundary rule that cites its authority document, and over lore's
  generated file is the provenance audit lore's `docs/` holds (§8 cites it as ai-9ec1eb);
  criterion 6 names `keep` explicitly. Two further departures: `proposed` is a fifth
  recorded verdict for edits the pass cannot make; lore's root `AGENTS.md` is judged
  under every applicable criterion, distinct from its generated global file. The ops
  pilot applied the seven source criteria plus completeness and drift before final v1;
  it did not test the final eleven-criterion skill end to end.

- **v2** (2026-10-24, lore-1e46ee): revised from ops-65a068's
  `docs/notes/2026-10-23-doc-review-pilot-report.md` (in ops). Three personal-profile
  projects yielded 24 actionable findings and 24 rejected candidates; the report
  gives no candidate breakdown sufficient to attribute false positives to each
  criterion. Low yield alone does not establish a defective criterion. The 40-line
  v1 dry run likewise gave no actionable 1, 6, 7 or 11 finding; its criterion 5 false
  positive on a design boundary prompted the authority-citation keep clause.

  Disposition of every recorded v1 departure from project-guides §8:

  | Departure | v2 decision and reason |
  |---|---|
  | `not judged` available to every criterion | Confirm: missing evidence must remain visible, distinct from `keep`. |
  | Criteria 1–7 per root and declared subsystem guide set | Confirm scope, with 5 conditional and 6 retired below: stale subsystem guides were a positive control. |
  | 2: undated authority or unattributable goal is `not judged` | Confirm: neither absence proves staleness; pilot supplies no contrary evidence. |
  | 2: document-linked done task before newest done fallback | Confirm: unrelated completions cannot date a document's authority; fallback remains disclosed. |
  | 3: README and dated measurements included; rendered status exempt | Confirm: pilot found dated gate history; generated status has its own check. |
  | 3: cited failures exempt; small deletions may be `refined`; dated note destination | Confirm: preserve rule evidence and useful history without leaving status prose in guides. |
  | 4 before 5, without judging restatements twice | Confirm: all three projects had restatements; one defect needs one resolution. |
  | 5: sentences rather than lines; cited design boundary is `keep` | Confirm: wrapping is not a rule boundary; the dry-run false positive supports the keep clause. |
  | 5: generated global file uses the provenance audit | Confirm and move the pointer into §2; resolve findings by manifest owner, including ops. |
  | 6: explicit `keep` for earned raises | Retire with the prose criterion, rather than revert: it never applied in the pilot. Mechanical limits remain in §1; their success is not an earned-budget judgment. |
  | Fifth recorded verdict `proposed` | Confirm: distinguishes an unmade edit from `refined`; cross-project edits must remain proposals. |
  | Lore root guide judged normally; generated global file under 5 alone | Confirm: these are now separate files with separate roles. |

  Further v2 decisions: keep 1–2 as quick checks and 3, 4, 7–9 in each pass;
  run 5 at baseline and after Rules changes (only decisions in the pilot); retain
  the criterion numbers so old notes remain interpretable. Criterion 9 now names
  source-table comparison explicitly. Long reference guides may be sampled by section,
  with exact coverage and unread ranges recorded; the pilot's partial CLI-guide read
  cannot stand for a whole-document review. Duplicate searches use literal paths and
  distinctive phrases. Retain 8's stub signal and 10–11: the pilot did not evaluate
  final v1's latter two criteria, so removal would be unsupported. These are bounded
  judgments from a small selected sample, not measured corpus-wide validation.

- **v3** (2026-10-25, lore-ae0e0b): criterion 3 distinguishes provisional constraints
  grounded in recorded intent from progress/history prose. crew-56ee1c's README edit
  (crew `9b45d43`) removed the first-slice qualification; the user's correction in
  crew-aaab30 asked to preserve both intended scope and delivered capabilities.
  lore-1d6126's seven-case study supports this bounded change, not a measured failure
  rate or review threshold. Rewrites retain intended direction and accurate current
  support together; missing/conflicting intent stays explicit and an intended-scope
  change needs a human decision, presented under §6's scope decisions before filing
  a finding task. Other criteria and their numbers are unchanged;
  date semantics and payload classification retain their separate tasks. Application
  probes are synthetic checks, not independent natural-case validation.

- **v4** (2026-10-28, lore-650b32): a §3 removal-provenance clause, cited by criteria 3,
  4, 5 and 9, makes every proposed or considered removal state the text's origin and
  current purpose apart from its merit, and keeps missing evidence and simplification
  out of the rationale. The lore pass at `209cf39` (lore-a4f7e2) recommended keeping the
  composition, explicitness, compatibility-layer, Unified and project-switch rules but
  classified them as criterion 5 `decision` removal candidates because no incident was
  recorded. After the user pointed out that a requested goal may be unimplemented rather
  than unwanted and asked for origin and intent to be assessed, the pass withdrew them;
  the user then added that origin and merit are separate questions. Criterion 5 now
  keeps a rule whatever its origin unless an evidenced reason stands against it, and a
  purpose that still holds does not cancel a reason against its means; a fixed incident
  does not end a purpose; a rule with unclear purpose and no reason against it is kept
  with purpose `unknown`; a reason against a rule whose origin or purpose is unknown is
  `not judged`, sent to questions; `no incident recorded` rules are listed in the note
  and on the §6 line, grouped by origin. A proposal under any criterion to delete a rule
  takes criterion 5's route, never a task filed before the human rules. Criterion 4
  names the global section that carries a deleted section's purpose; the note carries
  each removal's origin and purpose, and §6's removal candidates carry both. Criterion
  numbers are unchanged. Application probes are synthetic checks, not independent
  natural-case validation.
