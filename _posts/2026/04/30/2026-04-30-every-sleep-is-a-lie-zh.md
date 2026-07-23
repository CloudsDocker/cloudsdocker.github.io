---
title: 你脚本里的每一个 sleep 都在说谎
header:
    image: /assets/images/hd_kubenetes_bamboo_deployment.png
date: 2026-04-30
tags:
 - bash
 - kubernetes
 - devops
 - shell-scripting
permalink: /blogs/tech/zh/every-sleep-is-a-lie
layout: single
category: tech
---

> "知而不行，只是未知。" —— 王阳明

# 你脚本里的每一个 `sleep` 都在说谎

> *从 `kubectl wait` 到 Windows 路径陷阱 —— 三层修炼，把 Bash 脚本从 Senior 推到 Principal。*

---

## 开篇：王阳明的一句"未知"

王阳明说过一句让我反复琢磨的话：

> **"知而不行，只是未知。"**

我入行二十年，写过几百个部署脚本，调过无数次 CI。在最近一次 code review 里，一个看似平平无奇的 200 行 bash 脚本让我重新认识了这句话。

故事的主角叫 Alex，某数据平台团队新来的高级工程师。前一天刚领到 ThinkPad，对着 README 满怀信心地按下回车，结果一晚上掉进了三个层层叠叠的坑。

到他凌晨找我视频时，他已经修了五次代码、各种姿势重启，**问题反复出现**。我让他把脚本贴出来。

我看了三十秒后告诉他：你这个脚本里有三类**普遍存在**于无数生产部署脚本里的 anti-pattern。我们今晚一个个讲透。

读完这一篇，你会带走三条直觉。每一条都能改变你看脚本、看错误、看默认行为的方式：

- ✅ **`sleep` 是说谎的注释，`kubectl wait` 是会执行的注释**
- ✅ **`set -e` 不够。它是 bash 给你的温柔谎言**
- ✅ **修了代码 ≠ 修了系统。状态机和代码一样需要被维护**

我按这三条对你职业生涯**痛点频率**的排序来讲，而不是按 Alex 撞上它们的时间顺序。第一条你今天就能用，第二条让你的脚本从此不在凌晨炸，第三条是当所有显性问题都修完之后，那个让你头皮发麻的 *"我明明改对了"*。

---

## Chapter 1：`sleep` 是 Bash 里最贵的一行注释

Alex 脚本中段卡了 3 秒，再继续。再后面有一段：

```bash
# wait until namespace created
sleep 3

# ... apply more configs ...

# wait for pods to start
while true; do
    n=$(kubectl get pod | grep -v test- | grep Running | wc -l)
    [ "$n" -ge 5 ] && break
    sleep 2
done
```

我让他停下来，问他这段在干什么。他说："等所有 pod 起来。"

我说："这九行代码同时犯了五个错。"

### 五个 anti-pattern，一个不漏

| # | 病灶 | Why |
|---|---|---|
| 1 | `sleep 3` | **魔法常数**。3 秒在你机子上够，CI 慢机器上不够；快机器上又是浪费。本质是把"我猜"写进脚本。 |
| 2 | `kubectl get \| grep \| grep \| wc -l` | **解析人类输出，不查询 API**。任何列宽变化、状态文案变化都会破。Kubernetes 给了你 structured API，你却在抓屏。 |
| 3 | `>= 5` | **硬编码业务真相**。今天 5 个组件，明天加一个 deployment 还是 5？这数字和真实状态之间没有任何 invariant。新人加一个 deployment，这条 check 就开始撒谎。 |
| 4 | `while true` 没 timeout | **CI 杀手**。pod 永远起不来时，整段 loop 转到 CI runner 的 wall-clock 上限被外部 kill，没有任何诊断信息。 |
| 5 | `set -e` 救不了 pipeline 内部的失败 | （第二章细讲）|

