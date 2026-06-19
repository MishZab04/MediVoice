import logging
import os
from io import BytesIO

from django.conf import settings

from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

logger = logging.getLogger('services')

_LANGUAGE_DISPLAY = {
    'en':  'English',
    'fr':  'French',
    'pcm': 'Pidgin English',
}

# Known section headers in both English and French report formats
_SECTION_HEADERS = [
    'Patient Complaints',
    'Patient complaints',
    'Symptoms',
    'Symptoms collected',
    'Relevant Medical History and Risk Factors',
    'Relevant Medical History',
    'Medical History',
    'Medications and Allergies',
    'Medications',
    'Allergies',
    'Red Flags Detected',
    'Red flags detected',
    'Assessment Priority',
    'Antécédents médicaux',
    'Médicaments',
    'Allergies',
    'Drapeaux rouges détectés',
    'Priorité d\'évaluation',
    'Plaintes du patient',
    'Symptômes',
]


def _is_offline_format(text: str) -> bool:
    return 'RÉPONSES DU PATIENT' in text or 'PATIENT RESPONSES' in text or text.strip().startswith('Q:')


def _parse_offline_report(text: str) -> str:
    """Handle the Q&A offline questionnaire format."""
    lines = text.strip().splitlines()
    html = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('Q:'):
            html.append(f'<p class="qa-question"><span class="qa-q">Q:</span> {line[2:].strip()}</p>')
        elif line.startswith('A:'):
            html.append(f'<p class="qa-answer"><span class="qa-a">A:</span> {line[2:].strip()}</p>')
        elif line.isupper() or (line.endswith(':') and len(line) < 60):
            html.append(f'<div class="section-header">{line.rstrip(":")}</div>')
        elif line.startswith('NOTE:') or 'hors ligne' in line.lower() or 'offline' in line.lower():
            html.append(f'<p class="disclaimer">{line}</p>')
        elif line.startswith('(') and line.endswith(')'):
            html.append(f'<p class="disclaimer">{line}</p>')
        else:
            html.append(f'<p>{line}</p>')
    return '\n'.join(html)


def _parse_report_to_html(text: str) -> str:
    """
    Convert the AI-generated flat report text into structured HTML
    with sections, bullet points, and highlighted key terms.
    """
    lines = text.strip().splitlines()
    html = []
    in_list = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if in_list:
                html.append('</ul>')
                in_list = False
            continue

        # Bullet point line
        if line.startswith('- ') or line.startswith('* '):
            if not in_list:
                html.append('<ul class="report-list">')
                in_list = True
            content = line[2:].strip()
            # Sub-header within bullet: "Headache: description..."
            if ':' in content:
                key, _, val = content.partition(':')
                html.append(
                    f'<li><span class="bullet-key">{key.strip()}:</span>'
                    f'<span class="bullet-val">{val.strip()}</span></li>'
                )
            else:
                html.append(f'<li>{content}</li>')
            continue

        # Close list if open
        if in_list:
            html.append('</ul>')
            in_list = False

        # Detect section headers: lines ending with ":" or matching known headers
        is_header = False
        for header in _SECTION_HEADERS:
            if line.lower().startswith(header.lower() + ':') or line.lower() == header.lower() + ':':
                # Check if content follows on same line
                rest = line[len(header):].lstrip(':').strip()
                css_class = 'section-header'
                # Red flags get special styling
                if 'red flag' in header.lower() or 'drapeau' in header.lower():
                    css_class = 'section-header red-flag-header'
                html.append(f'<div class="{css_class}">{header}</div>')
                if rest:
                    # Highlight URGENT / NORMAL in priority section
                    if 'priority' in header.lower() or 'priorité' in header.lower():
                        rest = _highlight_priority(rest)
                    html.append(f'<p class="section-content">{rest}</p>')
                is_header = True
                break

        if is_header:
            continue

        # Disclaimer line
        if 'healthcare professional' in line.lower() or 'professionnel de santé' in line.lower():
            html.append(f'<p class="disclaimer">{line}</p>')
            continue

        # Lines with "Key: value" that aren't full section headers
        if ':' in line:
            key, _, val = line.partition(':')
            val = val.strip()
            if val and len(key) < 60:
                if 'red flag' in key.lower() or 'urgent' in val.upper():
                    html.append(
                        f'<p><span class="inline-key">{key}:</span> '
                        f'<span class="red-text">{val}</span></p>'
                    )
                elif 'priority' in key.lower() or 'priorité' in key.lower():
                    html.append(
                        f'<p><span class="inline-key">{key}:</span> {_highlight_priority(val)}</p>'
                    )
                else:
                    html.append(f'<p><span class="inline-key">{key}:</span> {val}</p>')
            else:
                html.append(f'<p>{line}</p>')
        else:
            html.append(f'<p>{line}</p>')

    if in_list:
        html.append('</ul>')

    return '\n'.join(html)


