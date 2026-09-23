from tools import list_files, read_file, search_files


REPO = "demo-repo"


print("\n=== FILES ===")

for file in list_files(REPO):
    print(file)


print("\n=== SEARCH: environment ===")

for file in search_files(REPO, "environment"):
    print(file)


print("\n=== READ FILE ===")

print(
    read_file(
        REPO,
        "terraform/modules/network/main.tf"
    )
)
