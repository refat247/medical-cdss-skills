#!/usr/bin/env python3
"""VISUAL_POLISH engine: presentation-only restyle of a built evidence-locked deck.

    python -m scripts.visual_polish.polish BUILT.pptx OUT.pptx \
        [--profile projector_default|dense_case_reveal] [--profile-approved-by NAME] \
        [--only 1 2 3 ...] [--report polish_report.json]

Contract (see docs/visual_polish_protocol.md):
  * Text is copied run by run from the built slide (bold/italic/super/subscript
    kept). Nothing is retyped, shortened, merged or paraphrased.
  * Slide order, slide ids, layouts, layout/master chrome and speaker notes are
    never touched. Only the slide's own shape tree is rebuilt.
  * Fail closed:
      SKIPPED         - slide role or text structure not recognised -> left as built
      SPLIT_REQUIRED  - text cannot fit at the profile's font floor -> left as
                        built; route upstream (SKILL.md section 17 repair order:
                        notes / split / restructure; never blind shrinking)
  * This script never certifies anything. Run verify.py, then the existing
    render + 100% visual review + promotion gates.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Pt

try:
    from scripts.visual_polish import style as S
except ModuleNotFoundError:  # direct execution from the folder
    import style as S

_ALIGN = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}
_ANCH = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}
E = S.emu


class Skip(Exception):
    """Structure not recognised: leave slide exactly as built."""


class SplitRequired(Exception):
    """Locked text cannot fit at the profile floor: leave slide as built."""


# ====================================================================== drawing
def _rgb(h):
    return RGBColor.from_string(h)


def shape(slide, x, y, w, h, fill=None, line=None, lw=0.75, radius=0, oval=False, name=None):
    kind = MSO_SHAPE.OVAL if oval else (MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE)
    sp = slide.shapes.add_shape(kind, E(x), E(y), E(w), E(h))
    if radius and not oval:
        sp.adjustments[0] = min(0.5, radius / max(1e-6, min(w, h)))
    if fill:
        sp.fill.solid(); sp.fill.fore_color.rgb = _rgb(fill)
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = _rgb(line); sp.line.width = E(lw)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    if name:
        sp.name = name
    return sp


def gradient(sp, c1, c2, angle):
    sp.fill.gradient(); sp.fill.gradient_angle = angle
    st = sp.fill.gradient_stops
    st[0].color.rgb = _rgb(c1); st[0].position = 0
    st[1].color.rgb = _rgb(c2); st[1].position = 1.0


def text(slide, x, y, w, h, content, size, color, bold=False, font=S.FONT, align='l', anchor='t',
         pitch=None, spacing=0.0, fill=None, line=None, radius=0, inset=0.0, wrap=True, name=None,
         src_paragraphs=None):
    """Exact-pitch text box. `src_paragraphs` copies python-pptx paragraphs run by
    run so emphasis and super/subscript survive."""
    if fill or line:
        sp = shape(slide, x, y, w, h, fill, line, radius=radius)
    else:
        sp = slide.shapes.add_textbox(E(x), E(y), E(w), E(h))
    if name:
        sp.name = name
    tf = sp.text_frame
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = E(inset)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = _ANCH[anchor]
    paras = src_paragraphs if src_paragraphs is not None else content.split('\n')
    for i, src in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = _ALIGN[align]
        p.line_spacing = Pt(S.fpt(size * (pitch or 1.2)))
        p.space_before = p.space_after = 0
        runs = list(src.runs) if src_paragraphs is not None else [None]
        for sr in runs:
            r = p.add_run()
            r.text = sr.text if sr is not None else src
            f = r.font
            f.size = Pt(S.fpt(size)); f.name = font; f.color.rgb = _rgb(color)
            f.bold = bool(sr.font.bold) if (sr is not None and sr.font.bold is not None) else bold
            if sr is not None and sr.font.italic:
                f.italic = True
            if sr is not None and sr.font.underline:
                f.underline = True
            rpr = r._r.get_or_add_rPr()
            if sr is not None and sr._r.rPr is not None and sr._r.rPr.get('baseline'):
                rpr.set('baseline', sr._r.rPr.get('baseline'))
            if spacing:
                rpr.set('spc', str(int(round(S.fpt(spacing) * 100))))
    return sp


def pill_w(label, size=16, padx=8, spacing=0.0):
    return S.text_width(label, size, True) + 2 * padx + spacing * len(label) + 2


def pill(slide, x, y, label, fg, bg, border, size=16, h=24, radius=12, padx=8, spacing=0.0, name='Pill'):
    w = pill_w(label, size, padx, spacing)
    text(slide, x, y, w, h, label, size, fg, bold=True, align='c', anchor='m', fill=bg, line=border,
         radius=radius, spacing=spacing, wrap=False, name=name)
    return w


def clear(slide):
    """Remove the slide's own shapes. Layout/master chrome and notes untouched."""
    tree = slide.shapes._spTree
    for sp in list(slide.shapes):
        tree.remove(sp._element)


