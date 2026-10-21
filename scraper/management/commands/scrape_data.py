import datetime

from django.core.management.base import BaseCommand

from scraper.tasks import get_matching_json_files, get_products_info, save_to_db


class Command(BaseCommand):
    help = "Extract product data from saved Prozis link files and store in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Date of the link files to process (YYYY-MM-DD). Defaults to today.",
        )
        parser.add_argument(
            "--query",
            type=str,
            default=None,
            help="Filter link files by search query (e.g. 'whey', 'creatine').",
        )

    def handle(self, *args, **options):
        date = None
        if options["date"]:
            date = datetime.datetime.strptime(options["date"], "%Y-%m-%d")

        json_files = get_matching_json_files(date=date, search_query=options["query"])

        if not json_files:
            self.stdout.write(self.style.WARNING(
                "No link files found. Add product URLs to the links/ folder first."
            ))
            return

        products = get_products_info(json_files)

        saved = 0
        for product_data in products:
            try:
                save_to_db(product_data)
                saved += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to save {product_data.get('name')}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Done — {saved}/{len(products)} products saved to DB."))
