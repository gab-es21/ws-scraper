# WorkoutSavings Frontend

## Table of Contents

- [Introduction](#introduction)
- [Data to be Displayed](#data-to-be-displayed)
  - [Protein Powder Information](#protein-powder-information)
  - [Brands (Work in Progress)](#brands-work-in-progress)
  - [Product Name](#product-name)
  - [Quantity](#quantity)
  - [Prices](#prices)
  - [Nutritional Table](#nutritional-table)
  - [Coupons](#coupons)
- [Requirements](#requirements)
- [Installation](#installation)
- [Environment Variables (.env file)](#environment-variables-env-file)
- [Running the Project](#running-the-project)


## Introduction

The frontend of the Workout Savings project aims to visualize and provide insights into the data collected from protein powder products, including prices, nutritional values, and more. This README.md provides an overview of how to work with the frontend and its key features.

## Data to be Displayed

### Protein Powder Information
- [**Brand**](#brand)
- [**Product Name**](#product-name)
- **Flavour**
- [**Quantity (g)**](#quantity)
- [**Prices (€):**](#price)
  - Normal Price (€)
  - Price w/ Promo Code (€)
  - Price w/o Promo /100g of Product (€)
  - Price w/ Promo /100g of Product (€)
  - Price w/o Promo /100g of Protein (€)
  - Price w/ Promo /100g of Protein (€)
- [**Nutritional Value (100g):**](#nutritional-table)
  - Carbs (%)
  - Fat (%)
  - Protein (%)
- [**Coupons:**](#coupons)
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

## Installation

Follow these steps to set up the project:

1. Clone this repository.

2. Install project dependencies using Poetry:
```
poetry install
```

3. Activate the virtual environment:
```
poetry shell
```

##Environment Variables (.env file)

Create a .env file in the project root and set the following variables:

```
DJANGO_SECRET_KEY=dummy
ALLOWED_HOSTS=127.0.0.1,localhost
DEBUG=True
```

## Running the project

1. Apply existing migrations:

```
make migrate
```

2. Start the development server:

```
make runserver
```
