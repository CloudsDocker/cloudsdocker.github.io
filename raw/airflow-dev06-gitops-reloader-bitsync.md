> "换分支是疏散整栋楼，push 代码只是换冰箱里的菜。" — GitOps 老鸟

# Airflow dev06 双项目联调：ArgoCD、Reloader 与 bit-sync 分工

> 系列：数据平台 GitOps 手记 · 场景：Airflow 3 dev06 · 仓库：`airflow-kubernetes` + `mq-airflow`

---

### 1. 🎯 30秒版本

在 MQU 的 Airflow 3 dev 环境里，**一个实例同一时刻只能 sync 一个 `mq-airflow` git 分支**——ConfigMap 里的 `BRANCH` 字段就是开关。两个项目（例如 UAC 与 Ascender）若要在 **同一个 dev06** 上联合测试，需要一条 **集成分支**（类似 org 里已有的 `dev-af3` → `uat-af3` → `prod-af3` 晋升 ladder），并把 dev06 的 `BRANCH` **指向一次**。

部署链路其实是 **两条 CD 管道**，别混：

| 管道 | 仓库 | 触发 | 谁干活 |
|------|------|------|--------|
| **配置 / 换分支** | `airflow-kubernetes` | merge ConfigMap → ArgoCD auto sync | **Reloader** 重启 Pod |
| **DAG 代码更新** | `mq-airflow` | push 到当前 `BRANCH` | **bit-sync** 每 ~120s pull |

**Reloader** = ConfigMap 变了，重启引用它的 Deployment。**bit-sync** = 同一分支上有新 commit，定时 git pull 到 EFS。**ArgoCD 不监控 mq-airflow 分支**，只 sync K8s 清单。

```yaml
BRANCH: "feature/SN-2788-sync-offers-uac-dwh-to-salesforce-ec"
REPO: "github.com/macquarie-it/mq-airflow.git"
INTERVAL: "120"
```

---

### 2. ⚙️ 底层原理

#### 2.1 架构总览

```text
GitHub (mq-airflow)              GitHub (airflow-kubernetes)
       │                                    │
       │ git pull / INTERVAL                  │ ArgoCD watch dev 分支
       ▼                                    ▼
   bit-sync Pod ──写入──► EFS ◄──读取── scheduler / dag-processor / api-server / triggerer
                            ▲
                            │ ConfigMap(BRANCH) 变更
                            │ Stakater Reloader → rolling restart
```

- **EFS** 是交接点：bit-sync **写**，Airflow **读**。
- **ArgoCD Application**（`airflow3-dev06`）配置了 `automated: prune + selfHeal`，merge ConfigMap 后 **无需人工点 Sync**（除非 ArgoCD 本身不健康）。

#### 2.2 集成分支策略（两项目共 dev06）

**适用**：DAG 之间有依赖，必须同一 Airflow 实例端到端测（例如都写 Salesforce EC）。

**步骤**：

1. 从 `dev-af3` 拉 **集成分支**，如 `integration/dev06-uac-ascender-sf-ec`
2. 分别 merge UAC / Ascender 的 feature 分支（PR + CI，解决 `dags/common/`、`configs/` 冲突）
3. **一次性**改 dev06 ConfigMap 的 `BRANCH` + 更新 `AIRFLOW__WEBSERVER__INSTANCE_NAME`
4. merge 到 `airflow-kubernetes` 的 `dev` → ArgoCD sync → Reloader 重启 → bit-sync clone 新分支
5. 日常联调：**只 merge 到集成分支**，不改 ConfigMap

**不适用 / 缺陷**（dev 可接受，不能直接当 prod 模式）：

- 无 branch protection → 集成地狱
- 共享 `dags/common/` 互相踩
- 频繁改 `BRANCH` → Reloader 风暴 + EFS 压力
- 集成分支若无 expiry，会变成「第二个 main」

**替代方案**：若无硬依赖，用 **两个 dev 实例**（dev01–dev06 本即 one branch per slot）——更简单，符合现有 MQU 分配习惯。

#### 2.3 Stakater Reloader 重启谁？

挂载 `airflow-env` ConfigMap 且标注 `reloader.stakater.com/auto: "true"` 的 Deployment：

