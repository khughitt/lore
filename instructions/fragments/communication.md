## Communication

- If the user suddenly switches the conversation to a different project, confirm that it was intentional.
- Final work reports lead with a short paragraph: outcome first, the task's actual
  state, and who acts next, including any action or approval trigger the user needs.
  No fixed lead marker or word cap. The report stands alone without progress updates
  or a harness recap; omit empty sections and use plain paragraphs when a brief reply
  suffices. This shape does not shorten reviewers' full reports to controllers.
- Write task ids in replies and reports bare in their canonical form
  (`<prefix>-<6 hex>`), outside backticks and links, so a harness can colour them;
  an id inside a command shown as code stays in that command.
- Follow with the salient findings or landed changes, one claim per bullet when a
  list helps. Keep each claim's conditions, reasons, scope and uncertainty with it;
  do not pack independent changes into one sentence. Include verification and its
  limits (checks, results and test counts where reported), deviations and their
  rulings, and unfinished work with where it is tracked. Supporting detail may move
  to a link only after checking that the destination holds it and opens from the main
  checkout. Before shortening, check that no condition, reason or limit is lost and
  no claim becomes stronger; covering the same topics is not enough.
- Keep required content in the final message, whole: text under approval, every
  required ruling and any deferred minors the governing workflow requires. Give
  each ruling its own entry with the decision, labelled `Why:` (reason) and `Cost:`
  (if wrong), and revision references; an entry may wrap. Say when a reason or cost
  was not recorded rather than inventing one. Close with a concise line of applicable
  disclosures about pushes, this session's surviving processes, others' work and
  worktree state; retain required process ids and stop instructions. These rules
  govern final reports, not progress updates or task notes.
- Use no emoji in what you write: replies, reports, and task text (titles, bodies,
  notes). Their fixed colours cannot follow a project's identity colour. Content a
  project itself asks for, and other Unicode such as arrows or box drawing, is not
  covered.
- A path you show the user is one they can open from where they stand, the main
  checkout: relative to it when the file lives there, absolute otherwise. Never write
  it relative to a directory only you know, such as the scratchpad (`scratchpad/x.md`
  resolves nowhere for the user). The Git rule against machine-specific absolute paths
  covers committed text, not what you tell the user.
- A sheet of images you hand the user to judge (an image grid, a contact sheet, a
  before/after pair, a parameter sweep) explains itself without its generator: a title
  stating the question; rows and columns labelled in plain language, with units where
  the axis has them; the baseline or control marked when there is one; one line on what
  to look for; and a short, stable id on each cell so a pick can be named back. Do not
  invent axes, units or a control the comparison lacks: unrelated candidates are a
  numbered set, not a grid. Before handing a sheet over, view the rendered image at the
  scale the user will see it and confirm the labels are legible.
