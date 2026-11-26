"""Cutting: omitted rules leave, emptied headings go with them, blank runs collapse only near a removal."""
import json

from lore.context._corpus import MANIFEST, load
from lore.context._cutting import HEADING, cut

from .conftest import A, AH, B, BH, C, CH, ROOT, build, corpus_of


def cut_parts(parts, omitted):
    return cut(corpus_of(*build(parts)), set(omitted))


def test_empty_omission_is_byte_identical_on_the_real_artifact():
    corpus = load(ROOT, 'working')
    assert cut(corpus, frozenset()) == corpus.artifact


def test_emptied_section_loses_its_heading():
    parts = [('text', '## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n## B\n\n'), ('rule', BH, '- b\n')]
    assert cut_parts(parts, {B}) == b'## A\n\n- a\n'


def test_partly_emptied_section_keeps_heading_and_one_blank_line():
    parts = [('text', '## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n'), ('rule', BH, '- b\n'),
             ('text', '\n'), ('rule', CH, '- c\n')]
    assert cut_parts(parts, {B}) == b'## A\n\n- a\n\n- c\n'


def test_subheading_dropped_when_its_rules_go_but_parent_kept():
    parts = [('text', '## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n### A1\n\n'), ('rule', BH, '- a1\n'),
             ('text', '\n## B\n\n'), ('rule', CH, '- b\n')]
    assert cut_parts(parts, {B}) == b'## A\n\n- a\n\n## B\n\n- b\n'


def test_omitted_paragraph_rule_with_internal_blank_lines_leaves_one_blank_line():
    parts = [('text', '## A\n\n'), ('rule', AH, 'A text\n'), ('text', '\n'), ('rule', BH, 'para one\n\npara two\n'),
             ('text', '\n'), ('rule', CH, 'C text\n')]
    assert cut_parts(parts, {B}) == b'## A\n\nA text\n\nC text\n'


def test_no_omission_on_the_real_corpus_leaves_three_consecutive_newlines_it_did_not_have():
    corpus = load(ROOT, 'working')
    manifest = json.loads((ROOT / MANIFEST).read_bytes())
    baseline = corpus.artifact.count(b'\n\n\n')
    for fragment in manifest['fragments']:
        ids = {r['id'] for r in fragment.get('rules', [])}
        if ids:
            assert cut(corpus, ids).count(b'\n\n\n') <= baseline, fragment['id']


def test_indented_heading_and_tilde_fence_follow_the_assembler_rules():
    parts = [('text', '   ## H\n\n'), ('rule', AH, '- a\n'), ('text', '\n## K\n\n~~~\n```\n# not a heading\n~~~\n\n'),
             ('rule', BH, '- b\n')]
    # '   ## H' is a heading, so omitting A empties and drops it; the '```' inside '~~~' does not
    # close the fence, so '# not a heading' stays text in section K.
    assert cut_parts(parts, {A}) == b'## K\n\n~~~\n```\n# not a heading\n~~~\n\n- b\n'


def test_connective_text_in_emptied_section_goes_with_it():
    parts = [('text', '## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n## B\n\nThese apply to B:\n\n'),
             ('rule', BH, '- b\n')]
    assert cut_parts(parts, {B}) == b'## A\n\n- a\n'


def test_generated_block_keeps_its_section():
    parts = [('text', '## P\n\n'), ('rule', AH, '- a\n'), ('text', '\n'), ('generated', '- tasks: x\n')]
    assert cut_parts(parts, {A}) == b'## P\n\n- tasks: x\n'


def test_blank_lines_away_from_any_removal_are_untouched():
    parts = [('text', '## A\n\n\n'), ('rule', AH, '- a\n'), ('text', '\n## B\n\n'), ('rule', BH, '- b\n')]
    assert cut_parts(parts, {B}) == b'## A\n\n\n- a\n'


def test_omission_at_file_edges_keeps_single_trailing_newline():
    parts = [('text', '## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n## B\n\n'), ('rule', BH, '- b\n'),
             ('text', '\n## C\n\n'), ('rule', CH, '- c\n')]
    first = cut_parts(parts, {A})
    last = cut_parts(parts, {C})
    assert first == b'## B\n\n- b\n\n## C\n\n- c\n'
    assert last == b'## A\n\n- a\n\n## B\n\n- b\n'
    assert not first.startswith(b'\n') and last.endswith(b'\n') and not last.endswith(b'\n\n')


def test_heading_inside_fenced_non_rule_text_is_not_a_heading():
    parts = [('text', '## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n```\n## fenced\n```\n\n'),
             ('rule', BH, '- b\n')]
    # The fenced '## fenced' does not open a section, so A's section still holds B and keeps its heading.
    assert cut_parts(parts, {A}) == b'## A\n\n```\n## fenced\n```\n\n- b\n'


def test_section_without_any_removed_rule_is_kept_even_when_it_holds_no_rule():
    parts = [('text', '## Intro\n\nProse only.\n\n## A\n\n'), ('rule', AH, '- a\n'), ('text', '\n## B\n\n'),
             ('rule', BH, '- b\n')]
    assert cut_parts(parts, {B}) == b'## Intro\n\nProse only.\n\n## A\n\n- a\n'


def test_omitting_real_rules_never_leaves_an_empty_heading():
    corpus = load(ROOT, 'working')
    trials = {r.id for r in corpus.rules if r.fragment == 'trials'}
    assert trials
    out = cut(corpus, trials)
    assert b'## Trials' not in out
    lines = [line for line in out.splitlines(keepends=True) if line.strip()]
    for i, line in enumerate(lines):
        match = HEADING.match(line)
        if not match:
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        assert nxt is not None, line
        following = HEADING.match(nxt)
        assert not following or len(following.group(1)) > len(match.group(1)), (line, nxt)
