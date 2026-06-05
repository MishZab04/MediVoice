import re

# Common patterns where Whisper mishears Pidgin words.
# Applied in order — more specific phrases first, single words last.
_CORRECTIONS = [
    # ── Phrase-level fixes first (most specific) ──────────────────────────────
    (r'\bmy\s+eye\s+is\s+torn\b',       'my eye dey turn'),
    (r'\bmy\s+eye\s+is\s+turning\b',    'my eye dey turn'),
    (r'\bhead\s+is\s+hot\b',            'head dey hot'),
    (r'\bbody\s+is\s+hot\b',            'body dey hot'),
    (r'\bbody\s+they\s+hurt\b',         'body dey pain'),
    (r'\bbody\s+they\s+pain\b',         'body dey pain'),
    (r"\bdon't\s+give\s+vomit\b",       'don dey vomit'),
    (r'\bwant\s+me\s+to\s+times\b',     'vomit two times'),
    (r'\bwant\s+me\s+to\b',             'vomit'),
    (r'\bwant\s+to\s+times\b',          'vomit two times'),
    (r'\bfollow\s+like\b',              'vomit'),
    (r'\bstomach\s+is\s+turning\b',     'belle dey turn'),
    (r'\bbelly\s+is\s+paining\b',       'belle dey pain'),
    (r'\bjudge\s+the\s+week\b',         'just dey weak'),
    (r'\bpleasure\s+don\b',             'pressure don'),
    (r'\bnot\s+defy\b',                 'no dey'),
    (r'\bknow\s+the\b',                 'no dey'),
    (r'\bnot\s+get\b',                  'no get'),
    (r'\bhat\s+for\s+swallow\b',        'hard for swallow'),
    (r'\bthis\s+this\b',                'these days'),
    (r'\bto\s+be\b',                    'today'),
    (r'\bthe\s+hot\b',                  'dey hot'),
    (r'\bthe\s+pain\b',                 'dey pain'),
    (r'\bthe\s+turn\b',                 'dey turn'),
    (r'\bthe\s+weak\b',                 'dey weak'),

    # ── Single word fixes ─────────────────────────────────────────────────────
    # "dey" — Whisper hears as "defy", "defuse", "depend", "they", "day"
    (r'\bdefy\b',        'dey'),
    (r'\bdefuse\b',      'dey'),
    (r'\bthey\b',        'dey'),
    (r'\bday\b',         'dey'),
    # "don" — Whisper hears as "don't", "done"
    (r"\bdon't\b",       'don'),
    (r'\bdone\b',        'don'),
    # "belle" (stomach) — Whisper hears as "belay", "bele"
    (r'\bbelay\b',       'belle'),
    (r'\bbele\b',        'belle'),
    # "waka" (walk) — Whisper hears as "walker"
    (r'\bwalker\b',      'waka'),
    # "plenty" — Whisper hears as "splainty"
    (r'\bsplainty\b',    'plenty'),
    (r'\bsplenty\b',     'plenty'),
    # "dokta" — Whisper hears as "doctor"
    (r'\bdoctor\b',      'dokta'),
    # "cough" — Whisper hears as "recove", "recover"
    (r'\brecove\b',      'cough'),
    (r'\brecover\b',     'cough'),
    # "throat" — Whisper hears as "showed", "throw"
    (r'\bshowed\b',      'throat'),
    (r'\bthrow\b',       'throat'),
    # "piss/urinate" — Whisper hears as "peace"
    (r'\bpeace\b',       'piss'),
    # "knee" — Whisper hears as "need"
    (r'\bneed\s+dey\b',  'knee dey'),
    # "swell" — Whisper hears as "sweat"
    (r'\bdon\s+sweat\b', 'don swell'),
    # "twist" — Whisper hears as "choose"
    (r'\bchoose\s+my\s+leg\b', 'twist my leg'),
    # "pressure" — Whisper hears as "pleasure"
    (r'\bpleasure\b',    'pressure'),
    # "high" (blood pressure) — Whisper hears as "hide"
    (r'\bhide\b',        'high'),
    # "chop" (food/eat) — Whisper hears as "choke"
    (r'\bchoke\b',       'chop'),
    # "rash" — Whisper hears as "rush"
    (r'\brush\b',        'rash'),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), r) for p, r in _CORRECTIONS]


def normalize(text: str) -> str:
    """Apply Pidgin normalization corrections to Whisper output."""
    for pattern, replacement in _COMPILED:
        text = pattern.sub(replacement, text)
    return text
