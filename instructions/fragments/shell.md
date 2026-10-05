## Shell

- Claude Code's Bash tool runs bash (`CLAUDE_CODE_SHELL` in its settings); Codex's
  shell tool runs the login shell, zsh. Under zsh an unquoted word starting with `=`
  (`echo ===`) or a glob that matches nothing (`--include=*.py`) fails the whole
  command line: quote them (`echo '==='`, `--include='*.py'`).
- `pkill -f <pattern>` also matches the shell running it, whose command line contains
  the pattern, and kills it: use `pkill -f '[p]attern'` or kill the pid you recorded.