def background(slide, color):
    f = slide.background.fill
    f.solid(); f.fore_color.rgb = _rgb(color)


# ====================================================================== parsing
def T(sp):
    return sp.text_frame.text if getattr(sp, 'has_text_frame', False) else ''


def G(prs, sp):
    """Shape geometry in design points."""
    k = S.DESIGN_W / (prs.slide_width / 12700)
    return dict(x=sp.left / 12700 * k, y=sp.top / 12700 * k, w=sp.width / 12700 * k, h=sp.height / 12700 * k)


def classify(index, slide):
    texts = [T(s).strip() for s in slide.shapes if T(s).strip()]
    if not texts:
        return 'unknown'
    t0 = texts[0]
    if t0 == 'CASE / DECIDE':
        return 'decide'
    if t0 == 'GUIDELINE / SOURCE REVEAL':
        return 'reveal'
    if t0 == 'TEACHING CONTRACT':
        return 'contract'
    if re.fullmatch(r'M\d{2}', t0):
        return 'divider'
    if t0 == 'CLOSURE':
        return 'closure'
    if index == 0 and any('\u2192' in t for t in texts):
        return 'cover'
    return 'unknown'


def parse_case(prs, slide):
    shapes = list(slide.shapes)
    geo = {id(s): G(prs, s) for s in shapes}
    texts = [s for s in shapes if T(s).strip()]
    eyebrow, title = texts[0], texts[1]
    used = {id(eyebrow), id(title)}
    thin = sorted((geo[id(s)]['w'] for s in shapes if not T(s).strip() and geo[id(s)]['h'] < 8 and geo[id(s)]['w'] > 10))
    ratio = thin[0] / thin[-1] if len(thin) >= 2 and thin[-1] else 0
    cards = sorted((s for s in shapes if not T(s).strip() and geo[id(s)]['h'] > 200 and geo[id(s)]['w'] > 100),
                   key=lambda s: geo[id(s)]['x'])
    if not cards:
        raise Skip('no case cards found')
    cases = []
    for c in cards:
        g = geo[id(c)]
        inside = [s for s in texts if g['x'] - 2 <= geo[id(s)]['x'] < g['x'] + g['w'] and g['y'] - 2 <= geo[id(s)]['y'] < g['y'] + g['h']]
        ids = [s for s in inside if re.fullmatch(r'CASE \d+', T(s).strip())]
        badges = [s for s in inside if T(s).strip().startswith('REVEAL') or T(s).strip() == 'DECIDE']
        bodies = [s for s in inside if s not in ids and s not in badges]
        if len(ids) != 1 or len(badges) > 1 or len(bodies) != 1:
            raise Skip(f'unrecognised card structure ({len(ids)} ids, {len(badges)} badges, {len(bodies)} bodies)')
        used.update(id(s) for s in ids + badges + bodies)
        cases.append(dict(id=T(ids[0]).strip(), badge=T(badges[0]).strip() if badges else '',
                          body=T(bodies[0]), paragraphs=list(bodies[0].text_frame.paragraphs)))
    sources = [s for s in texts if id(s) not in used and T(s).strip().upper().startswith('SOURCE')]
    used.update(id(s) for s in sources)
    leftover = [T(s) for s in texts if id(s) not in used]
    if leftover:
        raise Skip(f'unrecognised text elements: {leftover[:2]}')
    if len(sources) > 1:
        raise Skip('more than one source line')
    return dict(eyebrow=T(eyebrow).strip(), title=T(title).strip(), ratio=ratio, cases=cases,
                source=T(sources[0]).strip() if sources else '')


def rows_by_y(prs, slide, start):
    texts = [s for s in slide.shapes if T(s).strip()][start:]
    rows = []
    for s in sorted(texts, key=lambda s: G(prs, s)['y']):
        y = G(prs, s)['y']
        if rows and abs(rows[-1][0] - y) < 12:
            rows[-1][1].append(s)
        else:
            rows.append([y, [s]])
    return [sorted(r[1], key=lambda s: G(prs, s)['x']) for r in rows]


