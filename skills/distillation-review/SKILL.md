---
name: distillation-review
description: Use when asked for a project distillation pass, or to find deletion, simplification and consolidation opportunities in a fast-moving project's code and test architecture. Not for task-corpus curation or public-guide prose drift.
---

# Distillation review

Produce a small set of changes the owner can judge against the project's intent.
A small implementation is not sufficient evidence that its contract is unnecessary.
This is a read-only assessment, not permission to implement or file its proposals.

## Scope and inputs

Use the tasks skill for the owning review task. Resolve the target prefix with
`tasks projects --json`: `<checkout>` is its code checkout and `<records>` is its
full project records directory, not merely `docs/specs`. Read `<checkout>/README.md`,
`AGENTS.md`, reference docs, and relevant goals and source records. Read both
`<records>/docs/specs/` and `<records>/docs/plans/`, plus task bodies and notes under
`<records>/tasks/` through the CLI. Follow references and human clarifications.
Record unavailable evidence as a gap; an empty code-local docs directory says
nothing about detached records. Keep implemented capability distinct from intended
scope and provisional limits.

Exclude dated-document migration (ops-9a11f4) and public-guide prose drift
(`bin/doc-review`, curate-docs); use those existing owners. Selection and recurring
cadence belong to the calling workflow, not this skill.

## Read-only pass

The controller may do the investigation itself or dispatch a researcher with these
instructions and the resolved roots. Researchers and critics must not edit code,
create files, run tasks writes, commit, start servers, or run broad test suites.
They return full findings in their final message. The controller alone maintains
the owning review record and saves the report in its authorized records destination.
No target-project proposals are filed before owner acceptance.

1. Pin the code revision and records basis; note dirty paths and scan limits.
   Rank current tracked code files, including tests, by **30-day non-task commits
   touching the file × current line count**. Use a fixed UTC cutoff, exclude merge
   commits and task-only bookkeeping, and state the exclusions and counting method.
   Exclude generated/vendor files; do not exclude tests merely because they are large.
   Show the top three products and assess each for internal responsibility coupling
   and a possible `simplify` change. Fewer than three eligible files: assess all.
2. Investigate deletion and consolidation candidates as well. For any caller or
   probe deletion, follow its dependency chain into `src/` (or the project's source
   roots), recursively distinguishing newly dead plumbing from shared live code.
   Record the checked chain and surviving consumers, not just the deleted entrypoint.
3. Complete the evidence card below for **every proposal and direction question**.
   Missing evidence means unverified, never a verified proposal. Put rejected
   candidates and their reasons under **Not proposed**.

## Evidence card: Chesterton's fence

| Required check | Evidence to record |
| --- | --- |
| Origin and purpose | `git log -S '<symbol or contract text>' -- <paths>` and the relevant introducing/changing diffs; search earlier history beyond the 30-day ranking window. |
| Accepted contracts | Relevant specs **and plans**, their approval/source records, request guards, parsers, test guards and semantics the replacement must preserve. Follow historical moved-document references. |
| Task overlap and intent | `tasks search --project <prefix>` with explicit status coverage: `todo`, `doing`, `blocked`, `idea`, `shelved`, `done`, and `dropped`; follow moved records. Read matching tasks and notes; search does not search notes. Record search terms and results, including absent matches. |
| Caller completeness | Before removing an import/module, enumerate every occurrence in affected files and all callers across source, tests, scripts, configuration and exports. Check indirect/public consumers; a narrow grep or no internal caller alone does not prove dead code. |
| Replacement safety | Explain how the proposed replacement preserves every applicable contract and plan-mandated guard. Green tests cannot justify replacing a real checker hook with a success stub. |
| Retirement | Separate code/test retirement from state/evidence inventory and disposition. Preserve “after nothing needs it” conditions; code retirement grants no evidence deletion. |
| Convergence | Establish an unmet requirement before suggesting subsystem convergence, including as a direction question. Different commit/recovery constraints may justify distinct systems. Similar code alone is insufficient. |
| Gain | Verify exact counts and distinguish lines, symbols, variants and match arms. State branch/trigger conditions for scans or repeated work. Label unmeasured performance benefit as a hypothesis; do not invent a speedup. |

For example, removing a fixture's `common` import requires listing **all** its
helper calls and checking the accepted test plan's real-checker hook requirement.
Replacing only the displayed helper while stubbing that hook is not a safe deletion.

## Controller verification and critic

The controller checks every candidate and question against original code, history,
records and accepted intent: spot-checking three counts/imports is insufficient.
Recompute quantitative claims, verify the top-three simplify assessments and
transitive dependency coverage, and resolve or withdraw unsupported remedies.
Record which claims were checked at which revisions and what changed.

Then dispatch **one independent read-only critic pass** against the frozen draft,
cited code and records revisions, and this protocol. The critic checks provenance,
caller exhaustiveness, required guards, retention conditions, convergence premises,
counts and scan conditions. It returns actionable findings with locations, severity,
reviewed revisions and verified reviewer identity. Preserve its full review using
the applicable reviewer-report convention; a designated report write, where required
by project instructions, is its sole write exception.

If independent review is unavailable, stop short of owner handoff and record the
missing critic as the next agent action; never label a self-review independent.
Resolve critic findings against the evidence, recording dispositions before saving
or handing over the final report. Withdraw unresolved items; do not silently accept
a conflicting verdict. Existing project correction/re-review requirements still apply.

## Report and handoff

Save `<slug>-distillation-report.md` under the owning review task's authorized
`docs/notes/`. Link it from that task. Use portable paths labelled as code or records;
include frozen revisions and the verification/critic record.

The report contains, in order:

1. **Summary:** where complexity concentrates; scan window, exclusions and limits;
   the top-three ranking and a simplify assessment for each (including reasons to keep).
2. **3–5 verified proposals**, labelled `delete`, `simplify` or `consolidate`:
   **What**, **Evidence** (paths, symbols, commits, specs/plans and task checks),
   **Gain**, **Risk and cost** (`xs`/`s`/`m`/`l`), **Overlaps**.
3. **1–2 direction questions**, each with checked provenance, the unresolved owner
   choice, a recommendation and its trade-off. A question must pass the same gate.
4. **Not proposed:** rejected candidates and the evidence that ruled them out.
5. **Verification:** controller checks, critic verdict/findings and dispositions,
   with remaining uncertainty and revision-bound limits.

These are caps and useful target sizes, not quotas: report fewer when evidence
supports fewer, explaining the shortfall. Never pad with unsafe changes or invent
an owner decision. Present the report for owner acceptance; only after acceptance
may the controller file the accepted items, checking overlap again then.

## Stop signs

| Temptation | Required response |
| --- | --- |
| “The reviewer says it is obvious.” | Complete the evidence cards and controller verification. |
| “We can send this tonight and verify later.” | Finish verification and the critic first; if blocked, report incomplete status. |
| “The specs directory is empty.” | Resolve and inspect the full records root, including plans and closed tasks. |
| “Tests pass, so this guard is redundant.” | Read the accepted guard contract and preserve its behavior. |

An incomplete pass is not an accepted report. Keep its missing checks explicit;
continue available agent work rather than handing the owner's decision back early.
