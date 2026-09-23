from tools import list_files, search_files, read_file


class Agent:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def inspect_repository(self):
        print("\n[AGENT] Inspecting repository...\n")

        files = list_files(self.repo_path)

        for file in files:
            print(f"  {file}")

    def search(self, keyword):
        print(
            f"\n[AGENT] Searching for: {keyword}\n"
        )

        results = search_files(
            self.repo_path,
            keyword
        )

        for result in results:
            print(f"  {result}")

        return results

    def read(self, file_path):
        print(
            f"\n[AGENT] Reading: {file_path}\n"
        )

        content = read_file(
            self.repo_path,
            file_path
        )

        print(content)

        return content
