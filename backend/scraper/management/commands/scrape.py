from django.core.management.base import BaseCommand, CommandError

from scraper.adapters import ADAPTERS
from scraper.models import ScrapeRun
from scraper.runner import run_store


class Command(BaseCommand):
    help = "Scrape stores and record price/nutrition changes. Without arguments, scrapes every store."

    def add_arguments(self, parser):
        parser.add_argument("stores", nargs="*", help=f"Store slugs ({', '.join(ADAPTERS)}). Default: all.")
        parser.add_argument("--limit", type=int, help="Only scrape the first N product pages per store.")
        parser.add_argument("--url", action="append", dest="urls", help="Scrape only this product URL (repeatable).")

    def handle(self, *args, stores, limit, urls, **options):
        unknown = set(stores) - set(ADAPTERS)
        if unknown:
            raise CommandError(f"Unknown store(s): {', '.join(sorted(unknown))}. Known: {', '.join(ADAPTERS)}")
        if urls and len(stores) != 1:
            raise CommandError("--url needs exactly one store, e.g. `scrape prozis --url https://...`")

        failed = []
        for slug in stores or ADAPTERS:
            run = run_store(ADAPTERS[slug](), urls=urls, limit=limit, log=self.stdout.write)
            if run.status == ScrapeRun.Status.FAILED:
                failed.append(slug)

        if failed:
            raise CommandError(f"Scrape failed for: {', '.join(failed)}")
