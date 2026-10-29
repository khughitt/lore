## Decisions

<!-- rule:fdd377a3c264435296d1792c8f74c68b begin -->
- When you hold a recommendation for a bounded decision, state it with the alternative
  you rejected and act on it. Do not end the turn to ask for confirmation: the user
  overrides in free text if they disagree, and a wrong default costs one correction
  while a question costs a stop. This applies to "which approach", "where should this
  land", "does this section look right", "which follow-ups to file", and "execute now".
<!-- rule:fdd377a3c264435296d1792c8f74c68b end -->
<!-- rule:8d52bc64e99b42d78f4219f73c3b375c begin -->
- Stop and ask only when the answer needs the user: an artifact they must inspect and
  judge (a sheet, a screenshot, a rendered page), a choice of taste, scope, or priority
  that no recommendation can settle, money to spend, or an action outside the repository.
<!-- rule:8d52bc64e99b42d78f4219f73c3b375c end -->
<!-- rule:db275842f3af447dbe84d8b1dfc68051 begin -->
- Two written artifacts keep their gate: a design spec and an implementation plan are
  reviewed before the next phase starts. Within writing them, sections are not
  individually approved.
<!-- rule:db275842f3af447dbe84d8b1dfc68051 end -->
<!-- rule:f431707097c0418c9822d67074875c51 begin -->
- A request to review a spec or plan names the frozen revision under review: the
  repository, commit and path, so the reviewer reads `git -C <repo> show <sha>:<path>`
  rather than the working file. Where the profile keeps the document out of the tree,
  the request names its path and sha256, and the reviewer checks that sha256 before
  reading and stops on a mismatch. While that review is open, never amend or rebase
  the commit, and leave an out-of-tree file unedited. A later draft reaches review only
  as a new frozen revision, named in the next round's request, and each finding is
  judged against the revision its request named.
