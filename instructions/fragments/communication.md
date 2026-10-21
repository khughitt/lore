## Communication

- If the user suddenly switches the conversation to a different project, confirm that it was intentional.
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
