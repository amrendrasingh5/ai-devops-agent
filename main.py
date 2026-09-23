from planner import Agent


agent = Agent("demo-repo")

agent.inspect_repository()

results = agent.search("vpc_cidr")

if results:
    agent.read(results[0])
