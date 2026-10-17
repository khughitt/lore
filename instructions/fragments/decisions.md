## Decisions

- When you hold a recommendation for a bounded decision, state it with the alternative
  you rejected and act on it. Do not end the turn to ask for confirmation: the user
  overrides in free text if they disagree, and a wrong default costs one correction
  while a question costs a stop. This applies to "which approach", "where should this
  land", "does this section look right", "which follow-ups to file", and "execute now".
- Stop and ask only when the answer needs the user: an artifact they must inspect and
  judge (a sheet, a screenshot, a rendered page), a choice of taste, scope, or priority
  that no recommendation can settle, money to spend, or an action outside the repository.
- Two written artifacts keep their gate: a design spec and an implementation plan are
  reviewed before the next phase starts. Within writing them, sections are not
  individually approved.
- A question, when asked, carries your recommendation as the first option and is one
  question, not a series. A question that asks the user to describe what they want
  (brainstorming's open questions, and its playback asking what is wrong or missing)
  carries no options; a guess they can correct stands in for the recommendation. That
  playback is not a "does this section look right" decision: what they want is theirs
  to say.
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
- A skill's scripted question or stop (an integration menu, a "surface residual
  findings" step) is a bounded decision under this rule unless it falls in the stop
  list above; this rule outranks the skill's "exactly as written".
- Integrating a finished, reviewed branch by local merge is a bounded decision only in
  a repository the user owns (a `personal` profile checkout). In a work or external
  checkout, never merge on your own: present the integration choice. A push, a PR, or
  a merge that changes a live global surface (these global instructions, hooks,
  services) stays an action outside the repository.
- Reviewers stay read-only and return their full review in their final message;
  dispatches must not ask them to write report files. When persistence is needed,
  the controller saves the full returned text in the plan workspace as
  `<slug>-report.md`, with the reviewer identity recorded alongside it. This applies
  to initial task reviews, scoped re-reviews and final whole-branch reviews. Keep
  the existing ledger, ruling and retention rules; saving a report does not replace
  those records.
- After a final whole-branch review, in subagent-driven and inline (executing-plans)
  execution alike, fix (or rule on, as the skills allow) its Critical and Important
  findings in corrective rounds, up to five; then surface what remains. A round is one
  fix pass plus one scoped re-review of it, and another follows while that re-review
  reports any Critical or Important finding, persisting or introduced by the fix. Minor
  findings never enter a round; they go to the ledger as `minor (deferred)`, as both
  skills say. A fix subagent makes the fixes under subagent-driven execution; inline,
  you make them yourself, each still proven RED→GREEN with a green suite. A fresh
  reviewer runs the re-review whenever a subagent tool exists, inline too. This outranks
  executing-plans' "do not dispatch a re-review" and "no second fix pass" and
  subagent-driven-development's "exactly one scoped re-review" and "no second fix wave".
  Without a subagent tool, the re-review is a self-review, recorded as such in the
  ledger and the final message, as executing-plans' final-review fallback does. External
  actions stay gated.
