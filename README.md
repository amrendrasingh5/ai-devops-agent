# AI DevOps Agent

An agentic DevOps assistant for investigating Kubernetes and Amazon EKS issues using automated evidence collection and AI-assisted root-cause analysis.

The project combines deterministic Kubernetes tooling with GitHub Copilot CLI to investigate pod health, events, logs, deployments, container states, and policy violations.

> **Current status:** Read-only Kubernetes investigation and AI-assisted analysis. No production write operations are implemented.

---

## Overview

Troubleshooting Kubernetes incidents often requires checking several sources of information:

* Pod status
* Container readiness and restart counts
* Container states and failure reasons
* Kubernetes events
* Container logs
* ReplicaSets and Deployments
* Admission/policy violations
* Container image configuration

The AI DevOps Agent automates this evidence-gathering process and provides a structured investigation that can then be analyzed by an AI model.

### Current workflow

```text
User
  │
  ▼
AI DevOps Agent
  │
  ▼
Kubernetes Investigation Tools
  │
  ├── Pod health
  ├── Container states
  ├── Events
  ├── Logs
  └── Deployment information
  │
  ▼
Evidence
  │
  ▼
GitHub Copilot CLI
  │
  ▼
Root-Cause Analysis
  │
  ▼
Recommended Next Steps
```

The design intentionally separates **evidence collection** from **AI reasoning**.

---

## Current Capabilities

### Kubernetes investigation

The agent can currently:

* List pods in a namespace
* Identify healthy and unhealthy pods
* Inspect container readiness
* Inspect container restart counts
* Inspect container states
* Detect image-pull failures
* Retrieve Kubernetes events
* Retrieve container logs
* Resolve a Pod → ReplicaSet → Deployment relationship
* Retrieve Deployment replica information
* Detect selected Kubernetes policy violations
* Automatically investigate unhealthy pods

### AI-assisted analysis

Investigation evidence can be passed to GitHub Copilot CLI for analysis.

The AI is instructed to:

1. Identify the most likely root cause
2. Explain the evidence supporting the conclusion
3. Distinguish confirmed facts from assumptions
4. Recommend safe next steps
5. Avoid production modifications
6. Avoid inventing information that is not present in the evidence

---

## Example Investigation

A controlled lab failure was created using a Kubernetes Deployment with a
non-existent container image:

```bash
kubectl create deployment ai-devops-test-failing \
  --image=nginx:this-image-does-not-exist
```

The Deployment created a ReplicaSet and Pod:

```text
Deployment
  ↓
ReplicaSet
  ↓
ai-devops-test-failing-<pod-id>
```

The agent was then asked:

```text
Hey, check why the pod is not running in the default namespace.
```

Using the DevOps MCP tools, the agent:

1. Discovered the unhealthy pod.
2. Collected pod and container state.
3. Collected Kubernetes events.
4. Collected Deployment information.
5. Checked whether logs were available.
6. Searched the repository for supporting configuration.
7. Analyzed the evidence and identified the root cause.
8. Recommended safe remediation without modifying the cluster.

The investigation identified:

* Pod phase: `Pending`
* Container state: `Waiting`
* Container reason: `ImagePullBackOff`
* Configured image: `nginx:this-image-does-not-exist`
* Image pull error: `ErrImagePull`
* Repeated Kubernetes image-pull failure events
* A `PolicyViolation` from the cluster image-registry policy
* No application logs because the container never started
* Deployment: `ai-devops-test-failing`

The agent distinguished confirmed evidence from assumptions and did not make
any Kubernetes changes.

The lab workload can be removed with:

```bash
kubectl delete deployment ai-devops-test-failing -n default
```

---

## Healthy Pod Investigation

The same investigation workflow can analyze a healthy workload.

For example, a healthy NGINX deployment can produce evidence such as:

```text
Current Health: HEALTHY

✓ Pod is Running
✓ All containers are Ready
✓ No container restarts detected
✓ Logs contain successful HTTP 200 responses

Deployment:
Name: nginx-deployment
Replicas: 3/3
```

