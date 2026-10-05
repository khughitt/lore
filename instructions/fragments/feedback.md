## Feedback

- Friction, a gap, or a notable success in the shared tooling goes to the project that
  owns it, at the moment, in one command; then carry on:
  `tasks feedback --project <owner> "<one line about the tool>" --category <friction|gap|idea|positive>`.
  "Feedback owners" under Projects below lists who owns what; the tasks skill has the
  mechanics (`-b`, `--recur`, `--new`, following up).
- Report when a hook or gate blocked you wrongly, or its message did not say what to do
  (`friction`, to the owner it names); when an instruction or skill told you to do
  something a tool refused, or two instructions contradicted each other (`friction`, to
  the instruction's owner); when you needed something the tooling does not do and worked
  around it (`gap`); when something saved you real work (`positive`); and when a flow
  retro's lesson is about the tooling rather than the task (file it too, and put the
  returned id in the retro).
- Describe the tool, never the project: no repository names, paths, people, or project
  content, whatever the checkout's profile. One report per distinct issue; never triage
  your own.
- Filing needs a tracked checkout (one with `tasks/.config.toml`) to stand in. Elsewhere,
  do not file and do not borrow another checkout with `-C`, which would misstate the
  source: name the tool, its owner, and what went wrong in your end-of-turn report, and
  the user decides.
