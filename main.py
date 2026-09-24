from agent.agent import DevOpsAgent


def main():
    agent = DevOpsAgent()

    print("================================")
    print("AI DEVOPS AGENT")
    print("================================")
    print()
    print("Type your DevOps question.")
    print("Type 'exit' or 'quit' to stop.")
    print()

    while True:
        try:
            request = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not request:
            continue

        if request.lower() in {"exit", "quit"}:
            print("Exiting...")
            break

        agent.handle_request(request)

        print()


if __name__ == "__main__":
    main()