The agent also separates runtime health from configuration and policy findings.

For example, a pod can be healthy at runtime while still using a mutable image tag such as:

```text
nginx:latest
```

This distinction is important because a configuration or policy issue does not necessarily mean that the workload is currently unhealthy.

---

## AI Analysis

GitHub Copilot CLI is used as the current AI interface.

The project invokes Copilot through the GitHub CLI:

```text
gh copilot
```

The integration is intentionally kept separate from Kubernetes access.

The Kubernetes Python tools collect evidence.

The AI receives that evidence and performs analysis.

```text
Kubernetes API
      │
      ▼
Python investigation tools
      │
      ▼
Structured evidence
      │
      ▼
GitHub Copilot CLI
      │
      ▼
AI analysis
```

The AI does not receive unrestricted Kubernetes access through the current implementation.

---

## Safety Model

Safety is a core design principle of this project.

### Current boundary

The current Kubernetes tools are **read-only**.

They can inspect resources but do not:

* Delete workloads
* Modify Deployments
* Modify Pods
* Modify ConfigMaps
* Modify Secrets
* Apply Kubernetes manifests
* Scale workloads
* Restart production workloads

### Planned approval model

Future write operations will follow a human-in-the-loop workflow:

```text
Investigation
     │
     ▼
Root-cause analysis
     │
     ▼
Recommended change
     │
     ▼
Human approval
     │
     ▼
Git change / Pull Request
     │
     ▼
Review
     │
     ▼
Deployment
```

The agent should not autonomously make production changes.

---

## Project Structure

```text
ai-devops-agent/
│
├── agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── investigator.py
│   ├── llm.py
│   │
│   └── tools/
│       ├── __init__.py
│       └── kubernetes.py
│
├── demo-repo/
│   ├── docs/
│   │   └── terraform-standards.md
│   │
│   └── terraform/
│       ├── environments/
│       │   └── qa/
│       │       └── main.tf
│       │
│       └── modules/
│           └── network/
│               └── main.tf
│
├── knowledge/
│   └── terraform-standards.md
│
├── agent_planner.py
├── main.py
├── mcp_server.py
├── planner.py
├── rag.py
├── tools.py
├── test_tools.py
├── requirements.txt
└── README.md
```

Some of these components represent experimental or planned parts of the agent architecture and will evolve as the project develops.

---

## Requirements

The current project uses:

* Python 3.14+
* Kubernetes Python client
* MCP Python SDK
* `kubectl`
* AWS CLI
* Git
* GitHub CLI
* GitHub Copilot CLI

Python dependencies are pinned in:

```text
requirements.txt
```

Current dependencies:

```text
kubernetes==36.0.3
mcp==2.2.0
```

---

## Installation

Clone the repository:

```bash
git clone git@github.com:amrendrasingh5/ai-devops-agent.git
cd ai-devops-agent
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Verify Kubernetes access:

```bash
kubectl get pods
```

The Python Kubernetes client uses the current kubeconfig context.

---

## Kubernetes Access

The current implementation uses:

```python
config.load_kube_config()
```

This means the agent uses the Kubernetes context configured on the local machine.

Before running investigations, verify the active context:

```bash
kubectl config current-context
```

Then verify access:

```bash
kubectl get pods
```

For the current development environment, investigations are performed against a non-production Kubernetes/EKS environment.

---

## Running an Investigation

The investigation functionality can be used directly from Python.

Example:

```python
from agent.investigator import investigate_pod

investigation = investigate_pod(
    "nginx-deployment-65b5d9df77-hvl67",
    "default",
)

print(investigation)
```

Human-readable summaries can be generated with:

```python
from agent.investigator import (
    investigate_pod,
    summarize_investigation,
)

investigation = investigate_pod(
    "nginx-deployment-65b5d9df77-hvl67",
    "default",
)

