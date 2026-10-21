from decimal import Decimal

import pytest

from scraper.adapters.base import Blocked, HttpClient, jsonld_objects, plain, size_in_grams, to_decimal

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
