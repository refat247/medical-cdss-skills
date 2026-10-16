"""Explicit, source-ordered reference blocks. No clinical inference or sentence splitting."""
import html
import json
import re
from html.parser import HTMLParser

ROLES = {'heading', 'context', 'dose', 'preparation', 'concentration', 'example',
         'brands', 'loading', 'dilution', 'maintenance', 'indication', 'comparison',
         'review', 'source'}


def validate_entry(entry):
    if not isinstance(entry, dict) or entry.get('schema') != 'reference-entry-v1':
        raise ValueError('reference-entry: expected schema reference-entry-v1')
    source = entry.get('source_text')
    rows = entry.get('rows')
    if not isinstance(source, str) or not source.strip() or not isinstance(rows, list) or not rows:
        raise ValueError('reference-entry: source_text and nonempty rows required')
    position = 0
    closed_groups = set()
    previous_group = None
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('reference-entry: row must be an object')
        start, end = row.get('start'), row.get('end')
        if type(start) is not int or type(end) is not int or start != position or not start < end <= len(source):
            raise ValueError('reference-entry: spans must cover source in order without gaps or overlaps')
        if row.get('role', 'source') not in ROLES:
            raise ValueError('reference-entry: unknown role')
        group = row.get('group', '')
        if not isinstance(group, str) or len(group) > 100:
            raise ValueError('reference-entry: invalid group')
        if group != previous_group:
            if previous_group:
                closed_groups.add(previous_group)
            if group and group in closed_groups:
                raise ValueError('reference-entry: formulation group must remain contiguous')
            previous_group = group
        position = end
    if position != len(source):
        raise ValueError('reference-entry: source tail missing')
    explanation = entry.get('explanation_bn', '')
    if not isinstance(explanation, str) or (explanation and not re.search('[\u0980-\u09ff]', explanation)):
        raise ValueError('reference-entry: explanation_bn must contain Bengali text')
    if 'locator' in entry and not isinstance(entry['locator'], str):
        raise ValueError('reference-entry: locator must be a string')
    return entry


def render_entry(entry, entry_id):
    validate_entry(entry)
    source = entry['source_text']
    parts = [f'<section class="reference-entry" data-reference-id="{entry_id}">']
    group = None
    for row in entry['rows']:
        current = row.get('group', '')
        if current != group:
            if group:
                parts.append('</div>')
            if current:
                parts.append('<div class="reference-formulation" data-formulation="' + html.escape(current, quote=True) + '">')
            group = current
        role = row.get('role', 'source')
        start, end = row['start'], row['end']
        text = html.escape(source[start:end])
        # Do not interpret Markdown within immutable clinical source spans.
        if role in {'heading', 'preparation'}:
            text = '<strong>' + text + '</strong>'
        parts.append(f'<p class="reference-span reference-{role}" data-reference-owner="{entry_id}" data-start="{start}" data-end="{end}">{text}</p>')
    if group:
        parts.append('</div>')
    if entry.get('explanation_bn'):
        parts.append('<aside class="reference-explanation" lang="bn"><p>' + html.escape(entry['explanation_bn']) + '</p></aside>')
    if entry.get('locator'):
        parts.append('<p class="reference-locator">' + html.escape(entry['locator']) + '</p>')
    # Encode markup-sensitive characters so source text cannot terminate the script.
    payload = json.dumps(entry, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    parts.append(f'<script type="application/json" data-reference-source="{entry_id}">' + payload + '</script>')
    parts.append('</section>')
    return '\n'.join(parts)


def density_findings(sections, intro):
    findings = []
    def scan(blocks, location):
        for kind, data in blocks:
            if kind == 'reference':
                texts = [data['source_text'][r['start']:r['end']] for r in data['rows']]
            elif kind in {'p', 'ul', 'ol'}:
                texts = data if kind in {'ul', 'ol'} else [data]
            else:
                continue
            for i, text in enumerate(texts):
                if not isinstance(text, str):
                    continue
                labels = re.findall(r'\b(?:Dose|Syrup|Drop|Brands?|Loading|Maintenance|Dilution|DS(?:/Forte)?|Example)\s*:', text, re.I)
                if len(text) > 320 or (len(text) > 180 and len(labels) >= 2):
                    findings.append({'location': location, 'block_type': kind, 'item': i + 1,
                                     'characters': len(text), 'explicit_labels': len(labels),
                                     'status': 'READABILITY REVIEW REQUIRED'})
    scan(intro, 'front matter')
    for section in sections:
        scan(section.get('intro', []), section['title'])
        for chapter in section['chapters']:
            scan(chapter['blocks'], section['title'] + ' — ' + chapter['title'])
    return findings


class ReferenceArtifactParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sources, self.spans, self.capture = {}, {}, None
        self.owners = []
        self.errors = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in {'br', 'hr', 'img', 'input', 'meta', 'link', 'wbr', 'source'}:
            self.stack.append((tag, attrs))
        if tag == 'section' and 'data-reference-id' in attrs:
            self.owners.append(attrs['data-reference-id'])
        if tag == 'script' and 'data-reference-source' in attrs:
            self.capture = ('source', attrs['data-reference-source'], '', attrs)
        elif tag == 'p' and 'data-reference-owner' in attrs:
            section = next((a.get('data-reference-id') for t, a in reversed(self.stack) if t == 'section' and 'data-reference-id' in a), None)
            if section != attrs['data-reference-owner']:
                self.errors.append('reference row escaped its entry')
            attrs['_group'] = next((a['data-formulation'] for t, a in reversed(self.stack) if t == 'div' and 'data-formulation' in a), '')
            self.capture = ('span', attrs['data-reference-owner'], '', attrs)

    def handle_data(self, data):
        if self.capture:
            kind, owner, text, attrs = self.capture
            self.capture = (kind, owner, text + data, attrs)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break
        if not self.capture:
            return
        kind, owner, text, attrs = self.capture
        if (kind == 'source' and tag == 'script') or (kind == 'span' and tag == 'p'):
            if kind == 'source':
                if owner in self.sources:
                    self.errors.append('duplicate reference source ID')
                self.sources[owner] = text
            else:
                self.spans.setdefault(owner, []).append((attrs, text))
            self.capture = None


def check_reference_artifact(text):
    parser = ReferenceArtifactParser()
    parser.feed(text)
    errors = list(parser.errors)
    if len(parser.owners) != len(set(parser.owners)):
        errors.append('duplicate reference entry ID')
    if set(parser.sources) != set(parser.spans) or set(parser.owners) != set(parser.sources):
        errors.append('reference sources, entries and rendered spans mismatch')
    for owner, payload in parser.sources.items():
        try:
            entry = validate_entry(json.loads(payload))
            rendered = parser.spans.get(owner, [])
            if len(rendered) != len(entry['rows']):
                raise ValueError('reference row count mismatch')
            for (attrs, content), row in zip(rendered, entry['rows']):
                if attrs['_group'] != row.get('group', ''):
                    raise ValueError('reference formulation ownership changed')
                if 'reference-' + row.get('role', 'source') not in attrs.get('class', '').split():
                    raise ValueError('reference role changed')
                if attrs['data-start'] != str(row['start']) or attrs['data-end'] != str(row['end']):
                    raise ValueError('reference offsets changed')
                if content != entry['source_text'][row['start']:row['end']]:
                    raise ValueError('reference source text changed or lost')
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f'{owner}: {exc}')
    return errors
