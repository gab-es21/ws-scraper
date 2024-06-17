# scraper/tasks.py
import datetime
import json
import random
import time
import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import chromedriver_autoinstaller
import firebase_admin
from firebase_admin import firestore

chromedriver_autoinstaller.install()

# Initialize Firebase
#cred = firebase_admin.credentials.Certificate('./cred/serviceAccount.json')
#firebase_admin.initialize_app(cred)
db = firestore.client()

class NutritionalInfo:
    def __init__(self, protein_per_100g, fat_per_100g, carbs_per_100g):
        self.protein_per_100g = protein_per_100g
        self.fat_per_100g = fat_per_100g
        self.carbs_per_100g = carbs_per_100g

    def to_dict(self):
        return {
            "protein_per_100g": self.protein_per_100g,
            "fat_per_100g": self.fat_per_100g,
            "carbs_per_100g": self.carbs_per_100g
        }

class Flavor:
    def __init__(self, name, price, nutritional_info):
        self.name = name
        self.price = price
        self.nutritional_info = nutritional_info

    def to_dict(self):
        return {
            "name": self.name,
            "price": self.price,
            "nutritional_info": self.nutritional_info.to_dict() if self.nutritional_info else None
        }

class Product:
    def __init__(self, title, url, flavors=None):
        self.title = title
        self.unique_id = url.split('/')[-1]
        self.url = url
        self.flavors = flavors or []

    def add_flavor_and_price(self, flavor):
        self.flavors.append(flavor)

    def to_dict(self):
        return {
            "title": self.title,
            "unique_id": self.unique_id,
            "url": self.url,
            "flavors": [flavor.to_dict() for flavor in self.flavors]
        }

def random_sleep():
    time.sleep(random.uniform(0.5, 1.5))

def accept_cookies(driver):
    try:
        cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll'))
        )
        random_sleep()
        cookies_button.click()
    except NoSuchElementException:
        pass
    except Exception as e:
        print("Cookies Error:", str(e))

def perform_search(driver, search_query):
    random_sleep()
    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'quick-search_query'))
        )
        search_input.clear()
        search_input.send_keys(search_query)
        search_input.send_keys(Keys.RETURN)
    except Exception as e:
        print("Search Error:", str(e))

def extract_item_links(driver):
    random_sleep()
    links = []
    try:
        items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.col.list-item'))
        )
        for item in items:
            link_element = item.find_element(By.TAG_NAME, 'a')
            href = link_element.get_attribute('href')
            links.append(href+"?label=TlVUMDAvMTQxNzY1MDE2Mg%3D%3D")
    except Exception as e:
        print("Links Error:", str(e))
    return links

def write_links_to_json(links, search_query, language):
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    file_name = f'links/prozis_{search_query}_{language}_links_{date_string}.json'
    try:
        with open(file_name, 'w') as json_file:
            json.dump(links, json_file, indent=4)
    except Exception as e:
        print("Error writing links to JSON:", str(e))

def scrape_links_prozis(search_queries, url, languages=['pt']):
    for search_query in search_queries:
        for language in languages:
            try:
                driver = webdriver.Chrome()
                driver.get(url)
                accept_cookies(driver)
                perform_search(driver, search_query)
                item_links = extract_item_links(driver)
                write_links_to_json(item_links, search_query, language)
                driver.quit()
            except Exception as e:
                print("An error occurred:", e)

def get_matching_json_files(date=None, search_query=None):
    print("\n[EXTRACTING INFO FROM FILES]\n")
    if date is None:
        now = datetime.datetime.now()
        date_string = now.strftime("%Y-%m-%d")
    else:
        date_string = date.strftime("%Y-%m-%d")

    json_files = [file for file in os.listdir('links') if file.startswith(f'prozis') and file.endswith(f'{date_string}.json')]

    if search_query:
        json_files = [file for file in json_files if search_query in file]

    if not json_files:
        print(f"\tNo matching JSON files found for {date_string}.")
    else:
        if search_query:
            print(f"\tMatching JSON files for {search_query} on {date_string}:")
        else:
            print(f"\tMatching JSON files for {date_string}:")
        for file in json_files:
            print("\t",file)

    return json_files

