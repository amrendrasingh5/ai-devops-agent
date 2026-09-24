from pathlib import Path

from agent.tools.kubernetes import find_pods
from agent.investigator import investigate_pod

from mcp.server.mcpserver import MCPServer


mcp = MCPServer("devops-tools")

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

@mcp.tool()
def find_unhealthy_pods(
    namespace: str | None = None,
) -> list[dict]:
    """
    Find unhealthy Kubernetes pods.

    If namespace is provided, search only that namespace.
    If namespace is omitted, search all namespaces.

    This tool is read-only.
    """

    return find_pods(
        namespace=namespace,
        health="unhealthy",
    )


@mcp.tool()
def get_pod_investigation(
    pod_name: str,
    namespace: str = "default",
) -> dict:
    """
    Collect read-only Kubernetes investigation evidence for a pod.

    Returns pod state, container state, events, logs, and deployment
    information when available.
    """

    return investigate_pod(
        pod_name=pod_name,
        namespace=namespace,
    )

if __name__ == "__main__":
    mcp.run()