def badge_parts(badge):
    """'REVEAL • 3: No Benefit/A; 1/C-LD' -> ('REVEAL •', ['3: No Benefit/A', '1/C-LD'])."""
    m = re.match(r'^(REVEAL\s*•?)\s*(.*)$', badge)
    if not m:
        return badge, []
    label, code = m.group(1).strip(), m.group(2).strip()
    return label, [p.strip() for p in code.split(';') if p.strip()]


def cor_colors(code):
    m = re.match(r'(1|2a|2b|3)\b', code)
    return S.COR[m.group(1)] if m else (S.PHASE['reveal']['text'], S.PHASE['reveal']['tint'], S.PHASE['reveal']['border'])


# ====================================================================== case slides
L = dict(margin=32, phase_y=9, eyebrow_y=20, title_y=41, title_h=50, prog_y=93, card_top=106,
         card_bottom=474, source_y=480, gap=14, pad=12, stripe=5)


def fit_title(title, profile):
    w = (S.DESIGN_W - 2 * L['margin']) * 0.96  # margin for renderer metric differences
    for s in range(profile['title_max'], 23, -1):
        if S.text_width(title, s, True) <= w:
            return s
    return None


def plan_header(case, inner_w, size=None):
    """Lay out case pill + phase/COR badges; wrap to a second row if needed."""
    if size is None:  # 16 pt when it fits on one row, else 14 pt (S.BADGE_MIN)
        one = plan_header(case, inner_w, 16)
        return one if one['rows'] == 1 else plan_header(case, inner_w, S.BADGE_MIN)
    items = []
    if case['badge'] == 'DECIDE':
        items = [('phase', 'DECIDE', pill_w('DECIDE', size, spacing=1.0))]
    elif case['badge']:
        label, codes = badge_parts(case['badge'])
        if codes:
            items = [('label', label, S.text_width(label, size, True) + 2 * len(label) * 0.5 + 4)]
            items += [('cor', c, pill_w(c, size)) for c in codes]
        else:
            items = [('phase', case['badge'], pill_w(case['badge'], size, spacing=1.0))]
    case_w = pill_w(case['id'], size, spacing=0.5)
    group_w = sum(w for _, _, w in items) + 6 * max(0, len(items) - 1)
    if case_w + 10 + group_w <= inner_w:
        return dict(rows=1, case_w=case_w, rows_items=[items], align='r', size=size)
    rows, cur, cw = [], [], 0
    for it in items:
        add = it[2] + (6 if cur else 0)
        if cur and cw + add > inner_w:
            rows.append(cur); cur, cw = [], 0; add = it[2]
        if it[2] > inner_w:
            raise SplitRequired(f'badge {it[1]!r} wider than card')
        cur.append(it); cw += add
    if cur:
        rows.append(cur)
    return dict(rows=1 + len(rows), case_w=case_w, rows_items=rows, align='l', size=size)