| Deployment | 重启原因 |
|------------|----------|
| `airflow-bit-sync` | 读 `BRANCH` / `REPO` |
| `airflow-scheduler-deployment` | 启动时加载 `AIRFLOW__*` |
| `airflow-dag-processor-deployment` | DAG parse 状态 / env |
| `airflow-api-server-deployment` | UI + env |
| `airflow-triggerer-deployment` | deferrable tasks env |

**Rolling restart**：api-server 2 副本逐个替换，通常不会全挂，但可能有 ~1–2 分钟窗口。

**换 BRANCH 时间线**（约 1–2 min）：

```text
merge ConfigMap → ArgoCD sync (~30s) → Reloader 检测 → 滚动重启
→ 新 bit-sync clone 新分支 → Airflow 重新 parse DAG
```

#### 2.4 Reloader vs bit-sync（餐厅比喻）

| 角色 | 组件 | 干什么 |
|------|------|--------|
| 备货员 | **bit-sync** | 每 120s 问 GitHub「有新菜吗？」更新 EFS 冷库 |
| 店长 | **Reloader** | Lobby 制度牌（ConfigMap）改了 → 全员重新打卡 |
| 冷库 | **EFS** | 共享 DAG 文件 |
| 厨师 | **Airflow pods** | 从冷库取菜；上班时间才读制度牌 |

**场景对照**：

| 操作 | ArgoCD | Reloader | bit-sync | 等多久 |
|------|--------|----------|----------|--------|
| push `mq-airflow`（同一分支） | ❌ | ❌ | pull | ≤120s |
| 改 ConfigMap `BRANCH` | ✅ | ✅ 全家 | 新 Pod clone | ~1-2min |
| merge 集成分支（不改 BRANCH） | ❌ | ❌ | pull | ≤120s |
| 改 `INSTANCE_NAME` / `INTERVAL` | ✅ | ✅ 全家 | 需新 Pod 读 env | ~1-2min |

#### 2.5 组织已有的分支晋升 ladder

```text
feature/*  →  dev01–dev06（单 squad / 单分支）
          →  dev-af3（CI 集成）
          →  uat-af3
          →  prod-af3
```

dev06 集成分支 = **短生命周期**的「本地 dev-af3」，测稳后应 merge 进 `dev-af3`，并释放 dev06 slot。

#### 2.6 验证命令

```bash
kubectl -n airflow3-dev06 get configmap airflow-env -o yaml | grep BRANCH
kubectl -n airflow3-dev06 get pods
kubectl -n airflow3-dev06 logs deploy/airflow-bit-sync --tail=50
kubectl -n reloader logs deploy/reloader-reloader --tail=30
```

Reloader 日志关键词：`Changes detected in ConfigMap airflow-env` → `Reloading deployment ...`

---

### 3. 🔬 常见追问

**Q: ArgoCD 会自动部署 mq-airflow 的 DAG 吗？**  
A: **不会。** ArgoCD 只 sync `airflow-kubernetes` 里的 K8s 资源。DAG 由 bit-sync 从 `REPO`+`BRANCH` 拉到 EFS。

**Q: 我 push 了 mq-airflow，为什么 UI 没更新？**  
A: 等 **INTERVAL（dev06 为 120s）**；查 bit-sync logs。不是 Reloader / ArgoCD 的锅。

**Q: 改了 BRANCH 还要 push mq-airflow 吗？**  
A: 新分支上要有代码；bit-sync 会在 restart 后 **clone 整个分支**。若分支已在 remote，不必额外 push。

**Q: 为什么改 UI 标题也会重启 scheduler？**  
A: Reloader `auto: true` 是 **粗粒度**：只要 mount 了 `airflow-env` 就重启，不做字段级 diff。

**Q: 两团队联调最少操作是什么？**  
A: `BRANCH` **焊死在集成分支**；之后只 merge `mq-airflow`，**别 ping-pong 改 ConfigMap**。

**Q: 这和生产一样吗？**  
A: **不一样。** 生产走 `prod-af3` 长期分支 + 变更流程；dev06 集成分支是 **sandbox**，要有 expiry 和 merge 回 `dev-af3` 的退出标准。

**Q: Reloader 和 bit-sync 一句话区分？**  
A: bit-sync 问「**这分支有新 commit 吗**」；Reloader 问「**制度牌换了吗，请重新打卡**」。
