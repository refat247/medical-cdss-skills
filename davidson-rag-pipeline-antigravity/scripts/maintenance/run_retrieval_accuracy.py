"""Advisory self-retrieval sanity check over a chapter corpus (Phase 5 future work
harness, v2.6.10).

SELF-SUPERVISED, STRUCTURAL, LEXICAL-ONLY — this is NOT an independent retrieval
benchmark and must never be cited as retrieval accuracy. It is explicitly NOT a substitute for the
retrieval/generation/clinical/educational validation that the corpus protected markers
disclaim. It answers only: "for each RAG_Optimised L2 chunk, if a user asks about that
chunk's own section heading + declared topic, can a pure lexical BM25 retriever
recover that chunk?" It measures corpus retrievability / self-consistency.

Method
------
1. Parse every `*_RAG_Optimised.md` in <corpus_root> into L2 chunks (frontmatter blocks).
2. Query per chunk = section heading (first body line, markdown-stripped) + `topic`
   frontmatter, with parenthetical noise stripped (e.g. "(heading)", "(section heading)")
   and tokens lowercased / stopword-filtered / deduped / capped.
3. Index = all chunk bodies; Okapi BM25 (k1=1.5, b=0.75), IDF with +1 smoothing.
4. Score every chunk against every query; ground truth = the query's own chunk.
5. Metrics: hit-rate@k (target in top-k, k=1/3/5/10) and MRR, per-chapter and corpus-wide.

Read-only w.r.t. the corpus: never touches chunks.md / RAG_Optimised.md / checkpoints /
protected markers.

v2.6.3 SAFETY GUARDRAIL: CLASSIFICATION = generates new outputs (its own advisory
retrieval-accuracy report only; never modifies any certified corpus output). Lower
risk than the chapter-specific repair scripts, but still a mutation-capable runner
(writes its report files) -- reviewed and declared per the repository-wide
safety-declaration requirement (requirement 8).

Verified reproducibility (2026-08-15): hit@1=92.52%, hit@3=98.36%, hit@5=99.30%,
hit@10=99.53%, MRR=0.9561 over 428 L2 chunks. Cross-checked against an independent
TF-IDF-cosine retriever (hit@1=82.94%) and a term-overlap baseline (hit@1=84.11%);
metric is sensitive to query construction (heading-only queries: hit@1=69.25%), i.e.
not saturated by design.
"""

import argparse
import io
import json
import math
import os
import re
import sys
import time
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

K1 = 1.5
B = 0.75
KS = (1, 3, 5, 10)
MAX_QUERY_TERMS = 12

_STOP = set("""a an and are as at be but by for from had has have he her his if in is it its may
not of on or our per she so that the their them then there these they this to was we were will
with would you your can could should does do did what which who whom when where why how both
each few more most other some such only own same too very just also than into over under again
further once upon""".split())


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower())
            if len(t) > 1 and t not in _STOP]


def _extract_blocks(text):
    return re.findall(r'^---\nchunk_id:\s*(\S+)\n(.*?)\n---\n(.*?)(?=^---\nchunk_id:|\Z)',
                      text, re.MULTILINE | re.DOTALL)


def parse_rag(path):
    """Return [(chunk_id, body, topic)] for one RAG_Optimised.md file."""
    text = open(path, encoding='utf-8').read()
    out = []
    for cid, front, body in _extract_blocks(text):
        m = re.search(r'^topic:\s*(.*)$', front, re.MULTILINE)
        out.append((cid, body.strip(), m.group(1) if m else ''))
    return out


def discover_corpus(corpus_root):
    corpus = []
    for d in sorted(os.listdir(corpus_root)):
        full = os.path.join(corpus_root, d)
        if not os.path.isdir(full):
            continue
        rag = [f for f in os.listdir(full) if f.endswith('_RAG_Optimised.md')]
        if not rag:
            continue
        for cid, body, topic in parse_rag(os.path.join(full, rag[0])):
            corpus.append((d, cid, body, topic))
    return corpus


def build_queries(corpus):
    queries = []
    for i, (ch, cid, body, topic) in enumerate(corpus):
        first = body.strip().splitlines()[0] if body.strip() else ''
        heading = re.sub(r'^#{1,6}\s*', '', first)
        topic = re.sub(r'\([^)]*\)', ' ', topic)  # drop "(heading)" etc. noise
        terms = list(dict.fromkeys(tokenize(heading + ' ' + topic)))[:MAX_QUERY_TERMS]
        queries.append({'index': i, 'chapter': ch, 'chunk_id': cid, 'terms': terms})
    return queries


class BM25Index:
    def __init__(self, doc_tokens):
        self.doc_tokens = doc_tokens
        self.n = len(doc_tokens)
        self.avgdl = sum(len(t) for t in doc_tokens) / self.n
        df = Counter()
        for toks in doc_tokens:
            df.update(set(toks))
        self.idf = {t: math.log((self.n - df[t] + 0.5) / (df[t] + 0.5) + 1.0) for t in df}

    def score(self, doc_index, qterms):
        toks = self.doc_tokens[doc_index]
        denom = 1 - B + B * len(toks) / self.avgdl
        tf = Counter(toks)
        s = 0.0
        for t in qterms:
            f = tf.get(t, 0)
            if f:
                s += self.idf.get(t, 0.0) * (f * (K1 + 1)) / (f + K1 * denom)
        return s

    def rank(self, qterms, target_index):
        ranked = sorted(((self.score(j, qterms), j) for j in range(self.n)),
                        key=lambda x: (-x[0], x[1]))
        for pos, (_, j) in enumerate(ranked, 1):
            if j == target_index:
                return pos
        return None


