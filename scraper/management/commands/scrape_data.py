# scraper/management/commands/scrape_data.py
from django.core.management.base import BaseCommand
from scraper.tasks import scrape_links_prozis, store_product_data, get_matching_json_files, get_products_info

class Command(BaseCommand):
    help = 'Scrapes data from the specified website and stores it in Firestore'

    def handle(self, *args, **kwargs):
        search_queries = ['caseina', 'whey', 'vegan_protein', 'creatine']
        url = 'https://www.prozis.com/pt/pt/'
        languages = ['pt']

        # Step 1: Scrape Links
        scrape_links_prozis(search_queries, url, languages)

        # Step 2: Extract Product Info and Store in Firestore
        # Assuming you have a function `get_matching_json_files` to get the JSON files and `get_products_info` to parse the JSON files
        json_files = get_matching_json_files()
        products = get_products_info(json_files)

        for product in products:
            store_product_data(product)

        self.stdout.write(self.style.SUCCESS('Successfully scraped data and stored in Firestore'))
