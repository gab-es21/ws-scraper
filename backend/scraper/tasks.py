import datetime
import json
import os
import random
import re
import time

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
XHR_HEADERS = {**HEADERS, "X-Requested-With": "XMLHttpRequest", "Accept": "application/json, */*"}
BASE = "https://www.prozis.com/pt/pt"


def random_sleep():
    time.sleep(random.uniform(0.8, 2.0))


# ── Link file helpers ─────────────────────────────────────────────────────────


def write_links_to_json(links, search_query, language):
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    file_name = f"links/prozis_{search_query}_{language}_links_{date_string}.json"
    try:
        with open(file_name, "w") as f:
            json.dump(links, f, indent=4)
        print(f"Saved {len(links)} links -> {file_name}")
    except Exception as e:
        print(f"Error writing links to JSON: {e}")


def get_matching_json_files(date=None, search_query=None):
    print("\n[READING LINK FILES]\n")
    date_string = (date or datetime.datetime.now()).strftime("%Y-%m-%d")

    json_files = [f for f in os.listdir("links") if f.startswith("prozis") and f.endswith(f"{date_string}.json")]
    if search_query:
        json_files = [f for f in json_files if search_query in f]

    if not json_files:
        print(f"\tNo link files found for {date_string}.")
    else:
        print(f"\tFound {len(json_files)} file(s) for {date_string}:")
        for f in json_files:
            print(f"\t  {f}")

    return json_files


# ── Extraction helpers ────────────────────────────────────────────────────────


def _parse_weight_g(name):
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*g\b", name, re.IGNORECASE)
    return float(match.group(1).replace(",", ".")) if match else None


def _parse_g(val):
    m = re.search(r"[\d,\.]+", str(val))
    return float(m.group().replace(",", ".")) if m else 0.0


def _extract_group_id(page_text):
    """Find the Prozis internal group ID embedded in the page JS."""
    m = re.search(r"product/index\?_id=(\d+)", page_text)
    return m.group(1) if m else None


def extract_nutrition(session, group_id, sku):
    """
    Call the Prozis nutrition-table API and return (protein_g, fat_g, carbs_g) per 100g.
    Returns (None, None, None) on failure.
    """
    try:
        r = session.get(
            f"{BASE}/product/nutrition-table",
            params={"_id": group_id, "sku": sku},
            headers=XHR_HEADERS,
            timeout=15,
        )
        if r.status_code != 200 or not r.text.strip():
            return None, None, None

        data = r.json()
        nutrients = data.get("nutTable", {}).get("table", {}).get("nutrients", [])

        protein = fat = carbs = None
        for n in nutrients:
            name = n.get("name", "").lower()
            val = _parse_g(n.get("amount", {}).get("by100", "0"))
            if "prote" in name:
                protein = val
            elif "lipid" in name or "gordura" in name:
                fat = val
            elif "hidratos" in name or "carbo" in name:
                carbs = val

        return protein, fat, carbs
    except Exception as e:
        print(f"    Nutrition error: {e}")
        return None, None, None


def _find_product_jsonld(soup):
    """Return the first JSON-LD block of @type Product on the page, or None."""
    for script in soup.find_all("script", type="application/ld+json"):
        raw = re.sub(r"/\*<!\[CDATA\[\*/\s*", "", script.text.strip())
        raw = re.sub(r"\s*/\*\]\]>\*/", "", raw)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if data.get("@type") == "Product":
            return data
    return None


