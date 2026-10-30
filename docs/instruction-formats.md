# Instruction formats

Type: data model; document types 1. Covers the assembly catalog
(`instructions/assembly.toml`, version 1) and the provenance manifest
(`instructions/AGENTS.manifest.json`, version 2). `bin/assemble-instructions`
accepts catalog version 1 and writes manifest version 2; other delivery manifest
versions fail check. Historical proofs execute their pinned assembler. How to run the assembler and diagnose its checks is in
[instruction-assembly.md](instruction-assembly.md).

## Catalog

A TOML document with exactly three top-level keys:

| Key | Value |
| --- | --- |
| `version` | Integer `1`. |
| `separator` | The string `"\n"`. Fragments are joined with one newline. |
| `fragments` | Nonempty array of fragment tables, in delivery order. |

Each fragment table has exactly these fields; every text field is nonempty:

| Field | Value |
| --- | --- |
| `id` | Matches `[a-z][a-z0-9-]*`; unique within the catalog. |
| `owner` | Project prefix (`[a-z][a-z0-9]{1,7}`) whose checkout holds the source. |
| `source` | Canonical owner-relative POSIX path: not absolute, no `..`, no backslash or NUL, unchanged by normalization, and resolving inside the owner checkout. |
| `classification` | `mandatory` or `adaptable`. |
| `rationale` | Why the fragment exists. |
| `provenance_date` | ISO date, `YYYY-MM-DD`. |
| `evidence` | Nonempty array of evidence tables. |

The source bytes must be UTF-8 and end in exactly one newline. The fragment with id
`projects` must begin with the `<!-- ops:projects start … -->` marker line and end
with the `<!-- ops:projects end -->` line, each appearing once.

A fragment that the committed catalog at `HEAD` records as `mandatory` must stay
in the catalog and stay `mandatory`; removing or downgrading one is rejected.

### Evidence

Each evidence table has exactly `owner`, `path`, `revision`, `location` and
`status`, all nonempty text.

| Field | Value |
| --- | --- |
| `owner` | `PREFIX` reads that project's checkout; `PREFIX:records` reads its records directory. |
| `path` | Owner-relative canonical path, or a sentinel. A records path is relative to the project's records directory, not its repository root. |
| `revision` | Full 40- or 64-hex commit id, or the same sentinel as `path`. |
| `location` | Where in the document the evidence is (sections, rule labels). |
| `status` | Whether incident evidence supports the fragment; see below. |

Status values:

- `recorded`: the pointer cites recorded incident evidence for the fragment's rules.
- `none recorded`: no incident evidence was recorded. Absence of evidence is never
  read as evidence that a rule works.
- `n/a`: the fragment states preferences or environment facts, for which incident
  evidence does not apply.

Status never controls lookup: a concrete pointer with status `none recorded` or
`n/a` (for example the audit that found nothing for a rule) is read and validated
like any other.

The path/revision sentinels are `none recorded` and `n/a`. When either `path` or
`revision` is a sentinel, both must be the same sentinel, and the pointer is not
read. Otherwise
the revision must resolve to exactly that commit in the owner's repository and
`revision:path` must name a file blob there. A branch name, short id or tag is
rejected. Evidence is checked for content at an immutable commit; the commit
does not have to be on any branch the owner currently publishes.

Owner roots: `lore` is the executing checkout. Every other owner, including
`lore:records`, comes from the tasks registry (`$XDG_CONFIG_HOME/tasks/projects.toml`,
its `[projects]` and `[records]` tables). The registry's format belongs to the
tasks project.

## Manifest

JSON written with sorted keys, two-space indent and a trailing newline. Top-level
keys are exactly:

| Key | Value |
| --- | --- |
| `version` | Integer `2`. |
| `mode` | `production` for the delivered manifest; `baseline` or `initial` only in a historical proof's temporary manifest. |
| `separator` | `"\n"`. |
| `fragments` | One record per catalog fragment, in order. |
| `artifact` | `path` (`instructions/AGENTS.md`) and `sha256` of the delivered bytes. |
| `catalog` | `path` (`instructions/assembly.toml`) and `sha256` of the catalog bytes. |
| `assembler` | `path` (`bin/assemble-instructions`), `revision` (Git blob id) and `sha256` of the assembler that wrote the pair. |

A fragment record copies every catalog field and adds:

| Field | Value |
| --- | --- |
| `revision` | Git SHA-1 blob id of the source bytes (content, not a commit). |
| `sha256` | SHA-256 of the source bytes. |
| `rendered_sha256` | SHA-256 after stripping local rule markers. |
| `rules` | Current rule IDs, hashes, artifact offsets/lengths, record paths and clause IDs/hashes/offsets/lengths. External fragments have an empty array. |
| `offset` | Byte offset of the rendered fragment in the artifact. |
| `length` | Byte length of the rendered fragment. |

The artifact is the rendered fragments' bytes joined by the separator, so each `offset` is
the previous offset plus the previous length plus one. Fragment `revision` is a
content id and evidence `revision` is a commit id; the two are never interchangeable.
Because the assembler records its own blob id and hash, editing the assembler
stales the manifest even when the artifact is unchanged.

The committed catalog supplies the mandatory minimum, independently of an old
manifest version. The selected delivery manifest must exactly equal freshly
assembled version 2 bytes. Rule records are addressed by stable path, without a
record hash: new evidence or assessments alone do not stale delivery. Source
hashes, current subjects, clause selectors and their locations still do.

