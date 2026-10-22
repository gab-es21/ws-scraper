from decimal import Decimal

import pytest

from scraper.adapters.base import (
    Blocked,
    HttpClient,
    jsonld_objects,
    nutrition_from_tables,
    plain,
    sitemap_urls,
    size_in_grams,
    strip_size,
    to_decimal,
)

from .fakes import FakeResponse


@pytest.mark.parametrize(
    "text, expected",
    [("€19.54", Decimal("19.54")), ("2,90 g", Decimal("2.90")), ("<0.5 g", Decimal("0.5")), (22.99, Decimal("22.99"))],
)
def test_to_decimal(text, expected):
    assert to_decimal(text) == expected


@pytest.mark.parametrize("text", [None, "", "n/a"])
def test_to_decimal_without_a_number(text):
    assert to_decimal(text) is None


@pytest.mark.parametrize(
    "text, expected",
    [("700 g", Decimal("700")), ("907g", Decimal("907")), ("2.27 kg", Decimal("2270")), ("2 Kg", Decimal("2000"))],
)
def test_size_in_grams(text, expected):
    assert size_in_grams(text) == expected


@pytest.mark.parametrize("text", ["90 cápsulas", "20 doses", "", None])
def test_size_in_grams_for_non_weight_sizes(text):
    assert size_in_grams(text) is None


def test_plain_drops_accents_and_case():
    assert plain(" Lípidos ") == "lipidos"
    assert plain("Proteína Whey") == "proteina whey"


def test_jsonld_objects_finds_types_in_lists_and_graphs():
    html = """
    <script type="application/ld+json">{"@type": "BreadcrumbList"}</script>
    <script type="application/ld+json">[{"@type": "Product", "name": "A"}]</script>
    <script type="application/ld+json">{"@graph": [{"@type": "Product", "name": "B"}]}</script>
    <script type="application/ld+json">not json</script>
    """
    assert [p["name"] for p in jsonld_objects(html, "Product")] == ["A", "B"]


class ScriptedSession:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.headers = {}

    def get(self, url, timeout, **kwargs):
        return self.responses.pop(0)


def client(*responses):
    sleeps = []
    http = HttpClient(delay=(0, 0), retries=2, backoff=30, sleep=sleeps.append)
    http.session = ScriptedSession(*responses)
    return http, sleeps


def test_http_client_backs_off_on_429_and_retries():
    http, sleeps = client(FakeResponse(429, "slow down", {"Retry-After": "7"}), FakeResponse(200, "ok"))

    assert http.get("https://x").text == "ok"
    assert 7 in sleeps


def test_http_client_gives_up_when_still_limited():
    http, sleeps = client(*[FakeResponse(429, "slow down")] * 3)

    with pytest.raises(Blocked):
        http.get("https://x")
    assert [s for s in sleeps if s >= 30] == [30, 60, 90]


def table(*rows):
    return "<table>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows) + "</table>"


def test_nutrition_table_per_100g_column():
    html = table(
        ["", "Por 100g", "Por Dose"],
        ["Lípidos", "3,0g", "0,7g"],
        ["Hidratos de Carbono", "10g", "2,6g"],
        ["dos quais açúcares", "2,9g", "0,7g"],
        ["Proteína", "79g", "20g"],
    )
    assert nutrition_from_tables(html) == {
        "fat_g": Decimal("3.00"),
        "carbs_g": Decimal("10.00"),
        "protein_g": Decimal("79.00"),
    }


def test_nutrition_table_header_without_label_cell():
    html = table(["Por Dose", "Por 100 g"], ["Proteína", "20 g", "80 g"])
    assert nutrition_from_tables(html) == {"protein_g": Decimal("80.00")}


def test_nutrition_table_per_serving_only_is_scaled_to_100g():
    # Zumub-style: one "Por 30 g" column, mixed Portuguese/English labels.
    html = table(
        ["", "Por 30 g", "% Valor Diário"],
        ["Fat", "1.8 g", "3%"],
        ["Hidratos de carbono", "1.7 g", "1%"],
        ["Proteína", "21.4 g", "*"],
    )
    assert nutrition_from_tables(html) == {
        "fat_g": Decimal("6.00"),
        "carbs_g": Decimal("5.67"),
        "protein_g": Decimal("71.33"),
    }


def test_tables_without_protein_are_skipped():
    html = table(["", "Por 100 g"], ["Leucina", "7 g"]) + table(["", "Por 100 g"], ["Proteína", "75 g"])
    assert nutrition_from_tables(html) == {"protein_g": Decimal("75.00")}
    assert nutrition_from_tables(table(["Referência", "1ZUM9399"])) == {}


def test_sitemap_urls_unescape_entities():
    xml = b"<urlset><url><loc>https://x.pt/sitemap_products_1.xml?from=1&amp;to=2</loc></url></urlset>"
    assert sitemap_urls(xml) == ["https://x.pt/sitemap_products_1.xml?from=1&to=2"]


def test_strip_size_keeps_the_product_name():
    assert strip_size("Whey + Fibre 700 g") == "Whey + Fibre"
    assert strip_size("100% Whey Gold Standard 2,27kg") == "100% Whey Gold Standard"
    assert strip_size("Creatina Creapure 80 cápsulas") == "Creatina Creapure 80 cápsulas"
    assert strip_size("500g") == "500g"  # nothing left: keep the original
