import subprocess


def ask_llm(prompt: str) -> str:
    """
    Send a prompt to GitHub Copilot CLI and return the response.

    This function does not interact with Kubernetes.
    """

    result = subprocess.run(
        [
            "gh",
            "copilot",
            "-p",
            prompt,
            "-s",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()
