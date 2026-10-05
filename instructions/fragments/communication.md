## Communication

- If the user suddenly switches the conversation to a different project, confirm that it was intentional.
- A path you show the user is one they can open from where they stand, the main
  checkout: relative to it when the file lives there, absolute otherwise. Never write
  it relative to a directory only you know, such as the scratchpad (`scratchpad/x.md`
  resolves nowhere for the user). The Git rule against machine-specific absolute paths
  covers committed text, not what you tell the user.
