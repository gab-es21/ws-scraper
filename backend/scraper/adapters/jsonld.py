"""Read product variants from schema.org JSON-LD (ProductGroup / Product), as used by several stores."""

import re

from ..recording import ScrapedItem
from .base import jsonld_objects, plain, size_in_grams, to_decimal

GRAM_UNITS = {"g": 1, "grm": 1, "gram": 1, "grams": 1, "kg": 1000, "kgm": 1000}


def product_group(html):
    """(group, variants): the page's ProductGroup and its variants, or a lone Product as its only variant."""
    groups = jsonld_objects(html, "ProductGroup")
    if groups:
        return groups[0], groups[0].get("hasVariant") or []
    products = jsonld_objects(html, "Product")
    return (products[0], products[:1]) if products else (None, [])


def offer_of(product):
    offers = product.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    return offers


def crossed_out_price(offer, price):
    """The strikethrough / list price of an offer when it is higher than `price`."""
    specs = offer.get("priceSpecification") or []
    for spec in [specs] if isinstance(specs, dict) else specs:
        if re.search(r"Strikethrough|ListPrice", str(spec.get("priceType", ""))):
            value = to_decimal(spec.get("price"))
            if value and value > price:
                return value
    return None


def variant_size_g(variant):
    """Grams from `weight` (QuantitativeValue), else the `size` text, else the variant name."""
    weight = variant.get("weight")
    if isinstance(weight, dict) and weight.get("value") is not None:
        factor = GRAM_UNITS.get(plain(weight.get("unitText") or weight.get("unitCode") or "g"))
        value = to_decimal(weight["value"])
        if factor and value:
            return value * factor
    return size_in_grams(variant.get("size")) or size_in_grams(variant.get("name"))


def variant_flavor(variant):
    for prop in variant.get("additionalProperty") or []:
        if plain(prop.get("name")) in ("flavour", "flavor", "sabor"):
            return prop.get("value") or ""
    return ""


def image_url(product):
    image = product.get("image") or ""
    if isinstance(image, list):
        image = image[0] if image else ""
    if isinstance(image, dict):
        image = image.get("url") or ""
    return "https:" + image if image.startswith("//") else image


def scraped_items(group, variants, url, default_brand, nutrition=None):
    """One ScrapedItem per variant with a price. `nutrition` (per 100 g) applies to every variant."""
    brand = group.get("brand") or {}
    brand = (brand.get("name") if isinstance(brand, dict) else brand) or default_brand
    items = []
    for variant in variants:
        offer = offer_of(variant)
        price = to_decimal(offer.get("price"))
        sku = variant.get("sku") or offer.get("sku")
        if price is None or not sku:
            continue
        items.append(
            ScrapedItem(
                store_sku=str(sku),
                url=url,
                brand=brand,
                product_name=group.get("name") or variant.get("name") or "",
                flavor=variant_flavor(variant),
                size_g=variant_size_g(variant),
                price=price,
                list_price=crossed_out_price(offer, price),
                in_stock="InStock" in str(offer.get("availability", "")),
                category=group.get("category") or "",
                image_url=image_url(variant) or image_url(group),
                gtin=str(variant.get("gtin13") or variant.get("gtin") or ""),
                **(nutrition or {}),
            )
        )
    return items
