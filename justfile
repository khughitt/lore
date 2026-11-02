# Front door for tests. Copy to the project root and fill in the three commands below.
# Inner loop: `just test-one <runner args>` on the test at hand, `just test-fast`
# (affected-only) before committing. Full suite: `just test`.
# Gates: `just check` at pre-commit, `just gate` at pre-push and in CI.
# The git hooks call `hook-pre-commit` and `hook-pre-push` instead, which run the very
# same commands under their own target names. Hook cost is the number this design exists
# to measure, and it is invisible if the hooks record as `check` and `test`.
# Adoption: copy templates/githooks/ to .githooks/ and run
# `git config core.hooksPath .githooks`; append templates/gitignore to .gitignore so the
# fallback log directory `.tt/` is never committed; vendor ops bin/tt as tools/tt and ops
# bin/ops-check as tools/ops-check; vendor ops bin/ops-docs as tools/ops-docs and copy templates/identity.toml, templates/README.md, and templates/AGENTS.md (design: docs/specs/2026-09-22-project-guides-design.md). The check command runs ops-check first: the shared
# hygiene checks (doc references exist, no Dropbox conflicted copies) in milliseconds.
# Every recipe runs through the vendored timing wrapper so the run is recorded. The
# wrapper counts tests from stdout; if the runner reports on stderr (python unittest
# does), end that command with `2>&1`.
# Design: ops docs/specs/2026-09-04-test-ci-audit-design.md, docs/specs/2026-09-28-test-ci-act-design.md.
# Recipe lines are not echoed: the wrapper records every command it runs, `tasks check`
# is silent when clean, and a clean commit should print nothing. `just --verbose` shows them.
set quiet
set positional-arguments

tt := "python3 tools/tt"

# Every test command first checks the locked environment `just setup` installs: a missing
# .venv, or one a system Python upgrade has broken, fails here and names the fix instead of
# letting a runner create or reuse an environment in place.
venv_guard := "{ .venv/bin/python -c \"import pytest, xdist\" >/dev/null 2>&1 || { echo \"test recipes need the locked environment: run just setup\" >&2; exit 1; }; }"

# The three commands, each written once. Recipes and hooks all run these, so a hook can
# never drift from the gate it is supposed to be. Avoid single quotes inside them.
# With no affected-only mechanism, set fast_cmd to the same command as test_cmd and say
# so here; the target must always exist and the report shows the gap as equal durations.
# Fast and full run the same tools directory; there is no affected-only selection.
# Both run it on 4 pytest-xdist workers from the locked environment. Pilot on a 32-CPU host,
# 2026-10-31, 396 tests: serial 149 s, -n 4 34.5 s, -n 8 19.6 s (load 7-8); 4 is the
# smallest count under the 45 s target. Not -n auto: that starts one worker per CPU (32
# there), each building its own fixture template, on a host shared with other sessions.
# Temporary JUnit reports let tt record each run's five slowest tests.
fast_cmd := venv_guard + " && .venv/bin/python -m pytest -n 4 tools -q -rs --junitxml=\"${TT_JUNIT_DIR:?run through tt}/pytest.xml\""
test_cmd := venv_guard + " && .venv/bin/python -m pytest -n 4 tools -q -rs --junitxml=\"${TT_JUNIT_DIR:?run through tt}/pytest.xml\""
check_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check && python3 bin/assemble-instructions check && python3 -m py_compile bin/skill-sizes.py bin/assemble-instructions tools/instruction-assembly-proof-driver.py hooks/claude-profile"

# Staged paths that cannot change the code checks' verdict: a commit staging only these
# runs docs_check_cmd instead of check_cmd. fnmatch globs, `*` crossing `/`. Narrow it
# when docs/ holds executable examples, fixtures, or anything a test reads; set it to
# "" to always run the full check.
docs_paths := "*.md docs/* instructions/* profiles/* skills/*"
docs_check_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check && python3 bin/assemble-instructions check"

# Remote refs whose push makes CI run the full suite (test_cmd or its equivalent), as
# space-separated fnmatch globs: "refs/heads/main", or "refs/heads/*" when CI runs it on
# every branch push. fnmatch's * crosses /, so "refs/heads/*" matches what Actions
# writes as branches: ['**'] (or no branch filter); Actions' ['*'] skips feature/x.
# Leave "" when CI runs no full suite on push: a workflow that runs a subset, or only on
# a schedule or on pull requests, covers no ref. A push takes the shortened gate only
# when CI covers every ref in it.
ci_suite_refs := ""

# The remote whose pushes CI runs for: a push to any other remote (a mirror, a fork)
# takes the full gate.
ci_remote := "origin"

# The profile-hook tests against the live ops checkout the host registry names. ops is
# private, so no hosted runner has it: the workflow sets LORE_TEST_LIVE_OPS=unavailable and
# those tests skip there with a stated reason. Both pre-push recipes run this target, which
# is not broad, so they stay routinely checked on the hosts that have ops (about 2 s).
live_cmd := venv_guard + " && .venv/bin/python -m pytest tools/test_claude_profile.py -q -rs --junitxml=\"${TT_JUNIT_DIR:?run through tt}/pytest.xml\""

