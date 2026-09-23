import sys

from agent.agent import DevOpsAgent


def main():
    if len(sys.argv) < 2:
        print('Usage: python main.py "<pod-name>"')
        sys.exit(1)

    pod_name = sys.argv[1]

    agent = DevOpsAgent()

    agent.investigate(
        pod_name=pod_name,
        namespace="default",
    )


if __name__ == "__main__":
    main()