更深层的罪：这九行代码是**用户态 reimplement Kubernetes 已经实现好的 reconcile loop**。Control plane 本来就是一个"看谁还没就绪"的状态机，你不去问它，反而在外面写一个粗糙的克隆版。

### 直觉口诀（背下来）

> **Don't poll, don't parse, don't pick magic numbers. Tell the API what you mean.**

Kubernetes 把"等到 X 满足"建模成了一等公民。你写"我想要什么"，控制器告诉你"什么时候到了"。这就是 *information directionality* 的正确方向：让权威源（API server）告诉你状态，而不是你去屏幕抓字符串猜。

### `kubectl wait` 完整心法

```bash
# 按 condition 名等
kubectl wait --for=condition=Ready pod/foo --timeout=60s
kubectl wait --for=condition=Available deployment --all -n ns --timeout=10m
kubectl wait --for=condition=Complete job/foo -n ns --timeout=10m

# 按 jsonpath 等任意字段（1.23+）—— 几乎所有"等到状态 X"都能这么写
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/ns --timeout=30s
kubectl wait --for=jsonpath='{.status.loadBalancer.ingress[0].ip}' svc/foo

# 按生命周期事件
kubectl wait --for=delete pod/foo --timeout=60s
kubectl wait --for=create deployment/foo                     # 1.31+

# 多 condition 任一满足（1.30+）—— 等可能成功也可能失败的 Job
kubectl wait --for=condition=Complete --for=condition=Failed job/foo
```

`kubectl rollout status` 是另一个独立原语 —— StatefulSet/DaemonSet 没有 `Available` condition，要用 `rollout status`；同时它会流式打印进度，看着安心。

### 替换之后的样子

```bash
WAIT_TIMEOUT="${WAIT_TIMEOUT:-10m}"

kubectl wait --for=jsonpath='{.status.phase}'=Active \
    namespace/airflow --timeout=30s

kubectl rollout status statefulset/postgres -n airflow --timeout="$WAIT_TIMEOUT"

if ! kubectl wait --for=condition=Complete job/db-init \
        -n airflow --timeout="$WAIT_TIMEOUT"; then
    echo "❌ db-init did not complete. Recent logs:"
    kubectl logs -n airflow job/db-init --tail=100 || true
    exit 1
fi

kubectl wait --for=condition=Available deployment --all \
    -n airflow --timeout="$WAIT_TIMEOUT"
```

五个赢回来的设计点：

1. **没有魔法数字**。再没有 `>= 5` 这种业务真相硬编码。
2. **不抓屏**。直接问 API。
3. **有边界**。`--timeout` 让失败可观测，不再永生。
4. **失败有现场**。db-init 挂了自动 dump 最后 100 行日志。**失败的脚本必须比成功的脚本输出更多信息**。这是 on-call 工作里 ROI 最高的一条习惯。
5. **向前兼容**。`deployment --all` 让脚本对资源数量变化免疫 —— ops 脚本里的 Open/Closed Principle。

### 适用范围远不止 Kubernetes

任何看到 `sleep N` 紧跟在这些命令后面的，立刻当 race condition 处理：

```
sleep N  +  kubectl apply
sleep N  +  helm install
sleep N  +  docker run
sleep N  +  terraform apply
sleep N  +  aws cloudformation deploy
sleep N  +  systemctl start
```

这些工具几乎都有自己的 `wait` / `--wait` / `rollout status` 原语。**用户态 polling 永远是次优解**。

### 一句话哲学

> **`sleep` 是说谎的注释。`kubectl wait` 是会执行的注释。**

`sleep N` 自我说明的语义是 *"我猜需要等这么久"* —— 它是一种被代码假装成解决方案的注释。每次看到它出现在生产部署脚本里，**99% 是一个 race condition 等着在最不方便的时候被引爆**。

---

## Chapter 2：`set -e` 是 Bash 给你的温柔谎言

Alex 的脚本顶部那一行：

