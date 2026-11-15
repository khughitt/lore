"""Validate profile definitions and merge disjoint public/private ownership."""
import pathlib
import re
import tomllib

KEYS = ("design_docs", "gh_account", "pr_draft", "git_identity")
VALUES = {"design_docs": ("commit", "exclude", "records"), "pr_draft": ("required", "by-permission")}
PROFILE_FIELDS = KEYS + ("fragment", "home", "private", "overlay")
RESERVED = ("core", "repository", "session")
NAME = re.compile(r"^[a-z][a-z0-9_-]*$")
CRUD = r"""<>\s.,;:"'"""
IDENTITY = re.compile(rf"[^{CRUD}](?:[^<>\r\n]*[^{CRUD}])? <[^{CRUD}@][^<>\s@]*@[^<>\s@]*[^{CRUD}@]>")
HARNESS = {"claude": ("CLAUDE_CONFIG_DIR", "~/.claude"), "codex": ("CODEX_HOME", "~/.codex"),
           "agy": (None, "~/.gemini/antigravity-cli")}

class ProfileError(Exception):
    """Invalid or unavailable profile inputs; never an implicit default."""


def expand(text, env):
    return pathlib.Path(env.get("HOME", str(pathlib.Path.home()))) / text[2:] if text.startswith("~/") else pathlib.Path(text)

def _names_problems(where, names, profiles):
    if not isinstance(names, list) or not names:
        return [f"{where}: profiles must be a non-empty list"]
    return [f"{where}: unknown profile {n!r}" for n in names if not isinstance(n, str) or n not in profiles]

def config_problems(data):
    """Every structural problem in a parsed profiles.toml, as lines. Empty means valid.
    Valid TOML is not valid configuration: every container is type-checked before it
    is walked, so a malformed file is a list of problems, never a traceback."""
    found = []
    if not isinstance(data, dict):
        return ["profiles.toml must be a table"]
    profiles = data.get("profile")
    if not isinstance(profiles, dict) or not profiles:
        found.append("no [profile.<name>] tables")
        profiles = {}
    homes = data.get("home", {})
    if not isinstance(homes, dict):
        found.append(f"home must be a table of [home.<name>] tables, not {type(homes).__name__}")
        homes = {}
    families = data.get("family", [])
    if not isinstance(families, list):
        found.append(f"family must be an array of [[family]] tables, not {type(families).__name__}")
        families = []
    default = data.get("default", {})
    if not isinstance(default, dict):
        found.append(f"default must be a table, not {type(default).__name__}")
        default = {}
    for name, table in profiles.items():
        if not NAME.match(name) or name in RESERVED:
            found.append(f"profile {name!r}: not a valid name")
        if not isinstance(table, dict):
            found.append(f"profile {name}: must be a table")
            continue
        found += [f"profile {name}: unknown key {key}" for key in sorted(set(table) - set(PROFILE_FIELDS))]
        for key, allowed in VALUES.items():
            if key in table and table[key] not in allowed:
                found.append(f"profile {name}: {key} must be one of {', '.join(allowed)}")
        for key in ("gh_account", "fragment", "home"):
            if key in table and (not isinstance(table[key], str) or not table[key].strip()):
                found.append(f"profile {name}: {key} must be a non-empty string")
        if "git_identity" in table and (not isinstance(table["git_identity"], str)
                                        or not IDENTITY.fullmatch(table["git_identity"])):
            found.append(f"profile {name}: git_identity must be 'Name <email>'")
        if "overlay" in table and (not isinstance(table["overlay"], str)
                                   or not table["overlay"].startswith(("/", "~/"))):
            found.append(f"profile {name}: overlay must be absolute or start with ~/")
        if "private" in table and not isinstance(table["private"], bool):
            found.append(f"profile {name}: private must be true or false")
        if isinstance(table.get("home"), str) and table["home"] not in homes:
            found.append(f"profile {name}: home {table['home']!r} is not defined")
    for i, family in enumerate(families):
        if not isinstance(family, dict):
            found.append(f"family {i}: must be a table")
            continue
        found += [f"family {i}: unknown key {k}" for k in set(family) - {"path", "profiles"}]
        path = family.get("path")
        if not isinstance(path, str) or not path.startswith(("/", "~/")):
            found.append(f"family {i}: path must be absolute or start with ~/")
        found += _names_problems(f"family {i}", family.get("profiles"), profiles)
    found += [f"default: unknown key {k}" for k in set(default) - {"profiles"}]
    found += _names_problems("default", default.get("profiles"), profiles)
    for name, table in homes.items():
        if isinstance(table, dict):
            found += [f"home {name}: unknown key {k}" for k in set(table) - set(HARNESS)]
        for harness in HARNESS:
            if not isinstance(table, dict) or not isinstance(table.get(harness), str):
                found.append(f"home {name}: {harness} must be a path")
    found += [f"unknown configuration key {key}" for key in set(data) - {"profile", "home", "family", "default"}]
    for name, table in profiles.items():
        if isinstance(table, dict) and isinstance(table.get("fragment"), str) and not NAME.fullmatch(table["fragment"]):
            found.append(f"profile {name}: fragment must be a name")
    return found

