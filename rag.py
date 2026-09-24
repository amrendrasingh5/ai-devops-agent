from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"


def search_knowledge(query: str, max_results: int = 3) -> list[dict]:
    """
    Search the local knowledge base using keyword matching.

    Returns the most relevant knowledge documents together with
    their relevance score and filename.

    This is a lightweight retrieval layer for the DevOps agent.
    It is read-only.
    """

    results = []

    query_words = {
        word.strip(".,!?():;[]{}")
        for word in query.lower().split()
    }

    query_words.discard("")

    for file in KNOWLEDGE_DIR.rglob("*"):

        if not file.is_file():
            continue

        if "__pycache__" in file.parts:
            continue

        if file.suffix.lower() not in {".md", ".txt"}:
            continue

        try:
            content = file.read_text()
        except Exception:
            continue

        content_lower = content.lower()

        content_words = set(
            re.findall(r"\b[\w.-]+\b", content_lower)
        )

        score = sum(
            1
            for word in query_words
            if word in content_words
        )
        if score > 0:
            results.append(
                {
                    "file": file.name,
                    "score": score,
                    "content": content,
                }
            )

    results.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return results[:max_results]