```bash
set -e
```

我让他打开新的 shell，跑这三行：

```bash
set -e
false | true
echo "我居然还在跑"
```

打印了 *"我居然还在跑"*。Alex 的表情 —— 你能想象。

### 为什么 `set -e` 看不到 pipe 里的失败

`a | b` 这个管道，bash 默认的退出码 = `b` 的退出码。`a` 失败了？无所谓。

应用到第一章那条被替换掉的代码：

```bash
kubectl get pod | grep -v test- | grep Running | wc -l
```

如果 `kubectl get pod` 因为 cluster auth 过期挂了：

1. `kubectl` 输出空 + 错误到 stderr，exit 1
2. `grep -v test-` 收到空 stdin → 无匹配 → exit 1（grep 没匹配也是 exit 1！）
3. `grep Running` 同上
4. `wc -l` 收到空 → 输出 `0`，exit 0
5. 整条管道 exit 0，**`set -e` 完全失效**

下游的 `[ $n -ge 5 ]` 看到 `0`，永远不满足，`while true` 转到天荒地老。

**两个 bug 互相抵消，错觉是脚本工作正常**。这是生产脚本里最常见的死法之一。

### Strict Mode 三件套

```bash
set -euo pipefail
```

| Flag | 修补的默认缺陷 |
|---|---|
| `-e` | 命令失败后不要继续往下跑 |
| `-u` | `$FOO` 没定义时不要当空字符串（防 `rm -rf "$DIR/$SUBDIR"` 在 `SUBDIR` 拼错时变成 `rm -rf "$DIR/"` 这种灾难）|
| `-o pipefail` | 管道任一段失败 → 整个管道失败 |

Aaron Maxwell 把这三件套命名为 **"Bash Unofficial Strict Mode"**。它不是花活，是修补 bash 三十年前一些为了向后兼容而做的"过度宽容"决策。每一个 flag 都对应**默认行为里的一个具体设计缺陷**：

| 默认 | 缺陷 | 修补 |
|---|---|---|
| 命令失败 → 继续往下跑 | 错误被悄悄吞掉 | `-e` |
| `$FOO` 没定义 → 当空字符串 | 拼错变量名变成静默炸弹 | `-u` |
| `a \| b` 的退出码只看 `b` | 管道前段失败被静默 | `pipefail` |

### `set -e` 的盲区（面试拿分点）

加了 strict mode，bash 也不是真严格。Principal 必须背下来这些**例外**：

| 场景 | `set -e` 触发吗？ | 修补 |
|---|---|---|
| `cmd \|\| true` | ❌ 不触发（这是显式忽略） | —— |
| `if cmd; then ...` 里的 `cmd` | ❌ 不触发 | —— |
| `cmd && other` 链中除最后一个 | ❌ 不触发 | —— |
| **命令替换 `$(cmd)` 失败** | ❌ **不触发！** | `shopt -s inherit_errexit` |
| 函数错误，被 `f \|\| handle` 调用 | ❌ 不触发 | `inherit_errexit` |

最阴险的就是命令替换那条：

```bash
set -e
DIR=$(this_command_does_not_exist)   # 失败了，但 set -e 不管
echo "DIR=[$DIR]"                      # 仍然执行，DIR 是空字符串
rm -rf "$DIR/cache"                    # 💀 rm -rf "/cache"
```

任何认真的生产 bash 脚本，闭环最小集：

```bash
set -euo pipefail
shopt -s inherit_errexit
```

### `IFS=$'\n\t'` 要不要加？

经典 Maxwell 版还有这一行，用来防止 `for x in $UNQUOTED` 的 word splitting。**我倾向不加**。它解决的问题是"你忘了加引号"，但你的代码本来就该用引号 + 数组。每加一行 boilerplate 都要赚到自己的位置 —— 这是 Parnas 的另一面：**代码的复杂度也是一种成本，哪怕是"最佳实践"的复杂度**。

