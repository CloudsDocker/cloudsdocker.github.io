---
title: "那个从没跑过一次的 CI 检查,给了我们一个假的绿色对勾"
date: 2026-08-04
categories: [engineering, python]
tags: [python, docker, ci-cd, github-actions, testing]
---

> "The first principle is that you must not fool yourself — and you are the easiest person to fool." —— Richard Feynman

---

上一篇写的是那个潜伏五个月的 `_cffi_backend` 事故:构建期 Python 3.11,运行期 3.10,一个数字写在了两个地方,产物悄悄错配,直到一次毫无信息量的格式化 PR 把 21 个镜像一次性带炸。

这一篇不讲那个 bug。这一篇讲**修完那个 bug 之后发生的事**——Alex 把修复合并了,CI 全绿,他松了口气,正准备去写下一张票的时候,停下来问了自己一句:

> "这个绿色对勾,到底证明了什么?"

答案是:几乎什么都没证明。他合并的那个 PR,里面新加的两个 CI 步骤,**一次都没有真正跑过**。

## 30 秒版本

Alex 加了一个新的 CI 步骤,从每个镜像自己的 `Dockerfile` 里推导构建用的 Python 版本,不再写死 `3.11`。PR 只改了 `.github/workflows/build-and-deploy.yml` 这一个文件。合并到 `develop` 后,check 全绿。

他去看了一眼具体是哪些 job 跑了——`Test and build Images` 那一行写着 `skipped`。

因为仓库的 CI 用路径过滤:只有 `images/*` 目录下有改动,才会触发对应镜像的构建矩阵。这次 PR 只碰了 workflow 文件本身,一个镜像目录都没动。新逻辑合并进了主干,但从没被执行过一次。

Alex 后来又做了四轮测试,一步比一步逼近真相,也一步比一步逼近这句话:

**一个"可用"但从没被执行过的安全网,和不存在没有区别。你必须亲手把它逼到跑起来,再看它到底接住了什么、漏掉了什么。**

这篇文章接下来会讲他怎么做的——包括最后揪出的两个真实存在、但当时全公司没人知道的盲区。

读完你会带走:

- **"CI 绿了" 和 "CI 跑过了" 是两件事**——路径过滤会让一段代码永远合并、永远不被执行。
- **拿真实的生产漂移去测试你的检查,比编造场景更有说服力**——但有些盲区,真实场景里根本还没出现过,只能自己动手造一个去撞。
- **一个安全检查的假设本身,可能就是它最大的漏洞**——"abi3 总是安全的"这句话,听起来像常识,其实是错的。

下面按 Alex 实际验证的顺序讲,而不是按"应该怎么做"的教科书顺序——因为他踩的每一个坑,都是下一步测试设计的直接原因。

---

## 1. 🎯 绿色对勾骗了谁

Alex 的第一反应很正常:PR 合并了,check 全绿,该干别的去了。

但他这次多看了一眼 job 列表:

```
Create Application Version   success
Test and build Images        skipped   ← 新逻辑就藏在这里面
Deploy to SIT/STG/PRD        skipped
```

`Test and build Images` 是个 matrix job,包含了新加的两个步骤:从 Dockerfile 推导版本、校验编译产物的 ABI 标签。这个 job 显示 `skipped`,不是 `success`。

原因很简单也很容易被忽略:仓库的 `List modified images` job 是按目录 diff 出"这次改动碰了哪些镜像",PR 只改了 workflow 文件,没有任何 `images/*` 路径变化,于是矩阵直接判定"没有镜像需要构建",整个 job 跳过。

> **普通人的看法**:CI 绿了,说明改动是对的。
> **资深工程师的洞察**:CI 绿了,只说明"跑过的那部分"是对的。先问一句"这次改动到底让哪些 job 真正执行了",再决定要不要信这个绿灯。

| 现象 | 看起来像 | 实际是 |
|---|---|---|
| PR checks 全绿 | 新逻辑验证通过 | 新逻辑所在的 job 被路径过滤跳过,根本没跑 |
| `skipped` | 一种"通过"的变体 | 一次都没执行过 |
| 合并到 `develop` | 代码生效 | 代码进了主干,但触发条件从没被满足过 |

