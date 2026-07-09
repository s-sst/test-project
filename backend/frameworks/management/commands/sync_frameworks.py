"""``python manage.py sync_frameworks`` — load control libraries into the DB.

Usage:
    python manage.py sync_frameworks                # sync changed frameworks
    python manage.py sync_frameworks --force        # re-sync all regardless of hash
    python manage.py sync_frameworks --dir path/to  # custom config directory
    python manage.py sync_frameworks --check         # validate only, no DB writes
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from common.exceptions import ConfigValidationError
from frameworks.config.loader import iter_config_paths, load_all
from frameworks.services import sync_all


class Command(BaseCommand):
    help = "Validate and synchronise governance framework control libraries into the database."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Re-sync even if config hash is unchanged.")
        parser.add_argument("--dir", dest="directory", default=None, help="Override the config directory.")
        parser.add_argument("--check", action="store_true", help="Validate configs only; make no DB changes.")

    def handle(self, *args, **options):
        directory = options["directory"]
        paths = iter_config_paths(directory)
        if not paths:
            self.stdout.write(self.style.WARNING("No framework config files found."))
            return

        self.stdout.write(f"Discovered {len(paths)} config file(s):")
        for p in paths:
            self.stdout.write(f"  · {p.name}")

        if options["check"]:
            try:
                loaded = list(load_all(directory))
            except ConfigValidationError as exc:
                raise CommandError(f"Configuration invalid: {exc.detail}") from exc
            self.stdout.write(self.style.SUCCESS(f"\nAll {len(loaded)} config(s) are valid."))
            for nf in loaded:
                self.stdout.write(
                    f"  · {nf.id}: {nf.control_count} controls, "
                    f"{nf.requirement_count} requirements, hash={nf.config_hash[:12]}…"
                )
            return

        try:
            results = sync_all(directory, force=options["force"])
        except ConfigValidationError as exc:
            raise CommandError(f"Configuration invalid: {exc.detail}") from exc

        self.stdout.write("\nSync results:")
        for r in results:
            style = self.style.SUCCESS if r.status != "unchanged" else self.style.NOTICE
            self.stdout.write(
                style(
                    f"  · {r.framework_id:16s} {r.status:10s} "
                    f"reqs+={r.requirements_upserted} reqs-={r.requirements_removed}"
                )
            )
        changed = sum(1 for r in results if r.status != "unchanged")
        self.stdout.write(
            self.style.SUCCESS(f"\nDone. {changed} changed, {len(results) - changed} unchanged.")
        )
