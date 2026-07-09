"""``python manage.py run_assessment <assessment_id>`` — run the pipeline."""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from assessments.models import Assessment
from assessments.pipeline import run_assessment


class Command(BaseCommand):
    help = "Run the ingest→index→assess→score→recommend pipeline for an assessment."

    def add_arguments(self, parser):
        parser.add_argument("assessment_id")

    def handle(self, *args, **options):
        try:
            assessment = Assessment.objects.get(pk=options["assessment_id"])
        except Assessment.DoesNotExist as exc:
            raise CommandError(f"Assessment {options['assessment_id']} not found.") from exc

        run_assessment(assessment)
        assessment.refresh_from_db()
        self.stdout.write(
            self.style.SUCCESS(
                f"{assessment.id}: {assessment.status} "
                f"score={assessment.overall_score} risk={assessment.risk_level} "
                f"recommendations={assessment.recommendations.count()}"
            )
        )
