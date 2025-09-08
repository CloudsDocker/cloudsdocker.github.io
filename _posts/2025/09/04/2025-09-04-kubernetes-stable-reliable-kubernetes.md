---
header:
    image: hd_kerberos.png
title:  从恐慌到掌控：一个K8s高可用架构的演进之路
date: 2025-09-04
tags:
    - tech
permalink: /blogs/tech/en/kubernetes-stable-reliable-kubernetes
layout: single
category: tech
---
> Your time is limited, don't waste it living someone else's life. - Steve Jobs

# **从恐慌到掌控：一个K8s高可用架构的演进之路**

作为一名老工程师，我见过太多因“我觉得没问题”而引发的线上事故。今天，我想通过一个故事，分享一套完整、层层递进的 Kubernetes 高可用架构，从基础的自愈能力，到精细化的流量管控。

故事始于一位充满热情的年轻工程师和一次关键应用的发布。

#### **第一幕：看似稳固的地基 - Deployment 与健康探测**

**场景：** 年轻工程师小李准备发布他的核心应用“信使”（Messenger），他自信满满。

“我部署了5个副本，”小李说，“Kubernetes 的 **Deployment** 会搞定一切。一个 Pod 挂了，它的 **ReplicaSet** 会立刻补上。万无一失。”

他说对了一半。**Deployment** 是K8s应用管理的基石，它通过管理 **ReplicaSet** 来确保 Pod 数量的稳定。ReplicaSet 的核心是一个**调谐循环 (Reconciliation Loop)**，它会持续对比期望状态（比如 `spec.replicas: 5`）与实际状态，并采取行动（创建或删除Pod）使两者一致。

这是一个基础的 `Deployment` 配置：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: messenger
spec:
  replicas: 5 # <-- 期望状态：5个副本
  selector:
    matchLabels:
      app: messenger
  template:
    metadata:
      labels:
        app: messenger
    spec:
      containers:
      - name: messenger-app
        image: my-app:1.0
        ports:
        - containerPort: 8080
```

**转折点：** 我向他提出了一个问题：“在滚动更新期间，新 Pod 启动了，但应用本身可能还在加载缓存、预热连接。这时 `kube-proxy` 把流量转给它，用户会看到什么？”

小李沉默了。他意识到，Pod `Running` 不等于应用 `Ready`。

**技术细节：健康探测 (Probes)**

为了解决这个问题，我们需要向 Kubernetes 提供更深层次的应用健康信息。

1.  **就绪探測 (Readiness Probe):** 这是告诉 Kubernetes“我的应用已准备好接收流量”的信号。`kubelet` 会定期执行探测。如果探测失败，**Endpoint Controller** 会将这个 Pod 的 IP 地址从对应 Service 的后端列表中移除。流量将不再转发给它，直到它下一次探测成功。这在发布期间至关重要，能确保零停机。

2.  **存活探測 (Liveness Probe):** 这是告诉 Kubernetes“我的应用还活着”的信号。如果应用发生死锁或内部崩溃，它可能仍在运行但无法处理请求。当存活探测失败时，`kubelet` 会杀死这个 Pod，然后 `ReplicaSet` 会创建一个新的来替代它，实现应用的自动修复。

在 Deployment 中加入探针配置：

```yaml
# ... spec.template.spec.containers ...
      - name: messenger-app
        image: my-app:1.0
        readinessProbe: # <-- 就绪探测
          httpGet:
            path: /health/ready # 应用需要提供一个健康检查端点
            port: 8080
          initialDelaySeconds: 15 # Pod启动后15秒开始探测
          periodSeconds: 5      # 每5秒探测一次
        livenessProbe: # <-- 存活探测
          httpGet:
            path: /health/alive
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

**小结：** 仅有副本数是不够的。必须通过健康探针，让 Kubernetes 理解应用的内部状态，才能实现真正的自愈和零停机发布。

-----

#### **第二幕：应对计划内风暴 - PDB 的契约精神**

**场景：** 运维团队发来通知，计划在周末对集群进行节点维护，需要依次排空（drain）节点。

小李感到不安：“如果运维同时排空了我们好几个 Pod 所在的节点，服务不就中断了吗？”

**转折点：** 我告诉他，我们不能指望口头约定，而是需要与 Kubernetes API Server 签订一份“技术契约”。

**技术细节：PodDisruptionBudget (PDB)**

PDB 是一种保护机制，用于限制在**自愿性中断 (Voluntary Disruptions)** 期间（如节点排空、集群缩容）同时不可用的 Pod 数量。它对硬件故障等**非自愿性中断**无效。

