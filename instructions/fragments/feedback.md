## Feedback

<!-- rule:09d96981ac844d2fbfcb375c3bd77994 begin -->
- Friction, a gap, or a notable success in the shared tooling goes to the project that
  owns it, at the moment, in one command; then carry on:
  `tasks feedback --project <owner> "<one line about the tool>" --category <friction|gap|idea|positive>`.
  "Feedback owners" under Projects below lists who owns what; the tasks skill has the
  mechanics (`-b`, `--recur`, `--new`, following up).
<!-- rule:09d96981ac844d2fbfcb375c3bd77994 end -->
<!-- rule:7bea58c0548e40e38d39247aa236a76d begin -->
- A report that relays the user's request, or carries more than one ask about one
  issue, is still one command (distinct issues still get one report each), with a body
  (`-b`, one line on a recurrence) of a few concrete sentences covering what applies:
  each distinct outcome asked for, in tool terms; the action that hit the friction; what
  happened against what was expected; and any constraint that matters. Mark what the
  user asked apart from your reading of it, and write the body to stand without the
  transcript. Like the title, it describes the tool, never the project, even when it
  relays the user's words (the rule below).
<!-- rule:7bea58c0548e40e38d39247aa236a76d end -->
<!-- rule:3626fd73a87c4d438ac6a0b6c3ffbf27 begin -->
- Report when a hook or gate blocked you wrongly, or its message did not say what to do
  (`friction`, to the owner it names); when an instruction or skill told you to do
  something a tool refused, or two instructions contradicted each other (`friction`, to
  the instruction's owner); when you needed something the tooling does not do and worked
  around it (`gap`); when something saved you real work (`positive`); and when a flow
  retro's lesson is about the tooling rather than the task (file it too, and put the
  returned id in the retro).
<!-- rule:3626fd73a87c4d438ac6a0b6c3ffbf27 end -->
<!-- rule:406df98201e14fe9b3a736887d7010b2 begin -->
- The user's feedback on how agents behave or what they produce, and any request to
  make a lesson a pattern, is filed the same way, to the project that owns the guidance
  or tool it would change (`lore` for the global instructions and skills). A memory may
  keep a local copy; it never replaces the report. A request about the current task
  alone (fix this file, relabel this sheet) is ordinary work, not a new rule.
<!-- rule:406df98201e14fe9b3a736887d7010b2 end -->
<!-- rule:a5554bc873f348648268c912ee06b92a begin -->
- Describe the tool, never the project: no repository names, paths, people, or project
  content, whatever the checkout's profile. One report per distinct issue; never triage
  your own.
<!-- rule:a5554bc873f348648268c912ee06b92a end -->
<!-- rule:92d0731cd46d4f88913d0e99ac92ec52 begin -->
- File from where you stand. A project checkout (one `tasks where` names a project
  for, whatever its `kind`: records in the tree, under the records root, or linked)
  reports under its project's prefix; outside every project the report
  is tagged `from:unregistered`. Never borrow another checkout with `-C`, which would
  misstate the source. If filing fails (a broken config, `tasks` missing), name the
  tool, its owner, and the error in your end-of-turn report, and the user decides.
<!-- rule:92d0731cd46d4f88913d0e99ac92ec52 end -->
<!-- rule:bd35453d8e704d1c8905187a28adc47f begin -->
- A defect in code the user does not maintain (a vendored submodule, an installed tool, a
  library) is checked upstream before anything else, scoping included: search the
  project's open and closed issues and PRs, its default and development branches, and
  its changelog for a report or fix, and note on the task what was searched and found.
  Reproduce or patch only after that search.
<!-- rule:bd35453d8e704d1c8905187a28adc47f end -->
<!-- rule:10ed8d349aee4d89b942d408f1e43176 begin -->
- When a report or fix exists, link it on the task and decide among waiting for the
  release, pinning the fixing commit, and carrying a local workaround that names the
  upstream link and the release that retires it. Comment or react upstream only to add
  what the maintainers lack (a new reproduction, environment, or confirmation).
<!-- rule:10ed8d349aee4d89b942d408f1e43176 end -->
<!-- rule:5478cf24c27543bfb7d7f9186b9e6199 begin -->
- When none exists, confirm the root cause with a minimal reproduction, read the
  project's contributor guidelines, agent instructions and issue or PR templates, and
  prepare the issue or patch to follow them. Any upstream post, comment or reaction is
  an action outside the repository: prepare it, and the user approves publishing it.
<!-- rule:5478cf24c27543bfb7d7f9186b9e6199 end -->
