## Processes

- A smoke or live-run script an agent launches detached (`setsid nohup … & disown`, a
  background `bun`, `node` or `weston`, a tmux server) owns its cleanup: it records the
  pids it spawns and reaps them on its own exit and on the harness's stop (a `trap` on
  EXIT, TERM and INT, or killing the tmux session), so a closed terminal never leaves a
  child burning CPU in a dead `kitty-*.scope`. A process that must outlive the turn (a
  server a later step drives) is named in the end-of-turn report with its pid and how to
  stop it; before that report, `host-load --section session` (ops's `bin/host-load`, on
  `~/.local/bin`) lists what this session's scope left running, and the report repeats
  it or says nothing was left. `host-load` also names the load a preflight refuses on
  and sweeps orphans across sessions; its `--kill` is the user's decision, not yours.
- A launcher that leaves a process running behind a tracked channel (the harness's
  shell tool, `ssh host cmd`, a hook) redirects all three of that process's standard
  streams (`</dev/null >log 2>&1`): a child that inherits stdout or stderr holds the
  call open after the launcher returns, and `&`, `nohup` and `setsid` close nothing.
- A process meant to outlive the session needs the user's approval at that moment (a
  persistent service is a host change), then starts as a transient user service:
  `systemd-run --user --unit=<name> --service-type=exec --working-directory=<dir>
  [-E VAR=value] <cmd>`, once `systemctl --user` answers and, for a launch over ssh,
  lingering is on (`loginctl show-user <user> -p Linger`; enabling it is the user's
  decision). When a check fails, report which one and launch nothing; `setsid` and
  `nohup` are no fallback. Its return means started, not ready, so a bounded readiness
  check (its port, a health command) follows, and the report names the unit,
  `journalctl --user -u <name>` and `systemctl --user stop <name>`. Neither `setsid`,
  which leaves the process in the terminal's scope, nor `systemd-run --scope`, which
  runs it as systemd-run's own child with the caller's environment and blocks until it
  exits, is a service launch. A server that a later step of this session drives stays
  under the cleanup bullet above.
- Never end a turn waiting on work the harness does not track. Run a long check in the
  foreground with a timeout that covers it, or through the harness's own background
  mechanism; a job detached with `&` or `nohup` never wakes you, so no turn ends waiting
  on a monitor of one. Claude Code's background Bash (`run_in_background`) is stopped at
  its `timeout`, 30 min when unset and at most 2 h: set it to cover the run. A run
  longer than 2 h is split into resumable slices (an incremental job run in bounded
  passes, each under the limit, e.g. with `timeout --signal=INT`) or handed to a tracked
  process the user agrees to. A controller with a running child ends its turn only where
  the harness is known to start its next turn when the child finishes (Claude Code: yes;
  Codex: no — probed 2026-09-24 and recorded in ops `hooks/claim-guard`'s
  `CHILD_WAKES`), and otherwise waits with the harness's bounded wait, at its longest
  (Codex: `wait_agent` with `timeout_ms: 3600000`, an empty `write_stdin` with
  `yield_time_ms: 300000`; both return as soon as the child or command finishes), never
  a loop of shorter waits. Before each such wait, post one line naming what you await,
  how long it should take and the wait's limit; when it returns, post one status line.
  This outranks a harness's own shorter guidance: Codex's base instructions' 60-second
  cap on blocking waits and on gaps between updates, and the vendored superpowers
  `codex-tools` reference's 5–10 minute stretches. A worker's turn end is its final
  report: it reports and stops only when its assignment is complete or blocked on its
  controller or a person, never with its own check still running. A child's "waiting on
  background work" is unverified until you check that the process or its output exists;
  after a wake-up, report what you observed, never a notification that did not arrive.
- Before committing to an extended run (a benchmark, capture, experiment, or sweep that
  takes more than a few minutes, and above all one that needs the user off the machine),
  first run the smallest version that exercises every gate end to end through its
  verdict, one case per check, and read the result. When a long run is refused or
  aborted partway, analyze the parts it completed before changing the environment and
  retrying. When asking for the machine, name the pilot and what it showed.
- A task that spans sessions keeps its inputs where a reboot cannot take them. Its
  scratch lives in a per-task directory on persistent host-local storage off the synced
  tree, `$WORK_ROOT/<project>/<task-id>/` (on a host without `WORK_ROOT`, ask the user
  where rather than inventing a path). tmpfs (`/dev/shm`, `/tmp`, `/run`) holds only
  per-run copies made from that persistent canonical copy, and a park names the
  canonical copy's path and sha256 (a sha256 manifest for a directory). A resume
  checks that its inputs exist and match the recorded hash before it claims an
  idle-host window or the user's machine.
- Work that takes the live desktop (opens windows on it, moves focus, switches
  workspaces, captures the screen) is a host-use action, and approving a plan does not
  grant it. Prefer a nested or headless compositor where the project has one; otherwise
  ask at that moment, naming what will appear and for how long, or `tasks park --reason
  quiet` the work. A retry or a later capture asks again rather than reusing an earlier
  yes.
- A dispatch that asks a subagent to write its report to a file names that file
  `<slug>-report.md` (`task-3-report.md`, `audit-report.md`), never a `.md` name
  starting with `report`, `summary`, `findings` or `analysis` in any case
  (`report.md`, `Summary-x.md`, `findings.md`). Claude Code refuses a subagent's write
  to those names ("Subagents should return findings as text"), and the whole report
  then lands in the subagent's final message instead of the file. hq's
  `subagent-write-refused` capability fact records the rule and its probe.
