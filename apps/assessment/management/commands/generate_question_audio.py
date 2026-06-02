from django.core.management.base import BaseCommand
from services.tts.manager import generate_all_question_audio


class Command(BaseCommand):
    help = 'Pre-generate TTS audio files for all 30 assessment questions (10 questions × 3 languages)'

    def handle(self, *args, **options):
        self.stdout.write('Generating question audio files...\n')
        results = generate_all_question_audio()

        ok = skipped = errors = 0
        for label, result in results.items():
            if result == 'ok':
                self.stdout.write(self.style.SUCCESS(f'  [OK] {label}'))
                ok += 1
            elif result.startswith('skipped'):
                self.stdout.write(f'  [--] {label} (skipped)')
                skipped += 1
            else:
                self.stdout.write(self.style.ERROR(f'  [FAIL] {label}: {result}'))
                errors += 1

        self.stdout.write(f'\nDone. Generated: {ok}  Skipped: {skipped}  Errors: {errors}')