def extract_product_jsonld(url):
    """
    Fetch a Prozis product page and extract price/name/brand via JSON-LD
    plus nutritional data via the internal nutrition-table API.
    Returns a dict or None on failure.
    """
    try:
        clean = url.split("?")[0]

        session = requests.Session()
        session.headers.update(HEADERS)

        # Step 1: load page (gets session cookies + page source)
        r = session.get(clean, timeout=15)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code} for {clean}")
            return None

        # Step 2: extract JSON-LD
        product_data = _find_product_jsonld(BeautifulSoup(r.text, "html.parser"))
        if not product_data:
            return None

        offers = product_data.get("offers", {})
        name = product_data.get("name", "")
        sku = product_data.get("sku", "")

        result = {
            "name": name,
            "brand": product_data.get("brand", {}).get("name", "Prozis"),
            "price": float(offers.get("price", 0)),
            "currency": offers.get("priceCurrency", "EUR"),
            "is_available": "InStock" in offers.get("availability", ""),
            "image_url": (
                "https:" + product_data["image"]
                if product_data.get("image", "").startswith("//")
                else product_data.get("image", "")
            ),
            "sku": sku,
            "url": clean,
            "weight_g": _parse_weight_g(name),
            "protein_g": None,
            "fat_g": None,
            "carbs_g": None,
        }

        # Step 3: get group ID — try page source first, fall back to SKU prefix
        group_id = _extract_group_id(r.text)
        if not group_id and sku:
            m = re.match(r"^(\d+)", sku)
            if m:
                group_id = m.group(1)
                print(f"    group_id from SKU prefix: {group_id}")

        if group_id and sku:
            idx_r = session.get(f"{BASE}/product/index?_id={group_id}", headers=XHR_HEADERS, timeout=15)
            print(f"    product/index status: {idx_r.status_code}")
            protein, fat, carbs = extract_nutrition(session, group_id, sku)
            result["protein_g"] = protein
            result["fat_g"] = fat
            result["carbs_g"] = carbs
        else:
            print(f"    no group_id (sku={sku!r})")

        return result

    except Exception as e:
        print(f"  Error extracting {url}: {e}")
        return None


def get_products_info(json_files):
    """Read saved link files, extract product data, return list of dicts."""
    products = []
    success = 0
    failed = []

    print("\n" + "*" * 60)
    print("\tSTARTING PRODUCT EXTRACTION")
    print("*" * 60)

    for json_file in json_files:
        full_path = os.path.join("links", json_file)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue

        with open(full_path) as f:
            links = json.load(f)

        print(f"\nProcessing {json_file} ({len(links)} links)")

        for link in links:
            slug = link.split("?")[0].split("/")[-1]
            print(f"  > {slug}", end=" ")
            data = extract_product_jsonld(link)
            if data:
                products.append(data)
                success += 1
                nut = (
                    f"P:{data['protein_g']}g F:{data['fat_g']}g C:{data['carbs_g']}g"
                    if data["protein_g"] is not None
                    else "no nutrition"
                )
                print(f"OK  {data['price']} EUR  [{nut}]")
            else:
                failed.append(link)
                print("FAIL")
            random_sleep()

    print("\n" + "*" * 60)
    print(f"\tDone: {success} extracted, {len(failed)} failed")
    if failed:
        print("\tFailed URLs:")
        for u in failed:
            print(f"\t  {u}")
    print("*" * 60)

    return products


# ── Django ORM storage ────────────────────────────────────────────────────────


def save_to_db(product_data):
    from scraper.models import (
        Brand,
        Flavor,
        NutritionalValue,
        Price,
        Product,
        ProductVariant,
        Quantity,
    )

    brand, _ = Brand.objects.get_or_create(name=product_data["brand"])

    product, _ = Product.objects.update_or_create(
        brand=brand,
        name=product_data["name"],
        defaults={
            "image_url": product_data["image_url"],
            "product_url": product_data["url"],
            "is_available": product_data["is_available"],
        },
    )

    flavor, _ = Flavor.objects.get_or_create(name="default")
    weight = product_data.get("weight_g") or 1000.0
    quantity, _ = Quantity.objects.get_or_create(amount_g=weight)

    variant, created = ProductVariant.objects.get_or_create(
        product=product,
        flavor=flavor,
        quantity=quantity,
    )

    # Update nutrition if we got values
    protein = product_data.get("protein_g") or 0
    fat = product_data.get("fat_g") or 0
    carbs = product_data.get("carbs_g") or 0

    NutritionalValue.objects.update_or_create(
        product_variant=variant,
        defaults={
            "protein_percentage": protein,
            "fat_percentage": fat,
            "carbs_percentage": carbs,
        },
    )

    price_obj, price_created = Price.objects.get_or_create(
        product_variant=variant,
        defaults={"normal_price": product_data["price"]},
    )
    if not price_created:
        price_obj.normal_price = product_data["price"]
        price_obj.save()

    return variant
