"""Profile selection, canonical checkout discovery, and read-only diagnostics."""
import os
import pathlib
import re
import shlex
import subprocess
from ._configuration import ProfileError, load, compose, expand, HARNESS, KEYS
from ._tasks import query
from ._projects import private_listing

CORPUS = pathlib.Path(__file__).resolve().parents[2]
OVERRIDE = "agent.profile"
DESIGN_DOCS_CONFIG = "ops.designDocs"
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")
DOCS_INSTRUCTION_FILES = ("docs/AGENTS.md", "docs/CLAUDE.md")
DESIGN_DOCS_NAMED = re.compile(r"docs/superpowers/[A-Za-z0-9_.-]+")
DESIGN_DOCS_NAMED_IN_DOCS = re.compile(r"(?<![\w/.-])(?:docs/)?superpowers/[{A-Za-z0-9_.-][{},A-Za-z0-9_.-]*")
RECORDS_DOC_DIRS = ("docs/specs", "docs/plans", "docs/superpowers", "docs/designs", "docs/reports")
RECORDS_NOTE = re.compile(r"^docs/notes/[^/]+-(?:brief|handoff)\.md$")
DOC_DIRS = re.compile(r"^/?docs/(?:specs|plans|superpowers|designs?|rfcs?|adrs?)(?:/|$)")
NAMED_DIRS = re.compile(r"\bdocs/[A-Za-z0-9_-]+/")
GLOB = re.compile(r"[*?\[]")


def _git(cwd, *args, env=None):
    cwd = pathlib.Path(cwd)
    while not cwd.is_dir():
        cwd = cwd.parent
    clean = {k:v for k,v in (env if env is not None else os.environ).items()
             if not k.startswith("GIT_") or k in {"GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_CEILING_DIRECTORIES"}}
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True,
                           text=True, errors="surrogateescape", env=clean, timeout=5)
    except (OSError, subprocess.SubprocessError) as error:
        raise ProfileError(f"git in {cwd}: {error}") from error
    if r.returncode == 0:
        return r.stdout.strip()
    if args[:2] == ("config", "--get") and r.returncode == 1:
        return None
    raise ProfileError(f"git in {cwd}: {r.stderr.strip() or r.returncode}")


def checkout_of(path, env):
    path = pathlib.Path(path).resolve()
    start = path if path.is_dir() else path.parent
    ceilings = {pathlib.Path(p).resolve() for p in env.get("GIT_CEILING_DIRECTORIES", "").split(":") if p}
    for directory in (start, *start.parents):
        if directory != start and directory in ceilings:
            break
        if not (directory / ".git").exists():
            continue
        top = pathlib.Path(_git(directory, "rev-parse", "--show-toplevel", env=env)).resolve()
        main = _git(directory, "worktree", "list", "--porcelain", "-z", env=env).split("\0", 1)[0]
        return pathlib.Path(main.removeprefix("worktree ")).resolve(), top
    return path, path


def _known(names, config):
    if not isinstance(names, list) or not names or any(not isinstance(n, str) or n not in config["profile"] for n in names):
        raise ProfileError("unknown or invalid profile selection")
    if len(set(names)) != len(names):
        raise ProfileError("duplicate selected profile")
    return names


def _config(env):
    row = query(["resolve", "lore", "--json"], env)["results"][0]
    entry = row.get("entry")
    if not isinstance(entry, dict) or not isinstance(entry.get("records"), str):
        raise ProfileError("tasks resolve lore: missing entry.records")
    return load(CORPUS / "profiles/profiles.toml", pathlib.Path(entry["records"]) / "profiles.toml", env)


def _selection(canonical, row, config, env, override=True):
    entry = row.get("entry", {})
    if not isinstance(entry, dict):
        raise ProfileError("invalid records entry")
    assigned = entry.get("profile")
    if assigned is not None:
        _known([assigned], config)
    value = _git(canonical, "config", "--get", OVERRIDE, env=env) if override and (canonical / ".git").exists() else None
    if value is not None:
        return _known([n.strip() for n in value.split(",")], config), f"git config {OVERRIDE}"
    if assigned is not None:
        return [assigned], f"{entry.get('config', 'records entry')} profile"
    matches = [r for r in config["family"] if canonical.is_relative_to(expand(r["path"], env).resolve())]
    if matches:
        rule = max(matches, key=lambda r:len(expand(r["path"],env).resolve().parts))
        return _known(rule["profiles"],config), f"profile path {rule['path']}"
    return _known(config["default"]["profiles"],config), "profile default"


