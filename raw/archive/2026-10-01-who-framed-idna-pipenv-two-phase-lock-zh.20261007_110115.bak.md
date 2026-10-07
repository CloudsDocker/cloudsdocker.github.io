---
title: "pipenv 甩锅记：ResolutionImpossible 说是 idna 的错，真凶却藏在「两段式锁定」里"
date: 2026-10-01
categories: [engineering, python, debugging]
tags: [pipenv, pip, dependency-resolution, idna, PEP592, ResolutionImpossible]
---

# pipenv 甩锅记：ResolutionImpossible 说是 idna 的错，真凶却藏在「两段式锁定」里

上一篇《[pip 装不上的那一晚](/)》里，我们翻过了 Ubuntu 24.04 的两堵墙，终于让 `pipenv` 跑了起来。本以为收工在即，结果真正的好戏才开场——`pipenv lock` 抛出一个 `ResolutionImpossible`，一口咬定是 `idna==3.7` 的错。

我顺着它的指控查了一路：换对 Python 版本、把一个被 yank 的包升级……错误岿然不动。直到我把同一组依赖丢给 `pip` 直接解析——**它一次就成功了**。于是问题变成了一个更有意思的悬案：**同样的输入，为什么 pip 能解、pipenv 不能？而且 pipenv 指认的「真凶」,根本是被冤枉的。**

这篇就复盘这场甩锅案，把大多数人从没注意过的 `pipenv` 两段式锁定机制挖出来。

---

### 1. 🎯 30秒版本

- `pipenv lock` 报 `ResolutionImpossible`，说「The user requested idna==3.7」。但把**完全相同**的依赖集丢给 `pip install --dry-run`，**解析成功**，idna 3.7 装得好好的。
- 两个工具对同一输入给出不同结论 → 问题不在依赖数学，而在**解析过程**。
- 真相：**pipenv 分两段锁定**——先锁 `[packages]`（默认），再锁「默认 + `[dev-packages]`」。
  - 默认包里 `aiobotocore → aiohttp → yarl → idna(>=2.0)` 悄悄把 idna 拉了进来，第一段把它锁到**最新的 3.20**。
  - 第二段遇到 `[dev-packages]` 里硬钉的 `idna==3.7`，`3.20 ≠ 3.7`，两段无法调和 → 爆炸。
- `pip` 是**一次性**解析默认+dev，所以直接选了同时满足所有约束的 3.7，根本不会撞上这个坑。
- 一路上的两个「伪线索」：Python 版本不对（3.12 vs 3.10）、`requests==2.32.0` 被 yank——都不是真凶。**我一度笃定是 yank 的 requests，升级后照样失败，被现实打脸。**
- 修法：把 `idna = "3.7"` 放宽成 `idna = ">=3.7"`，两段都收敛到 3.20，CVE 底线还在。但这是**安全 pin 决策**,要过 owner,不能擅自改。

---

### 2. ⚙️ 底层原理

#### 案发现场

仓库 `Pipfile` 的关键几行：

```toml
[dev-packages]
requests = "2.32.0"
idna = "3.7"

[requires]
python_version = "3.10"
```

`pipenv lock` 的输出（精简后）：

```text
Locking dependencies...
Resolving dependencies...
✔ Success!                          ← 第一段：锁 [packages]
Locking dependencies...
Resolving dependencies...
✘ Locking Failed!                   ← 第二段：锁 [dev-packages]
ERROR: ResolutionImpossible
The conflict is caused by:
    The user requested idna==3.7
```

#### 第一刀：把输出分层，别把 traceback 当回事

排障第一反射：**先给输出分类，再读**。

| 输出块 | 是什么 | 判定 |
|---|---|---|
| `Warning: Pipfile requires 3.10, but you are using 3.12.3` | 解释器不对 | 伪线索 A |
| `✘ Locking Failed! … ResolutionImpossible … idna==3.7` | 真正的失败 | 信号 |
| `Traceback … lock.py … resolver.py … raise exc` | pipenv 自己的调用栈 | **纯噪音，忽略** |

那串 `lock.py:408 → resolver.py:2061` 的 traceback 什么用都没有——它只是 pipenv 把错误重新抛出来路过的栈。信号是它**上面**的 `ResolutionImpossible` 块。

#### 两个被证伪的假设（排障的真实样子）

