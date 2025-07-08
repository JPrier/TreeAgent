import requests

from tools.web_search import web_search


class _Resp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_web_search_parses_urls(monkeypatch):
    def fake_get(url, timeout):
        return _Resp({"RelatedTopics": [{"FirstURL": "https://a.com"}, {"FirstURL": "https://b.com"}]})
    monkeypatch.setattr(requests, "get", fake_get)

    urls = web_search("foo")
    assert urls == ["https://a.com", "https://b.com"]


def test_web_search_handles_error(monkeypatch):
    def fake_get(url, timeout):
        raise requests.RequestException
    monkeypatch.setattr(requests, "get", fake_get)

    assert web_search("foo") == []
