## Communication

<!-- rule:016ceef1ef2547f8aa157cb7eb3157cc begin -->
- If the user suddenly switches the conversation to a different project, confirm that it was intentional.
<!-- rule:016ceef1ef2547f8aa157cb7eb3157cc end -->
<!-- rule:de5f1d0582294f77b597b1a5b42c9d76 begin -->
- A message to the user at a turn end or a decision point (a final report, a progress
  update, a decision or approval request, a relayed review) includes what changes the
  user's understanding, decision or next action, and links the supporting record. By
  default it is one to five statements or fragments: the outcome; the task's actual
  state (done, stopped, still running, or blocked and on what); the one decision or
  who acts next, with any approval trigger; and any uncertainty, trade-off or
  limitation that could change the user's answer. The count is a default, not a cap:
  a line that changes a decision stays, and a paragraph packed into a bullet is not
  one statement. Prefer plain sentences and fragments to word compression. The
  message stands alone, without progress updates or a harness recap. This covers a
  skill's templated output to the user (brainstorming's playback chunks,
  executing-plans' review relays) and outranks the length the skill states.
  Reviewers' full reports to controllers and explanations the user asks for keep
  their full length.
<!-- rule:de5f1d0582294f77b597b1a5b42c9d76 end -->
<!-- rule:2c1ea3727a7447348cb807cfae1c735e begin -->
- Write task ids in replies and reports bare in their canonical form
  (`<prefix>-<6 hex>`), outside backticks and links, so a harness can colour them;
  an id inside a command shown as code stays in that command.
<!-- rule:2c1ea3727a7447348cb807cfae1c735e end -->
<!-- rule:fb8d914a2eb44a64acc7e086970328a0 begin -->
- Supporting detail leaves the message for the task record: findings and landed
  changes with their conditions and scope, verification and its limits (checks,
  results, test counts), deviations and their rulings, rejected options, and
  unfinished work with where it is tracked. Put it in a task note, the plan ledger,
  an attachment or a linked report before writing the message, check that the
  destination holds it and opens from the main checkout, and name it in the message
  in a few words. A decision request is one line: what it is blocked on, the
  recommended option, and one clause of reason, with the alternatives in the record.
  Work with no task record (a read-only answer, an ad hoc fix) keeps the detail in
  the message, after what the user needs first. Before shortening, check that no condition, reason or limit that could change the
  user's answer is lost and no claim becomes stronger.
<!-- rule:fb8d914a2eb44a64acc7e086970328a0 end -->
<!-- rule:19c566200a204b339abf808f84984c7d begin -->
- Required content is kept whole in the record, not the message: every required
  ruling (its own entry with the decision, labelled `Why:` (reason) and `Cost:` (if
  wrong), and revision references; say when a reason or cost was not recorded rather
  than inventing one), deferred minors, and the closing disclosures (pushes, this
  session's surviving processes, others' work, worktree state, and each branch left
  unmerged with its location and what integrates it: who approves, which command).
  Rulings and deferred minors stay in the plan ledger, with one task note naming
  them; verification, deviations and disclosures go in the done or park note. What
  the user must act on stays in the message: the approval or decision asked for and
  the text they must read to give it (or its frozen revision: repository, commit,
  path), a surviving process with its pid and stop command, an error only they can
  resolve, and each branch left unmerged, with its location and who integrates it.
  "Nothing was pushed" does not establish integration state; name the branch. Task
  notes are not shortened by these rules.
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