# The runner with no selection of its own: `test-one` appends the caller's arguments,
# each one intact, and nothing else; do not end it with `2>&1` (the recipe does). Which
# forms work is the runner's business (pytest: a path, path::name, -k expr; vitest: a
# filename filter, -t "<name>"); name them in AGENTS.md under Gates.
one_cmd := venv_guard + " && .venv/bin/python -m pytest --junitxml=\"${TT_JUNIT_DIR:?run through tt}/pytest.xml\""

# What a fresh checkout or worktree needs before the suite can run: dependency installs
# (npm ci, uv sync) and any gitignored inputs the tests read, hydrated from the main
# checkout or a store. Idempotent; safe to rerun. The worktree convention runs it right
# after `git worktree add`, so a suite that fails before `just setup` is an unhydrated
# tree, not a bug. Recorded like the gates, because setup that recurs is a cost.
# Start with `just work-link` naming the directories this project generates
# (.venv, target; never node_modules), then install. In a Dropbox checkout,
# finish each install that creates a directory work-link does not cover
# (node_modules, caches) with the native ignore command on it, e.g.
# `npm ci && attr -s com.dropbox.ignored -V 1 node_modules`. Reapply after
# installation: package managers can replace the directory and lose its
# attribute. Build output (dist, build, .svelte-kit) is the same case: a build
# that removes its output directory ends by marking the new one, and one that
# can empty the directory instead keeps the attribute. Dots' dropbox-ignore-flux
# catches both kinds only every two hours. Use explicit, audited paths; never
# ignore source parents. Linux needs attr installed. Attribute failures must
# fail setup, not be swallowed.
# Initialize the pinned skill submodule after preparing host-local worktree storage, then
# install the locked test environment (pyproject.toml, uv.lock) into the work-linked .venv.
setup_cmd := "just work-link .worktrees .venv && git submodule update --init && uv sync --frozen"

# Affected-only: the inner loop.
test-fast:
    {{tt}} test-fast -- sh -c '{{fast_cmd}}'

# One file, one test, or a filter, while working on it. Needs at least one argument;
# the whole suite is `test`. The sh -c string never holds the arguments, so quotes, $
# and globs in them reach the runner untouched. stderr is folded in because the
# arguments come last, so one_cmd cannot end with `2>&1` itself, and runners such as
# unittest print their summary there.
test-one +args:
    {{tt}} test-one -- sh -c '{{one_cmd}} "$@" 2>&1' test-one "$@"

# The full suite. Broad: under a policy-off .tt.toml it records a skip instead of running.
test:
    {{tt}} test -- sh -c '{{test_cmd}}'

# The deliberate local full run, whatever the policy. Untimed alias: only the inner test
# is recorded, as forced.
test-full:
    TT_FORCE=1 just test

# The live-ops profile tests (see live_cmd). Not broad: runs under every policy.
test-live:
    {{tt}} test-live -- sh -c '{{live_cmd}}'

# Seconds, not minutes: the mandatory hygiene. Every check here is inexpensive, so
# there is no broad check-code target.
check-hygiene:
    {{tt}} check-hygiene -- sh -c '{{check_cmd}}'

check: check-hygiene

gate: check test-live test

# Regenerate identity regions in README.md and AGENTS.md, and the README status region,
# from identity.toml and the tracker. The only thing that edits those regions; `check`
# refuses a commit while they are out of date.
docs:
    {{tt}} docs -- python3 tools/ops-docs write

# Ask work-link to put the named generated directories (.venv, target; never
# node_modules) off the synced tree behind in-tree links. Absent command: this machine
# has no dotfiles, entries stay in-tree, exit 0. Present: its own exit status,
# so unavailable storage fails setup instead of rebuilding in-tree.
work-link *names:
    {{tt}} work-link -- sh -c 'if command -v work-link >/dev/null; then work-link --ensure {{names}}; fi'

# Make this checkout runnable. Run once after `git worktree add`; rerun after a
# dependency change.
setup:
    {{tt}} setup -- sh -c '{{setup_cmd}}'

# What the pre-commit hook runs: `check`'s command under its own hook target.
hook-pre-commit:
    {{tt}} hook-pre-commit -- sh -c '{{check_cmd}}'

# What the pre-commit hook runs when every staged path is in docs_paths.
hook-pre-commit-docs:
    {{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'

# What the pre-push hook runs: hygiene timed once under the hook target, then the
# live-ops tests and the suite under their own targets, each recording its own policy
# decision. From this split on, hook-pre-push times hygiene only: its earlier durations
# (hygiene plus suite) are not comparable.
hook-pre-push:
    {{tt}} hook-pre-push -- sh -c '{{check_cmd}}'
    just test-live
    just test

# What the pre-push hook runs when CI runs the full suite for every pushed ref. The fast
# loop is the same complete tools directory: lore has no affected-only selection.
hook-pre-push-fast:
    {{tt}} hook-pre-push-fast -- sh -c '{{check_cmd}}'
    just test-live
    just test-fast

# Build delivered instructions and their provenance; pass explicit owner roots in preparation.
assemble *args:
    {{tt}} assemble -- python3 bin/assemble-instructions write "$@"
