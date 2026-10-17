"""The SessionStart profile hook, in lore: context stdout and an AGENT_PROFILE export.

The sandbox is the subset of ops's ProfileSandbox the hook needs, built here because a test
cannot import another repository's helpers: a registry naming scratch ops, tack, lore, ns and
wrk4 (the last under a d/employer family directory, so the scratch profiles.toml's absolute
family path validates); profiles.toml and identity-mirror.toml in the scratch ops; lore
profile fragments; git checkouts; and the live ops checkout's bin/ops-profile with the two
siblings it loads from beside itself, copied into the scratch ops bin/. Beyond the live
registry (to find ops) and those three files, nothing on the machine is read.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

HOOK = pathlib.Path(__file__).resolve().parent.parent / "hooks" / "claude-profile"
OPS_SIBLINGS = ("ops-profile", "ops-projects", "tt")

PROFILES = """
[profile.personal]
fragment = "personal"
home = "personal"
design_docs = "commit"
gh_account = "khughitt"
pr_draft = "by-permission"
git_identity = "Me <khughitt@example.invalid>"

[profile.work]
fragment = "work"
home = "work"
design_docs = "exclude"
gh_account = "work-account"
pr_draft = "by-permission"
git_identity = "Me <work-account@example.invalid>"

[profile.external]
fragment = "external"
home = "personal"
design_docs = "exclude"
gh_account = "khughitt"
pr_draft = "required"
git_identity = "Me <khughitt@example.invalid>"

[profile.science]
fragment = "science"

[[family]]
path = "{employer}"
profiles = ["work"]

[default]
profiles = ["external"]

[home.personal]
claude = "~/.claude"
codex = "~/.codex"