def build_case(prs, slide, d, profile, rep):
    phase = 'reveal' if d['eyebrow'].startswith('GUIDELINE') else 'decide'
    P = S.PHASE[phase]
    k = len(d['cases'])
    if k > 3:
        raise Skip(f'{k} cards (max 3 supported)')
    floor, top = profile['body_floor'][k], profile['body_max'][k]
    tsize = fit_title(d['title'], profile)
    if tsize is None:
        raise SplitRequired('title does not fit on one line at 24 pt')
    cw = (S.DESIGN_W - 2 * L['margin'] - L['gap'] * (k - 1)) / k
    inner_w = cw - L['stripe'] - 2 * L['pad']
    ch = L['card_bottom'] - L['card_top']

    # ---------- plan every card first (all-or-nothing: no partial rebuilds)
    plans = []
    for c in d['cases']:
        hp = plan_header(c, inner_w)
        header_h = 12 + 24 * hp['rows'] + 6 * (hp['rows'] - 1) + 12
        body_h = ch - header_h - 12 - 12
        plans.append(dict(case=c, header=hp, header_h=header_h, body_h=body_h))
    body_h = min(p['body_h'] for p in plans)
    watermark = k == 1
    width = inner_w - (210 if watermark else 0)
    size = S.fit_size([p['case']['body'] for p in plans], width, body_h, top, floor)
    if size is None and watermark:
        watermark, width = False, inner_w
        size = S.fit_size([p['case']['body'] for p in plans], width, body_h, top, floor)
    if size is None:
        need = max(S.text_height(p['case']['body'], width, floor) for p in plans)
        raise SplitRequired(f'body needs {need:.0f} pt at {floor} pt floor; {body_h:.0f} pt available')

    # ---------- rebuild
    clear(slide)
    background(slide, S.BG)
    shape(slide, 0, L['phase_y'], S.DESIGN_W, 3, P['bar'], name='Phase bar')
    text(slide, L['margin'], L['eyebrow_y'], 20, 20, P['icon'], 13, 'FFFFFF', bold=True, align='c', anchor='m',
         fill=P['bar'], radius=10, wrap=False, name='Phase icon')
    text(slide, L['margin'] + 28, L['eyebrow_y'], 600, 20, d['eyebrow'], 16, P['text'], bold=True, anchor='m',
         spacing=1.5, wrap=False, name='Eyebrow')
    text(slide, L['margin'], L['title_y'], S.DESIGN_W - 2 * L['margin'], L['title_h'], d['title'], tsize, S.NAVY,
         bold=True, font=S.FONT_D, anchor='m', wrap=False, name='Title')
    shape(slide, L['margin'], L['prog_y'], S.DESIGN_W - 2 * L['margin'], 4, S.LINE, radius=2, name='Progress track')
    if d['ratio']:
        shape(slide, L['margin'], L['prog_y'], max(8, (S.DESIGN_W - 2 * L['margin']) * d['ratio']), 4, P['bar'],
              radius=2, name='Progress fill')
    for i, p in enumerate(plans):
        c, hp = p['case'], p['header']
        x = L['margin'] + i * (cw + L['gap']); y0 = L['card_top']
        shape(slide, x, y0, cw, ch, 'FFFFFF', S.CARD_BORDER, radius=6, name=f'Card {c["id"]}')
        shape(slide, x + L['stripe'], y0 + 0.75, cw - L['stripe'] - 0.75, p['header_h'] - 0.75,
              S.blend(P['tint'], 'FFFFFF', 0.6), name='Card header tint')
        shape(slide, x, y0, L['stripe'], ch, P['bar'], name='Card phase stripe')
        ix = x + L['stripe'] + L['pad']; ry = y0 + 12
        bs = hp['size']
        pill(slide, ix, ry, c['id'], S.BLUE, 'FFFFFF', S.BLUE_BORDER, size=bs, radius=4, spacing=0.5, name='Case id')
        for r, items in enumerate(hp['rows_items']):
            if hp['align'] == 'r':
                cx = ix + inner_w - (sum(w for _, _, w in items) + 6 * (len(items) - 1)); yy = ry
            else:
                cx = ix; yy = ry + 30 * (r + 1)
            for kind, lab, w in items:
                if kind == 'phase':
                    fg, bg, bd = (P['text'], P['tint'], P['border'])
                    pill(slide, cx, yy, lab, fg, bg, bd, size=bs, spacing=1.0, name='Phase badge')
                elif kind == 'cor':
                    fg, bg, bd = cor_colors(lab)
                    pill(slide, cx, yy, lab, fg, bg, bd, size=bs, name='COR/LOE badge')
                else:
                    text(slide, cx, yy, w, 24, lab, bs, P['text'], bold=True, anchor='m', align='l',
                         spacing=0.5, wrap=False, name='Reveal label')
                cx += w + 6
        if watermark:
            num = c['id'].split()[-1]
            text(slide, x + cw - 250, L['card_bottom'] - 150, 236, 140, num, 120, S.blend(P['bar'], 'FFFFFF', 0.10),
                 bold=True, font=S.FONT_D, align='r', anchor='b', pitch=1.0, wrap=False, name='Case watermark')
        text(slide, ix, y0 + p['header_h'] + 12, width, body_h, c['body'], size, S.INK, pitch=S.LINE_PITCH,
             src_paragraphs=c['paragraphs'], name=f'Body {c["id"]}')
    if d['source']:
        text(slide, L['margin'], L['source_y'], S.DESIGN_W - 2 * L['margin'], 22, d['source'], 16, S.MUTED,
             anchor='m', wrap=False, name='Source line')
    rep.update(cards=k, body_pt=size, title_pt=tsize, header_rows=max(p['header']['rows'] for p in plans),
               watermark=watermark)


