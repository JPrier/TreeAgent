import requests
from typing import List, Optional
from urllib.parse import quote

from pydantic import BaseModel, Field, TypeAdapter

from modelAccessors.base_accessor import Tool

MAX_RESULTS = 5
MAX_ATTEMPTS = 2

class _DDGTopic(BaseModel):
    FirstURL: Optional[str] = None
    Topics: List["_DDGTopic"] = Field(default_factory=list)


class _DDGResponse(BaseModel):
    RelatedTopics: List[_DDGTopic] = Field(default_factory=list)


_DDGTopic.model_rebuild()


def _fetch(query: str) -> List[str]:
    api_url = (
        f"https://duckduckgo.com/?q={quote(query)}&format=json&no_redirect=1&skip_disambig=1"
    )
    resp = requests.get(api_url, timeout=5)
    resp.raise_for_status()
    ddg = TypeAdapter(_DDGResponse).validate_python(resp.json())

    results: List[str] = []
    queue = ddg.RelatedTopics.copy()
    while queue and len(results) < MAX_RESULTS:
        item = queue.pop(0)
        if item.FirstURL:
            results.append(item.FirstURL)
        if item.Topics:
            queue.extend(item.Topics)

    return results


def web_search(query: str) -> List[str]:
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
