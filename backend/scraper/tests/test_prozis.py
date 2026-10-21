"""Prozis adapter, against fixtures shaped like the real responses (trimmed to the fields used)."""

import gzip
from decimal import Decimal

import pytest

from scraper.adapters.prozis import (
    BASE,
    SITEMAP_URL,
    ProzisAdapter,
    parse_coupons,
    parse_group_id,
    parse_nutrition,
    parse_sitemap,
    tracked_category,
)

from .fakes import FakeHttp, FakeResponse

URL = f"{BASE}/prozis/whey-fibre-700-g"

PAGE = """<html><head>
<script type="application/ld+json">/*<![CDATA[*/ {"@context": "https://schema.org", "@type": "Product",
 "name": "Whey + Fibre 700 g", "sku": "NUT00/1756750163",
 "image": "//static.sscontent.com/thumb/400/400/products/124/v1722939_whey-fibre.jpg",
 "offers": {"@type": "Offer", "price": "19.54", "priceCurrency": "EUR"}} /*]]>*/</script>
</head><body><script>App.js.vars = {"trackerInfo":{"store":"pt","groupId":"175675",
"productSku":"NUT00\\/1756750163"}};</script></body></html>"""


def sku(code, flavor, size, price, reference, stock=20, status="AC"):
    return {
        "sku": code,
        "groupId": "175675",
        "flavorDescription": flavor,
        "optionDescription": size,
        "price": price,
        "priceReference": reference,
        "stock": stock,
        "status": status,
        "isVisible": True,
    }


def breadcrumbs(*names):
    links = [{"pos": 1, "txt": "Prozis"}] + [{"pos": i + 2, "txt": n} for i, n in enumerate(names)]
    return {"links": links + [{"pos": len(links) + 1, "txt": "Whey + Fibre 700 g"}]}


INDEX = {
    "groupId": "175675",
    "breadcrumbs": breadcrumbs("Nutrição Desportiva", "Proteína", "Proteína Whey"),
    "addToCart": {
        "products": [
            sku("NUT00/1756750163", "Chocolate e Avelã", "700 g", "€19.54", 22.99),
            sku("NUT00/1756751163", "Chocolate e Avelã", "2 kg", "€49.99", 49.99),
            sku("NUT00/1756750089", "Baunilha", "700 g", "€19.54", 22.99, stock=0),
        ]
    },
    "bestPriceCoupons": [
        {"coupon": "SUPER", "discount": 15, "couponType": "DISCOUNT", "phrase": "Compra: <strong>Whey</strong> ..."}
    ],
}

NUTRITION = {
    "nutTable": {
        "table": {
            "nutrients": [
                {"name": "Lípidos", "amount": {"byServ": "0.58 g", "by100": "2.90 g"}},
                {"name": "dos quais saturados", "amount": {"by100": "1.80 g"}},
                {"name": "Hidratos de Carbono", "amount": {"by100": "40 g"}},
                {"name": "dos quais açúcares", "amount": {"by100": "3.1 g"}},
                {"name": "Fibra", "amount": {"by100": "5.50 g"}},
                {"name": "Proteínas", "amount": {"by100": "43 g"}},
                {"name": "Sal", "amount": {"by100": "0.31 g"}},
            ]
        }
    }
}


def adapter_for(index=INDEX, nutrition=NUTRITION, page=PAGE):
    http = FakeHttp(
        {
            URL: FakeResponse(200, page),
            f"{BASE}/product/index": FakeResponse(200, index),
            f"{BASE}/product/nutrition-table": FakeResponse(200, nutrition),
        }
    )
    return ProzisAdapter(http=http), http


def test_sitemap_keeps_protein_and_creatine_pages_only():
    urls = [
        f"{BASE}/prozis/100-real-whey-protein-1000-g",
        f"{BASE}/prozis/creatina-mono-hidratada-300-g",
        f"{BASE}/prozis/leggings-de-cintura-alta-preto",
        f"{BASE}/prozis/zero-protein-bar-x-12",
        f"{BASE}/prozis/oatmeal-whey-aveia-e-proteina-whey-900-g",
        f"{BASE}/gift-card/gift-card-50",
    ]
    xml = "<urlset>" + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"

    assert parse_sitemap(gzip.compress(xml.encode())) == urls[:2]
    assert parse_sitemap(xml.encode()) == urls[:2]


def test_group_id_is_read_from_the_page_script():
    assert parse_group_id(PAGE) == "175675"
    with pytest.raises(ValueError):
        parse_group_id("<html></html>")


@pytest.mark.parametrize(
    "crumbs, expected",
    [
        (("Nutrição Desportiva", "Proteína", "Proteína Whey"), "Proteína Whey"),
        (("Nutrição Desportiva", "Creatina"), "Creatina"),
        (("Alimentação Saudável", "Snacks Proteicos"), None),
        (("Roupa", "Leggings"), None),
    ],
)
def test_tracked_category_comes_from_breadcrumbs(crumbs, expected):
    assert tracked_category({"breadcrumbs": breadcrumbs(*crumbs)}) == expected