PDB 定义了两种策略，二选一：

  * **`minAvailable`**: 保证最少可用的 Pod 数量（可以是绝对值或百分比）。
  * **`maxUnavailable`**: 限制最大不可用的 Pod 数量（可以是绝对值或百分比）。

当运维执行 `kubectl drain` 时，Kubernetes 会检查该节点上的 Pod 是否受 PDB 保护。如果要驱逐的 Pod 会导致违反 PDB 设定的预算，驱逐操作将被暂停，直到可以安全地继续。

一份为“信使”服务准备的 PDB：

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: messenger-pdb
spec:
  minAvailable: 80% # <-- 核心契约：确保任何时候至少有80%的Pod可用
  selector:
    matchLabels:
      app: messenger # <-- 通过标签选择器，将PDB与上文的Deployment关联
```

**小结：** PDB 是应用所有者和集群管理者之间的重要协议。它确保了集群维护的自动化和安全性，防止善意的运维操作意外导致服务中断。

-----

#### **第三幕：驾驭复杂洋流 - Istio 服务网格**

**场景：** “信使”应用变得越来越复杂，它依赖于十几个下游服务。一个下游服务的性能抖动，通过服务间的直接调用，很容易引发雪崩效应。

小李的方案是在代码中加入复杂的超时、重试和熔断逻辑。但这导致业务代码与网络逻辑高度耦合，难以维护。

**转折点：** 我告诉他，是时候让专业工具做专业的事了。我们需要将这些复杂的网络治理能力从应用中剥离出来，下沉到基础设施层。

**技术细节：服务网格 (Service Mesh) 与 Istio**

服务网格通过在每个 Pod 中注入一个**边车代理 (Sidecar Proxy)** 来拦截应用的所有出入流量。这些代理构成了**数据平面**，由一个统一的**控制平面**进行管理。**Istio** 是目前最主流的服务网格实现。

  * **数据平面 (Envoy Proxy):** Envoy 是一个用 C++ 编写的高性能代理，负责执行具体的流量规则，如路由、负载均衡、熔断、加密等。
  * **控制平面 (Istiod):** Istio 的大脑，用 Go 编写。你通过声明式的 YAML 资源（CRD）告诉 Istiod 你的意图，它会将其翻译成 Envoy 能理解的配置并下发。

**用例：通过 Istio 实现优雅的金丝雀发布 (Canary Release)**

假设我们要发布 `my-app:2.0` 版本，但又担心它有未知 Bug。我们可以先让 10% 的流量进入新版本进行观察。

1.  **定义不同版本的服务子集 (Subset)**
    首先，通过 `DestinationRule` 告诉 Istio，我们的“信使”服务有两个版本，通过 Pod 的 `version` 标签来区分。

    ```yaml
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: messenger
    spec:
      host: messenger # 对应Kubernetes Service的名称
      subsets:
      - name: v1
        labels:
          version: "1.0"
      - name: v2
        labels:
          version: "2.0"
    ```

2.  **定义流量路由规则**
    然后，通过 `VirtualService` 定义具体的路由策略。

    ```yaml
    apiVersion: networking.istio.io/v1beta1
    kind: VirtualService
    metadata:
      name: messenger
    spec:
      hosts:
      - messenger
      http:
      - route:
        - destination:
            host: messenger
            subset: v1
          weight: 90 # <-- 90%的流量流向v1
        - destination:
            host: messenger
            subset: v2
          weight: 10 # <-- 10%的流量流向v2
    ```

部署完这些配置后，Istio 的数据平面（Envoy）会精确地按照 90/10 的比例分发流量。我们可以结合监控系统观察 v2 版本的各项指标（错误率、延迟），如果一切稳定，再逐步将 v2 的权重调整到 100%，完成发布。这个过程对用户完全透明，且风险极低。

**小结：** 服务网格通过将网络控制逻辑与业务逻辑解耦，提供了强大的流量管理、安全和可观测性能力。对于复杂的微服务系统，它是保障高可用的终极武器。

-----

### **总结：高可用的层次化防御体系**

一个真正可靠的系统，不是依赖于某个单一的功能，而是一套纵深防御体系：

  * **基础层 (Deployment):** 提供基础的副本保障和滚动更新能力。
  * **感知层 (Probes):** 通过健康探针，让系统能感知应用的内部状态，实现精细化的自愈和流量控制。
  * **契约层 (PDB):** 在计划性中断期间，保护应用不受外部运维操作的冲击。
  * **治理层 (Service Mesh):** 在微服务架构中，提供强大的流量治理能力，实现金丝雀发布、熔断、限流等高级容错模式。

下一次当你构建或审查一个系统时，不妨用这个分层模型来审视它。你的系统，真的准备好迎接风暴了吗？