**伪线索 A：解释器版本。** venv 是拿系统 3.12 建的，而 Pipfile 钉死 3.10。换成 `docker python:3.10-slim` 重锁——警告没了，**但 idna 错误还在**。排除。

**伪线索 B：被 yank 的 requests。** `pip --dry-run` 里闪过一条：

```text
WARNING: The candidate selected ... is a yanked version: 'requests' (2.32.0)
Reason: Yanked due to conflicts with CVE-2024-35195 mitigation
```

> **什么是 yank（PEP 592）**：维护者给某个版本打上「别自动选我」的标记，但文件还在、**显式 `==` 钉住时仍可安装**。这正是 pip 和 pipenv 容易产生分歧的经典地带。

我当时很笃定：「就是它了」。把 requests 升到非 yank 的 `2.32.5`——**pipenv 照样失败**。打脸。这里的教训值得单列（见追问链 Q4）。

#### 决定性对照：pip 成功，pipenv 失败

把**同一组钉死的依赖**丢给 pip 直接解：

```bash
pip install --dry-run --index-url <nexus> \
  pysftp python-gnupg cryptography==44.0.1 urllib3==1.26.19 paramiko==3.4.0 \
  botocore aiobotocore boto3 pytest==7.4.0 moto==4.2.14 ... \
  requests==2.32.5 "idna==3.7" pytest-sftpserver==1.3.0
```

结果：**`Would install ... idna-3.7 ... requests-2.32.5 ...`——成功。** 这就证明：**根本不存在真实的版本冲突**，idna 3.7 跟整组依赖完全兼容。既然 pip 能解、pipenv 不能，差别只能在**解析过程**。

#### 真凶：pipenv 的两段式锁定

注意 pipenv 输出里的「✔ 成功」后面跟着「✘ 失败」——那是**两个阶段**，而 pip 从不这么干：

1. **第一段：只锁 `[packages]`（默认）→ 成功。** 关键在于，默认包会**透传**拉进 idna：`aiobotocore → aiohttp → yarl → idna(>=2.0)`。默认段里没人钉 idna，于是它被锁到**最新版**。
2. **第二段：默认 + `[dev-packages]` → 失败。** 此时 dev 里的硬钉 `idna==3.7` 必须和第一段已经选定的新 idna 共存。pipenv 要求跨段**同包同版本**，于是 `idna==3.7`（dev）对上 `idna==<最新>`（默认透传）→ 无解。

一条命令坐实它——只解默认包，看 idna 被锁到几：

```bash
pip install --dry-run --index-url <nexus> \
  pysftp python-gnupg cryptography==44.0.1 urllib3==1.26.19 paramiko==3.4.0 \
  botocore aiobotocore boto3 2>&1 | grep -i idna
```

输出：

```text
Collecting idna>=2.0            ← yarl 的约束
  Downloading idna-3.20         ← 第一段选了最新：3.20
```

**3.20 vs 3.7，谜底揭晓。** pip 一次性解析默认+dev，直接给全组选了同时满足所有 `>=` 的 3.7，所以从不撞坑；pipenv 分两段，第一段先把 idna 锁到 3.20，第二段再也回不去 3.7。

#### 修法：放宽到 `>=3.7`

```toml
idna = "3.7"     →     idna = ">=3.7"
```

这样第二段就能接受第一段选的 3.20，两段收敛到同一个版本，锁成功。而 `idna==3.7` 的初衷本是 **CVE-2024-3651**（`idna.encode()` 的 DoS，3.7 修复）的下限;放宽成 `>=3.7` 后拿到的是 3.20 ——**不但没削弱，反而更安全**。

> ⚠️ 但这是**安全相关的 pin 决策**，不是机械改动。为什么当初只在 dev 段钉 3.7?意图是否仅为 CVE 下限?这些要 repo owner 拍板，不能为了让自己的 PR 变绿就擅自松绑。

#### 实战复现：换个 repo,一条探针照穿整条连环坑

上面那套「只解默认段 → 看它把透传依赖锁到几 → 对比 dev 段的死 pin」,不是一次性的侦探手法,而是一个**可复用的通用流程**。换到另一个仓库 `edr-cba-iq`,`pipenv lock` 第二段又爆了,这次点名的是 `certifi`:

