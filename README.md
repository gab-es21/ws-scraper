# WorkoutSavings Sracper

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
