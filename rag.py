from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"


def search_knowledge(query: str) -> list[str]:

    results = []

    query_words = query.lower().split()

    for file in KNOWLEDGE_DIR.rglob("*"):

        if not file.is_file():
            continue

        try:
            content = file.read_text()
        except Exception:
            continue

        content_lower = content.lower()

        score = sum(
            1
            for word in query_words
            if word in content_lower
        )

        if score > 0:
            results.append(
                (score, file, content)
            )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        content
        for score, file, content
        in results[:3]
    ]