<!-- rule:f431707097c0418c9822d67074875c51 end -->
<!-- rule:2c5785f136ca4ee590e1c69406276623 begin -->
- A question, when asked, carries your recommendation as the first option and is one
  question, not a series. A question that asks the user to describe what they want
  (brainstorming's open questions, and its playback asking what is wrong or missing)
  carries no options; a guess they can correct stands in for the recommendation. That
  playback is not a "does this section look right" decision: what they want is theirs
  to say.
<!-- rule:2c5785f136ca4ee590e1c69406276623 end -->
<!-- rule:c165eee5aa0a4b819061b34386c78c23 begin -->
- Before a question asks the user what work should achieve or why (brainstorming's
  opening questions, its playback, its builder check's "theirs" pile), find out who
  holds that intent. Work the user describes in this session starts with the
  question; naming a task to take up is not describing it. Other work (filed by
  another session or agent, captured earlier, grown by scope passes, or derived as a
  follow-up, feedback report or decomposition child) starts by reading what already
  exists: the task's body, notes and references, its `source` and parent chain, and
  the session that filed it, whose human turns around the filing the session-logs
  skill recovers. Reading needs no offer or permission. Play back
  what you found and where each part came from, keeping the user's recorded words
  apart from what agents added. Then ask only what the evidence leaves to the user (a
  choice of taste, scope or priority, or a premise the evidence contradicts), each
  question naming what you found; when nothing remains, write the design and mark each
  call as yours. Never ask the user to recall what a record or transcript holds; when
  a source cannot be found, say so and offer your reading for them to correct. The
  written design's review stays the user's gate. This outranks brainstorming's first
  message and its offer to go look.
<!-- rule:c165eee5aa0a4b819061b34386c78c23 end -->
<!-- rule:96e7765f238045f4af07742ea0783816 begin -->
- In assessments and reviews, distinguish tree-verified current capability from
  recorded intended direction. Before characterising intended scope, read the relevant
  goals, authority and task/source records. Code establishes current behaviour, not
  eventual scope: preserve the recorded goal and any limit's provisional meaning
  beside what works today. When intent is missing or records conflict, state what is
  unknown and which evidence is missing or conflicting; neither invent intent nor
  replace it with implemented behaviour. A proposed change to intended scope remains
  a human decision.
<!-- rule:96e7765f238045f4af07742ea0783816 end -->
<!-- rule:4fd096e0dfb040c7b5f77277569bbabd begin -->
- A turn that ends with work still owed reports the observed status, not what the turn
  ending implies: which work has stopped and why, what is still running (a background
  check, a dispatched child) and how its result is picked up, and who owns the next step
  — never "is underway" for work that stopped. A step you own (a review you dispatch, a
  check you rerun, a child you have not started) is never reported as waiting on the
  user: finish it, or `tasks park` the task with that step as the next action and resume
  it; hand it over only explicitly (`--waiting-on user --reason review`). A park's next
  step is an action and who takes it ("rerun `just gate` in .worktrees/x, then dispatch
  the Task 6 review"), never a state ("waiting for next steps"). An unblocked task you
  hold is not parked between increments: continue until a blocker, a gate that needs a
  person, or the end of the session.
<!-- rule:4fd096e0dfb040c7b5f77277569bbabd end -->
<!-- rule:717a50b29e794e72b327bf60820479bf begin -->
- A skill's scripted question or stop (an integration menu, a "surface residual
  findings" step) is a bounded decision under this rule unless it falls in the stop
  list above; this rule outranks the skill's "exactly as written".
<!-- rule:717a50b29e794e72b327bf60820479bf end -->
<!-- rule:5a5808d0572f49e49afe103d7569231e begin -->
- Integrating a finished, reviewed branch by local merge is a bounded decision only in
  a repository the user owns. The profile sets the default: a `personal` checkout
  allows it; in a `work` or `external` checkout, never merge on your own: present the
  integration choice. A user-owned checkout under another profile allows it only when
  its repository instructions or the user in the session say so explicitly (for
  example, "Reviewed branches may be merged locally into main without asking."). Never
  infer that permission from the account, the path, the profile's name or assumed
  ownership. A push, a PR, or a merge that changes a live global surface (these global
  instructions, hooks, services) stays an action outside the repository under every
  profile and authorization.
<!-- rule:5a5808d0572f49e49afe103d7569231e end -->
<!-- rule:046dfb8c365f454a86390b6b4167e487 begin -->
- Reviewers stay read-only and return their full review in their final message;
  dispatches must not ask them to write report files. When persistence is needed,
  the controller saves the full returned text in the plan workspace as
  `<slug>-report.md`, with the reviewer identity recorded alongside it. This applies
  to initial task reviews, scoped re-reviews and final whole-branch reviews. Keep
  the existing ledger, ruling and retention rules; saving a report does not replace
  those records.
<!-- rule:046dfb8c365f454a86390b6b4167e487 end -->
<!-- rule:d21e7a02223e4d00adbb602627e441a6 begin -->
- After a final whole-branch review, in subagent-driven and inline (executing-plans)
  execution alike, fix (or rule on, as the skills allow) its Critical and Important
  findings in corrective rounds, up to five; then surface what remains. A round is one
  fix pass plus one scoped re-review of it, and another follows while that re-review
  reports any Critical or Important finding, persisting or introduced by the fix. Minor
  findings never enter a round; they go to the ledger as `minor (deferred)`, as both
  skills say. In either execution mode, a final review's "fix before merge" call on a
  deferred minor is a re-grade proposal: the controller confirms or rejects it by its
  consequence for the person, records each decision as a ledger `Ruling:` line, and
  admits confirmed proposals to corrective rounds as Important; rejected proposals
  stay `minor (deferred)` and reach the final message. A fix subagent makes the fixes
  under subagent-driven execution; inline,
  you make them yourself, each still proven RED→GREEN with policy-appropriate checks
  under Tests: a green suite when policy is enabled, focused evidence and mandatory
  hygiene when it is off. A skipped suite is never green evidence. A fresh
  reviewer runs the re-review whenever a subagent tool exists, inline too. This outranks
  executing-plans' "do not dispatch a re-review" and "no second fix pass" and
  subagent-driven-development's "exactly one scoped re-review" and "no second fix wave".
  Without a subagent tool, the re-review is a self-review, recorded as such in the
  ledger and the final message, as executing-plans' final-review fallback does. External
  actions stay gated.
<!-- rule:d21e7a02223e4d00adbb602627e441a6 end -->
<!-- rule:e5201d5768794401bf9d88a39b1ee445 begin -->
- A review correction to a task already closed as `done`, before its branch is
  integrated, reopens that record: the agent that makes the fix (the fix subagent, or
  you inline) runs `tasks edit <id> --status todo`, then `tasks start <id>`, since a
  bare `start` refuses a done record. A task still open, parked or not, needs only
  `tasks start <id>`. The fix owner releases it with `tasks done` or `tasks park`
  before reporting. Such a correction stays a review finding; a `concerns:` task is
  filed only for work that fell short after its branch landed.
<!-- rule:e5201d5768794401bf9d88a39b1ee445 end -->
