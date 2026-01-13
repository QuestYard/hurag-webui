from ..models import Citation
from ..kernel import conf

from typing import Sequence

def load_citations_by_ids(
    citation_ids: Sequence[str]|set[str],
    cached_citations: dict[str, dict],
    user_path: str,
)-> list[Citation]:
    """Load citations by their IDs from cached citations or HuRAG API.

    Args:
        citation_ids (Sequence|set): Citation IDs to load.
        cached_citations (dict): Dictionary of cached citations.

    Returns:
        list[Citation]: List of loaded Citation objects.
    """
    ids = set(citation_ids)
    uncached_ids = ids - cached_citations.keys()
    cached_ids = ids & cached_citations.keys()
    # Load cached citations
    citations = [
        Citation.model_validate(cached_citations[cid]) for cid in cached_ids
    ]
    if not uncached_ids:
        return citations

    # Load uncached citations from HuRAG API
    import httpx
    url = f"{conf().api.url}/v1/hurag/knowledge"
    headers = {"Content-Type": "application/json"}
    payload = {
        "ids": list(uncached_ids),
        "user_path": user_path,
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        for knowledge in data:
            citation = Citation().from_knowledge(knowledge)
            citations.append(citation)
            # Update cached citations
            cached_citations[citation.id] = citation.model_dump()

    return citations