```text
✘ Locking Failed!
ERROR: ResolutionImpossible
The conflict is caused by:
    The user requested certifi==2024.7.4
```

不急着去搬 certifi——先跑**同一条探针**(只解默认包),一次把所有将要冲突的 pin 全照出来:

```bash
docker run --rm python:3.10-slim bash -lc '
  pip install --dry-run --index-url <nexus> \
    pycryptodome boto3 urllib3==1.26.19 moto==4.2.14 2>&1 | grep -iE "certifi|idna"'
```

输出:

```text
Collecting certifi>=2023.5.7
  Downloading certifi-2026.7.22        ← 默认段(moto→requests)顶到最新
Collecting idna<4,>=2.5
  Downloading idna-3.20
Would install ... cryptography-50.0.2 ... requests-2.34.2 ...
```

把它跟 `[dev-packages]` 里的死 pin 逐行对一下,**整条连环坑一次现形**:

| 包 | dev 段死钉 | 默认段透传顶到 | 结果 |
|---|---|---|---|
| `certifi` | `2024.7.4` | **2026.7.22** | 冲突(当前报错) |
| `idna` | `3.7` | **3.20** | 下一个会爆 |
| `cryptography` | `43.0.1` | **50.0.2** | 也会爆(跨度最大) |
| `requests` | `2.32.0`(被 yank) | **2.34.2** | 冲突 + yank 双重 |

**这就是「读懂机制」相对「读懂报错」的回报**:报错一次只甩锅一个 `certifi`,你要是一个个去锁、一个个等它爆,得来回四趟;而默认段探针 + `grep`,一遍就把 4 个 pin 全照出来了。定位清楚后,修法还是那一招——把这些过期 `==` 统一放宽成 `>=` 下限,让两段收敛到默认段已经在用的最新版,同时保住 CVE 底线:

```toml
[dev-packages]
cryptography = ">=43.0.1"
requests = ">=2.32.4"     # 放宽 + 避开已被 yank 的 2.32.0/2.32.1
idna = ">=3.7"
certifi = ">=2024.7.4"
```

> 📌 一个值得多看一眼的信号:`cryptography 43→50` 跨了 7 个大版本。certifi/idna/requests 都是小步,但 cryptography 是编译型安全库,大版本间 API/行为可能变——虽然它在 dev 段(只影响测试),放宽前仍值得跟 owner 单独点一句。**同样是「放宽 pin」,风险不是一刀切的,要按包的性质分级看待。**

#### 放大一层:pip / pipenv / poetry 的底层差异

这个坑的根,不在依赖本身,而在**工具用什么策略去解依赖**。把三个工具摆一起看,一眼就明白为什么同一组 pin,有的工具炸、有的不炸:

| 工具 | 角色 | 依赖分组 | 解析方式 | 会踩「两段式」坑吗 |
|---|---|---|---|---|
| **pip** | 纯安装器 + 解析器 | 无(你喂什么解什么) | **单遍**,一次把所有需求一起解 | 不会 |
| **pipenv** | Pipfile 封装 pip | `[packages]` / `[dev-packages]` | **两段**:先锁默认,再锁「默认+dev」并要求跨段同版本 | **会(本案根因)** |
| **poetry** | 全家桶(管理+解析+打包) | `main` + `group.<name>` | **单遍**,所有 group 一起解进同一个 lock | 不会 |

一句话串起来:

- **pip** 本身没有「lock 文件」「dev/prod 分组」这些概念。你给它一串需求,它用回溯解析器(2020 年起)**一次性**找一组同时满足所有约束的版本。所以前面我们拿 pip `--dry-run` 一喂默认+dev,它直接选了满足全组的 `idna 3.7`——从不分段,也就从不撞坑。**pip 是我们的「真值裁判」:它能解,就证明依赖数学本身没问题。**
- **pipenv** 在 pip 之上加了 Pipfile 的两个段,而它的锁是**分两步**走的:先把 `[packages]` 解出来锁定,再把 `[dev-packages]` 叠上去解,并要求**跨段同包同版本**。于是第一段若把某个透传依赖(idna/certifi)锁到了最新,第二段的 dev 死 pin 就再也塞不回去——**「两段式」这个设计本身,就是这个 bug 的制造者**,不是你的依赖有错。
- **poetry** 虽然也分 `main` / `dev` group,但它**一遍就把所有 group 一起解**进一个统一的 `poetry.lock`,每个包全局只选一个同时满足所有 group 的版本。dev group 的 pin 和 main 的透传需求在**同一遍**里被一起协调,不存在「第一段先锁死、第二段搬不动」。所以 `edr-nonstandard-etl` 那 24 个 poetry 子项目,**天然不会**重演 idna/certifi 的连环坑。

