"""The SessionStart profile hook: context stdout and an AGENT_PROFILE export."""
import json
import pathlib
import subprocess
import sys

from tests.test_ops_profile import ProfileSandbox

HOOK = pathlib.Path(__file__).resolve().parent.parent / "hooks" / "claude-profile"


class ProfileHookTests(ProfileSandbox):
    def run_hook(self, cwd, **extra):
        env_file = self.base / "env.sh"
        payload = json.dumps({"hook_event_name": "SessionStart", "cwd": str(cwd)})
        env = self.env(CLAUDECODE="1", CLAUDE_ENV_FILE=str(env_file), **extra)
        result = subprocess.run([sys.executable, str(HOOK)], input=payload, env=env,
                                capture_output=True, text=True)
        return result, env_file.read_text() if env_file.exists() else ""

    def test_the_line_and_fragments_reach_stdout(self):
        result, exports = self.run_hook(self.ns)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("profile: personal, science (identity.toml [ns].profiles); "))
        self.assertIn("# Profile: science", result.stdout)
        self.assertEqual(exports, "export AGENT_PROFILE=personal,science\n")

    def test_a_failure_is_one_line_and_exit_zero(self):
        self.identity("")
        result, exports = self.run_hook(self.ai)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "profile: unresolved — ai is registered but identity.toml [ai] declares no profiles; "
                                        "run ops-profile session after fixing it\n")
        self.assertEqual(exports, "")

    def test_bad_input_falls_back_to_the_process_cwd(self):
        result = subprocess.run([sys.executable, str(HOOK)], input="not json", env=self.env(CLAUDECODE="1"),
                                cwd=self.wrk4, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("profile: work (identity.toml [wrk4].profiles); "))