def resolve(path, env, payload=None):
    config = _config(env)
    canonical, top = checkout_of(path, env)
    row = query(["resolve", str(canonical), "--json"], env)["results"][0]
    names, source = _selection(canonical, row, config, env)
    keys = compose(names, config)
    marker = row.get("records_store")
    store = isinstance(marker,str) and pathlib.Path(marker).resolve() == canonical
    if store and row["status"] != "unregistered":
        raise ProfileError("contradictory records-store metadata")
    entry = row.get("entry", {})
    linked = entry.get("kind") == "linked"
    layout = None
    if store:
        keys["design_docs"] = {"value": "not-applicable", "source": "tasks records store"}
        layout = {"kind": "records-store", "records": str(canonical)}
    else:
        if (top / ".git").exists():
            keys.update(repository_layer(top, env))
        if keys["design_docs"]["value"] == "records":
            layout = ({"kind": entry["kind"], "records": entry["records"]} if entry else
                      {"kind": "in-tree", "records": str(top)})
    home = home_of(env, config, payload)
    warnings = []
    expected = sorted({config['profile'][n].get('home') for n in names} - {None})
    if home['name'] and expected and home['name'] not in expected:
        warnings.append(f"profile {', '.join(names)} expects home {', '.join(expected)}; running in {home['name']}")
    if not store and keys['design_docs']['value'] == 'commit':
        excluded = exclude_audit(canonical, top, env)
        if excluded:
            noun = 'entry' if len(excluded) == 1 else 'entries'
            warnings.append(f".git/info/exclude hides {len(excluded)} design-doc {noun}; run profile audit")
    fragments = []
    for name in names:
        fragment = config['profile'][name].get('fragment')
        if fragment:
            file = CORPUS / 'profiles' / f'{fragment}.md'
            if not file.is_file(): warnings.append(f"fragment {fragment}: {file} does not exist")
            else: fragments.append(str(file))
    private = [] if store else private_listing(names, config, env)
    notes = pathlib.Path(entry['records']) / 'AGENTS.md' if linked and entry.get('records') else None
    result = {'kind':'records-store' if store else 'checkout', 'records_store':str(canonical) if store else None,
              'checkout':str(canonical),'path':str(pathlib.Path(path).resolve()),'worktree':top!=canonical,
              'project':None if store else row.get('prefix'),
              'records':{'prefix':row['prefix'],'root':entry['records'],'linked':True} if linked and not store else None,
              'layout':layout,'notes':str(notes) if notes and notes.is_file() and not store else None,
              'profiles':[{'name':n,'source':source} for n in names], 'home':home,'keys':keys,
              'fragments':[str(CORPUS/'profiles/records-store.md')] if store else fragments,
              'private_projects':private,'warnings':warnings}
    if source == f'git config {OVERRIDE}':
        otherwise, origin = _selection(canonical,row,config,env,override=False)
        result['_otherwise']={'names':otherwise,'source':origin}
    return result


def repository_layer(top, env):
    """The keys the working tree overrides: a config key the user set in the clone, or
    an instruction file at the top, or in docs/, naming a place inside docs/superpowers/."""
    if _git(top, "config", "--get", DESIGN_DOCS_CONFIG, env=env) == "commit":
        return {"design_docs": {"value": "commit", "source": f"git config {DESIGN_DOCS_CONFIG}"}}
    readings = [(name, DESIGN_DOCS_NAMED) for name in INSTRUCTION_FILES]
    readings += [(name, DESIGN_DOCS_NAMED_IN_DOCS) for name in DOCS_INSTRUCTION_FILES]
    for name, pattern in readings:
        try:
            found = pattern.search((top / name).read_text(errors="replace"))
        except OSError:
            continue
        if found:
            return {"design_docs": {"value": "commit", "source": f"{name} names {found.group(0).rstrip('/')}"}}
    return {}

def records_doc(path):
    """Whether a repository-relative POSIX path is a working document the records
    profile keeps under the records root."""
    return path.startswith(tuple(f"{directory}/" for directory in RECORDS_DOC_DIRS)) or bool(RECORDS_NOTE.match(path))

