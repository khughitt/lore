"""git-identity-check: judge a commit's author and committer against the profile's git_identity.

Git runs it as a hook declared in the global config (`hook.identity-check`, events
pre-commit and pre-merge-commit), so it judges every repository on the host. Without a
path it judges the repository git resolves from the environment, an inherited GIT_DIR
included, which inside a hook is the one being committed to; with a path, that checkout,
whatever repository the environment names.

The expected identity is the profile key `git_identity` (`Name <email>`) that lore's
resolver selects (`select`: the selection alone, without the session's private project
listing, so an unrelated catalogue problem never blocks a commit), never git config: a
test that rewrote git config is what this exists to catch. A repository whose profile comes from lore's default (scratch repositories,
test fixtures, the records store) is not judged, and neither is any repository while
the tasks registry does not register lore (a sandboxed XDG_CONFIG_HOME). The committer
is always judged; `OPS_IDENTITY_AUTHOR=allow` lets a deliberately foreign author through.
Reference: docs/profile-delivery.md (Commit identity check).
"""
import pathlib
import re
import subprocess
import sys

from ._configuration import ProfileError
from ._profiles import DEFAULT_SOURCE, LoreUnregistered, select

ALLOW_AUTHOR = "OPS_IDENTITY_AUTHOR"
ROLES = ("author", "committer")
LOCAL_SCOPES = ("local", "worktree")
IDENT = re.compile(r"^(?P<name>[^<>]*?) <(?P<email>[^<>]*)>$")
BYPASS = "To commit past it once: git -c hook.identity-check.enabled=false commit …"
# Variables that point git at one repository; the resolver must never see them.
GIT_LOCAL_ENV = frozenset("""
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG GIT_CONFIG_PARAMETERS GIT_CONFIG_COUNT
    GIT_OBJECT_DIRECTORY GIT_DIR GIT_WORK_TREE GIT_IMPLICIT_WORK_TREE GIT_GRAFT_FILE
    GIT_INDEX_FILE GIT_NO_REPLACE_OBJECTS GIT_REPLACE_REF_BASE GIT_PREFIX
    GIT_SHALLOW_FILE GIT_COMMON_DIR
""".split())


class CannotJudge(Exception):
    """No verdict can be reached; never read as a pass."""


def _git(cwd, env, *args):
    """git's stdout in cwd under env, which keeps its repository variables (this is the
    commit being judged); None for a `config --get` of an unset key. Output is decoded as
    the filesystem decodes a path, so a repository whose path is not UTF-8 reads back as
    the path Python names it by."""
    try:
        result = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True,
                                errors="surrogateescape", timeout=5)
    except (OSError, subprocess.SubprocessError) as error:
        raise CannotJudge(f"git {' '.join(args)}: {error}") from error
    if result.returncode == 0:
        return result.stdout.rstrip("\n")
    if args[0] == "config" and result.returncode == 1:
        return None
    raise CannotJudge(f"git {' '.join(args)}: {result.stderr.strip() or f'exit {result.returncode}'}")


def without_local(env):
    """env without the variables that point git at one repository."""
    return {key: value for key, value in env.items() if key not in GIT_LOCAL_ENV}


def split_ident(text):
    """(name, email) of `Name <email>`."""
    found = IDENT.match(text)
    if not found:
        raise CannotJudge(f"not an identity: {text!r}")
    return found["name"], found["email"]


def actual(cwd, env, role):
    """The identity git will write for a role, without git var's date."""
    return split_ident(_git(cwd, env, "var", f"GIT_{role.upper()}_IDENT").rsplit(" ", 2)[0])


def origin(cwd, env, role, field, value):
    """(text, configured): where git took one field of a role's identity, and whether that
    is git config. Git reads the environment first, then the role's key, then user.*: the
    first config value set is the one written unless the identity differs from it, and
    then the environment (or --author) won. With neither key set, git falls back to EMAIL
    for an email, then to a default from the system user."""
    keys = (f"{role}.{field}", f"user.{field}")
    variable = f"GIT_{role.upper()}_{field.upper()}"
    for key in keys:
        line = _git(cwd, env, "config", "--show-scope", "--show-origin", "--get", key)
        if line is None:
            continue
        scope, where, configured = line.split("\t", 2)
        if configured != value:
            break
        text = f"  {key}={configured}   {where} ({scope})"
        if scope in LOCAL_SCOPES:
            text += f"\n    remove it: git config --{scope} --unset {key}"
        return text, True
    else:
        if env.get(variable) != value:
            if field == "email" and env.get("EMAIL") == value:
                return f"  {role} {field} {value!r} came from the environment (EMAIL)", False
            system = "the system user and host name" if field == "email" else "the system user"
            return (f"  {role} {field} {value!r} is git's default from {system}: "
                    f"neither {keys[0]} nor {keys[1]} is set"), False
    via = " or --author" if role == "author" else ""
    return f"  {role} {field} {value!r} came from the environment ({variable}){via}", False