[home.work]
claude = "~/.claude-work"
codex = "~/.codex-work"
"""


def live_ops_root():
    registry = pathlib.Path(os.environ.get("XDG_CONFIG_HOME") or pathlib.Path.home() / ".config") / "tasks" / "projects.toml"
    return pathlib.Path(os.path.expanduser(tomllib.loads(registry.read_text())["projects"]["ops"]))


class ProfileSandbox(unittest.TestCase):
    def setUp(self):
        self.base = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.enterContext(patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.base.parent)}))
        self.config = self.base / ".config" / "tasks"
        self.config.mkdir(parents=True)
        self.ops = self.base / "ops"
        (self.ops / "bin").mkdir(parents=True)
        live = live_ops_root() / "bin"
        for name in OPS_SIBLINGS:
            shutil.copy2(live / name, self.ops / "bin" / name)
        self.tack = self.base / "tack"
        self.lore = self.base / "lore"
        (self.lore / "profiles").mkdir(parents=True)
        for name in ("personal", "work", "external", "science"):
            (self.lore / "profiles" / f"{name}.md").write_text(f"# Profile: {name}\n\nText for {name}.\n")
        self.employer = self.base / "d" / "employer"
        self.employer.mkdir(parents=True)
        self.profiles(PROFILES.format(employer=self.employer))
        self.identity('[lore]\nname = "lore"\npurpose = "p"\nprofiles = ["personal"]\n'
                      '[tack]\nname = "tack"\npurpose = "p"\nprofiles = ["personal"]\n'
                      '[wrk4]\nname = "workproj-2"\npurpose = "p"\nprofiles = ["work"]\n'
                      '[ns]\nname = "ns"\npurpose = "p"\nprofiles = ["personal", "science"]\n')
        self.wrk4 = self.employer / "workproj-2"
        self.ns = self.base / "d" / "ns"
        for path in (self.tack, self.lore, self.wrk4, self.ns):
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
        self.registry(lore=self.lore, tack=self.tack, ops=self.ops, wrk4=self.wrk4, ns=self.ns)

    def registry(self, **roots):
        body = "".join(f'{p} = "{r}"\n' for p, r in roots.items())
        (self.config / "projects.toml").write_text(f"[projects]\n{body}")

    def profiles(self, text):
        (self.ops / "profiles.toml").write_text(text)

    def identity(self, text):
        (self.ops / "identity-mirror.toml").write_text(text)

    def env(self, **extra):
        env = {"HOME": str(self.base), "XDG_CONFIG_HOME": str(self.base / ".config"), "PATH": os.environ["PATH"],
               "GIT_CEILING_DIRECTORIES": os.environ["GIT_CEILING_DIRECTORIES"]}
        env.update(extra)
        return env


class ProfileHookTests(ProfileSandbox):
    def run_hook(self, cwd, payload=None, **extra):
        env_file = self.base / "env.sh"
        payload = json.dumps(payload or {"hook_event_name": "SessionStart", "cwd": str(cwd)})
        env = self.env(CLAUDECODE="1", CLAUDE_ENV_FILE=str(env_file), **extra)
        result = subprocess.run([sys.executable, str(HOOK)], input=payload, env=env,
                                capture_output=True, text=True)
        return result, env_file.read_text() if env_file.exists() else ""

    def test_the_line_and_fragments_reach_stdout(self):
        result, exports = self.run_hook(self.ns)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("profile: personal, science (identity-mirror.toml [ns].profiles); "))
        self.assertIn("# Profile: science", result.stdout)
        self.assertEqual(exports, "export AGENT_PROFILE=personal,science\n")

    def test_the_payload_transcript_names_the_home(self):
        # Codex inside a Claude session: CLAUDECODE=1 inherited, transcript under the Codex work home
        payload = {"hook_event_name": "SessionStart", "cwd": str(self.wrk4), "source": "startup",
                   "transcript_path": str(self.base / ".codex-work" / "sessions" / "r.jsonl")}
        result, _ = self.run_hook(self.wrk4, payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("; home: work; ", result.stdout.splitlines()[0])
        self.assertNotIn("warning:", result.stdout)

    def test_a_failure_is_one_line_and_exit_zero(self):
        self.identity("")
        result, exports = self.run_hook(self.tack)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "profile: unresolved — tack is registered but identity-mirror.toml [tack] declares no profiles; "
                                        "run ops-profile session after fixing it\n")
        self.assertEqual(exports, "")

    def test_bad_input_falls_back_to_the_process_cwd(self):
        result = subprocess.run([sys.executable, str(HOOK)], input="not json", env=self.env(CLAUDECODE="1"),
                                cwd=self.wrk4, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("profile: work (identity-mirror.toml [wrk4].profiles); "))

    def test_an_unregistered_ops_is_one_line_naming_the_registry(self):
        self.registry(lore=self.lore, tack=self.tack, wrk4=self.wrk4, ns=self.ns)
        result, exports = self.run_hook(self.ns)
        self.assertEqual(result.returncode, 0)
        first = result.stdout.splitlines()[0] if result.stdout else ""
        self.assertTrue(first.startswith("profile: unresolved — "), result.stdout)
        self.assertIn(str(self.config / "projects.toml"), first)
        self.assertEqual(exports, "")

    def test_a_malformed_registry_is_one_line_with_the_parse_message(self):
        (self.config / "projects.toml").write_text("[projects\nops = ")
        result, _ = self.run_hook(self.ns)
        self.assertEqual(result.returncode, 0)
        first = result.stdout.splitlines()[0] if result.stdout else ""
        self.assertTrue(first.startswith("profile: unresolved — "), result.stdout)
        self.assertIn("is not valid TOML", first)

    def test_a_non_string_ops_entry_is_one_line_naming_the_registry(self):
        (self.config / "projects.toml").write_text("[projects.ops]\npath = 1\n")
        result, _ = self.run_hook(self.ns)
        self.assertEqual(result.returncode, 0)
        first = result.stdout.splitlines()[0] if result.stdout else ""
        self.assertTrue(first.startswith("profile: unresolved — "), result.stdout)
        self.assertIn(str(self.config / "projects.toml"), first)

    def test_a_registered_ops_without_the_resolver_is_one_line(self):
        (self.ops / "bin" / "ops-profile").unlink()
        result, _ = self.run_hook(self.ns)
        self.assertEqual(result.returncode, 0)
        first = result.stdout.splitlines()[0] if result.stdout else ""
        self.assertTrue(first.startswith("profile: unresolved — "), result.stdout)