# ====================================================================== other roles
def build_cover(prs, slide, rep):
    texts = [s for s in slide.shapes if T(s).strip()]
    flow = [s for s in texts if '\u2192' in T(s)]
    rest = [s for s in texts if s not in flow]
    if len(flow) != 1 or len(rest) != 5:
        raise Skip('cover structure not recognised')
    title, sub, aud, b1, b2 = [T(s) for s in rest]
    steps = [re.sub(r'\s+', ' ', p).strip() for p in T(flow[0]).split('\u2192') if p.strip()]
    tl = title.split('\n')
    if len(tl) != 2 or len(steps) != 3:
        raise Skip('cover title/flow shape not recognised')
    ssize = S.fit_size([sub], 560, 2 * 24 * 1.2, 24, 20, pitch=1.2, bold=True)
    if ssize is None:
        raise SplitRequired('cover subtitle')
    clear(slide); background(slide, S.NAVY)
    g = shape(slide, 0, 0, S.DESIGN_W, S.DESIGN_H, S.NAVY, name='Cover background'); gradient(g, '0E2A47', S.NAVY, 45)
    for i, col in enumerate((S.BLUE_BRIGHT, S.PHASE['decide']['bar'], S.PHASE['reveal']['bar'])):
        shape(slide, 45, 60 + i * 137, 7, 136, col, name='Phase rail')
    text(slide, 75, 66, 560, 40, tl[0], 32, '7CB8FF', bold=True, font=S.FONT_D, anchor='b', wrap=False, name='Cover kicker')
    text(slide, 75, 108, 560, 70, tl[1], 58, 'FFFFFF', bold=True, font=S.FONT_D, anchor='t', pitch=1.1, wrap=False, name='Cover title')
    sh = len(S.wrap_lines(sub, 560, ssize, True)) * ssize * 1.2
    text(slide, 75, 205, 560, sh + 4, sub, ssize, 'E3ECF7', bold=True, pitch=1.2, name='Cover subtitle')
    ay = 205 + sh + 18
    al = aud.split('\n')
    text(slide, 75, ay, 560, 26, al[0], 20, 'B7C6D8', pitch=1.2, name='Audience')
    if len(al) > 1:
        text(slide, 75, ay + 28, 560, 22, '\n'.join(al[1:]), 16, '8FA3B8', pitch=1.2, name='Audience note')
    shape(slide, 640, 75, 288, 235, S.blend('FFFFFF', S.NAVY, 0.05), S.blend('7CB8FF', S.NAVY, 0.35), lw=1,
          radius=10, name='Flow panel')
    shape(slide, 679, 120, 2, 145, S.blend('FFFFFF', S.NAVY, 0.25), name='Flow connector')
    cols = (S.BLUE_BRIGHT, S.PHASE['decide']['bar'], S.PHASE['reveal']['bar'])
    for i, lab in enumerate(steps):
        y = 105 + i * 70
        text(slide, 664, y, 32, 32, str(i + 1), 16, 'FFFFFF', bold=True, align='c', anchor='m', fill=cols[i],
             radius=16, wrap=False, name='Flow step number')
        text(slide, 708, y - 4, 212, 40, ('\u2192 ' if i else '') + lab, 19, 'FFFFFF', bold=True, anchor='m',
             wrap=False, spacing=0.5, name='Flow step label')
    shape(slide, 75, 400, 830, 1, '1D3550', name='Cover rule')
    text(slide, 75, 412, 830, 24, b1, 18, 'E3ECF7', bold=True, pitch=1.2, name='Boundary')
    text(slide, 75, 440, 830, 48, b2.replace('\n', ' '), 18, 'B7C6D8', pitch=1.25, name='Boundary detail')