def home_of(env, config, payload=None):
    """Which harness home the session runs in. A hook payload's transcript_path is the
    reliable witness: Claude writes it under CLAUDE_CONFIG_DIR/projects/, Codex under
    CODEX_HOME/sessions/, agy under ~/.gemini/antigravity-cli/brain/ (hq's agy wrapper
    maps transcriptPath to transcript_path, as the relay subscriber maps its
    transcriptPath fact), and Codex adds nothing to a SessionStart
    hook's environment (a Codex launched inside a Claude session even inherits
    CLAUDECODE=1). Without a payload, or with one whose transcript lies outside every
    configured home, the harness's own variable decides. A path that several homes
    declare names none of them: agy has one home whichever profile runs it."""
    homes = (config.get("home") or {}).items()
    transcript = payload.get("transcript_path") if isinstance(payload, dict) else None
    if isinstance(transcript, str) and transcript:
        running = pathlib.Path(transcript).resolve()
        for harness in HARNESS:
            names = [name for name, table in homes
                     if running.is_relative_to(expand(table[harness], env).resolve())]
            if names:
                path = dict(homes)[names[0]][harness]
                return _one_home(names, path, f"transcript_path under {path} ({harness})")
    harness = ("codex" if env.get("CODEX_THREAD_ID") or env.get("CODEX_HOME") else
               "agy" if env.get("AGY_SESSION_ID") else "claude" if env.get("CLAUDECODE") or env.get("CLAUDE_CONFIG_DIR") else None)
    if harness not in HARNESS:
        return {"name": None, "source": "no harness in the environment"}
    var, default = HARNESS[harness]
    value = env.get(var) if var else None
    source = f"{var}={value}" if value else (f"{var} unset" if var else f"{harness} has no home variable")
    running = expand(value or default, env).resolve()
    names = [name for name, table in homes if expand(table[harness], env).resolve() == running]
    if names:
        return _one_home(names, dict(homes)[names[0]][harness], source)
    return {"name": None, "source": source}

def _one_home(names, path, source):
    """The home `names` (every home whose `path` matched) points at, or none when it is shared."""
    if len(names) > 1:
        return {"name": None, "source": f"{path} is shared by homes {', '.join(names)}"}
    return {"name": names[0], "source": source}

def exclude_audit(checkout_path, top, env=None):
    """List design docs hidden by a commit checkout's shared Git exclude file."""
    exclude = pathlib.Path(_git(pathlib.Path(top), "rev-parse", "--path-format=absolute", "--git-path", "info/exclude", env=env))
    try:
        entries = exclude.read_text().splitlines()
    except OSError:
        return []
    named = set()
    for name in INSTRUCTION_FILES:
        try:
            named.update(NAMED_DIRS.findall((pathlib.Path(checkout_path) / name).read_text(errors="replace")))
        except OSError:
            continue
    checkout = shlex.quote(str(checkout_path))
    found = []
    for entry in entries:
        entry = entry.strip()
        if not entry or entry.startswith("#"):
            continue
        relative = entry.lstrip("/")
        if not (DOC_DIRS.match(entry) or any(relative == directory.rstrip("/") or relative.startswith(directory)
                                            for directory in named)):
            continue
        if GLOB.search(relative):
            prefix = GLOB.split(relative, maxsplit=1)[0]
            directory = shlex.quote(prefix.rsplit("/", 1)[0] + "/")
            found.append(f"{entry}\tpattern: remove the line from .git/info/exclude, then list what it hid with "
                         f"git -C {checkout} ls-files --others --exclude-standard -- {directory} and add the docs by hand")
        else:
            found.append(f"{entry}\tremove the line from .git/info/exclude, read the doc, then: "
                         f"git -C {checkout} add -- {shlex.quote(relative)}")
    return found

def records_audit(res, env=None):
    """Each working document tracked in the code tree, with what becomes of it: an
    in-tree project's move with its records; a detached or linked checkout revises one in
    place until the project rewrites it as a reference document (records-home design
    §7.2, §7.3)."""
    layout = res["layout"]
    listed = _git(res["path"], "ls-files", "-z", "--full-name", "--", ":/docs", env=env).split("\0")
    found = []
    for name in sorted(n for n in listed if records_doc(n)):
        if layout["kind"] == "in-tree":
            found.append(f"{name}\tmoves to the records root with this project's records unless records-migrate "
                         f"retains it as a document a tracked file cites")
        else:
            found.append(f"{name}\tstays in the code tree and is revised in place until this project rewrites it "
                         f"as a reference document; new working documents go under {layout['records']}/docs")
    return found


def check(env):
    config = _config(env)
    problems=[]
    for row in query(['resolve','--all','--json'],env)['results']:
        entry=row.get('entry',{})
        name=entry.get('profile')
        if name is None:
            problems.append(f"{row.get('prefix')}: no profile assigned")
        else:
            try: compose(_known([name],config),config)
            except ProfileError as error: problems.append(f"{row.get('prefix')}: {error}")
    for name, table in config['profile'].items():
        if table.get('fragment') and not (CORPUS/'profiles'/f"{table['fragment']}.md").is_file():
            problems.append(f"profile {name}: fragment missing")
        if table.get('overlay') and not expand(table['overlay'],env).is_dir():
            problems.append(f"profile {name}: overlay missing")
    return problems


def audit(path, env):
    result=resolve(path,env)
    if result['kind']=='records-store': return []
    if result['keys']['design_docs']['value']=='records': return records_audit(result, env)
    if result['keys']['design_docs']['value']=='commit': return exclude_audit(result['checkout'],path,env)
    return []
