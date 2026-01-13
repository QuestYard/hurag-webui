from .kernel import conf, logger
import httpx
import json
from typing import Literal

def chat(
    prompt: str,
    system_prompt: str|None = None,
    history: list|None = None,
    temperature: float|None = 0,
    stream: bool = True,
    timeout: int = 180,
):
    logger().debug("START chat")  # HACK for debugging

    url = f"{conf().api.url}/v1/llm/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "system_prompt": system_prompt,
        "history": history or [],
        "temperature": temperature,
        "stream": stream,
        "timeout": timeout,
    }

    if stream:
        async def stream_response():
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line.removeprefix("data: ")
                        if data.strip() == "[DONE]":
                            break
                        try:
                            yield json.loads(data)["delta"]
                        except json.JSONDecodeError:
                            continue

        return stream_response()
    else:
        async def get_response():
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        return get_response()

async def rag_retrieve(
    query: str,
    history: list[str]|None,
    mode: Literal["naive", "mix", "community", "global"]|None,
    user_path: str,
)-> list[dict]:
    """
    Retrieve relevant knowledge items for a given query using RAG.
    Args:
        query (str): The user query.
        history (list[str]|None): The user query history.
        mode (str|None): The retrieval mode.
        user_path (str): The user path for personalized retrieval.
    Returns:
        list[dict]: A list of retrieved knowledge items.
    """
    if mode is None:
        return []

    logger().debug("START rag_retrieve") # HACK for debugging

    url = f"{conf().api.url}/v1/hurag/retrieve"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "history": history or [],
        "graph_search": mode,
        "user_path": user_path,
    }
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            print(f"{len(data) = }")
            return data
    except Exception as e:
        logger().error(f"Retrieve knowledge error: {e}")
        return []


