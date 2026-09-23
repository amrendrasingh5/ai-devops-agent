from pathlib import Path


def list_files(repo_path: str) -> list[str]:
    """List files in a repository."""

    repo = Path(repo_path)

    results = []

    for path in repo.rglob("*"):
        if not path.is_file():
            continue

        if ".git" in path.parts:
            continue

        results.append(str(path.relative_to(repo)))

    return sorted(results)


def read_file(repo_path: str, file_path: str) -> str:
    """Read a file from the repository."""

    repo = Path(repo_path)
    path = repo / file_path

    if not path.exists():
        return f"ERROR: File does not exist: {file_path}"

    if not path.is_file():
        return f"ERROR: Not a file: {file_path}"

    return path.read_text()


def search_files(repo_path: str, keyword: str) -> list[str]:
    """Search for a keyword inside repository files."""

    repo = Path(repo_path)

    results = []

    for path in repo.rglob("*"):

        if not path.is_file():
            continue

        if ".git" in path.parts:
            continue

        try:
            content = path.read_text()
        except (UnicodeDecodeError, PermissionError):
            continue

        if keyword.lower() in content.lower():
            results.append(str(path.relative_to(repo)))

    return sorted(results)
