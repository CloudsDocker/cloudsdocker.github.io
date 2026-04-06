---
title: Deferrable Operators in Apache Airflow - Free Your Workers
header:
    image: /assets/images/swan.jpg
date: 2026-04-07
tags:
 - airflow
 - data-engineering
 - python
permalink: /blogs/tech/en/deferrable-operators-apache-airflow
layout: single
category: tech
---

> "Don't wait. The time will never be just right." - Napoleon Hill

# Deferrable Operators in Apache Airflow

## Overview

Deferrable operators are a paradigm for running long-running external tasks (such as ECS, EMR, or S3 sensor waits) without occupying an Airflow worker for the entire duration. Instead of blocking a worker thread, the operator **suspends itself**, hands off to a lightweight async process called the **Triggerer**, and only re-engages a worker when the external task completes.

This document covers:
- The history and versioning of the feature
- How it works under the hood
- How it is implemented in this codebase (`ECSOperator`)
- Why it matters for long-running ECS batch jobs

---

## History — When Was It Introduced?

Deferrable operators are **not new to Airflow v3**. They were introduced in **Airflow 2.2 (October 2021)** via [AIP-40: Deferrable Operators](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-40+Deferrable+Operators).

| Airflow Version | What Changed |
|---|---|
| **2.2** | `self.defer()`, `TaskDeferred` exception, `BaseTrigger`, and the `Triggerer` daemon process introduced. First-party providers began shipping deferrable operator variants. |
| **2.3 – 2.6** | Provider ecosystem expanded deferrable support broadly. `deferrable=False` remained the default on most operators — opt-in required. |
| **2.7** | Key operators (including `EcsRunTaskOperator`) switched their **default** to `deferrable=True` in the Amazon provider packages. This became the recommended production pattern. |
| **3.0** | The Triggerer is a first-class production component. The blocking sync path still exists but `deferrable=True` is the expected default for any operator that waits on an external system. |

The `EcsRunTaskOperator` in `apache-airflow-providers-amazon` gained deferrable support in **provider version 6.0.0** (mid-2022), requiring Airflow ≥ 2.2.

---

## The Problem It Solves

In the traditional (non-deferrable) model, a task that runs a 45-minute ECS job occupies a worker thread for the entire 45 minutes:

```
Worker 1  [====== ECS job running (45 min) ======]  (blocked)
Worker 2  [====== ECS job running (45 min) ======]  (blocked)
Worker 3  [====== ECS job running (45 min) ======]  (blocked)
Worker 4  (waiting for a free worker ...)
```

With a large number of concurrent ECS tasks, workers are exhausted. The Airflow scheduler also runs a **zombie detection** process — if a worker is blocked for too long without a heartbeat, the scheduler marks the task as a zombie and kills it, causing **false failures** on perfectly healthy ECS jobs.

With deferrable operators:

```
Worker 1  [submit ECS job] → free immediately
Worker 2  [submit ECS job] → free immediately
Worker 3  [submit ECS job] → free immediately

Triggerer [poll ECS status] [poll ECS status] [poll ECS status] ... (async, lightweight)

Worker 1  [resume: process results]  (re-engaged only when ECS task finishes)
```

A single Triggerer process can manage **thousands of concurrent waits** using asyncio at near-zero CPU cost.

---

## Core Concepts

### 1. `deferrable=True` — the operator flag

Any operator that supports deferrable mode accepts a `deferrable` kwarg. When `True`, the operator's `execute()` method calls `self.defer(...)` at the point where it would normally block and wait.

### 2. `self.defer()` — the suspension mechanism

`self.defer()` raises a special exception called `TaskDeferred`:

```python
# Inside EcsRunTaskOperator.execute() (simplified):
def execute(self, context):
    response = self.client.run_task(...)   # submit ECS task
    self.arn = response["tasks"][0]["taskArn"]

    if self.deferrable:
        self.defer(
            trigger=EcsTaskStateTrigger(task_arn=self.arn, ...),
            method_name="execute_complete",
        )
    # Non-deferrable path: block and wait here
    self._wait_for_task_ended()
```

`TaskDeferred` inherits from `BaseException` (not `AirflowException`), so it passes through any `except Exception` or `except AirflowException` blocks untouched. Airflow's scheduler catches it and registers the trigger.

### 3. `BaseTrigger` — the async poller

A trigger is a small asyncio coroutine that polls an external system and fires an event when done:

```python
class EcsTaskStateTrigger(BaseTrigger):
    async def run(self):
        while True:
            status = await self._get_ecs_task_status()
            if status in ("STOPPED", "FAILED"):
                yield TriggerEvent({"status": status, "arn": self.task_arn})
                return
            await asyncio.sleep(self.waiter_delay)
```

The Triggerer process runs all registered triggers concurrently in a single event loop.

### 4. `execute_complete()` — the resume method

When the trigger fires, Airflow re-schedules the task on a fresh worker and calls the `execute_complete()` method specified in `self.defer(method_name=...)`. This method processes the result:

```python
def execute_complete(self, context, event):
    if event["status"] == "FAILED":
        raise AirflowException(f"ECS task failed: {event}")
    return event["arn"]
```

### 5. The Triggerer process

A new Airflow daemon added in 2.2. It must be running for deferrable operators to work:

```bash
airflow triggerer
```

In MWAA, the Triggerer is managed automatically — no manual setup required.

---

## Full Execution Flow