> 路径过滤是为了省 CI 时间存在的,这个设计本身没错。错的是把"这个 job 允许被跳过"和"这次改动不需要被验证"划了等号——一个改的是触发规则,一个改的是新逻辑正不正确,这是两件完全不相关的事。

---

## 2. ⚙️ 逼它真正跑起来:一个用完就扔的 touch commit

发现"从没跑过"之后,Alex 没有去改测试框架,也没有去写单元测试模拟 GitHub Actions 的行为——那样测的是"我以为它会怎么跑",不是"它真的怎么跑"。

他的做法更直接:开一个新分支,对一个真实镜像的 `pyproject.toml` 做一次纯版本号的 touch commit(`0.1.0` → `0.1.1`,没有任何功能改动),让 `List modified images` 认为这个镜像"变了",从而把矩阵里对应的那一个 job 真正跑起来。

```bash
git checkout -b verify-ci-python-version-resolution develop
# fs__qcc__core 依赖 paramiko/cryptography,是仓库里少数真的会产出
# 编译扩展的镜像之一——选它不是随便选的,选一个只有纯 Python 依赖的
# 镜像,新逻辑压根没有东西可测
sed -i '' 's/version = "0.1.0"/version = "0.1.1"/' images/fs__qcc__core/pyproject.toml
git commit -am "touch fs__qcc__core to exercise new CI python-version resolution"
git push
```

选哪个镜像去触发,是这一步真正的技术含量所在——选错了,job 是跑了,但新逻辑没有任何东西可以校验(比如一个纯 boto3 依赖的镜像,根本不会产出任何编译扩展),又是一次"绿灯但没验证任何东西"。

这次真跑起来之后,CI 立刻红了:

```
Building fs__qcc__core against Python 3.11 (derived from Dockerfile base image)
...
ERROR: Package 'edr-common-python' requires a different Python: 3.10.20 not in '<3.12,>=3.11'
```

这不是一个演出来的场景。`fs__qcc__core` 的 `Dockerfile` 当时真的是 `FROM python:3.10-slim`,而它依赖的 `edr-common-python`(一个没锁死版本、直接跟 git HEAD 走的内部包)最新的要求是 `>=3.11,<3.12`。这个漂移是仓库里本来就存在的,新逻辑第一次真正执行,第一次就抓到了一个真实、有机生长出来的问题,报错信息也直接可操作。

> **一句话哲学**:测试一段"检查漂移"的代码,最好的素材不是你编出来的场景,是仓库里本来就有、只是还没被踩到的那个坑。

---

## 3. 🔍 第二次真实测试:边界反过来撞

第一次测试撞见的是"版本太旧"。Alex 想知道另一个方向会怎样——如果有人为了打安全补丁,顺手把某个镜像的 Dockerfile 从 3.11 升到 3.12,新逻辑会不会拦住?

他选了另一个真实存在、依赖 `edr-common-python` 的镜像 `dm_oru`,只改了 Dockerfile 的一行,`pyproject.toml` 一个字都没动:

```diff
- FROM python:3.11-slim
+ FROM python:3.12-slim
```

结果:

```
Building dm_oru against Python 3.12 (derived from Dockerfile base image)
...
ERROR: Package 'edr-common-python' requires a different Python: 3.12.13 not in '<3.12,>=3.11'
```

版本推导本身完全正确——Dockerfile 说 3.12,CI 就真的拿 3.12 去构建。挡住这次升级的,是 `edr-common-python` 自己的版本上限。

这次测试真正的价值在于对比:**旧的 CI(写死 3.11)会怎么处理同样这次升级?** 答案是:完全不会处理——不管 Dockerfile 写的是 3.10、3.11 还是 3.12,旧 CI 永远拿 3.11 去构建、去测试,一次真实的、有风险的基础镜像升级,会在没有任何人验证过依赖是否兼容 3.12 的情况下,直接绿灯上线。新逻辑第一次让"升级基础镜像"这个动作,真正经过了一次它本该经过的校验。

