"""Deterministic DECIDE prompt guard; source fidelity still needs human adjudication."""
from __future__ import annotations

import argparse
import json
import re

try:
    from scripts.common import read_csv
except ModuleNotFoundError:
    from common import read_csv


PASS = {'pass', 'yes', 'true', '1', 'adjudicated'}
SOURCE_META = re.compile(
    r'\b(?:source[- ](?:defined|supported|listed|table|native|based)|'
    r'SOURCE_[AB]|scenario criteria|branch/comparison|comparison branch)\b', re.I
)
RECOMMENDATION = re.compile(
    r'\b(?:is|are|was|were|may be|can be|should be)\s+(?:not\s+)?'
    r'(?:recommended|reasonable|indicated|beneficial|useful|considered)\b|'
    r'\bshould\s+(?:not\s+)?(?:receive|use|undergo|start|initiate|continue|stop)\b', re.I
)
ACTION_NOUN = re.compile(
    r'[,;]\s*(?:the\s+)?(?:addition|initiation|use|treatment|rechallenge|'
    r'screening|measurement|referral|prescription)\s+(?:of|with|to)\b', re.I
)
TRAILING_FRAGMENT = re.compile(
    r'(?:[,;:]\s*(?:and\s+|or\s+)?(?:rechallenge|treatment|screening|'
    r'monitoring|follow[- ]up|therapy|referral)\s*\.?|[,;:/-]\s*)$', re.I
)
ORPHAN = re.compile(r'^(?:it|is|are|risk|events|treatment|clinicians|and|or|the|a|an)\W*$', re.I)


def norm(value):
    return re.sub(r'\s+', ' ', value.strip())


def add(issues, rid, issue):
    issues.append({'severity': 'HIGH', 'id': rid, 'issue': issue})


def validate(path):
    issues = []
    for i, row in enumerate(read_csv(path), 2):
        rid = (row.get('case_id') or f'row-{i}').strip()
        prompt = norm(row.get('prompt_text') or '')
        answer = norm(row.get('expected_answer') or row.get('withheld_decision_text') or '')
        scenario = norm(row.get('source_derived_scenario') or '')
        question = norm(row.get('case_query_setup') or '')
        has_scenario_column = 'source_derived_scenario' in row

        if not prompt:
            add(issues, rid, 'empty prompt')
            continue
        if SOURCE_META.search(prompt):
            add(issues, rid, 'source/pipeline metalanguage visible to learner')
        # New ledgers keep the source-derived setup and neutral question separately.
        # Old ledgers remain readable; their semantic statuses still gate release.
        if has_scenario_column:
            if not scenario or not question:
                add(issues, rid, 'source-derived scenario or neutral decision question missing')
            elif norm(f'{scenario} {question}') != prompt:
                add(issues, rid, 'source_derived_scenario / case_query_setup / prompt_text drift')
            if question and not question.endswith('?'):
                add(issues, rid, 'DECIDE question does not end with a question mark')
            if scenario and (RECOMMENDATION.search(scenario) or ACTION_NOUN.search(scenario)):
                add(issues, rid, 'recommendation/action leaked in scenario before commitment')
            if scenario and (TRAILING_FRAGMENT.search(scenario) or scenario.endswith((';', ':', ','))):
                add(issues, rid, 'scenario ends with a dangling fragment')
        elif RECOMMENDATION.search(prompt):
            add(issues, rid, 'source-native action predicate visible before commitment')

        words = re.findall(r"[A-Za-z][A-Za-z'-]*|\d+", prompt)
        if ORPHAN.match(prompt) or len(words) < 8:
            add(issues, rid, 'extremely short/non-decision stem')
        if TRAILING_FRAGMENT.search(prompt) or prompt.endswith(('/', '-', ',', ';', ':')):
            add(issues, rid, 'prompt is fragment/orphan or ends mid-clause')
        if not prompt.endswith('?') and not has_scenario_column:
            # Legacy records can carry a reviewed declarative setup, but cannot
            # silently pass a source recommendation as a DECIDE prompt.
            if not re.search(r'\b(?:what|which|how|whether|would|should|is|are|can|could)\b', prompt, re.I):
                add(issues, rid, 'no discernible learner decision question')
        if answer and len(answer.split()) >= 2 and answer.casefold() in prompt.casefold():
            add(issues, rid, 'expected answer phrase leaked into prompt')
        for field, label in (
            ('prompt_leak_status', 'prompt leak status unresolved/failed'),
            ('prompt_coherence_status', 'prompt coherence status unresolved/failed'),
            ('prompt_semantic_review_status', 'mandatory prompt semantic comparison unresolved/failed'),
        ):
            if (row.get(field) or '').strip().lower() not in PASS:
                add(issues, rid, label)
    return {'gate': 'PROMPT_SEMANTICS', 'issues': issues, 'pass': not issues}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    args = ap.parse_args()
    result = validate(args.csv)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
