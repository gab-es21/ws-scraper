# WorkoutSavings Sraper

## Table of Contents

- [WorkoutSavings Frontend](#workoutsavings-frontend)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Data to be Displayed](#data-to-be-displayed)
    - [Protein Powder Information](#protein-powder-information)
    - [Brand](#brand)
    - [Product Name](#product-name)
    - [Quantity](#quantity)
    - [Price](#price)
    - [Nutritional Table](#nutritional-table)
    - [Coupons](#coupons)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Environment Variables (.env file)](#environment-variables-env-file)
  - [Running the Project](#running-the-project)
  - [Running the Scraper](#running-the-scraper)
  - [Additional Notes](#additional-notes)
- [Workout Savings Data Management](#workout-savings-data-management)
  - [Project Structure](#project-structure)
    - [Firestore Collections and Documents](#firestore-collections-and-documents)
  - [Management Scripts](#management-scripts)
    - [Brands Management](#brands-management)
      - [Functions](#functions)
    - [Categories Management](#categories-management)
      - [Functions](#functions-1)
    - [Products Management](#products-management)
      - [Functions](#functions-2)
    - [Coupons Management](#coupons-management)
      - [Functions](#functions-3)
    - [Links Management](#links-management)
      - [Functions](#functions-4)
  - [Usage](#usage)

## Introduction

The frontend of the Workout Savings project aims to visualize and provide insights into the data collected from protein powder products, including prices, nutritional values, and more. This README.md provides an overview of how to work with the frontend and its key features.

## Data to be Displayed

### Protein Powder Information
- **Brand**
- **Product Name**
- **Flavour**
- **Quantity (g)**
- **Prices (€):**
  - Normal Price (€)
  - Price w/ Promo Code (€)
  - Price w/o Promo /100g of Product (€)
  - Price w/ Promo /100g of Product (€)
  - Price w/o Promo /100g of Protein (€)
  - Price w/ Promo /100g of Protein (€)
- **Nutritional Value (100g):**
  - Carbs (%)
  - Fat (%)
  - Protein (%)
- **Coupons:**
  - Coupon Codes
  - Coupon Discounts
- **Notes:**
  - w/ - with
  - w/o - without
  - /100g - per 100g

### Brand
- Prozis
- My Protein
- Zumub
- Gold Nutrition
- Decathlon
- More brands to be added in future versions

### Product Name
- Display the product name along with an image and a link to the seller's website.

### Quantity
- Compare quantities, with a focus on 1000g. If not available, show the predefined option available on the site.

### Price
- Display prices with and without promotional codes applied.
- Account for slight weight variations by showing the price for 100g of the product.
- Consider different compositions of protein powder by showing the price for 100g of protein in each product.

### Nutritional Table
- Present a nutritional table for each product, including Carbs, Fat, and Protein.
- Future versions may include additional optional information.

### Coupons
- If the seller provides promotional codes, recalculate and provide prices for each product with all known promotional codes.
- Allow users to contribute new promotional codes to benefit others.

## Requirements

To run this project, you'll need the following:

- Python 3.10
- Poetry
- Google Chrome and chromedriver

## Installation

Follow these steps to set up the project:

1. Clone this repository:
    ```sh
    git clone <repository_url>
    cd workoutsavings
    ```

2. Install project dependencies using Poetry:
    ```sh
    poetry install
    ```

3. Activate the virtual environment:
    ```sh
    poetry shell
    ```

## Environment Variables (.env file)

Create a `.env` file in the project root and set the following variables:

```dotenv
DJANGO_SECRET_KEY=dummy
ALLOWED_HOSTS=127.0.0.1,localhost
DEBUG=True
FIREBASE_CREDENTIALS_PATH=path/to/your/firebase/credentials.json
```

## Running the Project

1. Apply existing migrations:
    ```sh
    python manage.py migrate
    ```

2. Create a superuser:
    ```sh
    python manage.py createsuperuser
    ```

3. Start the development server:
    ```sh
    python manage.py runserver
    ```

4. Access the server at `http://127.0.0.1:8000/`.

## Running the Scraper

To run the scraper and start getting data:

1. Activate your virtual environment if not already active:
    ```sh
    poetry shell
    ```

2. Run the management command to start the scraping process:
    ```sh
    python manage.py scrape_data
    ```

This command will start the scraping process, extract the necessary data, and store it in Firestore.

## Additional Notes

- Ensure that you have Google Chrome and chromedriver installed and correctly set up in your PATH.
- The `scrape_data` command will scrape data based on the predefined search queries and store the data in Firestore as per the structure defined in the `tasks.py` file.
- You can customize the scraping logic and the data storage format as needed.

# Workout Savings Data Management

This project is designed to manage product data, prices, and historical price data using Firestore. It includes management scripts for brands, categories, products, coupons, and links.

## Project Structure

### Firestore Collections and Documents

1. **brands** (collection):
   - **{brand_name}** (document):
     - `name`: Brand name.
     - `website`: Brand website URL.
     - `product_links` (subcollection):
       - **{hashed_product_url}** (document):
         - `link`: URL of the product.
         - `last_updated`: Timestamp of the last update.
         - `category`: Product category.
     - `search_links` (subcollection):
       - **{hashed_search_url}** (document):
         - `link`: URL of the search link.
         - `last_updated`: Timestamp of the last update.
         - `category`: Product category.

2. **categories** (collection):
   - **{category_name}** (document):
     - `name`: Category name.

3. **coupons** (collection):
   - **{coupon_code}** (document):
     - `brand`: Reference to the brand.
     - `discount`: Discount value.
     - `is_percentage`: Boolean indicating if the discount is a percentage.
     - `is_active`: Boolean indicating if the coupon is active.

4. **products** (collection):
   - **{brand_category_name_weight}** (document):
     - `brand`: Reference to the brand.
     - `category`: Reference to the category.
     - `name`: Product name.
     - `image_url`: URL of the product image.
     - `product_url`: URL of the product.
     - `weight`: Weight of the product in grams.
     - `carbs_percentage`: Carbohydrates percentage.
     - `fat_percentage`: Fat percentage.
     - `protein_percentage`: Protein percentage.
     - `is_available`: Boolean indicating if the product is available.
     - `latest_price` (subcollection):
       - **latest** (document):
         - `price`: Latest price of the product.
         - `last_updated`: Timestamp of the last update.
     - `price_history` (subcollection):
       - **{auto-generated_id}** (document):
         - `price`: Historical price of the product.
         - `date`: Date of the historical price.

## Management Scripts

### Brands Management

Manages the brands in the Firestore database.

#### Functions

- `add_or_update_brand(name, website)`: Adds or updates a brand with the given name and website.
- `delete_brand(name)`: Deletes the brand with the given name.

### Categories Management

Manages the categories in the Firestore database.

#### Functions

- `add_category(name)`: Adds a category with the given name.

### Products Management

Manages the products in the Firestore database.

#### Functions

- `add_or_update_product(brand_name, category_name, product_name, image_url, product_url, weight, carbs_percentage, fat_percentage, protein_percentage, price, date=None)`: Adds or updates a product with the given details. If the product already exists, it updates the price and adds an entry to the price history if the date is not already in the history.
- `delete_product(brand_name, product_name)`: Deletes the product with the given brand and product name.

### Coupons Management

Manages the coupons in the Firestore database.

#### Functions

- `add_or_update_coupon(brand_name, code, discount, is_percentage, is_active)`: Adds or updates a coupon with the given details.
- `delete_coupon(code)`: Deletes the coupon with the given code.

### Links Management

Manages the links in the Firestore database.

#### Functions

- `add_or_update_search_link(brand_name, link, category=None)`: Adds or updates a search link for the given brand. Optionally associates it with a category.
- `add_or_update_product_link(brand_name, link, category=None)`: Adds or updates a product link for the given brand. Optionally associates it with a category.
- `list_links(brand_name, link_type='search_links')`: Lists all links of the specified type (search_links or product_links) for the given brand.
- `delete_link(brand_name, link, link_type='search_links')`: Deletes the specified link of the specified type for the given brand.

## Usage

Run each management script as needed to manage the respective collections and documents in your Firestore database.