| | 旧 CI(写死 3.11) | 新 CI(从 Dockerfile 推导) |
|---|---|---|
| Dockerfile 升到 3.12 | 构建仍然用 3.11,升级本身**从未被验证** | 构建真的用 3.12,立刻撞见 `edr-common-python` 的版本上限 |
| 反馈时机 | 可能是生产环境的一次 `ModuleNotFoundError` | PR 阶段,一条能直接定位到哪个依赖的报错 |

---

## 4. 🧪 造一个还不存在的攻击:多阶段 Dockerfile

前两次测试用的都是仓库里真实存在的状态。第三次,Alex 主动去找了一个仓库里**目前一个镜像都没有**的模式——多阶段 Dockerfile——因为这是 Docker 里再正常不过的写法,迟早会有人用上,而新逻辑的推导脚本长这样:

```bash
version="$(sed -nE 's|^FROM[[:space:]]+python:([0-9]+\.[0-9]+).*|\1|p' Dockerfile | head -1)"
```

`head -1`——只取文件里**第一条** `FROM python:` 行。单阶段 Dockerfile 里这没问题,因为全文只有一条。多阶段呢?

```dockerfile
FROM python:3.11-slim AS builder   # ← 第一条 FROM,head -1 会抓这个

FROM python:3.10-slim              # ← 最后一条才是真正要发布的镜像
RUN adduser --system --home /edr-python --group edr-python
...
```

Alex 把这个改动推上同一条测试分支。结果是:CI 用 3.11 构建、测试、打包,校验编译产物的那一步拿"期望的 ABI 是 cpython-311"去比对——而产物**确实**是用 3.11 编译的,两边完全对得上。

**绿灯。**

但这个绿灯是假的。真正会被发布出去的镜像,基础层是 `python:3.10-slim`,不是 3.11。校验逻辑用来"验证"的那个期望值,和产生构建产物的版本,来自**同一处错误的推导**——它们永远不可能互相矛盾,因为它们本来就是同一个错。

> **对称性破缺**:这个检查看起来像是"两个独立信号互相印证"(推导出的版本 vs 实际编译出的产物),实际上是同一个 bug 的两个投影。任何"自证"式的校验都要先问一句:这两个信号真的相互独立吗,还是共享同一个上游假设?

这是仓库今天完全没有的风险——24 个镜像全是单阶段 Dockerfile。但"新逻辑今天没被这个模式坑过"和"新逻辑不会被这个模式坑"是两句话。前者是运气,后者才是工程保证。

---

## 5. 💥 abi3 地雷:一个绿灯逻辑自己都不知道自己错哪了

到这一步,Alex 已经不想再往 GitHub Actions 上推测试了——多阶段这个场景已经证明,继续在 CI 上折腾成本越来越高,而且很多假设可以在本地更快、更干净地验证。他打开本地 Docker,几分钟内复现了一个更深的问题。

新加的校验逻辑里有一句注释:

```
Version-tagged .so files must carry the target ABI tag; abi3 (.abi3.so)
and pure-Python files are portable and skipped.
```

`abi3` 是 CPython 提供的稳定 ABI 子集——一个扩展只要不碰这个子集之外的东西,编译一次就能跨所有 3.x 小版本通用,不用为每个 Python 版本单独发 wheel。这句注释背后的假设是:**abi3 文件永远安全,不用检查。**

这个假设听起来完全合理。Alex 决定亲手撞一次:

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
RUN pip install --target /build/pkgs cryptography paramiko

FROM python:3.10-slim
COPY --from=builder /build/pkgs /app/pkgs
ENV PYTHONPATH=/app/pkgs
CMD ["python", "-c", "import paramiko"]
```

```
$ docker build -t py-drift-test . && docker run --rm py-drift-test

