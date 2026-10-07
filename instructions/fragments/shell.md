## Shell

- Claude Code's Bash tool runs bash (`CLAUDE_CODE_SHELL` in its settings); Codex's
  shell tool runs the login shell, zsh. Under zsh an unquoted word starting with `=`
  (`echo ===`) or a glob that matches nothing (`--include=*.py`) fails the whole
  command line: quote them (`echo '==='`, `--include='*.py'`).
- `pkill -f <pattern>` also matches the shell running it, whose command line contains
  the pattern, and kills it: use `pkill -f '[p]attern'` or kill the pid you recorded.
- A skill read through the shell rather than loaded natively is read completely before
  you rely on it, in explicit ranges (`sed -n '1,150p'`) small enough for both the
  command's output limit and the response that carries it: reads batched into one call
  share that response, so never concatenate large skills into one. Line counts do not
  bound bytes; size ranges from `wc -c`. Any truncation marker means the read is
  incomplete: fetch the omitted range in smaller calls before acting on the skill. A
  heading search or `head` locates content but does not replace reading it. A complete
  read already in context stands until truncation or context loss removes part of it.