## Rule authoring and assessment data

The authoring and `provenance` commands validate JSON against the closed contracts
in `instructions/schemas/`. A rule retains exact public policy revisions and clause
byte selectors separately from events, incidents and assessments. Unknown origin,
purpose and impact are explicit skeleton values. Claims and rationales paraphrase
private evidence; source locators and held-byte hashes identify evidence kept in
records attachments. Policy text itself remains exact, since it binds identity.

A schema-1 assessment has a kind-specific result (`approval`, `applicability` or
`effectiveness`) and an exact retained subject hash. Context snapshots record
observed inputs; dependency declarations select surrounding instructions. Explicit
supersession must address the same kind and subject and cannot form a cycle.
Local references and qualified `rule:<id>#<local-id>` references resolve to the
same identity, including source fields and assessment supersession across records.
Use `human` or `user` as an adoption actor for human authority; an agent action is
not human adoption. The JSON fixtures under `tools/fixtures/rule-provenance/` are
synthetic examples, including separate Claude/Codex/unknown target snapshots.


## Local boundaries and coverage

Every local instruction obligation is bounded by standalone paired markers
`<!-- rule:<32-lowercase-hex> begin -->` and the corresponding `end` line.
Markers cannot nest, repeat an ID or appear inside a code fence. Only marker
lines are stripped; raw and rendered sources each end in exactly one newline.
The current rule hash covers the exact UTF-8 bytes between markers. Clause
selectors bind exact UTF-8 byte offsets and hashes within a retained revision;
overlap must be declared. Retired rules keep their records and have no marker.

Blank lines and ATX headings outside fences need no record. Every other uncovered
block needs an exact-text exclusion with a reason in
`instructions/rules/exclusions/<fragment-id>.json`. A block is a maximal run
between a marker, heading, blank line or file boundary; a fenced block keeps its
internal blank lines. Each exclusion matches exactly one block; duplicate, missing
and unused entries fail. No offsets or fragment hashes are stored in exclusions.
Reviewers judge whether excluded prose is connective; the parser cannot infer it.

All rule, exclusion and schema files select the full index in staged checks.
Missing or renamed required files cannot fall back to disk. Records are validated
from that same view. Included evidence copies with a hash use selected local bytes;
external evidence locators are shape-checked without fetching transcripts or the
network. Availability is recorded independently from the truth of a claim.

The initial Git backfill maps the pilot's nine containers and 26 sub-rows to
identities, including two historical-only clauses. Its excerpt bindings hash
exact rows of the preserved secondary pilot report, not reconstructed original
transcripts. Original Git locators were checked for readability; original session
interpretations remain reported-only. Historical adoption targets name that scope,
not today's text hash. Source preservation points to the portable evidence packet
attached on lore-45303d; lore-f95780 owns the retained raw copies. Each captured
session source identifies one transcript line: `sha256` hashes its portable bytes
without the newline, and `raw_sha256` matches that line in the packet's row map.
Splitting grouped session locators preserves their existing evidence references
and quality labels; it adds no new historical interpretation or adoption claim.
No current applicability or effectiveness assessment is inferred from this backfill.

## Correction event contract

A schema-1 event of kind `correction` requires a closed `correction` object:
`target` (ordinary event reference), `dimension` (`authorship` or `adoption`),
`action` (`withdraw` or `restore`), nonblank `reason`, and `supersedes` (correction
references in the same target/dimension stream). Other event kinds forbid this
payload. Local and explicitly qualified same-record references are equivalent;
foreign correction targets/supersession, dangling references, duplicate canonical
references, cross-stream supersession and cycles fail. Forward references are
valid within the complete selected record.

The correction copies its target's exact subject binding, including historical
excerpt fields, and names that target among its unique predecessors. Predecessors
alone have no withdrawal effect. Correction event evidence is nonempty; authorship
is unknown with an explanatory statement, and adoption is `none-recovered` with
null actor/target, empty adoption evidence and false clause coverage. Supporting
source IDs must resolve; unavailable evidence files are not fetched. Original
claims, sources, searches and revisions are retained. Correcting both dimensions
requires two correction events. Restoring eligibility cannot upgrade the original
claim's actor, evidence, scope or revision.

Schema-variant failures identify the event index as `invalid variant`, using the
existing assessment-variant diagnostic convention. Semantic correction/reference
failures name their reason. No event-specific schema diagnostic parser is added.

The schema-1 provenance report adds `history[].event_contributions`, ordered by
ordinary event ID. Each row has `event` (unchanged local ID), its complete `subject`
binding, and independent `authorship`/`adoption` objects with `state`
(`active`, `withdrawn`, `conflicted`), sorted qualified `corrections` and `tips`.
Correction events remain in the original `events` array but have no contribution
row. Restored eligibility never upgrades the original claim's qualifications.

Each `conflicting-correction` detail names `target_event` (qualified ordinary event),
`dimension`, `corrections`, `tips` and the complete original `bound_subject`.
Its `subject` is the bound ID and `sha256` is the bound hash, possibly null for a
historical excerpt. Details retain their own source evidence and dimensions. The
group's `subject` is the owning container; its hash is the current delivered hash,
or null for a retired container. Detail-only event/tip fields are not promoted to
the group. Group differences and its bounded reason include every conflicted
dimension. Conflicts are reported for historical/retired subjects too, separately
in each target context and independently of unrelated adoption or origin warnings.