ImportError: /app/pkgs/cryptography/hazmat/bindings/_rust.abi3.so: undefined symbol: PyType_GetName
```

崩溃的正是那个被判定"永远安全"的 `abi3.so` 文件。原因是:`PyType_GetName` 这个 C API 符号,是 Python **3.11** 才被加进稳定 ABI 的。`cryptography` 的 Rust 绑定编译时用到了它,所以这个 abi3 wheel 实际的最低可运行版本是 3.11——比 3.11 老的解释器,不管文件名标不标 `abi3`,一样会崩。

**abi3 保证的从来不是"跨所有版本通用",是"从编译时那个最低版本开始,向后(更新的版本)通用"。** 它是单向的兼容性,不是对称的可移植性。把"跨小版本安全"简化成"文件名里有 abi3 就跳过检查",这个简化本身就是漏洞。

| 文件 | 检查怎么处理它 | 实际情况 |
|---|---|---|
| `_cffi_backend.cpython-311-*.so` | 会被扫到,标签对不上就报错 | 正确处理 |
| `_rust.abi3.so`(cryptography) | 直接跳过,判定"天生安全" | **错的**——这次崩的就是它 |

### 一个常见的直觉纠正

看到这里,很容易冒出一个念头:"那把 Docker 基础镜像统一升到 3.12,不就没这个问题了?"

不是。这次崩溃的根因是"运行的版本比编译产物需要的最低版本更老"(3.10 < 3.11 的 floor),不是"版本太旧"这个抽象概念本身——只要最终运行的版本 ≥ 3.11,不管是 3.11 还是 3.12,这个具体的 `abi3` 崩溃都不会发生。

而"升到 3.12"这条路,在这个仓库里已经被验证过是走不通的——第 3 节里 `dm_oru` 的测试已经证明,任何依赖 `edr-common-python` 的镜像,升到 3.12 会立刻撞上它自己 `<3.12` 的版本上限,报错和这次完全一样。升级版本不是在修这个问题,是在拿一个已知会炸的方案去换。

真正的修法只有一个:**构建阶段和运行阶段的 Python 版本永远保持一致,不要有漂移。** 这正是上一篇文章的结论,在这一篇里被一个完全不同的失败模式重新证明了一遍。

---

## 收尾:五轮测试连起来看

| 轮次 | 测什么 | 素材 | 结果 |
|---|---|---|---|
| 1 | 新逻辑到底跑没跑 | 仓库真实的路径过滤规则 | 一次都没跑过 |
| 2 | 逼它真正执行,看它能不能接住真实漂移 | 仓库里本来就有的 3.10 vs `edr-common-python` 要求 | 接住了,报错清晰可操作 |
| 3 | 反过来测版本升级会不会被拦住 | 真实改一行 Dockerfile(3.11→3.12) | 接住了,而旧 CI 永远接不住 |
| 4 | 结构性盲区:资源解析逻辑本身的假设 | 手工构造的多阶段 Dockerfile(仓库里还不存在) | 假绿灯——校验逻辑和构建逻辑共享同一个错误假设 |
| 5 | 检查逻辑自己的假设是否成立 | 本地 Docker 复现,真实 `ImportError` | 假绿灯——"abi3 天生安全"这个假设本身是错的 |

前两轮测的是"这段代码能不能用真实场景验证",后两轮测的是"这段代码的假设本身站不站得住"。两种测试都做完,才敢说这个安全网真正被检验过——不是"合并了就算数",是"逼它跑起来、逼它接一次真实的漂移、逼它去撞一个它自己都不知道自己会输的场景"之后,才算数。

## 立刻可以做的事

1. 下次合并一个只改 CI 配置文件本身、不改任何业务代码的 PR 之前,先看一眼具体是哪些 job 真正执行了——`skipped` 和 `success` 长得很像,含义完全不同。
2. 如果你的 CI 用路径过滤触发矩阵构建,任何一次"只改 workflow 逻辑"的 PR,考虑配一次专门的、用完即弃的 touch commit,强制至少一个真实分支跑一遍新逻辑,再合并。
3. 审查任何"跳过某类文件/某种标签"的安全检查逻辑时,把这句话当成必答题:这个跳过条件成立的前提,是不是"单向的",还是"只在特定范围内成立"?——`abi3` 这个词听起来像"通用",实际上是"以某个版本为起点,向后通用"。

---

*绿色对勾从来不是终点,它只是一个问题:这个勾,到底是谁打的、验证了什么、又是在什么条件下打上去的。*
