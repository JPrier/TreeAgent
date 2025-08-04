import requests
from typing import Optional
from urllib.parse import quote

from pydantic import BaseModel, Field, TypeAdapter

from src.modelAccessors.data.tool import Tool

MAX_RESULTS = 5
MAX_ATTEMPTS = 2

class _SearchTopic(BaseModel):
    url: Optional[str] = Field(None, alias="FirstURL")
    subtopics: list["_SearchTopic"] = Field(default_factory=list, alias="Topics")

    model_config = {
        "populate_by_name": True,
    }


class _SearchResponse(BaseModel):
    topics: list[_SearchTopic] = Field(default_factory=list, alias="RelatedTopics")

    model_config = {
        "populate_by_name": True,
    }


_SearchTopic.model_rebuild()


def _fetch(query: str) -> list[str]:
    api_url = (
        f"https://duckduckgo.com/?q={quote(query)}&format=json&no_redirect=1&skip_disambig=1"
    )
    resp = requests.get(api_url, timeout=5)
    resp.raise_for_status()
    parsed = TypeAdapter(_SearchResponse).validate_python(resp.json())

    results: list[str] = []
    queue = parsed.topics.copy()
    while queue and len(results) < MAX_RESULTS:
        item = queue.pop(0)
        if item.url:
            results.append(item.url)
        if item.subtopics:
            queue.extend(item.subtopics)

    return results


def web_search(query: str) -> list[str]:
    """Search DuckDuckGo and return up to 5 result URLs."""
    for _ in range(MAX_ATTEMPTS):
        try:
            links = _fetch(query)
        except Exception:
            links = []
        if links:
            return links
    return []


WEB_SEARCH_TOOL = Tool(
    name="web_search",
    description="Search the web and return a list of URLs",
    parameters={"query": {"type": "string"}},
)
