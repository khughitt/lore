## Shell

<!-- rule:5b1c2e9a734c498fb8285b1eb1cba9cf begin -->
- Claude Code's Bash tool runs bash (`CLAUDE_CODE_SHELL` in its settings); Codex's
  shell tool runs the login shell, zsh. Under zsh an unquoted word starting with `=`
  (`echo ===`) or a glob that matches nothing (`--include=*.py`) fails the whole
  command line: quote them (`echo '==='`, `--include='*.py'`).
<!-- rule:5b1c2e9a734c498fb8285b1eb1cba9cf end -->
<!-- rule:14ca161849ea4f398d3ce84106c6cfa2 begin -->
- `tasks root <task-id>` takes a full task id and prints the registered root of its
  project (`--pretty` for the bare path); it refuses a bare prefix. To find a project
  by prefix, read `tasks projects --paths --pretty`, or the `root` field of its default
  JSON rows. Never invent an id to feed `root` or hardcode a host path. Both name the
  registered root, the main checkout: a command run without a scope inside a worktree
  still reads that worktree, and neither lookup replaces it.
<!-- rule:14ca161849ea4f398d3ce84106c6cfa2 end -->
<!-- rule:b94c3ae8c7ca4e1db9a4c1502357ebe0 begin -->
- `pkill -f <pattern>` also matches the shell running it, whose command line contains
  the pattern, and kills it: use `pkill -f '[p]attern'` or kill the pid you recorded.
<!-- rule:b94c3ae8c7ca4e1db9a4c1502357ebe0 end -->
<!-- rule:0472de81465f41dcb870eec7f86bfa47 begin -->
- A skill read through the shell rather than loaded natively is read completely before
  you rely on it, in explicit ranges (`sed -n '1,150p'`) small enough for both the
  command's output limit and the response that carries it: reads batched into one call
  share that response, so never concatenate large skills into one. Line counts do not
  bound bytes; size ranges from `wc -c`. Any truncation marker means the read is
  incomplete: fetch the omitted range in smaller calls before acting on the skill. A
  heading search or `head` locates content but does not replace reading it. A complete
  read already in context stands until truncation or context loss removes part of it.
<!-- rule:0472de81465f41dcb870eec7f86bfa47 end -->