def build_divider(prs, slide, rep):
    texts = [T(s).strip() for s in slide.shapes if T(s).strip()]
    if len(texts) != 5 or '\u2192' not in texts[3]:
        raise Skip('divider structure not recognised')
    code, name, meta, flow, lock = texts
    nsize = S.fit_size([name], 750, 2 * 46 * 1.15, 46, 36, pitch=1.15, bold=True)
    if nsize is None:
        raise SplitRequired('module name')
    clear(slide); background(slide, S.NAVY)
    g = shape(slide, 0, 0, S.DESIGN_W, S.DESIGN_H, S.NAVY, name='Divider background'); gradient(g, S.NAVY, '10325A', 315)
    text(slide, 500, 130, 440, 390, code[1:], 300, S.blend(S.BLUE_BRIGHT, S.NAVY, 0.10), bold=True, font=S.FONT_D,
         align='r', anchor='b', pitch=1.0, wrap=False, name='Module watermark')
    text(slide, 52, 70, 350, 90, code, 75, S.BLUE_BRIGHT, bold=True, font=S.FONT_D, anchor='m', wrap=False, name='Module code')
    nh = len(S.wrap_lines(name, 750, nsize, True)) * nsize * 1.15
    text(slide, 52, 165, 750, nh + 4, name, nsize, 'FFFFFF', bold=True, font=S.FONT_D, pitch=1.15, name='Module name')
    y = 165 + nh + 26
    text(slide, 52, y, 750, 26, meta, 20, 'B7C6D8', name='Module meta')
    y += 54
    shape(slide, 52, y, 600, 1, '24476E', name='Divider rule')
    a, b = [p.strip() for p in flow.split('\u2192', 1)]
    w1 = pill(slide, 52, y + 20, a, 'F7C063', S.blend(S.PHASE['decide']['bar'], S.NAVY, 0.15), S.PHASE['decide']['bar'],
              size=16, h=30, radius=15, padx=11, spacing=1.0, name='Phase pill')
    text(slide, 52 + w1 + 4, y + 20, 26, 30, '\u2192', 16, '8FA3B8', bold=True, align='c', anchor='m', wrap=False, name='Arrow')
    pill(slide, 52 + w1 + 34, y + 20, b, '6FD3AE', S.blend(S.PHASE['reveal']['bar'], S.NAVY, 0.15), S.PHASE['reveal']['bar'],
         size=16, h=30, radius=15, padx=11, spacing=1.0, name='Phase pill')
    text(slide, 52, y + 66, 750, 22, lock, 16, '8FA3B8', name='Lock note')


def build_list(prs, slide, rep, kind):
    shapes = list(slide.shapes)
    texts = [s for s in shapes if T(s).strip()]
    eyebrow, title = T(texts[0]).strip(), T(texts[1]).strip()
    rows = rows_by_y(prs, slide, 2)
    items, note = [], None
    for r in rows:
        ts = [T(s).strip() for s in r]
        if kind == 'contract' and len(ts) == 3 and re.fullmatch(r'\d+', ts[0]):
            items.append(ts)
        elif kind == 'closure' and len(ts) == 2 and ts[0] == '\u2713':
            y = G(prs, r[0])['y']
            red = False
            for c in shapes:
                if not T(c).strip() and abs(G(prs, c)['y'] - y) < 8:
                    try:
                        red = red or str(c.fill.fore_color.rgb) == S.HARM_RED
                    except Exception:
                        pass
            items.append(ts + [red])
        elif len(ts) == 1 and r is rows[-1]:
            note = ts[0]
        else:
            raise Skip(f'unrecognised {kind} row: {ts}')
    n = len(items)
    if not n:
        raise Skip(f'no {kind} rows')
    top, bottom = 108, 500
    note_h = 0
    if note:
        nsize = S.fit_size([note], 860, 2 * 18 * 1.2, 18, 16, pitch=1.2, bold=True)
        if nsize is None:
            raise SplitRequired('note')
        note_h = len(S.wrap_lines(note, 860, nsize, True)) * nsize * 1.2 + 16
    step = min(84, (bottom - top - (note_h + 12 if note else 0)) / n)
    rh = step - 10
    tx = 330 if kind == 'contract' else 94
    tw = S.DESIGN_W - 32 - tx - 14
    tsize = S.fit_size([it[2] if kind == 'contract' else it[1] for it in items], tw, rh - 8, 24, 20, pitch=1.15)
    if tsize is None:
        raise SplitRequired(f'{kind} row text')
    clear(slide); background(slide, S.BG)
    text(slide, 32, 22, 600, 20, eyebrow, 16, S.BLUE, bold=True, anchor='m', spacing=1.5, wrap=False, name='Eyebrow')
    text(slide, 32, 48, 896, 46, title, 36, S.NAVY, bold=True, font=S.FONT_D, anchor='m', wrap=False, name='Title')
    cols = [S.BLUE_BRIGHT, S.PHASE['decide']['bar'], S.PHASE['reveal']['bar'], '6B7A8C']
    for i, it in enumerate(items):
        y = top + i * step
        shape(slide, 32, y, 896, rh, 'FFFFFF', S.CARD_BORDER, radius=6, name='Row card')
        if kind == 'contract':
            col = cols[i % len(cols)]
            shape(slide, 32, y, 5, rh, col, name='Row stripe')
            dd = min(36, rh - 14)
            text(slide, 54, y + (rh - dd) / 2, dd, dd, it[0], 18, 'FFFFFF', bold=True, align='c', anchor='m',
                 fill=col, radius=dd / 2, wrap=False, name='Row number')
            text(slide, 106, y, 216, rh, it[1], 20, S.NAVY, bold=True, anchor='m', spacing=0.5, wrap=False, name='Row label')
            text(slide, tx, y, tw, rh, it[2], tsize, S.INK, anchor='m', pitch=1.15, name='Row text')
        else:
            col = S.HARM_RED if it[2] else S.PHASE['reveal']['bar']
            dd = min(30, rh - 14)
            text(slide, 50, y + (rh - dd) / 2, dd, dd, '\u2713', 16, 'FFFFFF', bold=True, align='c', anchor='m',
                 fill=col, radius=dd / 2, wrap=False, name='Check')
            text(slide, tx, y, tw, rh, it[1], tsize, S.INK, anchor='m', pitch=1.15, name='Row text')
    if note:
        tone = (S.BLUE, S.BLUE_T, S.BLUE_BORDER) if kind == 'contract' else \
            (S.PHASE['reveal']['text'], S.PHASE['reveal']['tint'], S.PHASE['reveal']['border'])
        y = top + n * step + 2
        text(slide, 32, y, 896, note_h, note, nsize, tone[0], bold=True, anchor='m', pitch=1.2, fill=tone[1],
             line=tone[2], radius=6, inset=18, name='Note')
    rep.update(row_pt=tsize)


