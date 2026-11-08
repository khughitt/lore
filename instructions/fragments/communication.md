## Communication

<!-- rule:016ceef1ef2547f8aa157cb7eb3157cc begin -->
- If the user suddenly switches the conversation to a different project, confirm that it was intentional.
<!-- rule:016ceef1ef2547f8aa157cb7eb3157cc end -->
<!-- rule:de5f1d0582294f77b597b1a5b42c9d76 begin -->
- A message to the user at a turn end or a decision point (a final report, a progress
  update, a decision or approval request, a relayed review) includes what changes the
  user's understanding, decision or next action, and links the supporting record. Lead
  with the direct answer to the user's question, the decision or action needed from the
  user (with any approval trigger), or the outcome when no user action is needed. By
  default the message is one to five short statements or fragments covering that lead,
  the task's actual state (done, stopped, still running, or blocked and on what), who
  acts next, and any uncertainty, trade-off or limitation that could change the user's
  answer. When the user asks what they need to do, list the user's own actions first,
  separated from remaining agent work; starting more work or narrating agent steps does
  not answer the question. The count is a default, not a cap: a line that changes a
  decision stays, and a paragraph packed into a bullet is not one statement. Prefer
  plain sentences and fragments to word compression, and in a multi-item status list
  put each item on its own line with a bold status or verdict and a short reason. The
  message stands alone, without restating earlier progress updates or a harness recap.
  This covers a skill's templated output to the user (brainstorming's playback chunks,
  executing-plans' review relays) and outranks the length the skill states. Reviewers'
  full reports to controllers and explanations the user asks for keep their full
  length.
<!-- rule:de5f1d0582294f77b597b1a5b42c9d76 end -->
<!-- rule:2c1ea3727a7447348cb807cfae1c735e begin -->
- Write task ids in replies and reports bare in their canonical form
  (`<prefix>-<6 hex>`), outside backticks and links, so a harness can colour them;
  an id inside a command shown as code stays in that command.
<!-- rule:2c1ea3727a7447348cb807cfae1c735e end -->
<!-- rule:41b38a6426b946db94eee97bc7f044db begin -->
- Write a conversation or session UUID in replies and reports shortened to its first
  8 hex characters, as git shortens commit ids (`conversation://0653876d`, not the
  full UUID). Task notes, ledgers, reports to controllers and any command the user
  must run keep the full id.
<!-- rule:41b38a6426b946db94eee97bc7f044db end -->
<!-- rule:fb8d914a2eb44a64acc7e086970328a0 begin -->
- Supporting detail leaves the message for the task record: findings and landed
  changes with their conditions and scope, verification and its limits (routine
  passing checks, results, test counts), routine cleanup and non-actions ("nothing
  pushed", "no paid calls", "worktree cleaned up"), raw audit identifiers (full
  commit or file hashes, `rule:` UUIDs, retention flags) unless the user must run a
  command containing them, deviations and their rulings, rejected options, and
  unfinished work with where it is tracked. Put it in a task note, the plan ledger,
  an attachment or a linked report before writing the message, check that the
  destination holds it and opens from the main checkout, and name it in the message
  in a few words. A decision or approval request is one or two short sentences
  stating what is asked or blocked on, the recommended option, and one clause of
  reason, linking the record or change summary that holds the exact frozen revision
  and rejected alternatives (for example: "Approve activating the revised review
  policy? I recommend it because it removes redundant reviews. [Change summary](…).");
  for an amendment, state the change and its consequences, with the full document
  linked. Work with no task record (a read-only answer, an ad hoc fix) keeps in the
  message what these or any other rules send to the task record, after what the user
  needs first; the note lines under Task notes for outcome measures need a task and
  are skipped without one. Before shortening, check that no condition, reason or
  limit that could change the user's answer is lost and no claim becomes stronger.
<!-- rule:fb8d914a2eb44a64acc7e086970328a0 end -->
<!-- rule:19c566200a204b339abf808f84984c7d begin -->
- Required content is kept whole in the record, not the message: every required
  ruling (its own entry with the decision, labelled `Why:` (reason) and `Cost:` (if
  wrong), and revision references; say when a reason or cost was not recorded rather
  than inventing one), deferred minors, and the closing disclosures (pushes, this
  session's surviving processes, others' work, worktree state, and each branch left
  unmerged with its location and what integrates it: who approves, which command).
  Rulings and deferred minors stay in the plan ledger, with one task note naming them,
  and each deferred minor has an open owner before close (Processes);
  verification, deviations and disclosures (including routine non-actions such as
  "nothing pushed", no surviving process, a merged branch or a cleaned-up worktree)
  go in the done or park note. What the user must act on stays in the message: the
  approval or decision asked for and a link to the text or change summary they must
  read to give it (with its frozen revision — repository, commit and path, or path
  and sha256 — preserved in that linked record), a surviving process with its pid and
  stop command, an error only they can resolve, and each branch left unmerged, with
  its location and who integrates it. "Nothing was pushed" does not establish
  integration state; name an unmerged branch in the message and record a merged one
  in the note. Task notes are not shortened by these rules.
<!-- rule:19c566200a204b339abf808f84984c7d end -->
<!-- rule:f002b1ef713f42709b9de6b6b3701dc3 begin -->
- Use no emoji in what you write: replies, reports, and task text (titles, bodies,
  notes). Their fixed colours cannot follow a project's identity colour. Content a
  project itself asks for, and other Unicode such as arrows or box drawing, is not
  covered.
<!-- rule:f002b1ef713f42709b9de6b6b3701dc3 end -->
<!-- rule:718e79f5b3fa40249cb178139c26b28f begin -->
- A path you show the user is one they can open from where they stand, the main
  checkout: relative to it when the file lives there, absolute otherwise. Never write
  it relative to a directory only you know, such as the scratchpad (`scratchpad/x.md`
  resolves nowhere for the user). The Git rule against machine-specific absolute paths
  covers committed text, not what you tell the user.
<!-- rule:718e79f5b3fa40249cb178139c26b28f end -->
<!-- rule:65fcb49d5d7344d9a052800af708b9ee begin -->
- A sheet of images you hand the user to judge (an image grid, a contact sheet, a
  before/after pair, a parameter sweep) explains itself without its generator: a title
  stating the question; rows and columns labelled in plain language, with units where
  the axis has them; the baseline or control marked when there is one; one line on what
  to look for; and a short, stable id on each cell so a pick can be named back. Do not
  invent axes, units or a control the comparison lacks: unrelated candidates are a
  numbered set, not a grid. Before handing a sheet over, view the rendered image at the
  scale the user will see it and confirm the labels are legible.
<!-- rule:65fcb49d5d7344d9a052800af708b9ee end -->
