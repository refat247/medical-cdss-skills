"""v2.6.7 -- Chapter 05 Stage 4.7 completeness recomputation (Part E of the
v2.6.7 emergency correctness task; REPOSITORY_PRODUCTION_READINESS_AUDIT.md
Blocker 1: CompletenessChecklist.md declares "Disease clusters (>=2 chunks):
14" but only 8 are individually named anywhere -- the other 6 were never
enumerated, no COMPLETE_DISEASES.json, no complete_count field).

This is READ-ONLY, diagnostic only: it re-derives the multi-chunk
disease_focus clustering fresh from the CURRENT chunks.md, using the exact
unmodified Stage 4.7 clustering algorithm from SKILL.md's inline block
(infer_categories / REQUIRED_CATEGORIES / BODY_PATTERNS / the >=2-missing
SCATTERED rule / the SUSPECTED_GAP_RULE mechanism) -- pipeline/stages/stage_4_7_serialize.py
itself is untouched, and this script does not write anything to Ch05's real
files. It only prints the full recomputed cluster inventory so it can be
individually verified and then hand-transcribed into the real
CompletenessChecklist.md / SCATTERED.json / SUSPECTED_GAP.json /
COMPLETE_DISEASES.json / checkpoint by a separate, explicit write step.

The SUSPECTED_GAP_RULE below reproduces the exact curated ruleset the
2026-07-28 original Stage 4.7 run used for this chapter (transcribed from
the existing CompletenessChecklist.md's own SUSPECTED_GAP section, since the
original curation script is not preserved) -- this is necessary to get an
apples-to-apples re-derivation of the ALREADY-VERIFIED 6 SCATTERED + 2
SUSPECTED_GAP entries (so this script can confirm, not silently diverge
from, that already-good work), while additionally surfacing every other
multi-chunk cluster this chapter has that the original run's curated rule
never named.
"""
import re
import os
import json

OUT_DIR = r"D:\davidson_25_full_pipeline\05"
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"
CHUNK_PATH = os.path.join(OUT_DIR, f"{PREFIX}_chunks.md")

DISEASES_CH = {}
SUSPECTED_GAP_RULE = {
    'vitamin_k_deficiency': {
        'implied_categories': ['complication_or_safety'],
        'reason': ("Vitamin K's clinical relevance is dominated by anticoagulation "
                   "interactions (warfarin) and bleeding risk in deficiency/excess -- a "
                   "chapter covering vitamin K without any safety/interaction content "
                   "would be a real gap worth flagging."),
    },
    'anorexia_nervosa': {
        'implied_categories': ['investigation'],
        'reason': ("Anorexia nervosa nutritional management typically requires specific "
                   "monitoring/investigation protocols (e.g. MEED guideline bloods, ECG) "
                   "beyond generic under-nutrition investigations -- worth checking this "
                   "chapter names any."),
    },
}

REQUIRED_CATEGORIES = ['causes', 'clinical_presentation', 'investigation',
                        'treatment', 'complication_or_safety']


def extract_disease_names(topic, diseases):
    topic_l = topic.lower()
    matches = [k for k, aliases in diseases.items() if any(a.lower() in topic_l for a in aliases)]
    return matches or [re.sub(r'\W+', '_', topic_l).strip('_')[:50]]


BODY_PATTERNS = {
    'causes': [r'\bcause[sd]?\s+(?:is|are|unknown|of)\b', r'\bcaused by\b',
               r'\baetiology\b', r'\betiology\b', r'\bgenetic (?:component|association|factor|variant)',
               r'\brisk factor'],
    'clinical_presentation': [r'\bpresents?\s+with\b', r'\bpresentation is\b'],
    'investigation': [r'\bdiagnos(?:is|ed)\s+(?:is|can be|confirmed)\b',
                       r'\binvestigation', r'\bbiopsy\b', r'\bimaging (?:shows|reveals)\b'],
    'treatment': [r'\btreatment is\b', r'\btreated with\b', r'\bmanagement is\b',
                  r'\bfirst-line\b', r'\btherapy (?:is|with|includes)\b',
                  r'\bmanaged with\b', r'\bcan be managed\b'],
    'complication_or_safety': [r'\badverse effect', r'\bside.?effect', r'\bcomplication',
                                r'\bcontraindicat', r'\bshould be (?:checked|monitored)\b',
                                r'\bsafety\b', r'\brisk of\b'],
}


def infer_categories(semantic_type, topic, body=''):
    t = topic.lower()
    cats = set()
    if any(w in t for w in ['cause', 'aetiology', 'etiology', 'risk factor']):
        cats.add('causes')
    if any(w in t for w in ['clinical', 'feature', 'presentation', 'sign', 'symptom', 'complication', 'manifestation']):
        cats.add('clinical_presentation')
    if any(w in t for w in ['investigation', 'imaging', 'scan', 'lab', 'test', 'csf', 'culture', 'biopsy', 'dxa']):
        cats.add('investigation')
    if any(w in t for w in ['treatment', 'management', 'drug', 'therapy', 'antibiotic', 'medication', 'surgery']):
        cats.add('treatment')
    if any(w in t for w in ['adverse', 'side effect', 'contraindication', 'toxicity', 'harm']):
        cats.add('complication_or_safety')

    if semantic_type in ('diagnostic_criteria', 'clinical_feature'):
        cats.add('clinical_presentation')
    if semantic_type == 'diagnostic_criteria':
        cats.add('causes')
    if semantic_type == 'pathophysiology':
        cats.add('causes')
    if semantic_type == 'laboratory_investigation':
        cats.add('investigation')
    if semantic_type in ('drug_info', 'management_step'):
        cats.add('treatment')
    if semantic_type == 'drug_info':
        cats.add('complication_or_safety')

    if body:
        bl = body.lower()
        for cat, patterns in BODY_PATTERNS.items():
            if cat not in cats and any(re.search(p, bl) for p in patterns):
                cats.add(cat)
    return cats