### 上 `trap` 给失败留现场

`set -e` 只是"挂了就退出"，**不告诉你死在哪一行**。一行 `trap` 让脚本失败时打印命令位置：

```bash
trap 'echo "❌ failed at line $LINENO: $BASH_COMMAND" >&2' ERR
```

CI 部署脚本里这条**必备**。出事了能直接告诉值班的人是哪一行炸的，而不是让他对着 100 行输出做考古。

### 一句话哲学

> **默认行为是历史包袱。新代码要主动开严。**

Bash 的默认行为是为了和 1989 年的脚本兼容设计的，不是为了你 2026 年的生产脚本。strict mode 不是可选项，**是文明社会的最低基线**。

---

## Chapter 3：当所有显性问题都修完之后 —— Windows 路径与"隐形状态"

到这里 Alex 已经修好了 strict mode、把所有 sleep + grep 换成 `kubectl wait`。脚本理论上无懈可击。

他重跑。15 秒后吐出这一行：

```
❌  Exiting due to GUEST_PROVISION:
    config: '\Program Files\Git\host' container path must be absolute
```

Alex 愣住了。**`\Program Files\Git\host` 是什么鬼？我没有写过这个路径啊。**

他翻遍脚本，确认自己只传了 `--mount-string="$ROOT_DIR:/host"`。`/host` 怎么会变成 `\Program Files\Git\host`？

如果你也遇到过类似 *"我明明没写这个，它怎么会出现"* 的诡异错误，下面这一节就是为你准备的。

### 第一性原理：Shell 不是透明的

我们都习惯把 shell 当成 *"用户和程序之间的玻璃"*：你输什么，程序看到什么。

**这是一个深远的误解。**

Git Bash 不是 Linux 的 bash。它跑在 MSYS2 运行时上 —— 一层专门为 *"让 POSIX 风格的命令行工具能调用 Win32 原生程序"* 而设计的翻译层。它的好心办坏事如下：

```
你写的字符串                bash 变量展开            ⚠️ MSYS 路径转换层               minikube 看到的
─────────────             ─────────────           ─────────────────────         ───────────────
"$ROOT_DIR:/host"   ──►  /c/Users/.../proj   ──►  C:\Users\...\proj         ──►  source 正确 ✓
                            :/host                    :\Program Files\Git\host        dest 错误  ✗
                                                       ▲
                                                       │
                                MSYS 看到 `/host` —— 一个以 `/` 开头的 POSIX 路径，
                                就好心地把它替换成 Win32 路径，
                                替换的"根"用的是 MSYS 安装目录 = `C:\Program Files\Git`
```

MSYS 的 heuristic 是按 **字符串外形** 工作的：

```
/foo            →  <MSYS_ROOT>\foo
/c/Users/x      →  C:\Users\x
//foo           →  /foo            (开头双斜杠 = 不要碰我)
a:/foo          →  按 `:` 切两半，每半都转
```

它**不知道** `/host` 在你脑子里的含义是 *"VM 里的挂载点"*。它只看到一个 `/` 开头的字符串。

> **语义在你心里，语法在工具手里。**

这就是 **信息单向性 (Information Directionality)** —— 信息每穿过一个上下文边界，都会被那一层按"自己以为对"的方式改写。从 host 到 guest、从 frontend 到 backend、从 ORM 到 SQL，无一例外。

### Principal 的解法

不是 Stack Overflow 上常见的 `//host` 这种"撞大运"魔法（双斜杠这个魔法字符串，三个月后没人记得为什么是双斜杠 —— 这是**代码考古学陷阱**），而是显式声明每一层的责任：

```bash
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        HOST_MOUNT_SRC="$(cygpath -m "$ROOT_DIR")"
        NO_PATHCONV="MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL=*"
        ;;
    *)
        HOST_MOUNT_SRC="$ROOT_DIR"
        NO_PATHCONV=""
        ;;
esac

# shellcheck disable=SC2086
env $NO_PATHCONV minikube start \
    --mount --mount-string="${HOST_MOUNT_SRC}:/host" \
    -p platform-minikube
```

