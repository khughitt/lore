"""Remove omitted rules' lines from the artifact, with the headings and blank runs they empty."""
import re

FENCE_OPEN = re.compile(rb' {0,3}(`{3,}|~{3,})(.*)\n$')
HEADING = re.compile(rb' {0,3}(#{1,6})(?:[ \t]|\n)')


def cut(corpus, omitted):
    """The artifact without the omitted rules (spec section 7); unchanged when nothing is omitted."""
    if not omitted:
        return corpus.artifact
    lines, kinds, owners = _classify(corpus)
    removed = [kind == 'rule' and owners[i] in omitted for i, kind in enumerate(kinds)]
    lost = list(removed)        # lines removed as rule text, before any section removal
    _empty_sections(lines, kinds, removed, lost)
    return _join(lines, kinds, removed)


def _classify(corpus):
    """Each line with its kind: rule, generated, heading, blank or text (outside a fence)."""
    data = corpus.artifact
    lines = data.splitlines(keepends=True)
    rule_at = {}
    for rule in corpus.rules:
        rule_at[rule.offset] = rule
    kinds, owners = [], []
    offset, current, end, fence = 0, None, 0, None
    for line in lines:
        if current is None and offset in rule_at:
            current, end = rule_at[offset].id, offset + rule_at[offset].length
        generated = any(start <= offset < start + length for start, length in corpus.generated)
        was_fenced = fence is not None
        if fence:
            if re.fullmatch(rb' {0,3}' + re.escape(fence[:1]) + rb'{' + str(len(fence)).encode() + rb',}[ \t]*\n',
                            line):
                fence = None
        else:
            opened = FENCE_OPEN.match(line)
            if opened:
                fence = opened.group(1)
        if current is not None:
            kinds.append('rule')
            owners.append(current)
        elif generated:
            kinds.append('generated')
            owners.append(None)
        elif was_fenced or fence:
            kinds.append('text')
            owners.append(None)
        elif HEADING.match(line):
            kinds.append('heading')
            owners.append(None)
        elif not line.strip():
            kinds.append('blank')
            owners.append(None)
        else:
            kinds.append('text')
            owners.append(None)
        offset += len(line)
        if current is not None and offset >= end:
            current = None
    return lines, kinds, owners


def _level(line):
    return len(HEADING.match(line).group(1))


def _empty_sections(lines, kinds, removed, lost):
    """Remove each section that lost rule text and keeps no rule line and no generated line."""
    for i, kind in enumerate(kinds):
        if kind != 'heading' or removed[i]:
            continue
        level = _level(lines[i])
        end = next((j for j in range(i + 1, len(lines)) if kinds[j] == 'heading' and _level(lines[j]) <= level),
                   len(lines))
        section = range(i + 1, end)
        if not any(lost[j] for j in section):
            continue
        if any((kinds[j] == 'rule' and not removed[j]) or kinds[j] == 'generated' for j in section):
            continue
        for j in (i, *section):
            removed[j] = True


def _join(lines, kinds, removed):
    """Kept lines, with each blank run that a removal touched collapsed to one blank line."""
    out = []
    run = []                # kept blank lines since the last kept non-blank line
    touched = False         # a removed line since the last kept non-blank line
    for i, line in enumerate(lines):
        if removed[i]:
            touched = True
            continue
        if kinds[i] == 'blank':
            run.append(line)
            continue
        if run:
            out.extend(run if not touched else ([run[0]] if out else []))
        run, touched = [], False
        out.append(line)
    if run and not touched:
        out.extend(run)
    text = b''.join(out)
    if text:
        text = text.rstrip(b'\n') + b'\n' if text.endswith(b'\n') else text + b'\n'
    return text