print(summarize_investigation(investigation))
```

---

## Investigating Unhealthy Pods

The agent can automatically discover unhealthy pods:

```python
from agent.investigator import investigate_unhealthy_pods

results = investigate_unhealthy_pods("default")

for result in results:
    print(result["summary"])
```

The workflow is:

```text
Find unhealthy pods
        │
        ▼
Investigate each pod
        │
        ├── Pod status
        ├── Containers
        ├── Events
        ├── Logs
        └── Deployment
        │
        ▼
Generate investigation summary
```

---

## AI-Assisted Investigation

The collected evidence can be analyzed using GitHub Copilot:

```python
from agent.investigator import (
    investigate_pod,
    analyze_with_llm,
)

investigation = investigate_pod(
    "nginx-deployment-65b5d9df77-hvl67",
    "default",
)

analysis = analyze_with_llm(investigation)

print(analysis)
```

The AI analysis is based on evidence collected by the project's Kubernetes tools.

---

## Design Principles

The project follows several principles.

### 1. Evidence before reasoning

The agent should collect concrete infrastructure evidence before asking an AI model to reason about the problem.

### 2. Separate tools from reasoning

Kubernetes access and AI reasoning are separate components.

This makes the system easier to test and reduces the risk of an AI model directly controlling infrastructure.

### 3. Human approval for changes

Future remediation actions should require explicit human approval.

### 4. Production safety

Production environments should not be modified autonomously.

### 5. Infrastructure as Code

Future infrastructure changes should be represented through Git-based workflows and reviewed Pull Requests rather than direct manual production changes.

### 6. Explainability

The agent should explain:

* What it observed
* What is confirmed
* What is inferred
* Why a particular root cause is suspected
* What action is recommended

---

## Roadmap

### Phase 1 — Kubernetes Investigation

* [x] Pod discovery
* [x] Pod health detection
* [x] Container state inspection
* [x] Event collection
* [x] Log collection
* [x] Deployment relationship discovery
* [x] Unhealthy pod investigation
* [x] Human-readable investigation summaries

### Phase 2 — AI Reasoning

* [x] GitHub Copilot CLI integration
* [x] Evidence-based root-cause analysis
* [x] Fact vs assumption distinction
* [x] Safe remediation recommendations

### Phase 3 — Agent Tools

Planned integrations:

* [ ] Flux
* [ ] GitHub
* [ ] AWS
* [ ] CloudWatch
* [ ] Dynatrace
* [ ] Additional Kubernetes resources
* [ ] MCP-based tool integration

### Phase 4 — Knowledge / RAG

Planned capabilities:

* [ ] Terraform standards
* [ ] Kubernetes standards
* [ ] Internal engineering documentation
* [ ] Runbooks
* [ ] Architecture documentation
* [ ] Retrieval-augmented investigation

### Phase 5 — GitOps Remediation

Planned workflow:

```text
Incident
   │
   ▼
Evidence collection
   │
   ▼
AI root-cause analysis
   │
   ▼
Suggested remediation
   │
   ▼
Human approval
   │
   ▼
Git change
   │
   ▼
Pull Request
   │
   ▼
CI validation
   │
   ▼
Human review
```

Direct production modification is intentionally excluded from the design.

---

## Development Philosophy

This project is intended to explore how AI agents can assist DevOps engineers without removing engineering controls.

The goal is not simply to allow an LLM to execute shell commands.

Instead, the project focuses on:

```text
Deterministic tools
       +
Infrastructure evidence
       +
AI reasoning
       +
Engineering standards
       +
Human approval
       =
Controlled Agentic DevOps
```

The architecture is designed to evolve from Kubernetes troubleshooting into a broader platform-engineering assistant while maintaining clear boundaries around infrastructure access and production changes.

---

## Status

**Active development**

Current milestone:

> Kubernetes evidence collection → structured investigation → GitHub Copilot AI analysis

Future milestones will expand the agent toward AWS, GitOps, observability, knowledge retrieval, and human-approved remediation workflows.