def findings(cwd, env, chosen):
    """(findings, configured): one finding per role whose identity is not the profile's,
    and whether any wrong field came from git config."""
    identity = chosen["keys"]["git_identity"]
    expected = split_ident(identity["value"])
    allow = env.get(ALLOW_AUTHOR)
    if allow not in (None, "", "allow"):
        raise CannotJudge(f"{ALLOW_AUTHOR} must be allow or unset, not {allow!r}")
    whose = f"{identity['source']}; selected by {chosen['source']}"
    found, configured = [], False
    for role in ROLES:
        if role == "author" and allow == "allow":
            continue
        got = actual(cwd, env, role)
        if got != expected:
            lines = [f"{role} {got[0]} <{got[1]}> is not this checkout's identity,",
                     f"  {expected[0]} <{expected[1]}> ({whose})"]
            for i, field in enumerate(("name", "email")):
                if got[i] != expected[i]:
                    text, from_config = origin(cwd, env, role, field, got[i])
                    lines.append(text)
                    configured = configured or from_config
            found.append("\n".join(lines))
    return found, configured


def written(cwd, env):
    """(top, checkout): the working tree git commits from, and a path inside the
    repository the commit writes to. They differ when an inherited GIT_DIR names another
    repository than the one around the working tree; the resolver, which discovers from a
    path with that variable stripped, is then given the repository's own git directory,
    from which it finds the checkout."""
    top = _git(cwd, env, "rev-parse", "--show-toplevel")
    common = pathlib.Path(_git(cwd, env, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    try:
        around = _git(top, without_local(env), "rev-parse", "--path-format=absolute", "--git-common-dir")
    except CannotJudge:
        around = None
    if around is not None and pathlib.Path(around).resolve() == common:
        return top, top
    return top, str(common)


def verdict(cwd, env):
    """findings() for the repository a commit from cwd writes to; none when it passes or
    is not judged. A registry that does not register lore is a sandbox (a redirected
    XDG_CONFIG_HOME under the real HOME, whose global config still runs the hook): no
    profile resolves there, so it is not judged, and says so once."""
    top, checkout = written(cwd, env)
    try:
        chosen = select(checkout, without_local(env))
    except LoreUnregistered:
        where = env.get("XDG_CONFIG_HOME")
        named = f"XDG_CONFIG_HOME={where}" if where else "XDG_CONFIG_HOME unset"
        print(f"git-identity-check: not judged: the tasks registry ({named}) does not register lore "
              "(a sandboxed XDG_CONFIG_HOME?)", file=sys.stderr)
        return [], False
    except (ProfileError, ValueError) as error:
        raise CannotJudge(str(error)) from error
    if chosen["source"] == DEFAULT_SOURCE:
        return [], False
    return findings(top, env, chosen)


def run(path, env, cwd):
    """Judge the commit and report on stderr; the exit status: 0 pass or not judged,
    1 mismatch, 2 cannot judge."""
    if path is not None:
        cwd = str(pathlib.Path(cwd) / path)
    cause = None
    try:
        if path is not None:
            env = without_local(env)
        found, configured = verdict(cwd, env)
    except CannotJudge as error:
        cause = str(error)
    except Exception as error:  # an unreadable file, a broken resolver: never a pass, never a traceback
        cause = f"{type(error).__name__}: {error}"
    if cause is not None:
        print(f"git-identity-check: cannot judge {cwd}: {cause}\n  {BYPASS}", file=sys.stderr)
        return 2
    for finding in found:
        print(f"git-identity-check: {finding}", file=sys.stderr)
    if found:
        cause = "A test or tool may have rewritten git config. " if configured else ""
        print(f"  {cause}Fix the value at that origin, then commit again.", file=sys.stderr)
    return 1 if found else 0
