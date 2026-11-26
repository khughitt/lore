"""Selection vocabulary version 1: fact names and types, duties, moments and test operators."""

# fact -> (type, allowed values or None for any value of that type)
FACTS = {
    'actor.harness': ('scalar', frozenset({'claude-code', 'codex', 'agy', 'pi', 'opencode'})),
    'actor.model': ('scalar', None),
    'actor.role': ('scalar', frozenset({'root', 'worker', 'reviewer', 'search'})),
    'actor.interactive': ('bool', None),
    'actor.shell': ('scalar', frozenset({'bash', 'zsh'})),
    'actor.skills': ('scalar', frozenset({'native', 'shell', 'none'})),
    'actor.child_wake': ('bool', None),
    'target.project': ('scalar', None),
    'target.stage': ('scalar', frozenset({'experimental', 'pre-release', 'supported'})),
    'target.profile': ('list', None),
    'target.family': ('scalar', frozenset({'guild', 'verifiably', 'none'})),
    'target.test_policy': ('scalar', frozenset({'broad', 'off'})),
    'target.code_guide': ('bool', None),
    'target.test_front_door': ('bool', None),
    'host.host_budget': ('bool', None),
    'moment': ('scalar', frozenset({'launch', 'session-start'})),
}
DUTIES = frozenset({'edit-code', 'commit', 'run-tests', 'worktree-lifecycle', 'task-records', 'integrate',
                    'file-feedback', 'trials', 'ask-user', 'dispatch', 'run-reviews', 'host-services',
                    'desktop', 'spend'})
MOMENTS = frozenset({'launch', 'session-start', 'first-edit'})   # values allowed in an entry's `by`
OPERATORS = frozenset({'eq', 'in', 'not_in'})


def value_problem(name, value):
    """Why value is not a valid known value of fact name, or None when it is."""
    kind, allowed = FACTS[name]
    if kind == 'bool':
        return None if isinstance(value, bool) else f'{name} takes true or false, not {value!r}'
    if kind == 'list':
        if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
            return f'{name} takes a list of names, not {value!r}'
        return None
    if not isinstance(value, str) or not value:
        return f'{name} takes a name, not {value!r}'
    if allowed is not None and value not in allowed:
        return f'{name} has no value {value!r}; values: {", ".join(sorted(allowed))}'
    return None