def compose(names, config):
    """The typed keys the selected profiles set, each with its source. A key set twice
    or a key set by nobody is an error: composition is by ownership, never last-wins,
    and the core supplies no defaults."""
    keys = {}
    owners = {}
    for name in names:
        table = config["profile"][name]
        for key in KEYS:
            if key in table:
                if key in keys:
                    raise ProfileError(f"{key} is set by both profile {owners[key]} and profile {name}")
                source = config.get("_sources", {}).get(("profile", name, key), "profile definitions")
                keys[key] = {"value": table[key], "source": f"{source} profile {name}"}
                owners[key] = name
    missing = [key for key in KEYS if key not in keys]
    if missing:
        raise ProfileError(f"no selected profile sets {', '.join(missing)} (selected: {', '.join(names)})")
    return keys

def load(public_path, private_path, env):
    paths = [pathlib.Path(public_path), pathlib.Path(private_path)]
    docs = []
    for path in paths:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, ValueError) as error:
            raise ProfileError(f"{path}: {error}") from error
        if set(data) - {"profile", "home", "family", "default"}:
            raise ProfileError(f"{path}: unknown configuration keys")
        docs.append(data)
    result = {"profile": {}, "home": {}, "family": []}
    sources = {}
    for index, (data, path) in enumerate(zip(docs, paths)):
        for section in ("profile", "home"):
            tables = data.get(section, {})
            if not isinstance(tables, dict):
                raise ProfileError(f"{path}: {section} must be a table")
            for name, table in tables.items():
                if not isinstance(table, dict):
                    raise ProfileError(f"{path}: {section} {name} must be a table")
                if section == "profile" and index == 0 and set(table) & {"gh_account", "git_identity", "overlay"}:
                    raise ProfileError(f"{path}: account/identity/overlay fields belong in private definitions")
                merged = result[section].setdefault(name, {})
                for key, value in table.items():
                    if key in merged:
                        raise ProfileError(f"{path}: {section} {name}.{key} is set twice")
                    merged[key] = value
                    sources[(section, name, key)] = str(path)
        rules = data.get("family", [])
        if not isinstance(rules, list):
            raise ProfileError(f"{path}: family must be an array")
        result["family"].extend(rules)
        if "default" in data:
            if "default" in result:
                raise ProfileError(f"{path}: default is set twice")
            result["default"] = data["default"]
    problems = config_problems(result)
    if problems:
        raise ProfileError("; ".join(problems))
    seen = set()
    for rule in result["family"]:
        path = expand(rule["path"], env).resolve()
        if path in seen:
            raise ProfileError(f"path rule {path} is set twice")
        seen.add(path)
    result["_sources"] = sources
    result["_paths"] = [str(p) for p in paths]
    return result