def _highlight_priority(text: str) -> str:
    text = text.replace('URGENT', '<span class="badge-urgent">URGENT</span>')
    text = text.replace('NORMAL', '<span class="badge-normal">NORMAL</span>')
    return text


def _logo_path() -> str:
    from django.conf import settings
    return os.path.join(settings.BASE_DIR, 'static', 'images', 'meditok_logo.png')


def _get_logo_base64() -> str:
    """Return base64 data URI for the logo (full opacity) for the header."""
    import base64
    path = _logo_path()
    if os.path.exists(path):
        with open(path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        return f'data:image/png;base64,{encoded}'
    return ''


def _get_watermark_base64() -> str:
    """
    Return base64 data URI of the logo icon only (cropped to top 52% to exclude
    the MediTok text and tagline) at ~9% opacity for use as a page watermark.
    """
    import base64
    import io
    from PIL import Image
    path = _logo_path()
    if not os.path.exists(path):
        return ''
    img = Image.open(path).convert('RGBA')
    # Keep only the top 42% of the image (icon only — excludes "MediTok" text and tagline)
    w, h = img.size
    img = img.crop((0, 0, w, int(h * 0.42)))
    # Reduce alpha to 10%
    r, g, b, a = img.split()
    a = a.point(lambda x: int(x * 0.10))
    img = Image.merge('RGBA', (r, g, b, a))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{encoded}'


def generate_assessment_pdf(session) -> bytes:
    patient = session.patient
    worker = session.health_worker
    now = timezone.localtime()

    context = {
        'session_id':         str(session.id)[:8].upper(),
        'patient_name':       patient.full_name,
        'patient_sex':        patient.sex.title(),
        'patient_dob':        patient.date_of_birth.strftime('%d %B %Y') if patient.date_of_birth else '—',
        'patient_location':   patient.location or '—',
        'patient_phone':      patient.phone_number or '—',
        'language_display':   _LANGUAGE_DISPLAY.get(session.language, session.language),
        'health_worker_name': worker.get_full_name(),
        'facility_name':      worker.facility_name or '—',
        'assessment_date':    session.completed_at.strftime('%d %B %Y, %H:%M') if session.completed_at else '—',
        'generated_at':       now.strftime('%d %B %Y'),
        'generated_time':     now.strftime('%H:%M:%S'),
        'priority':           session.assessment_priority,
        'report_html':        (
            _parse_offline_report(session.assessment_report)
            if _is_offline_format(session.assessment_report)
            else _parse_report_to_html(session.assessment_report)
        ),
        'logo_src':           _get_logo_base64(),
        'watermark_src':      _get_watermark_base64(),
    }

    html = render_to_string('reports/assessment_report.html', context)
    buffer = BytesIO()
    result = pisa.CreatePDF(html, dest=buffer, encoding='utf-8')

    if result.err:
        logger.error('PDF generation error for session %s: %s', session.id, result.err)
        raise RuntimeError(f'PDF generation failed with error code {result.err}')

    return buffer.getvalue()


def save_assessment_pdf(session, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"assessment_{session.id}.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf_bytes = generate_assessment_pdf(session)
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)
    logger.info('PDF saved: %s', filepath)
    return filepath