`★ Insight ─────────────────────────────────────`
- **同样的依赖数学,解析「策略」不同,结论就不同。** 三个工具面对完全相同的约束集,pip/poetry 单遍能解,pipenv 两段不能解。所以当两个工具对同一输入给出不同结论时,差别一定在**它们怎么搜索**,而不在依赖本身——这也是为什么「拿 pip 当裁判」是戳破 pipenv 误导性报错的最快办法。
- **分组(group)是给人看的,不该变成给解析器的硬墙。** dev/prod 的区分本意是「装不装」,poetry 把它当成最后输出时的过滤器(解的时候一起解);pipenv 却把它当成解析的边界(分两段解),于是一个只想表达「测试时也要这个版本」的 dev pin,意外变成了跨段的硬约束。理解这层,你就知道为什么同一个 `idna==3.7`,挪到 poetry 里就风平浪静。
`─────────────────────────────────────────────────`

---

### 3. 🔬 面试官追问链

**Q1：`ResolutionImpossible` 和 `No matching distribution` 有什么区别?**
前者是「约束互斥」——多个条件无法同时满足（本案）；后者是「索引里根本没这个版本」。pipenv 会把两者都糊成 `ResolutionImpossible`，所以要降到 pip 自己的报错去区分。

**Q2：为什么 pip 能解、pipenv 不能?输入明明一样。**
因为**解析过程不同**。pip 一次性解析所有需求；pipenv 分两段（先默认、再默认+dev），并要求跨段同包同版本。同一组 pin，一次性可解、分两段不可解。工具的「流程」决定了它的「报错」。

**Q3：错误说「The user requested idna==3.7」，为什么说 idna 是被冤枉的?**
因为 pip 证明了 idna 3.7 和整组依赖毫无冲突。pipenv 的「conflict is caused by X」是一句**概括**，不是真相——它指认的是它处理到的那个直接 pin，而真正的矛盾是「第一段把 idna 锁成了 3.20」。当 pipenv 指控的包 pip 装得好好的,就去 pip 的输出里找 `yanked`/真实约束。

**Q4：你一度咬定是被 yank 的 requests,结果错了。教训是什么?**
**靠「动手验证」来确认假设,而不是靠「故事讲得通」。** yank 警告真实存在,听起来也顺理成章,但它在因果上无关。证明它无关的方式,是升级 requests 后再锁一次——然后看着它照样失败。一个听起来很对的假设,在你用它做出的改动没能复现修复之前,都只是假设。

**Q5：这类坑怎么从根上避免?**
**别把 pin 放错段。** `idna==3.7` 钉在 `[dev-packages]` 里,只要没有别的包拉 idna 就相安无事。可一旦某个**默认段**的依赖透传把 idna 拉进来(aiobotocore→aiohttp→yarl),dev 段的孤立 pin 就和默认段的自由选择撞车。**透传依赖不认你的 dev/prod 分界。** 要钉就钉在影响到的那一段,或者干脆用范围而非死版本。

**Q6：换个内网 PyPI 代理,怎么就把老问题炸出来了?**
因为**换索引会改变「可选版本集合」**。公网 pypi.org 什么老版本都在;Nexus 这类带防火墙的代理会 quarantine 某些版本,可选集是 PyPI 的子集。再叠加「最新版一直在往上走(idna 都 3.20 了)」,一个以前能解的死 pin,今天就可能解不动。**你的 PR 没制造问题,它只是把潜伏的 pin 问题照了出来。**

---

**一句话收尾**：`ResolutionImpossible` 指着 idna 喊「就是它」,但 idna 是被冤枉的——真凶是 pipenv 两段式锁定,加上一个钉错段、又恰好被默认依赖透传拉进来的版本 pin。大多数人一看到报错就去搬 idna,搬错了方向。读懂工具**怎么搜索**,比读懂它**报什么错**更值钱。
