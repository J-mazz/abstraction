import types

import pytest

from src.tools.web_tools import WebScraperTool, HTTPRequestTool


class DummyResponse:
    def __init__(self, text: str = "response", status_code: int = 200, headers=None):
        self.text = text
        self.content = text.encode()
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/plain"}

    def json(self):  # pragma: no cover - only invoked when JSON is valid
        raise ValueError("no json")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError("error")


@pytest.fixture
def allowed_host():
    return "example.com"


def test_web_scraper_blocks_disallowed_hosts(allowed_host):
    scraper = WebScraperTool(allowed_hosts=[allowed_host])
    result = scraper.execute("http://malicious.test")
    assert not result.success
    assert "not allowlisted" in result.error.lower()


def test_web_scraper_allows_configured_host(monkeypatch, allowed_host):
    scraper = WebScraperTool(allowed_hosts=[allowed_host])

    def fake_get(url, timeout):
        assert url == "http://example.com/"
        assert timeout == scraper._timeout
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>hi</h1>
                <a href="/docs">Docs</a>
            </body>
        </html>
        """
        return DummyResponse(html)

    monkeypatch.setattr("src.tools.web_tools.requests.get", fake_get)
    result = scraper.execute("http://example.com/", selector="h1", extract_links=True)
    assert result.success
    assert result.result["hostname"] == allowed_host
    assert result.result["selected_content"] == ["hi"]
    assert result.result["links"][0]["url"].endswith("/docs")


def test_http_request_blocks_disallowed_hosts(allowed_host):
    requester = HTTPRequestTool(allowed_hosts=[allowed_host])
    result = requester.execute("http://not-example.com")
    assert not result.success
    assert "not allowlisted" in result.error.lower()


def test_http_request_allows_hosts(monkeypatch, allowed_host):
    requester = HTTPRequestTool(allowed_hosts=[allowed_host])

    def fake_request(method, url, headers, data, json, timeout):
        assert url == "http://example.com"
        assert method == "GET"
        resp = DummyResponse("ok")
        resp.json = types.MethodType(lambda self: {"status": "ok"}, resp)
        return resp

    monkeypatch.setattr("src.tools.web_tools.requests.request", fake_request)
    result = requester.execute("http://example.com")
    assert result.success
    assert result.result["hostname"] == allowed_host
    assert result.result["json"] == {"status": "ok"}


def test_web_scraper_supports_wildcard_hosts(monkeypatch):
    scraper = WebScraperTool(allowed_hosts=["*.example.org"])

    def fake_get(url, timeout):
        return DummyResponse("<html><body>ok</body></html>")

    monkeypatch.setattr("src.tools.web_tools.requests.get", fake_get)
    response = scraper.execute("https://sub.example.org/page")
    assert response.success
    assert response.result["hostname"] == "sub.example.org"


def test_http_request_invalid_scheme():
    tool = HTTPRequestTool()
    result = tool.execute("ftp://example.com")
    assert not result.success
    assert "scheme" in result.error.lower()


def test_http_request_handles_non_json(monkeypatch, allowed_host):
    requester = HTTPRequestTool(allowed_hosts=[allowed_host])

    def fake_request(method, url, headers, data, json, timeout):
        return DummyResponse("plain text")

    monkeypatch.setattr("src.tools.web_tools.requests.request", fake_request)
    response = requester.execute("http://example.com")
    assert response.success
    assert "json" not in response.result
