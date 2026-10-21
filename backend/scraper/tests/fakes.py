import json


class FakeResponse:
    def __init__(self, status_code=200, body=b"", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        self.status_code = status_code
        self.content = body if isinstance(body, bytes) else body.encode()
        self.text = self.content.decode("utf-8", "replace")
        self.headers = headers or {}

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeHttp:
    """
    Answers from a {url-without-query: response} map and records every request.
    A route can also be a function of the query params returning the response.
    """

    def __init__(self, routes):
        self.routes = routes
        self.requests = []

    def get(self, url, params=None, headers=None):
        self.requests.append((url, params))
        route = self.routes.get(url, FakeResponse(404, "not found"))
        return route(params or {}) if callable(route) else route
