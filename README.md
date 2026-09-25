# AI DevOps Agent

An agentic DevOps assistant for investigating Kubernetes and Amazon EKS issues using automated evidence collection, RAG-based knowledge retrieval, MCP tools, and AI-assisted root-cause analysis.

The project combines deterministic Kubernetes and endpoint investigation tools with GitHub Copilot CLI to investigate pod health, application failures, Kubernetes events, deployments, services, endpoint connectivity, Helm configuration, and policy violations.

> **Current status:** Read-only Kubernetes and endpoint investigation with AI-assisted analysis. No automatic Kubernetes write operations are implemented.

---

## Overview

Troubleshooting Kubernetes and application incidents often requires checking information from several different sources.

For example, a single problem may require investigating:

* Pod status
* Container readiness
* Container states and failure reasons
* Restart counts
* Kubernetes events
* Current and previous container logs
* ReplicaSets and Deployments
* Container image configuration
* Admission and policy violations
* Services
* EndpointSlices
* Ingress resources
* Endpoint connectivity
* DNS resolution
* TCP connectivity
* HTTP/HTTPS responses
* Helm releases
* Helm values
* Helm manifests
* Deployment configuration

The AI DevOps Agent automates this evidence-gathering process and provides the collected evidence to an AI model for structured investigation.

The design intentionally separates:

```text
Evidence collection
        ↓
Knowledge retrieval
        ↓
AI reasoning
        ↓
Finding
        ↓
Evidence
        ↓
Recommendation
```

The agent does not use hard-coded troubleshooting logic such as:

```text
IF connection refused
THEN load balancer is broken
```

Instead, tools collect evidence and the AI analyzes the complete evidence set.

---

# Current Capabilities

## 1. Pod Investigation

The agent can investigate a specific Kubernetes Pod.

Example:

```text
Hey, check why the pod is not running.
```

or:

```text
Check pod example-app-xxxx in namespace example-namespace.
```

The investigation can collect:

* Pod phase
* Pod readiness
* Container readiness
* Container state
* Container state reason
* Container restart count
* Container image
* Kubernetes events
* Current container logs
* Previous container logs
* Pod details
* Deployment information

The agent can also distinguish between a Kubernetes-level problem and an application-level problem.

For example, a Pod can be:

```text
Running
Ready
0 restarts
```

while the application itself is still failing.

Application logs and other evidence are therefore considered during the investigation.

---

## 2. Unhealthy Pod Discovery

The project can automatically discover unhealthy Pods instead of requiring the user to know the Pod name first.

For example:

```text
Find unhealthy pods.
```

The investigation can identify Pods with conditions such as:

* Pending
* Failed
* Container waiting states
* Container termination failures
* Image-pull problems
* Restart activity
* Readiness problems

The discovered Pods can then be investigated further.

---

## 3. Pod → ReplicaSet → Deployment Investigation

The agent can follow the Kubernetes ownership relationship:

```text
Pod
 ↓
ReplicaSet
 ↓
Deployment
```

This allows the investigation to move from an individual failing Pod to the workload that created it.

Deployment evidence can include:

* Deployment name
* Namespace
* Desired replicas
* Available replicas
* Ready replicas
* Deployment configuration

This is important because fixing a Pod directly is normally not the correct long-term solution when the Pod is controlled by a Deployment.

---

## 4. Image and Container Startup Problems

The agent can investigate container startup problems using Kubernetes state and events.

For example, a controlled lab failure using:

```bash
kubectl create deployment ai-devops-test-failing \
  --image=nginx:this-image-does-not-exist
```

produces evidence such as:

```text
Pod phase:
Pending

Container state:
Waiting

Container reason:
ImagePullBackOff

Image:
nginx:this-image-does-not-exist
```

The agent can correlate this with Kubernetes events such as:

```text
ErrImagePull
ImagePullBackOff
```

It also recognizes when application logs are unavailable because the container never successfully started.

The agent does not invent a replacement image tag. Instead, it recommends checking the source configuration, Helm values, GitOps repository, or image registry configuration.

---

## 5. Runtime Application Failure Investigation

A Kubernetes Pod being `Running` does not necessarily mean the application is healthy.

The agent can inspect application logs in addition to Kubernetes status.

For example, a test application may produce:

```text
Application startup completed
ERROR: No space left on device while writing application data
```

Even if Kubernetes reports:

```text
Running
Ready
```

the AI analysis can identify the application error from the logs.

This allows the investigation to distinguish:

```text
Kubernetes runtime state
```

from:

```text
Application health
```

---

## 6. Kubernetes Events

Kubernetes events are collected as part of the investigation.

Events can provide important evidence about:

* Scheduling
* Image pulling
* Container startup
* Container termination
* Readiness
* Mounting
* Admission policies
* Other Kubernetes resource activity

The agent does not treat a single event as proof of the final root cause.

Events are combined with:

* Pod state
* Container state
* Logs
* Deployment configuration
* Other available evidence

---

## 7. Endpoint / URL Investigation

The agent can investigate an HTTP or HTTPS endpoint.

Example:

```text
Check https://example.company.com and investigate if there is any problem.
```

