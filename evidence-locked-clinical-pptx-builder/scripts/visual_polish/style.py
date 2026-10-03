"""Design tokens, density profiles and measured text fitting for VISUAL_POLISH.

Units: every coordinate and font size in this package is in POINTS on a
960 x 540 pt design canvas (13.333 x 7.5 in). `set_canvas()` scales to the
real slide width, so 10 in wide 16:9 decks also work.

Font floors follow SKILL.md section 17 (body >= 24 pt, source/citation labels
>= 16 pt). The denser profile mirrors the observed DYS_2026 v1.5 design
reference (docs/dys_2026_v1_5_design_reference.md). It is a project-level
choice: it must be approved and recorded in project state, and it never lowers
the 16 pt source-label floor.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache

# ------------------------------------------------------------------ palette
NAVY = '0B1F33'      # deck base (kept from the builder)
INK = '17212B'       # body text
MUTED = '536273'     # chrome text (contrast >= 4.5:1 on BG)
BG = 'F5F7FA'
LINE = 'DDE5ED'
CARD_BORDER = 'D5DEE8'
BLUE = '175CD3'; BLUE_T = 'EAF2FF'; BLUE_BORDER = 'B9CFF5'; BLUE_BRIGHT = '2E90FA'
HARM_RED = 'B42318'

# Teaching-phase semantics. Colour is never the only cue: each phase also has
# an icon and its own eyebrow text (SKILL.md section 17, "no reliance on colour alone").
PHASE = {
    'decide': dict(bar='E39A12', text='8A5300', tint='FFF5E6', border='F3C77A', icon='?'),
    'reveal': dict(bar='1E9E73', text='0F6B4E', tint='EAF7F1', border='9FD8BF', icon='\u2713'),
}

# ACC/AHA Class of Recommendation colour convention: (text, fill, border).
# The class code text is always printed inside the pill.
COR = {
    '1':  ('0E6B4E', 'DDF3E8', '9FD8BF'),
    '2a': ('6B4B00', 'FFF3C4', 'F2D675'),
    '2b': ('8A3605', 'FFE6D2', 'F6B98A'),
    '3':  ('A11A12', 'FDE2DF', 'F3A9A2'),
}

FONT = 'Aptos'
FONT_D = 'Aptos Display'

# ------------------------------------------------------------------ profiles
PROFILES = {
    # Default: SKILL.md section 17 floors. Slides that cannot fit are NOT shrunk;
    # they are left as built and reported SPLIT_REQUIRED for upstream repair.
    'projector_default': dict(
        title_max=40, title_min=32,
        body_floor={1: 24, 2: 24, 3: 24},
        body_max={1: 32, 2: 28, 3: 26},
        label=16, source=16, requires_approval=False),
    # Observed DYS_2026 v1.5 density. Opt-in only, approval must be recorded.
    'dense_case_reveal': dict(
        title_max=40, title_min=30,
        body_floor={1: 24, 2: 20, 3: 18},
        body_max={1: 32, 2: 28, 3: 24},
        label=16, source=16, requires_approval=True),
}

BADGE_MIN = 14      # case-id / phase / COR-LOE pills (not citations; see protocol doc)
LINE_PITCH = 1.25      # body line pitch (exact spacing, renderer-independent)
TITLE_PITCH = 1.10
WIDTH_SAFETY = 1.03    # extra margin for PowerPoint vs. LibreOffice line breaking

# ------------------------------------------------------------------ canvas
DESIGN_W, DESIGN_H = 960.0, 540.0
_K = 1.0  # real-slide scale factor


def set_canvas(prs):
    global _K
    _K = prs.slide_width / (DESIGN_W * 12700)


def emu(v):
    return int(round(v * 12700 * _K))


def fpt(v):
    """Design font size (pt) -> real font size (pt)."""
    return v * _K


def blend(fg, bg, a):
    f = [int(fg[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(bg[i:i + 2], 16) for i in (0, 2, 4)]
    return ''.join(f'{round(f[i] * a + b[i] * (1 - a)):02X}' for i in range(3))


# ------------------------------------------------------------------ metrics
def _fc(name, bold):
    if not shutil.which('fc-match'):
        return None
    try:
        out = subprocess.run(['fc-match', '-f', '%{file}', f'{name}:{"bold" if bold else "regular"}'],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        return out or None
    except Exception:
        return None


def _candidates(bold):
    env = os.environ.get('POLISH_METRIC_FONT_BOLD' if bold else 'POLISH_METRIC_FONT')
    win = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts')
    names = (['Aptos-Bold.ttf', 'aptos-bold.ttf'] if bold else ['Aptos.ttf', 'aptos.ttf'])
    c = [(env, 1.0)] if env else []
    c += [(os.path.join(win, n), 1.0) for n in names]
    c += [(os.path.expanduser(f'~/Library/Fonts/{n}'), 1.0) for n in names]
    # What the renderer substitutes for Aptos (LibreOffice usually: Noto Sans)
    c.append((_fc('Aptos', bold), 1.0))
    c += [('/usr/share/fonts/truetype/noto/NotoSans-%s.ttf' % ('Bold' if bold else 'Regular'), 1.0),
          ('/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf' % ('Bold' if bold else 'Regular'), 1.06),
          (os.path.join(win, 'arialbd.ttf' if bold else 'arial.ttf'), 1.06),
          ('/Library/Fonts/Arial%s.ttf' % (' Bold' if bold else ''), 1.06),
          ('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''), 1.0)]
    return c


@lru_cache(maxsize=None)
def metric_font(bold):
    for path, fudge in _candidates(bold):
        if path and os.path.exists(path):
            return path, fudge
    return None, 1.0


@lru_cache(maxsize=None)
def _font(size10, bold):
    path, fudge = metric_font(bold)
    if path is None:
        return None, fudge
    from PIL import ImageFont
    return ImageFont.truetype(path, max(1, size10)), fudge


def text_width(s, size, bold=False):
    # measure at 10x resolution in points for sub-point accuracy
    f, fudge = _font(int(round(size * 10)), bold)
    if f is None:
        return len(s) * size * 0.58 * WIDTH_SAFETY
    return f.getlength(s) / 10.0 * fudge * WIDTH_SAFETY


def wrap_lines(text, width, size, bold=False):
    lines = []
    for para in text.replace('\v', '\n').split('\n'):
        cur = ''
        for word in para.split(' '):
            trial = f'{cur} {word}' if cur else word
            if not cur or text_width(trial, size, bold) <= width:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def text_height(text, width, size, pitch=LINE_PITCH, bold=False):
    return len(wrap_lines(text, width, size, bold)) * size * pitch


def longest_word_fits(text, width, size, bold=False):
    return all(text_width(w, size, bold) <= width for w in text.split())


def fit_size(texts, width, height, hi, lo, pitch=LINE_PITCH, bold=False, step=1):
    """Largest size in [lo, hi] at which EVERY text fits (uniform type).
    Returns None when even `lo` does not fit -> caller must not shrink."""
    s = hi
    while s >= lo - 1e-6:
        if all(text_height(t, width, s, pitch, bold) <= height and longest_word_fits(t, width, s, bold)
               for t in texts):
            return s
        s -= step
    return None
