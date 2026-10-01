"""Stage 4.5c (L1/L2 source-span coverage gate) logic, extracted from
SKILL.md's inline block for the same testability reason as stage_3_reaudit.
Regex/threshold logic unchanged from the original — extraction, not rewrite.
"""
import re

COVERAGE_THRESHOLD = 0.90


def _body_of(block):
    parts = block.split('---\n')
    return parts[2].strip() if len(parts) >= 3 else ''


def _clean_sentences(body):
    """Line-scoped, NOT joined-then-sentence-split — see the original
    inline block's comment (SKILL.md Stage 4.5c) for why: joining first
    false-positived 48/72 gaps on a real chapter by merging multiple ###
    children's lines into one run-on unit before sentence-splitting."""
    units = []
    for l in body.splitlines():
        l = l.strip()
        if not l or l.startswith('|') or re.match(r'^#{1,6}\s', l):
            continue
        parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', l) if len(p.strip()) >= 20]
        units.extend(parts if parts else ([l] if len(l) >= 20 else []))
    return units


def compute_coverage_gaps(chunks_text, threshold=COVERAGE_THRESHOLD):
    """Same logic as the original SKILL.md Stage 4.5c inline block. Returns
    {l1_checked, gaps: [...], verdict}."""
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', chunks_text, re.DOTALL)

    l1_chunks, l2_bodies = [], []
    for b in blocks:
        lvl = re.search(r'chunk_level:\s*(\d)', b)
        if not lvl:
            continue
        if lvl.group(1) == '1':
            cid = re.search(r'chunk_id:\s*(.+)', b).group(1).strip()
            top = re.search(r'topic:\s*(.+)', b)
            top = top.group(1).strip() if top else ''
            src = re.search(r'source_lines:\s*"?([^"\n]+)"?', b)
            src = src.group(1).strip() if src else ''
            l1_chunks.append({'id': cid, 'topic': top, 'source_lines': src, 'body': _body_of(b)})
        elif lvl.group(1) == '2':
            l2_bodies.append(_body_of(b))

    l2_blob = '\n'.join(l2_bodies)

    gaps = []
    for l1 in l1_chunks:
        sentences = _clean_sentences(l1['body'])
        if not sentences:
            continue
        covered = sum(1 for s in sentences if s in l2_blob)
        pct = covered / len(sentences)
        if pct < threshold:
            uncovered = next((s for s in sentences if s not in l2_blob), '')
            gaps.append({**l1, 'coverage_pct': round(pct * 100, 1), 'excerpt': uncovered[:100]})

    verdict = "PASS" if not gaps else "BLOCKING FAIL"
    return {"l1_checked": len(l1_chunks), "gaps": gaps, "verdict": verdict}


def decide_checkpoint_action(result):
    """CP-02: no gaps -> complete; any gap -> blocked."""
    metadata = {"l1_checked": result["l1_checked"], "gaps_found": len(result["gaps"])}
    if not result["gaps"]:
        return "complete", metadata
    metadata["gaps"] = result["gaps"]
    return "blocked", metadata
