QUESTION_ORDER = [
    'fever',
    'vomiting',
    'duration',
    'body_weakness',
    'headache',
    'dizziness',
    'stomach_pain',
    'pain_description',
    'body_pain',
    'appetite',
]

QUESTIONS = {
    'en': {
        'fever':            'Do you have fever?',
        'vomiting':         'Are you vomiting?',
        'duration':         'How long have you been feeling this way?',
        'body_weakness':    'Do you feel body weakness?',
        'headache':         'Do you have headache?',
        'dizziness':        'Do you feel dizzy?',
        'stomach_pain':     'Do you have stomach pain?',
        'pain_description': 'Can you describe the pain?',
        'body_pain':        'Do you have body pain?',
        'appetite':         'Do you have appetite?',
    },
    'fr': {
        'fever':            'Avez-vous de la fièvre ?',
        'vomiting':         'Avez-vous des vomissements ?',
        'duration':         'Depuis combien de temps ressentez-vous ces symptômes ?',
        'body_weakness':    'Ressentez-vous une faiblesse générale ?',
        'headache':         'Avez-vous mal à la tête ?',
        'dizziness':        'Avez-vous des vertiges ?',
        'stomach_pain':     'Avez-vous mal au ventre ?',
        'pain_description': 'Pouvez-vous décrire la douleur ?',
        'body_pain':        'Ressentez-vous des douleurs corporelles ?',
        'appetite':         "Avez-vous de l'appétit ?",
    },
    'pcm': {
        'fever':            'Ya body dey hot?',
        'vomiting':         'You dey vomit?',
        'duration':         'Na how long this thing don start?',
        'body_weakness':    'You dey feel weak?',
        'headache':         'You get headache?',
        'dizziness':        'Head dey turn you?',
        'stomach_pain':     'Belle dey pain you?',
        'pain_description': 'Fit describe the pain?',
        'body_pain':        'All ya body dey pain?',
        'appetite':         'You get appetite for chop?',
    },
}

CONFIRMATION_MESSAGES = {
    'en':  'Thank you. Your response has been recorded.',
    'fr':  'Merci. Votre réponse a été enregistrée.',
    'pcm': 'Tank yu. We don record your answer.',
}


def get_question_text(key: str, language: str) -> str:
    return QUESTIONS[language][key]


def get_confirmation(language: str) -> str:
    return CONFIRMATION_MESSAGES[language]
