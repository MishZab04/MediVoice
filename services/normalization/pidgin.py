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

    # ── Additional phrase-level fixes ────────────────────────────────────────
    (r'\bmy\s+back\s+is\s+paining\s+me\b',         'back dey pain me'),
    (r'\bmy\s+waist\s+is\s+paining\s+me\b',        'waist dey pain me'),
    (r'\bmy\s+leg\s+is\s+paining\s+me\b',          'leg dey pain me'),
    (r'\bmy\s+knee\s+is\s+paining\s+me\b',         'knee dey pain me'),
    (r'\bmy\s+eyes\s+are\s+paining\s+me\b',        'eyes dey pain me'),
    (r'\bmy\s+ear\s+is\s+paining\s+me\b',          'ear dey pain me'),
    (r'\bmy\s+teeth\s+are\s+paining\s+me\b',       'teeth dey pain me'),
    (r'\bmy\s+joint\s+is\s+paining\s+me\b',        'joint dey pain me'),
    (r'\bmy\s+skin\s+is\s+itching\b',              'skin dey scratch me'),
    (r'\bmy\s+body\s+is\s+swelling\b',             'body dey swell'),
    (r'\bmy\s+leg\s+is\s+swelling\b',              'leg dey swell'),
    (r'\bmy\s+face\s+is\s+swelling\b',             'face dey swell'),
    (r'\bi\s+am\s+feeling\s+dizzy\b',              'i dey dizzy'),
    (r'\bi\s+am\s+feeling\s+cold\b',               'i dey cold'),
    (r'\bi\s+am\s+feeling\s+tired\b',              'i dey tire'),
    (r'\bi\s+am\s+feeling\s+nauseous\b',           'i wan vomit'),
    (r'\bi\s+feel\s+like\s+vomiting\b',            'i wan vomit'),
    (r'\bi\s+want\s+to\s+vomit\b',                 'i wan vomit'),
    (r'\bi\s+cannot\s+walk\b',                     'i no fit waka'),
    (r'\bi\s+can\'t\s+walk\b',                     'i no fit waka'),
    (r'\bi\s+cannot\s+stand\b',                    'i no fit stand'),
    (r'\bi\s+can\'t\s+stand\b',                    'i no fit stand'),
    (r'\bi\s+cannot\s+see\s+well\b',               'i no fit see well'),
    (r'\bi\s+can\'t\s+see\s+well\b',               'i no fit see well'),
    (r'\bi\s+have\s+a\s+fever\b',                  'i get fever'),
    (r'\bi\s+have\s+a\s+cough\b',                  'i get cough'),
    (r'\bi\s+have\s+a\s+headache\b',               'head dey pain me'),
    (r'\bi\s+have\s+a\s+rash\b',                   'rash don come out'),
    (r'\bi\s+have\s+been\s+coughing\b',            'i don dey cough'),
    (r'\bi\s+have\s+been\s+sneezing\b',            'i don dey sneeze'),
    (r'\bi\s+have\s+been\s+running\s+a\s+fever\b', 'fever don dey hold me'),
    (r'\bfever\s+is\s+holding\s+me\b',             'fever dey hold me'),
    (r'\bi\s+have\s+not\s+eaten\b',                'i never chop'),
    (r'\bi\s+have\s+not\s+slept\b',                'i never sleep'),
    (r'\bi\s+passed\s+out\b',                      'i fall down'),
    (r'\bi\s+fainted\b',                           'i fall down'),
    (r'\bmy\s+heart\s+is\s+beating\s+fast\b',      'heart dey beat fast'),
    (r'\bmy\s+heart\s+is\s+racing\b',              'heart dey run fast'),
    (r'\bi\s+am\s+sweating\s+a\s+lot\b',           'i dey sweat plenty'),
    (r'\bi\s+am\s+sweating\b',                     'i dey sweat'),
    (r'\bmy\s+urine\s+is\s+yellow\b',              'piss yellow'),
    (r'\bmy\s+urine\s+is\s+dark\b',                'piss dark'),
    (r'\bmy\s+stool\s+has\s+blood\b',              'blood dey my stool'),
    (r'\bblood\s+in\s+my\s+stool\b',               'blood dey my stool'),
    (r'\bblood\s+in\s+my\s+urine\b',               'blood dey my piss'),
    (r'\bi\s+am\s+not\s+getting\s+better\b',       'i no dey get better'),
    (r'\bi\s+have\s+been\s+sick\s+for\b',          'i don sick since'),
    (r'\bthe\s+pain\s+is\s+worse\b',               'pain don increase'),
    (r'\bthe\s+pain\s+is\s+very\s+bad\b',          'pain bad well well'),
    (r'\bit\s+is\s+painful\b',                     'e dey pain'),

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

    # ── Additional word-level fixes ──────────────────────────────────────────

    # waka (walk)
    (r'\bwalking\b',      'waka'),
    (r'\bwalk\b',         'waka'),

    # plenty / small
    (r'\ba\s+lot\b',      'plenty'),
    (r'\ba\s+little\b',   'small small'),

    # tire / tired
    (r'\btired\b',        'tire'),
    (r'\bfatigued\b',     'tire'),
    (r'\bexhausted\b',    'tire well well'),

    # scratch / itch
    (r'\bitching\b',      'dey scratch'),
    (r'\bitch\b',         'scratch'),

    # sweat
    (r'\bperspiring\b',   'dey sweat'),
    (r'\bperspiration\b', 'sweat'),

    # rash
    (r'\bhives\b',        'rash'),
    (r'\beczema\b',       'rash'),

    # vomit
    (r'\bnausea\b',       'wan vomit'),
    (r'\bnauseous\b',     'wan vomit'),

    # faint
    (r'\bfainted\b',      'fall down'),
    (r'\bunconcious\b',   'fall down'),
    (r'\bunconscious\b',  'fall down'),

    # blood
    (r'\bbloody\b',       'blood'),
    (r'\bbleeding\b',     'dey bleed'),

    # piss (urination)
    (r'\burine\b',        'piss'),
    (r'\burinates\b',     'piss'),

    # stool
    (r'\bfeces\b',        'stool'),
    (r'\bfaeces\b',       'stool'),
    (r'\bpoo\b',          'stool'),
    (r'\bpoop\b',         'stool'),

    # injection / drip
    (r'\bintravenous\b',  'drip'),
    (r'\biv\b',           'drip'),

    # malaria
    (r'\bmalarious\b',    'malaria'),
    (r'\bmalerian\b',     'malaria'),

    # wound / cut
    (r'\blaceration\b',   'cut'),

    # swallow
    (r'\bswallowing\b',   'swallow'),
    (r'\bdeglutition\b',  'swallow'),

    # body
    (r'\bbodily\b',       'body'),

    # fast / quick
    (r'\brapidly\b',      'fast fast'),
    (r'\bquickly\b',      'fast fast'),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), r) for p, r in _CORRECTIONS]


def normalize(text: str) -> str:
    """Apply Pidgin normalization corrections to Whisper output."""
    for pattern, replacement in _COMPILED:
        text = pattern.sub(replacement, text)
    return text
