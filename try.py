from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json

# Function to initialize the webdriver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Function to extract product details
def extract_product_details(driver, url):
    driver.get(url)
    
    product_info = {}
    product_info['flavors'] = []
    product_info['prices'] = []

    # Extract the product name
    try:
        product_info['name'] = driver.find_element(By.TAG_NAME, 'h1').text
    except:
        product_info['name'] = None

    # Extract price and flavors from the script tag containing the product_option variable
    script_elements = driver.find_elements(By.TAG_NAME, 'script')
    for script in script_elements:
        if 'var product_option' in script.get_attribute('innerHTML'):
            script_content = script.get_attribute('innerHTML')
            json_text = script_content.split('var product_option =')[1].split(';')[0].strip()
            product_option = json.loads(json_text)
            
            for product in product_option['products']:
                flavor = product['flavorDescription']
                weight = product['optionDescription']
                price = product['price']
                nutritional_info_url = product['variantInfoData']['url']
                
                product_info['flavors'].append({'flavor': flavor, 'weight': weight})
                product_info['prices'].append({'flavor': flavor, 'weight': weight, 'price': price})
                
                # Navigate to the nutritional info page and extract data
                driver.get('https://www.prozis.com' + nutritional_info_url)
                nutritional_info = extract_nutritional_info(driver)
                product_info['flavors'][-1]['nutritional_info'] = nutritional_info
                
                driver.back()

    return product_info

# Function to extract nutritional information
def extract_nutritional_info(driver):
    nutritional_info = {}
    try:
        table = driver.find_element(By.CLASS_NAME, 'nutrition-facts')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, 'td')
            if len(columns) == 2:
                key = columns[0].text.strip()
                value = columns[1].text.strip()
                nutritional_info[key] = value
    except:
        nutritional_info = None
    return nutritional_info

# Main script
if __name__ == "__main__":
    url = 'https://www.prozis.com/pt/pt/prozis/100-whey-prime-1000-g'
    driver = init_driver()
    product_details = extract_product_details(driver, url)
    driver.quit()
    
    print(json.dumps(product_details, indent=2, ensure_ascii=False))