四个设计选择，每个都有理由：

| 选择 | 理由 |
|---|---|
| `case "$(uname -s)"` | **知人论世**。脚本要先知道自己跑在谁的 shell 上。Linux/macOS 不需要这套，分支隔离，零干扰。 |
| `cygpath -m` | **显式翻译胜于隐式假设**。`-m` 输出 `C:/Users/...`（mixed slash），是 Docker、Java、几乎所有 CLI 都认的格式。 |
| `MSYS_NO_PATHCONV=1` 用 `env` 前缀 | **作用域最小化**（Parnas 信息隐藏 1972）。这个 quirk 只在调用 minikube 这一刻有意义，不应该污染整个脚本。 |
| 注释解释 *为什么* 不解释 *是什么* | 代码只说 *what*，注释要说 *why*。三年后的同事第一眼就懂"为什么不能去掉这个 case 分支"。 |

Alex 改完保存，重新运行。

终端打出：

```
Mounting C:/Users/.../proj to /host in Minikube VM
✨  Using the docker driver based on existing profile
🤦  StartHost failed: config: '\Program Files\Git\host' container path must be absolute
```

**Alex 直接懵了。** "我明明改对了，怎么还是这个错？"

这就是这个故事最后一个、也是最值钱的一节。

### 修代码 ≠ 修系统

Alex 看到的第一行是我们脚本里的 `echo`，已经打出 `C:/Users/...` —— 我们的修复**没问题**。

但第二行是关键：

```
✨  Using the docker driver based on existing profile
```

minikube 在告诉你：*"我没用你这次传的参数，我从磁盘上的 profile 里读了一份。"*

#### 持久化状态：CLI 工具的隐藏维度

minikube 第一次启动时，会把所有 `--mount-string`、`--cpus`、`--memory` 等参数**写进磁盘**：

```
~/.minikube/profiles/<profile-name>/config.json
```

之后每一次 `minikube start`：

| 你以为发生的 | 实际发生的 |
|---|---|
| 用我命令行的最新参数重启 | 读 profile 里的旧参数，**resume** |

这意味着：**当你的第一次 start 失败一半（mount 报错），minikube 已经把那个错的 mount-string 持久化了**。从此你怎么改脚本它都不看，永远从磁盘那个污染过的 config 里拿。

minikube 自己的提示信息已经把这事说明白了：

> *Running "minikube delete -p <profile>" may fix it*

它在**官方承认**：profile 状态污染了，得重置。

#### 修代码 vs 修系统：一个二维矩阵

```
                        State on disk (~/.minikube/profiles/...)
                        ─────────────────────────────────────────────
                        │   clean                       polluted
        OLD code (bug)  │   creates pollution           buggy + cached
                        │   on first run                
                        │
        NEW code (fix)  │   ✅ works first time         ❌ resume reads
                        │                                old polluted state
                        │                                ◄── Alex 在这里
                        ─────────────────────────────────────────────
```

**修代码只能让你纵向移动一格。** 横向那一格 —— 把已经污染的状态清掉 —— 是另一个动作。

口诀：

> **`git pull` 不能给煎熟的鸡蛋退煎。**
>
> 修代码 ≠ 修系统。状态和代码同样需要被维护。

#### 这是一个普适模式

这个坑**不是 minikube 独有的**。任何 CLI 只要词典里有这些词，都有同样的二维空间：

| 工具 | 隐藏状态 |
|---|---|
| `docker compose` | named volumes、网络、容器名 |
| `terraform` | `terraform.tfstate` 文件 |
| `kubectl` | `~/.kube/config` 的 contexts |
| `helm` | cluster 内 `helm.sh/release.v1.<name>` Secret |
| `gcloud config configurations` | `~/.config/gcloud/` |
| `aws configure --profile` | `~/.aws/credentials` 和 `config` |
| Conda / venv | `~/.conda/envs/<name>` |
| npm / pip lockfiles | `package-lock.json`, `poetry.lock` |
| Git submodules | `.git/modules/` |