def main():
    ap = argparse.ArgumentParser(
        description='Advisory BM25 self-retrieval sanity check over RAG_Optimised L2 chunks. '
                    'Not an independent retrieval benchmark; read-only over corpus evidence.')
    ap.add_argument('corpus_root', help='corpus root containing chapter directories')
    ap.add_argument('--report-dir', default=None,
                    help='directory for the advisory JSON+MD report (default: <corpus_root>\\..\\retrieval_accuracy_report)')
    args = ap.parse_args()

    corpus = discover_corpus(args.corpus_root)
    if not corpus:
        print('no RAG_Optimised.md chunks found under', args.corpus_root)
        return 1

    queries = build_queries(corpus)
    idx = BM25Index([tokenize(c[2]) for c in corpus])
    nq = sum(1 for q in queries if q['terms'])

    hits = {k: 0 for k in KS}
    rr = 0.0
    per_chapter = {}
    details = []
    t0 = time.time()
    for q in queries:
        if not q['terms']:
            continue
        rank = idx.rank(q['terms'], q['index'])
        if rank is None:
            continue
        rr += 1.0 / rank
        for k in KS:
            if rank <= k:
                hits[k] += 1
        pc = per_chapter.setdefault(q['chapter'], {'n': 0, 'hits': {k: 0 for k in KS}, 'rr': 0.0})
        pc['n'] += 1
        pc['rr'] += 1.0 / rank
        for k in KS:
            if rank <= k:
                pc['hits'][k] += 1
        details.append({'chapter': q['chapter'], 'chunk_id': q['chunk_id'],
                        'rank': rank, 'raw_query': ' '.join(q['terms'])})
    elapsed = time.time() - t0

    def pct(v, n_):
        return round(100.0 * v / n_, 2)

    hdr = '%-50s %5s %6s %6s %6s %6s %6s' % ('CHAPTER', 'N', 'H@1', 'H@3', 'H@5', 'H@10', 'MRR')
    print(hdr); print('-' * len(hdr))
    for ch in sorted(per_chapter):
        pc = per_chapter[ch]
        print('%-50s %5d %6.2f %6.2f %6.2f %6.2f %6.4f' % (
            ch[:50], pc['n'],
            pct(pc['hits'][1], pc['n']), pct(pc['hits'][3], pc['n']),
            pct(pc['hits'][5], pc['n']), pct(pc['hits'][10], pc['n']),
            pc['rr'] / pc['n']))
    print('-' * len(hdr))
    print('%-50s %5d %6.2f %6.2f %6.2f %6.2f %6.4f' % (
        'CORPUS', nq,
        pct(hits[1], nq), pct(hits[3], nq), pct(hits[5], nq), pct(hits[10], nq),
        rr / nq))
    print('elapsed=%.1fs  corpus_docs=%d  queries=%d' % (elapsed, idx.n, nq))

    report_dir = args.report_dir or os.path.join(os.path.dirname(os.path.abspath(args.corpus_root)),
                                                 'retrieval_accuracy_report')
    os.makedirs(report_dir, exist_ok=True)
    report = {
        'evaluation_scope': 'SELF_RETRIEVAL_SANITY_ONLY',
        'independent_queries': False,
        'independent_relevance_labels': False,
        'eligible_for_retrieval_benchmark_claim': False,
        'method': ('Self-supervised lexical self-retrieval sanity check (structural, not clinical). '
                   'Query per chunk = its section heading + declared topic frontmatter '
                   '(parentheticals stripped, stopword-filtered, deduped). Retriever = Okapi '
                   'BM25 (k1=1.5, b=0.75) over all RAG_Optimised L2 chunk bodies. Ground truth '
                   '= the source chunk itself. Metrics: hit-rate@k and MRR.'),
        'corpus_docs': idx.n,
        'avgdl': round(idx.avgdl, 2),
        'queries': nq,
        'elapsed_sec': round(elapsed, 1),
        'metrics': {f'hit@{k}': pct(hits[k], nq) for k in KS},
        'mrr': round(rr / nq, 4),
        'per_chapter': {ch: {'chunks': pc['n'],
                             **{f'hit@{k}': pct(pc['hits'][k], pc['n']) for k in KS},
                             'mrr': round(pc['rr'] / pc['n'], 4)}
                        for ch, pc in sorted(per_chapter.items())},
        'queries_detail': details,
    }
    with open(os.path.join(report_dir, 'retrieval_accuracy_report.json'), 'w',
              encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    lines = ['# Self-Retrieval Sanity Report (not an independent retrieval benchmark)', '',
             '**Scope:** SELF_RETRIEVAL_SANITY_ONLY — do not cite these metrics as retrieval accuracy.', '',
             '**Method:** ' + report['method'], '',
             '| Metric | Value |', '|---|---|']
    for k in KS:
        lines.append('| hit@%d | %.2f%% |' % (k, report['metrics']['hit@%d' % k]))
    lines.append('| MRR | %.4f |' % report['mrr'])
    lines += ['', '## Per-chapter', '',
              '| Chapter | N | hit@1 | hit@3 | hit@5 | hit@10 | MRR |',
              '|---|---|---|---|---|---|---|']
    for ch, pc in report['per_chapter'].items():
        lines.append('| %s | %d | %.2f | %.2f | %.2f | %.2f | %.4f |' % (
            ch, pc['chunks'], pc['hit@1'], pc['hit@3'], pc['hit@5'], pc['hit@10'], pc['mrr']))
    with open(os.path.join(report_dir, 'retrieval_accuracy_report.md'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('\nreport written to', report_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())