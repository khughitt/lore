## Trials

<!-- rule:b2d5d7b434c74989a11e2b7a88dcd829 begin -->
After `tasks start`, run `~/.agents/bin/trial-arm <id>` and follow what it prints.
`flow on` runs the task under the flow skill; `flow off` runs it without flow,
whatever else would choose it; `not enrolled` changes nothing. Every task in a unit
has the unit's arm, and the task's `process` is unchanged in both arms. Only the user
overrides an arm: record it with `tasks note <id> "arm: <trial> — override: <why>"`.
If it exits non-zero, show the user its error and do not choose flow on or off until they answer.
<!-- rule:b2d5d7b434c74989a11e2b7a88dcd829 end -->