The endpoint investigation collects evidence from several layers:

```text
URL
 ↓
DNS
 ↓
TCP
 ↓
TLS / HTTPS
 ↓
HTTP response
```

The agent can collect information such as:

* DNS resolution
* Resolved addresses
* TCP connectivity
* HTTPS connectivity
* HTTP status
* HTTP response reason
* Response headers
* Connection errors

The tools only collect evidence.

They do not contain hard-coded rules that assume a particular error always has a particular root cause.

---

## 8. Kubernetes Network Path Investigation

When an endpoint is associated with Kubernetes, the agent can continue the investigation into the Kubernetes request path.

The current flow is:

```text
Hostname
   ↓
Ingress
   ↓
Service
   ↓
EndpointSlice
   ↓
Backend Pods
   ↓
Deployment
```

The investigation can collect:

* Matching Ingress resources
* Ingress class
* Load balancer information
* Service configuration
* Service ports
* Service selectors
* EndpointSlice information
* Endpoint addresses
* Endpoint readiness
* Backend Pod information

This helps connect an external endpoint problem with the Kubernetes resources behind it.

---

## 9. Ingress and Load Balancer Investigation

The agent can identify Kubernetes Ingress resources matching an endpoint hostname.

For example:

```text
https://app.example.com
```

can be traced through the Kubernetes resources responsible for serving the hostname.

The investigation can identify information such as:

```text
Ingress
   ↓
ALB / Load Balancer
   ↓
Service
   ↓
EndpointSlice
   ↓
Pods
```

This provides a structured evidence path instead of investigating the endpoint and Kubernetes resources independently.

---

## 10. Service and EndpointSlice Investigation

The agent can inspect Kubernetes Services and EndpointSlices.

Service evidence can include:

* Service name
* Namespace
* Service type
* Cluster IP
* Ports
* Selector

EndpointSlice evidence can include:

* Service relationship
* Endpoint addresses
* Ready state
* Serving state
* Terminating state
* Node information
* Target references

The agent can therefore determine what backend endpoints Kubernetes currently exposes for a Service.

---

## 11. Helm Investigation

The agent can follow the workload configuration into Helm.

The current investigation can identify the relationship:

```text
Deployment
    ↓
Helm release
```

For a Helm-managed workload, the agent can collect:

* Helm release name
* Release namespace
* Chart
* Chart version
* Application version
* Release revision
* Release status
* Helm values
* Rendered Helm manifest
* Deployment configuration

The purpose is to connect runtime evidence with the configuration that created the workload.

The agent remains read-only.

---

## 12. Complete Endpoint → Kubernetes → Helm Investigation

For an endpoint investigation, the agent can combine the different evidence sources.

The overall flow is:

```text
User
  │
  │ "Check this URL"
  ▼
Endpoint investigation
  │
  ├── DNS
  ├── TCP
  └── HTTPS / HTTP
  │
  ▼
Kubernetes investigation
  │
  ├── Ingress
  ├── Service
  ├── EndpointSlice
  └── Pods
  │
  ▼
Workload investigation
  │
  ├── Deployment
  └── Helm
       ├── Release
       ├── Values
       ├── Manifest
       └── Status
  │
  ▼
RAG knowledge
  │
  ▼
AI analysis
  │
  ▼
Finding
Evidence
Recommendation
```

This makes it possible to investigate an issue across multiple infrastructure layers instead of stopping at the first failed check.

---

## 13. RAG Knowledge Retrieval

The project includes a knowledge base containing DevOps and Kubernetes troubleshooting guidance.

The investigation creates a query from the collected evidence and retrieves relevant knowledge.

For example:

```text
Kubernetes
ImagePullBackOff
container state
events
application logs
Helm
```

Relevant knowledge can then be supplied to the AI analysis.

The knowledge base is intended to provide general troubleshooting knowledge rather than hard-coded solutions for individual incidents.

Current knowledge includes topics such as:

* Kubernetes troubleshooting
* Image-pull failures
* Container startup problems
* Evidence interpretation
* Safe remediation
* Terraform standards

---

# MCP and GitHub Copilot

The project also includes an MCP server that exposes read-only DevOps tools.

Current MCP tools include:

```text
list_repository_files
read_repository_file
search_repository
find_unhealthy_pods
get_pod_investigation
```

GitHub Copilot CLI can use these tools to investigate the environment and repository.

The architecture is:

```text
GitHub Copilot
       │
       ▼
MCP Server
       │
       ├── Kubernetes investigation
       ├── Pod discovery
       ├── Repository search
       └── Repository inspection
```

The MCP layer provides controlled access to the investigation capabilities without giving the AI unrestricted Kubernetes write access.

---

# AI-Assisted Root-Cause Analysis

The collected evidence is provided to the AI for analysis.

The AI is instructed to:

1. Determine the most likely root cause.
2. Analyze all available evidence.
3. Read application logs when available.
4. Distinguish confirmed facts from strong indications.
5. Identify assumptions.
6. Identify missing evidence.
7. Recommend safe remediation.
8. Prefer source control and GitOps for configuration changes.
9. Avoid inventing information.
10. Never modify the environment during the investigation.