def test_nutrition_labels_with_accents_and_sub_rows():
    assert parse_nutrition(NUTRITION) == {
        "fat_g": Decimal("2.90"),
        "carbs_g": Decimal("40"),
        "protein_g": Decimal("43"),
    }


def test_coupon_is_kept_with_a_store_level_description():
    [coupon] = parse_coupons(INDEX)
    assert (coupon.code, coupon.discount_percent) == ("SUPER", Decimal("15"))
    assert "Whey" not in coupon.description


def test_fetch_returns_every_flavor_and_size_with_nutrition():
    adapter, _ = adapter_for()

    result = adapter.fetch(URL)

    choc_700, choc_2kg, vanilla = result.items
    assert (choc_700.product_name, choc_700.category) == ("Whey + Fibre", "Proteína Whey")
    assert (choc_700.flavor, choc_700.size_g) == ("Chocolate e Avelã", Decimal("700"))
    assert (choc_700.price, choc_700.list_price, choc_700.in_stock) == (Decimal("19.54"), Decimal("22.99"), True)
    assert choc_700.image_url.startswith("https://static.sscontent.com/")
    assert choc_2kg.size_g == Decimal("2000")
    assert choc_2kg.list_price is None  # same as price: not on sale
    assert vanilla.in_stock is False
    assert all(i.protein_g == Decimal("43") for i in result.items)
    assert [c.code for c in result.coupons] == ["SUPER"]


def test_nutrition_is_fetched_once_per_flavor():
    adapter, http = adapter_for()

    adapter.fetch(URL)

    nutrition_calls = [params["sku"] for url, params in http.requests if url.endswith("nutrition-table")]
    assert nutrition_calls == ["NUT00/1756750163", "NUT00/1756750089"]


def test_recently_checked_nutrition_is_not_fetched_again():
    adapter, http = adapter_for()

    result = adapter.fetch(URL, skip_nutrition_for={"NUT00/1756750163", "NUT00/1756751163"})

    assert [params["sku"] for url, params in http.requests if url.endswith("nutrition-table")] == ["NUT00/1756750089"]
    assert result.items[0].protein_g is None
    assert result.items[2].protein_g == Decimal("43")


def test_products_outside_tracked_categories_yield_nothing():
    index = {**INDEX, "breadcrumbs": breadcrumbs("Alimentação Saudável", "Snacks Proteicos")}
    adapter, http = adapter_for(index=index)

    assert adapter.fetch(URL).items == []
    assert not any(url.endswith("nutrition-table") for url, _ in http.requests)


def test_a_group_is_only_fetched_once_per_run():
    adapter, http = adapter_for()

    adapter.fetch(URL)
    second = adapter.fetch(URL)

    assert second.items == []
    assert sum(url.endswith("product/index") for url, _ in http.requests) == 1


def test_sizes_with_their_own_url_and_group_are_not_scraped_twice():
    # The 2 kg page has its own group, but its index lists the 700 g SKUs too (and vice versa).
    url_2kg = f"{BASE}/prozis/whey-fibre-2000-g"
    page_2kg = PAGE.replace('"groupId":"175675"', '"groupId":"175676"')
    skus = INDEX["addToCart"]["products"] + [
        {**sku("NUT00/1756760163", "Chocolate e Avelã", "2 kg", "€45.00", 45.00), "groupId": "175676"}
    ]
    index_2kg = {**INDEX, "groupId": "175676", "addToCart": {"products": skus}}
    url_700_again = f"{BASE}/prozis/whey-fibre-700-g-promo"
    http = FakeHttp(
        {
            URL: FakeResponse(200, PAGE),
            url_2kg: FakeResponse(200, page_2kg),
            url_700_again: FakeResponse(200, PAGE),
            f"{BASE}/product/index": lambda params: FakeResponse(
                200, INDEX if params["_id"] == "175675" else index_2kg
            ),
            f"{BASE}/product/nutrition-table": FakeResponse(200, NUTRITION),
        }
    )
    adapter = ProzisAdapter(http=http)
    order = [url_2kg, URL, url_700_again]

    results = [adapter.fetch(url) for url in order]

    assert [len(r.items) for r in results] == [4, 0, 0]
    assert [params["_id"] for url, params in http.requests if url.endswith("product/index")] == ["175676"]
    # nutrition is asked with each SKU's own group, not the group of the page it was found on
    nutrition_calls = [(p["_id"], p["sku"]) for url, p in http.requests if url.endswith("nutrition-table")]
    assert nutrition_calls == [("175675", "NUT00/1756750163"), ("175675", "NUT00/1756750089")]


def test_gone_products_yield_nothing():
    adapter = ProzisAdapter(http=FakeHttp({URL: FakeResponse(410, "gone")}))
    assert adapter.fetch(URL).items == []


def test_discover_reads_the_products_sitemap():
    xml = f"<urlset><url><loc>{URL}</loc></url></urlset>"
    adapter = ProzisAdapter(http=FakeHttp({SITEMAP_URL: FakeResponse(200, gzip.compress(xml.encode()))}))
    assert adapter.discover() == [URL]
