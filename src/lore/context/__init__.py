"""Select the rules of the delivered instructions that apply to a typed context, with a record."""
from . import _applicability
from ._corpus import load
from ._cutting import cut
from ._errors import ContextError
from ._facts import load_context
from ._record import build_record, selector_identity
from ._selection import decide

__all__ = ['ContextError', 'select_text', 'check']

EMPTY = {'schema': 1, 'name': 'empty'}


def select_text(root, context_data, *, shadow=False, view='auto'):
    """(selected text, selection record) for a context document over the checkout's corpus."""
    corpus = load(root, view)
    entries = _applicability.parse(corpus.applicability)
    found = _applicability.problems(entries, _hashes(corpus))
    if found:
        raise ContextError('applicability.toml has problems; run lore context check:\n' + '\n'.join(found))
    text, decisions = _select(corpus, entries, load_context(context_data), shadow)
    record = build_record('shadow' if shadow else 'live', context_data, corpus, decisions, text,
                          selector_identity(root))
    return text, record


def check(root, view='auto'):
    """(problems, warnings) for the applicability file and the empty-context invariant (G2)."""
    corpus = load(root, view)
    try:
        entries = _applicability.parse(corpus.applicability)
    except ContextError as error:
        return [str(error)], []
    rules = _hashes(corpus)
    problems = _applicability.problems(entries, rules)
    if not problems:
        empty = load_context(EMPTY)
        for shadow in (False, True):
            if _select(corpus, entries, empty, shadow)[0] != corpus.artifact:
                problems.append('empty-context selection differs from the artifact'
                                + (' in shadow mode' if shadow else ''))
    return problems, _applicability.stale(entries, rules)


def _hashes(corpus):
    return {rule.id: rule.sha256 for rule in corpus.rules}


def _select(corpus, entries, context, shadow):
    decisions = decide(corpus.rules, entries, context, shadow=shadow)
    return cut(corpus, {d.rule for d in decisions if not d.include}), decisions