The current analysis format is:

```text
Finding: ...

Evidence: ...

Recommendation: ...
```

---

# Example User Requests

The agent is designed to understand natural-language DevOps questions.

### Pod troubleshooting

```text
Hey, check why the pod is not running.
```

```text
Check pod example-app-xxxx in namespace example-namespace.
```

```text
Why is this pod unhealthy?
```

```text
Investigate the pod and tell me what is wrong.
```

### Cluster investigation

```text
Find unhealthy pods.
```

```text
Check the unhealthy workloads in this namespace.
```

### Endpoint troubleshooting

```text
I cannot reach https://example.company.com.
Find out why.
```

```text
Check https://example.company.com and investigate if there is any problem.
```

```text
Investigate the Kubernetes path behind this URL.
```

### Combined investigation

```text
Check the endpoint, investigate the Kubernetes backend,
and determine the most likely root cause.
```

```text
Check whether the Deployment or Helm configuration could
explain the endpoint problem.
```

The user does not need to specify which troubleshooting branch to execute.

The agent determines which evidence should be collected based on the request and the available resources.

---

# Evidence-Driven Troubleshooting

A core design principle is that the agent should not contain a large collection of hard-coded error-to-solution rules.

For example, the implementation should not contain logic such as:

```python
if connection_refused:
    return "The load balancer is broken"
```

Instead:

```text
User request
     ↓
Determine investigation scope
     ↓
Collect evidence
     ↓
Retrieve relevant knowledge
     ↓
AI analyzes evidence
     ↓
Identify supported findings
     ↓
Identify missing evidence
     ↓
Recommend safe next steps
```

This makes the approach applicable to different types of incidents, including problems that were not explicitly anticipated when the tool was developed.

---

# Safety Model

Safety is a core design principle of this project.

## Current boundary

The current Kubernetes investigation tools are read-only.

They can inspect resources but do not:

* Delete workloads
* Modify Deployments
* Modify Pods
* Modify ConfigMaps
* Modify Secrets
* Apply Kubernetes manifests
* Scale workloads
* Restart workloads
* Modify production resources

The endpoint investigation is also read-only.

The Helm integration uses read-only commands such as:

```text
helm get values
helm get status
helm get manifest
helm get metadata
```

No Helm upgrade or other write operation is performed.

---

# Human-in-the-Loop Remediation

The current agent only investigates and recommends.

Future write operations should follow a human-in-the-loop workflow:

```text
Investigation
     │
     ▼
Evidence
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
GitOps deployment
```

The goal is to keep investigation automated while keeping infrastructure changes controlled and reviewable.

---

# Project Structure

```text
ai-devops-agent/
│
├── agent/
│   ├── agent.py
│   ├── investigator.py
│   ├── request.py
│   │
│   └── tools/
│       ├── kubernetes.py
│       ├── endpoint.py
│       └── helm.py
│
├── knowledge/
│   ├── kubernetes-troubleshooting.md
│   └── terraform-standards.md
│
├── .github/
│   └── mcp.json
│
├── rag.py
├── mcp_server.py
├── main.py
├── requirements.txt
└── README.md
```

---

# Current Technology

The project currently uses:

* Python
* Kubernetes Python client
* Amazon EKS
* Kubernetes API
* Helm CLI
* MCP
* GitHub Copilot CLI
* RAG knowledge retrieval
* Git
* GitHub

---

# Installation and Running

## Clone the repository

```bash
git clone git@github.com:amrendrasingh5/ai-devops-agent.git
cd ai-devops-agent
```

## Create and activate the Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Python dependencies

```bash
pip install -r requirements.txt
```

## Verify Kubernetes access

The agent uses the Kubernetes context configured on the local machine.

Check the active context:

```bash
kubectl config current-context
```

Verify that Kubernetes is accessible:

```bash
kubectl get pods
```

The current development environment is intended for non-production Kubernetes/EKS investigation.

## Run the AI DevOps Agent

Start the interactive agent:

```bash
python main.py
```

You can then enter natural-language DevOps questions, for example:

```text
Hey, check why the pod is not running.
```

or:

```text
Check https://example.company.com and investigate if there is any problem.
```

Type `exit` or `quit` to stop the agent.

## GitHub Copilot and MCP

The project also includes an MCP server for read-only DevOps investigation tools.

Start GitHub Copilot CLI with workspace MCP support:

```bash
GITHUB_COPILOT_PROMPT_MODE_WORKSPACE_MCP=true gh copilot
```

The configured MCP tools provide read-only access to:

* Repository files
* Repository search
* Unhealthy Pod discovery
* Pod investigation

---

# Current Scope

The current implementation focuses on:

```text
Read-only investigation
+
Evidence collection
+
RAG knowledge retrieval
+
AI-assisted analysis
+
Human-approved remediation recommendations
```

Production write operations are intentionally outside the current scope.

The architecture is designed so additional evidence sources can be added later, such as:

```text
Flux / GitOps
GitHub repositories
AWS / CloudWatch
Prometheus
Dynatrace
Other observability systems
```

without changing the core principle of evidence-driven investigation.

