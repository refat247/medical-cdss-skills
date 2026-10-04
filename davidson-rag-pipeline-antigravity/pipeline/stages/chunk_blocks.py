"""One chunk-block splitter for every stage (second-sweep 1.21).

The old inline regex  (---\\nchunk_id:.*?\\n---\\n.*?)(?=\\n---\\nchunk_id:|\\Z)  needed the literal sequence
'\\n---\\n' (WITH a trailing newline) to close each chunk's frontmatter, so a final empty-body chunk whose closing
'---' ends the file silently vanished. Stage 6 got the v2.6.7 fix; Stages 4.5, 4.5c, 4.5d, 4.7, 5, 5.4 and the
precision scripts kept the old regex and therefore dropped that chunk (Stage 5 reported l2_chunks=1 for 2).

split_chunk_blocks() returns exactly what the old regex returned for well-formed input, plus the chunks the old
regex lost. Blocks whose frontmatter never closes are not returned (Stage 6 reports them explicitly).
"""
import re

_CHUNK_START_RE = re.compile(r"(?m)^---\nchunk_id:")
_FRONTMATTER_CLOSE_RE = re.compile(r"\A---\nchunk_id:.*?\n---(?:\n|\Z)", re.DOTALL)


def split_chunk_blocks(text):
    starts = [m.start() for m in _CHUNK_START_RE.finditer(text)]
    blocks = []
    for i, start in enumerate(starts):
        has_next = i + 1 < len(starts)
        raw = text[start:(starts[i + 1] if has_next else len(text))]
        if has_next and raw.endswith("\n"):
            raw = raw[:-1]          # the old regex's lookahead consumed one separating newline
        if _FRONTMATTER_CLOSE_RE.match(raw):
            blocks.append(raw)
    return blocks


def block_body(block):
    """Text after the frontmatter's closing '---' (not 'after the first ---', which cut bodies containing '---')."""
    m = _FRONTMATTER_CLOSE_RE.match(block)
    return block[m.end():].strip() if m else ""