**第一性原则**：凡是命令行工具用了这几个词 —— *profile / workspace / context / project / environment / release* —— 就一定有一份你看不见的状态机在磁盘上活着。修了代码不重置状态，等于换了油不换油底壳。

#### Principal 的工程化处理

让脚本**自带逃生口**，比让团队记忆"咒语"强一百倍：

```bash
CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean | --force) CLEAN=1 ;;
    esac
done

if [[ "$CLEAN" -eq 1 ]]; then
    echo "🧹 --clean: deleting any existing profile to clear stale config..."
    minikube delete -p platform-minikube || true
fi
```

之后 README 里写一行：

> *如果遇到 `Using the docker driver based on existing profile` 后报奇怪错误，加 `--clean` 重跑。*

部落知识 → 工程产物。这是 Principal 和 Senior 的分界线之一。

---

## 结语：三张地图

回到王阳明那句话：

> **"知而不行，只是未知。"**

Alex 这一晚学到的，不是三个 bug fix。是三种看世界的方式：

| 直觉 | 含义 | 适用范围 |
|---|---|---|
| **声明胜于命令式** | 当系统给了你一等公民的"等到 X 满足"原语，不要自己写 polling 循环。 | Kubernetes / Docker / Helm / Terraform / 任何带 `wait` 概念的工具 |
| **默认行为是历史包袱** | `set -e` 不够，`-u` 不够，`pipefail` 不够，`inherit_errexit` 才够。默认行为往往为兼容老脚本而留情，新代码要主动开严。 | 任何 shell 脚本、任何配置默认值、任何"开箱即用"的框架 |
| **修代码 ≠ 修系统** | 持久化状态是独立维度，需要独立的清理动作；脚本里要有 `--clean` 逃生口。 | 任何带 profile/context/workspace 概念的 CLI 和 IaC 工具 |

这三个直觉**不是关于 Kubernetes、bash 或 minikube**。

它们是关于 *声明式 vs 命令式*、*默认值的政治*、*状态机 vs 代码* 这些跨工具、跨语言的元结构。你写过的每一段 docker、terraform、kubectl、ansible、helm、git、gcloud 代码，都是这三张地图的某个角落。

---

## 立刻可以做的事

1. **审计你手上一个最常跑的部署脚本**。找出三类 smell：
   - 任何 `sleep N` 后面跟着 *"等待 X 就绪"* 的注释 → 换成 `kubectl wait` / `--wait` / `rollout status`
   - 任何 `... | grep ... | wc -l` 后面跟着的数值比较 → 用 `kubectl wait` 或 jsonpath 查询
   - 任何 `set -e` 没有配 `-u`、`pipefail`、`inherit_errexit` 的 → 一次性升到 strict mode

2. **把任何一个有 profile / context / state 概念的 CLI 工具调用，加上 `--clean` 或等价开关**。文档里写清楚：什么时候用、为什么要用。

3. **在团队 README 里加一句**："凡是 'Using existing X' 后面接错误，先尝试 reset/clean。"

部落知识写成代码或文档，是 Principal 最常做的事。

---

## 预告

下一篇我会写 **"为什么你的 Terraform `apply` 在第二次执行时不再做你以为的事"** —— 同样是 *修代码 ≠ 修系统* 这条主线，但发生在 IaC 的世界里，state drift 和 lock 文件之间的博弈让这个问题更阴险。

如果你觉得这一篇值，欢迎转给那个昨晚被部署脚本的 race condition 折磨到凌晨两点的同事。

---

> *Bug 不在终端里，在你和你工具之间的那张地图上。*
