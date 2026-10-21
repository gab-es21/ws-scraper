"""Gold Nutrition adapter, against a feed shaped like Shopify's /products.json (trimmed)."""

from decimal import Decimal

from scraper.adapters.gold_nutrition import BASE, FEED_URL, PAGE_SIZE, GoldNutritionAdapter, is_tracked

from .fakes import FakeHttp, FakeResponse


def variant(variant_id, options, price, compare_at, available=True, grams=450):
    values = {f"option{i}": value for i, value in enumerate(options, 1)}
    return {
        "id": variant_id,
        "title": " / ".join(options),
        **values,
        "price": price,
        "compare_at_price": compare_at,
        "available": available,
        "grams": grams,
    }


def product(handle, title, options, variants):
    return {
        "handle": handle,
        "title": title,
        "options": [{"name": name} for name in options],
        "variants": variants,
        "images": [{"src": f"https://cdn.shopify.com/{handle}.jpg"}],
    }


FEED = [
    product(
        "total-iso-whey",
        "Total Iso Whey",
        ["Sabor"],
        [
            variant(1, ["Baunilha"], "27.62", "35.99"),
            variant(2, ["Chocolate"], "24.64", "35.99", available=False),
        ],
    ),
    product(
        "total-whey-800g", "Total Whey 800g", ["Peso", "Sabor"], [variant(3, ["800g", "Baunilha"], "42.00", "49.99")]
    ),
    product("creatine-powder", "Creatine Powder", ["Title"], [variant(4, ["Default Title"], "23.99", None, grams=300)]),
    product(
        "total-protein-bar",
        "Total Protein Bar",
        ["Sabor", "Quantidade"],
        [variant(5, ["Chocolate", "1 Unidade"], "2.75", None)],
    ),
    product("camisola-ciclismo", "Camisola ciclismo", ["Tamanho"], [variant(6, ["L"], "44.00", None)]),
]


def adapter_for(feed=FEED):
    http = FakeHttp({FEED_URL: lambda params: FakeResponse(200, {"products": feed if params["page"] == 1 else []})})
    return GoldNutritionAdapter(http=http), http


def test_title_filter_keeps_protein_and_creatine_powders():
    assert [is_tracked(p["title"]) for p in FEED] == [True, True, True, False, False]


def test_discover_lists_tracked_products_from_one_feed_request():
    adapter, http = adapter_for()

    assert adapter.discover() == [
        f"{BASE}/products/total-iso-whey",
        f"{BASE}/products/total-whey-800g",
        f"{BASE}/products/creatine-powder",
    ]
    assert len(http.requests) == 1


def test_fetch_maps_variants_without_more_requests():
    adapter, http = adapter_for()
    adapter.discover()

    vanilla, chocolate = adapter.fetch(f"{BASE}/products/total-iso-whey").items

    assert (vanilla.store_sku, vanilla.brand, vanilla.product_name) == ("1", "Gold Nutrition", "Total Iso Whey")
    assert (vanilla.flavor, vanilla.price, vanilla.list_price) == ("Baunilha", Decimal("27.62"), Decimal("35.99"))
    assert vanilla.size_g == Decimal("450")  # from Shopify grams: no size in title or options
    assert vanilla.category == "Proteína"
    assert vanilla.image_url == "https://cdn.shopify.com/total-iso-whey.jpg"
    assert chocolate.in_stock is False
    assert vanilla.protein_g is None
    assert len(http.requests) == 1


def test_size_comes_from_the_weight_option_before_grams():
    adapter, _ = adapter_for()

    [item] = adapter.fetch(f"{BASE}/products/total-whey-800g").items

    assert (item.product_name, item.flavor, item.size_g) == ("Total Whey", "Baunilha", Decimal("800"))


def test_creatine_category_and_no_list_price_when_not_on_sale():
    adapter, _ = adapter_for()

    [item] = adapter.fetch(f"{BASE}/products/creatine-powder").items

    assert (item.category, item.flavor, item.list_price, item.size_g) == ("Creatina", "", None, Decimal("300"))


def test_feed_is_paginated():
    pages = {1: FEED[:1] * PAGE_SIZE, 2: FEED[1:2]}
    http = FakeHttp({FEED_URL: lambda params: FakeResponse(200, {"products": pages.get(params["page"], [])})})

    GoldNutritionAdapter(http=http).discover()

    assert [params["page"] for _, params in http.requests] == [1, 2]


def test_unknown_url_yields_nothing():
    adapter, _ = adapter_for()
    assert adapter.fetch(f"{BASE}/products/gone").items == []