```
DAG run triggers ECSOperator.execute(context)
       │
       ├── parse network_configuration (string → dict if needed)
       │
       ├── EcsRunTaskOperator.execute(context)
       │         │
       │         ├── call ECS run_task API
       │         ├── self.arn = "arn:aws:ecs:ap-southeast-2:..."
       │         └── raise TaskDeferred(
       │                   trigger=EcsTaskStateTrigger(arn=...),
       │                   method_name="execute_complete"
       │               )
       │
       ├── TaskDeferred is NOT caught by except(AirflowException, WaiterError)
       │   → propagates up to Airflow scheduler
       │
       ├── finally block runs:
       │         ├── arn is set → log CloudWatch URL
       │         └── log Splunk search URL
       │
       └── Worker is RELEASED ✓
       
Triggerer process:
       ├── EcsTaskStateTrigger polls ECS every N seconds (asyncio)
       └── ECS task status = STOPPED
               └── fires TriggerEvent

Airflow scheduler re-queues task on a worker:
       └── ECSOperator.execute_complete(context, event)
                 └── processes result / raises on failure
```

---

## Implementation in This Codebase

### `v3/plugins/operators/ecs.py`

#### `__init__` — deferrable by default

```python
def __init__(self, region_name="ap-southeast-2", **kwargs):
    # Every ECS task defers by default. Pass deferrable=False to opt out
    # (e.g. in integration tests that need synchronous execution).
    kwargs.setdefault("deferrable", True)
    # Airflow v3 uses region_name (AwsBaseOperator); the old 'region' kwarg was removed.
    kwargs.setdefault("region_name", region_name)
    super().__init__(**kwargs)
```

**Why `setdefault` instead of a hard assignment:**  
Callers can still pass `deferrable=False` explicitly to get synchronous behaviour. This is used in integration tests and in any DAG that specifically needs the blocking path.

**The `region` → `region_name` fix:**  
The v2 operator passed `region=` to the parent. Airflow v3's `AwsBaseOperator` renamed this to `region_name`. The old code silently dropped the region on every task construction, falling back to the AWS SDK default (which may not be `ap-southeast-2`). Fixed with `kwargs.setdefault("region_name", region_name)`.

---

#### `execute()` — retry logic is safe for deferrable mode

```python
def execute(self, context):
    if isinstance(self.network_configuration, str):
        self.network_configuration = ast.literal_eval(self.network_configuration)
    try:
        return super().execute(context)
    except (AirflowException, WaiterError) as e:
        # Retry logic for transient ECS failures (network timeout, rate exceeded)
        ...
    finally:
        arn = getattr(self, "arn", None)
        if arn:
            # Log CloudWatch and Splunk URLs for operators
            ...
```

The retry block only catches `AirflowException` and `WaiterError`. Since `TaskDeferred` inherits from `BaseException`, it passes straight through — the retry logic never interferes with the deferrable path.

| Exception type | Raised by | Caught by retry? | Result |
|---|---|---|---|
| `TaskDeferred` | Parent `execute()` when `deferrable=True` | **No** | Propagates to scheduler — task suspends |
| `AirflowException` (retriable) | Network timeout, rate exceeded | Yes | Retried up to `MAX_RETRIES=3` times with exponential backoff |
| `AirflowException` (non-retriable) | Any other ECS failure | Yes | Re-raised immediately, no retry |
| `WaiterError` (retriable) | Boto3 waiter, retriable reason | Yes | Retried |
| `WaiterError` (non-retriable) | Boto3 waiter, other reason | Yes | Re-raised immediately |

---

#### `finally` block — safe `arn` access

**v2 (original):**
```python
finally:
    cloud_watch_url = build_cloud_watch_url(self.task_definition, self.arn)
```

**v3 (fixed):**
```python
finally:
    arn = getattr(self, "arn", None)
    if arn:
        cloud_watch_url = build_cloud_watch_url(self.task_definition, arn)
```

In deferrable mode, `execute()` raises `TaskDeferred` and the `finally` block fires immediately. If the ECS `run_task` API call failed before the ARN was assigned, `self.arn` would not exist. The v2 code would raise `AttributeError` in `finally`, masking the real error. The v3 code guards with `getattr(..., None)`.

In the normal deferrable path, `self.arn` **is** set before `TaskDeferred` is raised (the ECS task was submitted successfully), so CloudWatch and Splunk URLs are logged as expected.

---

## MWAA Considerations

In Amazon Managed Workflows for Apache Airflow (MWAA):

- **Airflow 2.x environments:** The Triggerer process must be explicitly enabled. Check your MWAA environment configuration.
- **Airflow 3.x environments:** The Triggerer is always available as a core component.
- No code changes are needed — `deferrable=True` on the operator is sufficient.
- Worker instance sizing can be reduced because workers no longer block on long-running tasks. The Triggerer is very lightweight (a single small instance handles thousands of concurrent deferred tasks).

---

## Retry Behaviour (Exponential Backoff)

The operator retries on two specific transient ECS errors:

| Error message | Cause | Retry? |
|---|---|---|
| `Timeout waiting for network interface provisioning to complete` | VPC ENI attachment delay | Yes |
| `Rate exceeded` | AWS API rate limiting | Yes |
| Any other message | Task definition error, permissions, etc. | No |

Retry schedule with `retry_delay=30s` (example):

| Attempt | Delay before attempt |
|---|---|
| 1st retry | 30s |
| 2nd retry | 60s |
| 3rd retry (final) | 120s |

After 3 retries the last exception is re-raised and the Airflow task is marked as failed.

---

## Further Reading

- [AIP-40: Deferrable Operators](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-40+Deferrable+Operators) — original design proposal
- [Apache Airflow docs: Deferrable Operators](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/deferring.html)
- [Amazon Provider EcsRunTaskOperator source](https://github.com/apache/airflow/blob/main/providers/src/airflow/providers/amazon/aws/operators/ecs.py)
- [MWAA: Using deferrable operators](https://docs.aws.amazon.com/mwaa/latest/userguide/samples-deferrable-operators.html)
