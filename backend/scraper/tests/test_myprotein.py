"""Myprotein adapter, against a page shaped like the real one (trimmed to the parts used)."""

import json
from decimal import Decimal

from scraper.adapters.myprotein import BASE, SITEMAP_INDEX, MyproteinAdapter, is_candidate, parse_product_page

from .fakes import FakeHttp, FakeResponse

URL = f"{BASE}/p/sports-nutrition/impact-whey-protein/10530943/"


def offer(sku, price, strikethrough=None, in_stock=True):
    specs = [{"@type": "UnitPriceSpecification", "price": price}]
    if strikethrough:
        specs.append({"price": strikethrough, "priceType": "https://schema.org/StrikethroughPrice"})
    availability = "https://schema.org/InStock" if in_stock else "https://schema.org/OutOfStock"
    return {"@type": "Offer", "sku": sku, "price": price, "availability": availability, "priceSpecification": specs}


def variant(sku, name, flavour, price, weight=None, **offer_kwargs):
    data = {
        "@type": "Product",
        "sku": sku,
        "name": name,
        "gtin13": f"50{sku}",
        "additionalProperty": [{"@type": "PropertyValue", "name": "flavour", "value": flavour}],
        "offers": offer(sku, price, **offer_kwargs),
    }
    if weight:
        data["weight"] = {"@type": "QuantitativeValue", "value": weight, "unitText": "g"}
    return data


def page(category="Proteína Whey", variants=None):
    group = {
        "@type": "ProductGroup",
        "name": "Impact Whey Protein",
        "productGroupID": "10530943",
        "brand": {"@type": "Brand", "name": "Myprotein"},
        "category": category,
        "image": "https://static.thcdn.com/productimg/original/10530943.jpg",
        "hasVariant": variants
        or [
            variant(
                "10530944", "Impact Whey Protein 1kg Chocolate", "Chocolate", 32.99, weight=1000, strikethrough=45.99
            ),
            variant("10530945", "Impact Whey Protein Baunilha", "Baunilha", 32.99, strikethrough=45.99),
            variant("10530946", "Impact Whey Protein 2.5kg Morango", "Morango", 69.99, in_stock=False),
        ],
    }
    embedded = ",".join(
        f'{{"sku":{sku},"barcode":"50{sku}","inStock":true,"maxPerOrder":null,"choices":'
        + json.dumps([{"optionKey": "Flavour", "key": "x"}, {"optionKey": "Amount", "key": amount}])
        + ',"price":{}}'
        for sku, amount in [("10530944", "1kg"), ("10530945", "1kg - 40servings"), ("10530946", "2.5kg")]
    )
    return f"""<html><head><script type="application/ld+json">{json.dumps(group)}</script></head><body>
    <h3>Informação Nutricional</h3>
    <table>
      <tr><th>Valores típicos</th><th>Por 100 g</th><th>Por 30 g</th></tr>
      <tr><td>Energia</td><td>1602 kJ</td><td>481 kJ</td></tr>
      <tr><td>Lípidos</td><td>5.9 g</td><td>1.8 g</td></tr>
      <tr><td>dos quais saturados</td><td>3.6 g</td><td>1.1 g</td></tr>
      <tr><td>Hidratos de Carbono</td><td>8,9 g</td><td>2.7 g</td></tr>
      <tr><td>Proteína</td><td>72 g</td><td>21 g</td></tr>
    </table>
    <script>window.__DATA__ = [{embedded}]</script></body></html>"""


def test_candidates_are_protein_and_creatine_nutrition_pages():
    assert is_candidate(f"{BASE}/p/sports-nutrition/impact-whey-protein/10530943/")
    assert is_candidate(f"{BASE}/p/sports-nutrition/monohidrato-de-creatina/10530050/")
    assert not is_candidate(f"{BASE}/p/sports-clothing/protein-hoodie/123/")
    assert not is_candidate(f"{BASE}/p/sports-nutrition/barra-de-proteina-layered/456/")
    assert not is_candidate(f"{BASE}/p/sports-nutrition/impact-whey-protein-amostra/789/")


def test_every_variant_with_price_size_stock_and_nutrition():
    chocolate, vanilla, strawberry = parse_product_page(page(), URL)

    assert (chocolate.store_sku, chocolate.brand, chocolate.product_name) == (
        "10530944",
        "Myprotein",
        "Impact Whey Protein",
    )
    assert (chocolate.flavor, chocolate.size_g, chocolate.gtin) == ("Chocolate", Decimal("1000"), "5010530944")
    assert (chocolate.price, chocolate.list_price, chocolate.in_stock) == (Decimal("32.99"), Decimal("45.99"), True)
    assert chocolate.category == "Proteína Whey"
    assert (chocolate.protein_g, chocolate.carbs_g, chocolate.fat_g) == (Decimal("72"), Decimal("8.9"), Decimal("5.9"))
    assert strawberry.in_stock is False and strawberry.list_price is None


def test_size_missing_from_json_ld_comes_from_the_amount_choice():
    _, vanilla, strawberry = parse_product_page(page(), URL)

    assert vanilla.size_g == Decimal("1000")  # "1kg - 40servings"
    assert strawberry.size_g == Decimal("2500")  # from the variant name before the choice


def test_untracked_categories_yield_nothing():
    assert parse_product_page(page(category="Barras de Proteína"), URL) == []
    assert parse_product_page("<html>no structured data</html>", URL) == []


def test_discover_walks_the_sitemap_index():
    sitemap = f"{BASE}/sitemap-product-0.xml.gz"
    urls = [URL, f"{BASE}/p/sports-clothing/t-shirt/1/"]
    http = FakeHttp(
        {
            SITEMAP_INDEX: FakeResponse(200, f"<sitemapindex><sitemap><loc>{sitemap}</loc></sitemap></sitemapindex>"),
            sitemap: FakeResponse(200, "<urlset>" + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"),
        }
    )
    assert MyproteinAdapter(http=http).discover() == [URL]


def test_fetch_decodes_pages_as_utf8():
    # The site sends no charset; requests would guess Latin-1 and mangle 'Proteína'.
    http = FakeHttp({URL: FakeResponse(200, page().encode("utf-8"))})

    [item, *_] = MyproteinAdapter(http=http).fetch(URL).items

    assert item.category == "Proteína Whey"
