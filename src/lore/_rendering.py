"""Render the profile protocol from its resolved data and corpus prose."""
import pathlib
import shlex
from ._configuration import KEYS

ROOT = pathlib.Path(__file__).resolve().parents[2]


def command(subcommand):
    return shlex.join([str(ROOT / 'bin/lore'), 'profile', subcommand])

def _names(res):
    return ", ".join(p["name"] for p in res["profiles"])

def _design_docs(res):
    """The session line's design-docs clause: the value, or under records where they go."""
    if res["kind"] == "records-store":
        return "not applicable (records store)"
    value = res["keys"]["design_docs"]["value"]
    if value != "records":
        return value
    if res["layout"]["kind"] == "in-tree":
        return "in the tree until this project's records move to the records root"
    return f"under the records root ({res['layout']['records']}/docs)"

def session_text(res):
    """The complete profile layer: the line, any warnings, then every fragment in order,
    then private linked notes and the projects a private profile lists."""
    parts = [session_line(res)]
    if res.get("records"):
        parts.append(f"records: {res['records']['prefix']} at {res['records']['root']} (linked; this checkout is shared)")
    parts += [f"warning: {w.replace('run profile audit', 'run ' + command('audit'))}" for w in res["warnings"]]
    for fragment in res["fragments"]:
        parts += ["", pathlib.Path(fragment).read_text().rstrip("\n")]
    if res.get("notes"):
        parts += ["", pathlib.Path(res["notes"]).read_text().rstrip("\n")]
    if res["private_projects"]:
        parts += ["", "### Projects under this profile", "", *res["private_projects"]]
    return "\n".join(parts) + "\n"

def explain_text(res):
    """One fact per line with its source; no fragment text."""
    where = res["checkout"] + (f" (worktree at {res['path']})" if res["worktree"] else "")
    lines = [f"checkout: {where}", f"project: {res['project'] or '(unregistered)'}",
             f"profiles: {_names(res)}  ← {res['profiles'][0]['source']}"]
    if res.get("records"):
        lines.insert(2, f"records: {res['records']['prefix']} at {res['records']['root']} (linked)")
    otherwise = res.get("_otherwise")
    if otherwise:
        if "error" in otherwise:
            lines.append(f"otherwise: unresolved  ← {otherwise['error']}")
        else:
            lines.append(f"otherwise: {', '.join(otherwise['names'])}  ← {otherwise['source']}")
    lines.append(f"home: {res['home']['name'] or 'unknown'}  ← {res['home']['source']}")
    for key in KEYS:
        lines.append(f"{key}: {res['keys'][key]['value']}  ← {res['keys'][key]['source']}")
        if key == "design_docs" and res["layout"]:
            lines.append(f"layout: {res['layout']['kind']}, records at {res['layout']['records']}  ← tasks where")
    lines.append("fragments: " + (", ".join(res["fragments"]) or "none"))
    lines += [f"warning: {w}" for w in res["warnings"]]
    return "\n".join(lines) + "\n"


def session_line(res):
    keys = res['keys']
    label = 'records-store' if res['kind'] == 'records-store' else _names(res)
    source = res['profiles'][0]['source']
    if res['kind'] == 'records-store':
        source = f"{_names(res)}; {source}"
    precedence = ("later layers win: core < profile < this repository's instructions < you. "
                  f"`{command('explain')}` shows every source.")
    return (f"profile: {label} ({source}); home: {res['home']['name'] or 'unknown'}; "
            f"design docs: {_design_docs(res)}; gh: {keys['gh_account']['value']}; "
            f"PRs: {keys['pr_draft']['value']} — {precedence}")
