---
header:
    image: /assets/images/hd_rxjs.jpg
    alt: "Kubernetes YAML Best Practices"
title: "Your Kubernetes YAML is All Wrong: What Senior Engineers Actually Look For"
date: 2025-08-22
tags:
    - tech
    - kubernetes
    - devops
permalink: /blogs/tech/en/kubernetes-yaml-all-wrong-what-you-are-missing
layout: single
category: tech
---
> "Great minds discuss ideas; average minds discuss events; small minds discuss people." - Eleanor Roosevelt

# Your Kubernetes YAML is All Wrong: What Senior Engineers Actually Look For

![Kubernetes YAML Best Practices](https://upload-images.jianshu.io/upload_images/2380020-4d3d82e983402876.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

I remember my early days as a developer, full of enthusiasm and eager to solve complex problems with the coolest technologies. But in enterprise environments, success isn't just about writing elegant code—it's about building systems that are **reliable, scalable, and secure** while following production-grade best practices.

As seasoned developers, we've all written countless Kubernetes YAML files. But like chess, beginners learn the rules while masters see the entire board. Today, let's dissect what appears to be a simple `Namespace` manifest and explore what "senior-level thinking" really means in production environments.

Here's the YAML we'll analyze:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: open-webui
  labels:
    app: open-webui
    security.policy: restricted
    network.policy: enabled
  annotations:
    description: "Secure Open WebUI deployment with Ollama integration"
    security.level: "high"
    created-by: "kubernetes-admin"
```

---

## 1. Beyond "It Works": The Strategic Value of Metadata

**Junior approach**: Fill in the `name`, slap on an `app: xxx` label, and call it done. Annotations? What are those?

**Senior approach**: Treat metadata as this namespace's **identity card and instruction set**. It's not just for humans—it's consumed by the entire platform ecosystem (CI/CD, policy controllers, monitoring systems, billing systems).

### Key Insights and Best Practices:

#### **Semantic and Consistent Labeling**:
- `app: open-webui`: This is foundational—it identifies the primary application running in this namespace. All related resources (Deployment, Service, ConfigMap) must carry this label for unified operations via `-l app=open-webui`.
- `security.policy: restricted` and `network.policy: enabled`: **This is where it gets interesting!** These aren't random comments—they're communicating with **Policy Controllers** installed in the cluster.
  - Tools like [OPA/Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/) or [Kyverno](https://kyverno.io/) watch for namespaces with `security.policy=restricted` and automatically enforce security policies on all pods (no root users, read-only filesystems, etc.). **This is Policy as Code and GitOps in action.**
  - Similarly, `network.policy=enabled` triggers network policy controllers (Calico, Cilium) to apply default "deny-all" rules, forcing explicit microservice communication declarations. **This is the foundation of Zero Trust networking.**

#### **Contextual and Automation-Ready Annotations**:
- `description`: Provides human context—crucial in complex multi-team environments.
- `security.level: "high"`: Can be consumed by security scanning tools or compliance platforms for automated reporting.
- `created-by: "kubernetes-admin"`: **This is an anti-pattern and a red flag.**
  - **Why it's wrong**: In real enterprise environments, almost no one should directly use `kubernetes-admin`. All operations should go through automation tools (CI/CD runners) or service accounts following the Principle of Least Privilege.
  - **Best practice**: Record the **system** or **service account** that initiated the creation, like `created-by: "gitlab-ci-runner"` or `created-by: "argo-cd"`. This provides clear audit trails. If a human operated it, it should be their personal service account (`user:david-chen`), not a shared super-admin account.

---

## 2. Namespaces as Security Boundaries

**Junior understanding**: Namespaces separate resources—dev, test, prod environments.

**Senior understanding**: Namespaces are the **first and most critical boundary** for multi-tenancy and security isolation. Each namespace should correspond to a microservice or tightly coupled service group.

### Key Insights and Best Practices:

#### **Resource Quotas and Limit Ranges**:
- This manifest doesn't show them, but a "complete" namespace definition never stands alone. **Senior engineers immediately think about the next steps.**
- We must create `ResourceQuota` and `LimitRange` objects bound to this namespace.
- `ResourceQuota`: Limits total CPU, memory, pod count, storage consumption for the entire namespace. Prevents runaway deployments from bringing down the cluster.
- `LimitRange`: Sets default CPU/memory requests and limits for each pod/container, preventing resource contention and scheduling issues when developers forget to set them.

#### **Service Account Permissions**:
- After namespace creation, we never use the `default` service account for pods. We create a dedicated, fine-grained `ServiceAccount` (like `open-webui-sa`) and grant it **minimal necessary permissions** through `Role` and `RoleBinding`. This is Defense in Depth at its core.

---

## 3. GitOps and Infrastructure as Code

**Junior approach**: This YAML might be a template, manually applied with `kubectl apply`.

**Senior approach**: This file is a **declaration of desired system state**—it must be version-controlled, immutable, and applied through automated processes.

### Key Insights and Best Practices:

#### **It's Part of the Codebase**:
- This namespace manifest should live alongside application code, deployment configs, and policy definitions in a Git repository (`infra-live/production/apps/open-webui/namespace.yaml`).

#### **Driven by Automation**:
- Git commits (usually merge requests) trigger CI/CD pipelines (Jenkins, GitLab CI) or GitOps tools (ArgoCD, Flux) to automatically sync changes to clusters. **Humans should never directly `kubectl apply` to production.**

#### **Code Review Process**:
- Review infrastructure code like business code. When reviewing YAML files, look for: semantic labels/annotations, security policies, resource limits, service account permissions. **A change request might be rejected for a poorly written annotation.**

---

## The Senior Engineer's Mental Framework

Facing this simple YAML, a senior engineer's mind maps out a complete, dynamic picture:

1. **Policy & Governance**: Which cluster-level policies will my labels trigger? Does this meet our security baseline?
2. **Resource Management**: What's this namespace's resource quota? What are the default pod limits?
3. **Network**: Are default network policies deny-all? Which `NetworkPolicy` objects do I need for legitimate traffic?
4. **Identity & Access**: Who/what created this? What identity should pods use? What permissions do they need?
5. **Observability**: What's the monitoring and logging strategy? Will the `app` label be auto-discovered by Prometheus?
6. **Lifecycle**: How is this namespace created, updated, and destroyed? Is the process fully automated and auditable?

## The Bottom Line

In production environments, being "senior" means evolving from a "feature implementer" to a "complex, reliable, secure system operator." You don't just think about "how to do it"—you consider "why do it this way," "how to do it better," and "how to scale it."

The difference between junior and senior isn't just years of experience—it's the depth of systems thinking and the ability to see beyond the immediate code to its broader implications.

**Your YAML files are infrastructure code. Treat them with the same rigor as your application code, and your future self (and your team) will thank you.**