# ====================================================================== driver
def polish(src, dst, profile_name='projector_default', approved_by='', only=None, report_path=None):
    if profile_name not in S.PROFILES:
        raise SystemExit(f'unknown profile {profile_name!r}; choose from {sorted(S.PROFILES)}')
    profile = S.PROFILES[profile_name]
    if profile['requires_approval'] and not approved_by.strip():
        raise SystemExit(f'profile {profile_name!r} lowers body floors and needs --profile-approved-by '
                         '(record the approval in project_state.yaml release_policy.visual_polish)')
    prs = Presentation(src)
    S.set_canvas(prs)
    report = []
    for i, slide in enumerate(prs.slides):
        n = i + 1
        if only and n not in only:
            continue
        kind = classify(i, slide)
        r = dict(slide=n, kind=kind, status='POLISHED')
        try:
            if kind in ('decide', 'reveal'):
                build_case(prs, slide, parse_case(prs, slide), profile, r)
            elif kind == 'cover':
                build_cover(prs, slide, r)
            elif kind == 'divider':
                build_divider(prs, slide, r)
            elif kind in ('contract', 'closure'):
                build_list(prs, slide, r, kind)
            else:
                raise Skip('unknown slide role')
        except Skip as e:
            r.update(status='SKIPPED', reason=str(e))
        except SplitRequired as e:
            r.update(status='SPLIT_REQUIRED', reason=str(e))
        report.append(r)
    prs.save(dst)
    summary = {s: sum(1 for r in report if r['status'] == s) for s in ('POLISHED', 'SKIPPED', 'SPLIT_REQUIRED')}
    out = dict(gate='VISUAL_POLISH', source=str(src), output=str(dst), profile=profile_name,
               profile_approved_by=approved_by or None, metric_font=S.metric_font(False)[0],
               slides=len(prs.slides), summary=summary, slides_report=report, certifies_anything=False)
    if report_path:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--profile', default='projector_default', choices=sorted(S.PROFILES))
    ap.add_argument('--profile-approved-by', default='')
    ap.add_argument('--only', nargs='*', type=int, help='1-based slide numbers (sample run)')
    ap.add_argument('--report', default=None)
    a = ap.parse_args(argv)
    res = polish(a.src, a.dst, a.profile, a.profile_approved_by, set(a.only) if a.only else None, a.report)
    print(json.dumps(res['summary']))
    for r in res['slides_report']:
        if r['status'] != 'POLISHED':
            print(f"  slide {r['slide']:>3} {r['status']}: {r.get('reason', '')}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
