from tools import list_files, search_files, read_file
from rag import search_knowledge


class AgentPlanner:

    def __init__(self, repo_path):
        self.repo_path = repo_path

    def inspect_repository(self):
        print("\n=== REPOSITORY ===")

        files = list_files(self.repo_path)

        for file in files:
            print(f"- {file}")

        return files

    def search_repository(self, keyword):
        print(f"\n=== SEARCH: {keyword} ===")

        results = search_files(
            self.repo_path,
            keyword
        )

        for result in results:
            print(f"- {result}")

        return results

    def read_repository_file(self, file_path):
        print(f"\n=== READ: {file_path} ===")

        content = read_file(
            self.repo_path,
            file_path
        )

        print(content)

        return content

    def retrieve_standards(self, query):
        print(f"\n=== KNOWLEDGE: {query} ===")

        results = search_knowledge(query)

        for result in results:
            print(result)

        return results

    def create_plan(self, task):

        print("\n================================")
        print("AI AGENT PLANNING")
        print("================================")

        print(f"\nTask:\n{task}")

        self.inspect_repository()

        results = self.search_repository("vpc")

        if results:
            self.read_repository_file(results[0])

        self.retrieve_standards(
            "Terraform AWS modules validation"
        )

        print("\n=== IMPLEMENTATION PLAN ===")

        print("""
1. Understand the requested infrastructure change.
2. Search for an existing Terraform implementation.
3. Reuse existing Terraform modules where possible.
4. Keep environment-specific values in environment configuration.
5. Do not hard-code AWS account IDs.
6. Modify the minimum required files.
7. Run terraform fmt.
8. Run terraform validate.
9. Review the resulting git diff.
10. Prepare the changes for a pull request.
""")


if __name__ == "__main__":

    agent = AgentPlanner("demo-repo")

    agent.create_plan(
        """
        Implement PE-703.

        Add the required QA networking/NACL configuration
        while following the existing Terraform structure
        and engineering standards.
        """
    )
