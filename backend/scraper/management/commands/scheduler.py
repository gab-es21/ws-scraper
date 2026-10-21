import time
from zoneinfo import ZoneInfo

from decouple import config
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from scraper.models import ScrapeRun
from scraper.scheduling import is_overdue, next_run_at, parse_time


class Command(BaseCommand):
    help = (
        "Run `scrape` every day at SCRAPE_AT (default 04:00) in SCRAPE_TIMEZONE (default Europe/Lisbon). "
        "Also runs right away when the last successful scrape is more than a day old."
    )

    def add_arguments(self, parser):
        parser.add_argument("--at", default=config("SCRAPE_AT", default="04:00"), help="HH:MM, local time")
        parser.add_argument("--timezone", dest="tz_name", default=config("SCRAPE_TIMEZONE", default="Europe/Lisbon"))

    def handle(self, *args, at, tz_name, **options):
        at_time, tz = parse_time(at), ZoneInfo(tz_name)
        self.stdout.write(f"Scheduler: scraping every day at {at_time:%H:%M} {tz_name}")

        if is_overdue(self.last_success(), timezone.now()):
            self.stdout.write("Last successful scrape is more than a day old: scraping now")
            self.scrape()

        while True:
            next_run = next_run_at(timezone.now(), at_time, tz)
            self.stdout.write(f"Next scrape at {next_run:%Y-%m-%d %H:%M %Z}")
            while (remaining := (next_run - timezone.now()).total_seconds()) > 0:
                time.sleep(min(remaining, 600))
            self.scrape()

    def scrape(self):
        try:
            call_command("scrape", stdout=self.stdout, stderr=self.stderr)
        except Exception as error:  # keep the scheduler alive; the ScrapeRun rows hold the details
            self.stderr.write(f"Scrape failed: {error}")

    @staticmethod
    def last_success():
        finished = ScrapeRun.Status.SUCCESS, ScrapeRun.Status.PARTIAL
        return ScrapeRun.objects.filter(status__in=finished).aggregate(last=Max("started_at"))["last"]