def get_products_info(json_files):
    products = []
    success_count = 0
    failure_count = 0
    failed_links = []

    print('\n','*'*60)
    print("\tSTARTING PRODUCTS INFO EXTRACTION")
    print('*'*60)

    for json_file in json_files:
        full_path = os.path.join('links', json_file)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue

        try:
            with open(full_path, 'r') as file:
                links = json.load(file)

            for link in links:
                try:
                    driver = webdriver.Chrome()
                    driver.get(link)
                    print(f"\n[OPENING LINK]\n\t{link}")

                    # Accept Cookies
                    accept_cookies(driver)

                    # Get title
                    title = extract_product_title(driver)

                    # Create a Product object
                    product = Product(title, link)
                    #print(product)

                    product = extract_flavors(driver, product)

                    # Capture the screenshot
                    #capture_and_display_screenshot(driver)

                    driver.quit()

                    # Append the product to the products list
                    if product:
                        product.list_flavors()
                        products.append(product)
                        success_count += 1
                    else:
                        failure_count += 1
                        failed_links.append(link)
                except Exception as e:
                    print(f"An error occurred while processing link: {link}")
                    print("ERROR:", str(e))
                finally:
                  print('*'*60)
        except Exception as e:
            print(f"An error occurred while processing JSON file: {json_file}")
            print("ERROR:", str(e))

        print("\tSUMMARY")
        print('*' * 60)
        print(f"Processed {len(json_files)} files.")
        print(f"Total successful extractions: {success_count}")
        print(f"Total failed extractions: {failure_count}")
        if failed_links:
            print("Failed links:")
            for link in failed_links:
                print("\t", link)
        print('*' * 60)

    return products

def store_product_data(product):
    product_ref = db.collection('products').document(product.unique_id)
    product_data = product.to_dict()
    product_ref.set(product_data, merge=True)

    for flavor in product.flavors:
        flavor_ref = product_ref.collection('flavors').document(flavor.name)
        flavor_data = flavor.to_dict()
        flavor_ref.set(flavor_data, merge=True)

        history_ref = flavor_ref.collection('history').document()
        history_data = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'price': flavor.price,
            'nutritionalInfo': flavor.nutritional_info.to_dict() if flavor.nutritional_info else None
        }
        history_ref.set(history_data)

def extract_product_title(driver):
    try:
        wait = WebDriverWait(driver, 10)
        product_title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.col-10.px-0.product-name.mb-2.mt-0')))
        product_title = product_title_element.text.strip()
        return product_title
    except NoSuchElementException:
        return None
    except Exception as e:
        print("An error occurred while extracting product title:")
        print("ERROR:", str(e))
        return None

def extract_product_price(driver):
    try:
        wait = WebDriverWait(driver, 10)
        price_element = wait.until(EC.presence_of_element_located((By.ID, 'ob-product-price')))
        price_text = price_element.text.strip()
        currency_symbol = price_text[0]
        price_value = float(price_text[1:].replace(',', '').strip())
        return currency_symbol, price_value
    except Exception as e:
        print("Error extracting product price")
        print("ERROR:", str(e))
        return None, None

def extract_flavors(driver, product):
    try:
        carousel = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'carouselPicker'))
        )
        flavor_elements = carousel.find_elements(By.CLASS_NAME, 'row.snap-slider-item')
        num_elements = len(flavor_elements)

        for i in range(num_elements):
            try:
                driver.execute_script("arguments[0].scrollIntoView();", flavor_elements[i])
                flavor_name = flavor_elements[i].find_element(By.CLASS_NAME, 'row.mx-0.item-description').text
                flavor_elements[i].click()
                _, price = extract_product_price(driver)
                nutritional_info = extract_product_nutritional_table(driver)
                flavor = Flavor(flavor_name, price, nutritional_info)
                product.add_flavor_and_price(flavor)
            except StaleElementReferenceException:
                print("Stale element reference encountered. Retrying...")
    except Exception as e:
        print("Flavors Extraction Error")
        print("ERROR:", str(e))
        return None
    return product

def extract_product_nutritional_table(driver):
    try:
        wait = WebDriverWait(driver, 10)
        table_tab_element = wait.until(EC.presence_of_element_located((By.ID, 'tab_NUTRITION_TABLE')))
        driver.execute_script("arguments[0].scrollIntoView();", table_tab_element)
        table_tab_element.click()
        random_sleep()
        nut_facts_tabs = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'nut-facts-tabs'))
        )
        button_inside_nut_facts_tabs = nut_facts_tabs.find_element(By.CLASS_NAME, 'sel')
        random_sleep()
        button_inside_nut_facts_tabs.click()
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'nut-tbl-values'))
        )
        rows = table.find_elements(By.TAG_NAME, 'tr')
        protein_per_100g = 0
        fat_per_100g = 0
        carbs_per_100g = 0
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) > 1:
                nutrient = cells[0].text.strip().lower()
                value = cells[1].text.strip().lower()
                if 'protein' in nutrient:
                    protein_per_100g = float(value.split()[0].replace(',', '.'))
                elif 'fat' in nutrient:
                    fat_per_100g = float(value.split()[0].replace(',', '.'))
                elif 'carb' in nutrient:
                    carbs_per_100g = float(value.split()[0].replace(',', '.'))
        return NutritionalInfo(protein_per_100g, fat_per_100g, carbs_per_100g)
    except Exception as e:
        print("Error extracting product nutritional table")
        print("ERROR:", str(e))
        return None