def main():
    chunks_data = open(CHUNK_PATH, encoding='utf-8').read()
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', chunks_data, re.DOTALL)
    l2 = []
    for b in blocks:
        if not re.search(r'chunk_level:\s*2', b):
            continue
        cid = re.search(r'chunk_id:\s*(.+)', b).group(1).strip()
        sem = re.search(r'semantic_type:\s*(.+)', b).group(1).strip()
        top = re.search(r'topic:\s*(.+)', b).group(1).strip()
        df = re.search(r'disease_focus:\s*(.*)', b)
        df = df.group(1).strip() if df else ''
        parts = b.split('---\n')
        body = parts[2].strip() if len(parts) >= 3 else ''
        l2.append({'id': cid, 'semantic_type': sem, 'topic': top, 'disease_focus': df, 'body': body})

    disease_clusters = {}
    for c in l2:
        key = c['disease_focus'] or extract_disease_names(c['topic'], DISEASES_CH)[0]
        disease_clusters.setdefault(key, []).append(c)
    multi = {d: cs for d, cs in disease_clusters.items() if len(cs) >= 2}

    SCATTERED, SUSPECTED_GAP = {}, {}
    coverage_by_disease = {}
    for disease, cs in multi.items():
        coverage = {cat: False for cat in REQUIRED_CATEGORIES}
        for c in cs:
            for cat in infer_categories(c['semantic_type'], c['topic'], c['body']):
                coverage[cat] = True
        coverage_by_disease[disease] = coverage
        missing = [cat for cat, present in coverage.items() if not present]
        if len(missing) >= 2:
            SCATTERED[disease] = {'chunk_ids': [c['id'] for c in cs], 'missing': missing}
        elif len(missing) == 1 and disease in SUSPECTED_GAP_RULE:
            rule = SUSPECTED_GAP_RULE[disease]
            if missing[0] in rule['implied_categories']:
                SUSPECTED_GAP[disease] = {'missing': missing, 'reason': rule['reason'],
                                           'chunk_ids': [c['id'] for c in cs]}

    for disease, rule in SUSPECTED_GAP_RULE.items():
        if disease in SCATTERED or disease in SUSPECTED_GAP:
            continue
        cs = disease_clusters.get(disease, [])
        if not cs:
            continue
        coverage = {cat: False for cat in REQUIRED_CATEGORIES}
        for c in cs:
            for cat in infer_categories(c['semantic_type'], c['topic'], c['body']):
                coverage[cat] = True
        for implied in rule['implied_categories']:
            if not coverage[implied]:
                SUSPECTED_GAP[disease] = {'missing': [implied], 'reason': rule['reason'],
                                           'chunk_ids': [c['id'] for c in cs]}
                break

    COMPLETE_DISEASES = [d for d in multi if d not in SCATTERED and d not in SUSPECTED_GAP]

    print(f"Total L2 chunks: {len(l2)}")
    print(f"Total multi-chunk (>=2) disease_focus clusters: {len(multi)}")
    print(f"SCATTERED: {len(SCATTERED)}  SUSPECTED_GAP: {len(SUSPECTED_GAP)}  "
          f"COMPLETE (fresh): {len(COMPLETE_DISEASES)}")
    print(f"Arithmetic check: {len(SCATTERED)} + {len(SUSPECTED_GAP)} + {len(COMPLETE_DISEASES)} "
          f"= {len(SCATTERED) + len(SUSPECTED_GAP) + len(COMPLETE_DISEASES)} (must equal {len(multi)})")
    print()
    print("=== ALL MULTI-CHUNK CLUSTERS (full inventory) ===")
    for d in sorted(multi.keys()):
        cs = multi[d]
        cov = coverage_by_disease[d]
        missing = [cat for cat, present in cov.items() if not present]
        disp = ("SCATTERED" if d in SCATTERED else
                "SUSPECTED_GAP" if d in SUSPECTED_GAP else
                "COMPLETE(fresh)")
        sem_dist = {}
        for c in cs:
            sem_dist[c['semantic_type']] = sem_dist.get(c['semantic_type'], 0) + 1
        print(f"- {d} [{disp}] n={len(cs)} missing={missing}")
        print(f"    chunk_ids={[c['id'] for c in cs]}")
        print(f"    semantic_type_dist={sem_dist}")

    # v2.6.3 SAFETY GUARDRAIL: this script is PURE READ-ONLY / stdout-diagnostic
    # by design -- it never opens any path for writing and never touches any
    # real chapter evidence file. The full cluster inventory above (printed to
    # stdout) is the only output; hand-verified findings were subsequently
    # transcribed into CompletenessChecklist.md / SCATTERED.json /
    # SUSPECTED_GAP.json / COMPLETE_DISEASES.json / the checkpoint by a
    # separate, explicit, human-reviewed write step (not by this script).
    print("\n(Read-only diagnostic script -- no files written.)")


if __name__ == "__main__":
    main()
