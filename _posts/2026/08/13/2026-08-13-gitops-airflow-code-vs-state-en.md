---
title: 'Untangling Airflow GitOps: Code Sync vs. Infrastructure State'
header:
    image: /assets/images/2024/05/17/header.jpg
date: 2026-08-13
tags:
 - kubernetes
 - airflow
 - gitops
 - argocd
permalink: /blogs/tech/en/gitops-airflow-code-vs-state
layout: single
category: tech
---
> "If it hurts, do it more frequently, and bring the pain forward." — Jez Humble

# Untangling Airflow GitOps: Code Sync vs. Infrastructure State

I've watched teams turn a shared Airflow development cluster into a turf war. Team A changes the environment's target Git branch to test their ingestion pipeline. Team B changes it back ten minutes later to test their transformations. The cluster thrashes, pods continuously restart, and no one gets any testing done.

The fundamental mistake here is treating "deploying configuration" and "deploying code" as the same action. They aren't.

In a standard Kubernetes-native Airflow setup using ArgoCD, you are running two completely independent GitOps control loops. Conflating them is why your environment feels fragile.

**TL;DR:** Switching a Git branch requires evacuating the building. Pushing new commits to an active branch is just restocking the fridge.

### The Dual-Pipeline Mental Model

Let's map out exactly how code and state flow into your cluster. If you understand this routing, you understand why changing a branch name behaves differently than updating a DAG.

```text
[ Loop 1: Infrastructure State ]
Infra Repo (Git) -> ArgoCD -> ConfigMap Mutation -> Reloader -> Rolling Restart
                                                                (Cost: High, ~2 min)

[ Loop 2: Runtime Code ]
DAG Repo (Git)   -> git-sync sidecar -> Shared Volume -> Airflow Scheduler Parses File
                                                                (Cost: Low, ~120s)
```

**Loop 1: Infrastructure State (The Evacuation)**
Your infrastructure repository holds Kubernetes manifests. ArgoCD watches this repo. When you change the target `BRANCH` variable in your Airflow ConfigMap, ArgoCD syncs the change. A controller like Stakater Reloader detects the ConfigMap mutation and triggers a rolling restart of all mounted Deployments (Scheduler, Webserver, Triggerer).

This is a heavy operation. API server replicas are replaced one by one. In-flight local tasks might be disrupted. It takes a couple of minutes before the cluster settles.

**Loop 2: Runtime Code (The Restock)**
Your DAG repository holds Python code. A `git-sync` sidecar (or cron pod) runs alongside Airflow, pulling the currently configured branch every two minutes and writing to a shared persistent volume (NFS/EFS). The Airflow scheduler parses the new files on its next loop.

This is a lightweight operation. There are no pod restarts. ArgoCD is entirely oblivious to this process.

### The Integration Branch Pattern

When two teams need to test cross-DAG dependencies on a single instance, ping-ponging the ConfigMap branch is an anti-pattern. Every branch switch triggers Reloader, causing a restart storm and thrashing the shared volume.

Instead, use a short-lived integration branch:

1. Cut an integration branch (e.g., `integration/feature-x`) from your main development trunk.
2. Both teams merge their feature branches into this integration branch, resolving any conflicts in shared configurations locally.
3. Update the infrastructure ConfigMap `BRANCH` target **exactly once**. Let Reloader restart the cluster.
4. For the rest of the testing cycle, teams push commits directly to the integration branch. The `git-sync` sidecar handles the updates seamlessly without disrupting the environment.

This treats the shared instance as a sandbox. Once integration testing is verified, merge the integration branch back to trunk and release the environment slot.

### Honest Tradeoffs

This pattern is effective, but it is not a silver bullet. 

* **Merge conflicts shift left:** You are forcing conflict resolution into the integration branch. Teams have to coordinate on shared files (like common operators) before testing, rather than overwriting each other in the cluster.
* **No branch protection:** Development integration branches usually lack strict PR requirements. An integration branch can turn into a swamp if left alive too long. Put an expiry date on it and delete it when the test concludes.
* **Reloader's blunt instrument:** Reloader triggers on *any* ConfigMap change. If you update a UI title or an unrelated environment variable in the same ConfigMap, you still pay the price of a full rolling restart. It does not do field-level diffing.

### Action Items

Next time your DAGs aren't showing up in the UI, check your mental model before you start restarting pods or complaining about ArgoCD:

* **Did you push a commit to the currently active branch?** Do nothing. Wait your sync interval (e.g., 120 seconds). Check the `git-sync` container logs if it takes longer.
* **Did you change the branch name in the infrastructure repo?** Wait for ArgoCD to sync, then check Reloader's logs (`kubectl logs deploy/reloader-reloader`) for the `Reloading deployment` event to confirm the cluster is cycling.

Stop treating code syncs like infrastructure deployments. Your uptime will thank you.
