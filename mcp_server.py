from pathlib import Path

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("devops-tools")

REPO = Path("demo-repo")


@mcp.tool()
def list_repository_files() -> list[str]:
    """List files in the demo repository."""

    files = []

    for path in REPO.rglob("*"):

        if not path.is_file():
            continue

        if ".git" in path.parts:
            continue

        files.append(
            str(path.relative_to(REPO))
        )

    return sorted(files)


@mcp.tool()
def read_repository_file(
    file_path: str
) -> str:
    """Read a file from the demo repository."""

    path = REPO / file_path

    if not path.exists():
        return f"ERROR: File does not exist: {file_path}"

    return path.read_text()


@mcp.tool()
def search_repository(
    keyword: str
) -> list[str]:
    """Search repository files."""

    results = []

    for path in REPO.rglob("*"):

        if not path.is_file():
            continue

        if ".git" in path.parts:
            continue

        try:
            content = path.read_text()
        except Exception:
            continue

        if keyword.lower() in content.lower():
            results.append(
                str(path.relative_to(REPO))
            )

    return sorted(results)


if __name__ == "__main__":
    mcp.run()
