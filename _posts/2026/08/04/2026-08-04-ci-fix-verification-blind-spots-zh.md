---
title: "那个从没跑过一次的 CI 自动化构造脚本写的检查任务,给了我们一个假的绿色对勾"
header:
    image: /assets/images/hd_containers.png
date: 2026-08-04
tags:
 - python
 - docker
 - ci-cd
 - github-actions
 - testing
permalink: /blogs/tech/zh/ci-fix-verification-blind-spots
layout: single
category: tech
---

> 鸟儿在天空飞过时，是不会在乎地面上的栅栏的

---

批处理任务死在了半夜。

值班的人被叫醒时,日志里只有干巴巴的一行:

```
ModuleNotFoundError: No module named '_cffi_backend'
```

这个任务已经稳稳当当跑了很久,今晚什么都没改。第一反应是查依赖——`cffi` 好好地躺在 lock 文件里,镜像的 `site-packages` 目录里它也在。包,确实是装了的。

问题不在"装没装",在于**装它的那个 Python,和跑它的那个 Python,根本不是同一个**。CI 在 3.11 上把这个包编译打包,产物被塞进了一个基础镜像是 3.10 的容器。3.10 的解释器扫描扩展模块时,只认识几种特定后缀的文件名——`-311-` 那个后缀不在白名单里,于是它不是"加载失败",是**压根看不见这个文件**。库自己都分不清是哪种情况,只能报一句含糊的"缺失,或者是给另一个版本编译的"。

Alex 花了半天才把这条因果链理清楚,然后又花了两天,把修复推了上去:让 CI 不再写死 Python 版本,而是从每个镜像自己的 `Dockerfile` 里去读——这样构建和运行,永远是同一个数字,再也不用靠人记住"这两处要保持一致"这种脆弱的约定。

PR 合并,CI 全绿。他往后靠在椅子上,长舒一口气,正准备去关掉这张票,顺手点开下一个任务的时候——脑子里冒出一个念头,轻飘飘的,但赶不走:

> "这个绿色对勾,到底证明了什么?"

他后来才知道,答案几乎是:什么都没有。

## 30 秒版本

那个刚合并的 PR,只改了一个文件——`.github/workflows/build-and-deploy.yml`。他去翻了一下具体是哪些 job 真正跑过,`Test and build Images` 那一行,安静地写着 `skipped`。

仓库的 CI 按路径过滤触发构建矩阵:只有 `images/*` 目录下真的有改动,对应的镜像才会被拉出来构建。这次 PR 只碰了 workflow 文件本身,一个镜像目录都没动。新逻辑,已经堂堂正正地进了主干,却一次都没有被执行过。

Alex 接下来又跑了四轮测试,一轮比一轮凶,一步比一步逼近同一句话:

**一个"可用"但从没被执行过的安全网,和一个根本不存在的安全网,没有任何区别。你得亲手把它逼到跑起来,再盯着它,看它到底接住了什么、又漏掉了什么。**

这篇文章讲的就是这五轮测试——包括最后揪出的两个真实存在、当时全团队没人知道的盲区。读完你会带走:

- **"CI 绿了"和"CI 跑过了"是两件事**——路径过滤能让一段代码永远合并进主干、又永远不被执行。
- **拿仓库里本来就有的漂移去测试你的检查,比自己编一个场景更有说服力**——但有些盲区,现实里还没出现过,你只能亲手造一个去撞。
- **一条安全检查的假设本身,可能就是它最大的破口**——"abi3 总是安全的",听起来像常识,查到最后发现是错的。

下面按 Alex 实际踩坑的顺序讲,不是按"教科书应该怎么做"的顺序——因为他每一步踩到的东西,都是下一步测试设计的直接原因。

---

## 1. 🎯 绿色对勾骗过了谁

PR 合并,check 全绿,正常人的反应是接着干别的去了。

Alex 这次多看了一眼具体的 job 列表:

```
Create Application Version   success
Test and build Images        skipped   ← 新逻辑就藏在这里面
Deploy to SIT/STG/PRD        skipped
```

`Test and build Images` 是一个 matrix job,新加的两个步骤都在里面:从 Dockerfile 推导版本、校验编译产物的 ABI 标签。它显示的是 `skipped`,不是 `success`——这两个词长得像,意思天差地别。

原因简单到容易被直接跳过去:仓库的 `List modified images` job 靠目录 diff 判断"这次改动碰了哪些镜像"。PR 只改了 workflow 文件,`images/*` 路径没有任何变化,矩阵直接判定"没有镜像需要构建",整个 job 跳过。

> **普通人的看法**:CI 绿了,说明改动是对的。
> **资深工程师的洞察**:CI 绿了,只能说明"跑过的那部分"是对的。先问一句"这次改动到底让哪些 job 真正执行了",再决定要不要信这个绿灯。

| 现象 | 看起来像 | 实际是 |
|---|---|---|
| PR checks 全绿 | 新逻辑验证通过 | 新逻辑所在的 job 被路径过滤跳过,根本没跑 |
| `skipped` | 一种"通过"的变体 | 一次都没执行过 |
| 合并到 `develop` | 代码生效 | 代码进了主干,但触发条件从没被满足过 |

> 路径过滤是为了省 CI 时间存在的,这个设计本身没错。错的是把"这个 job 允许被跳过"和"这次改动不需要被验证"划了等号——一个改的是触发规则,一个改的是新逻辑正不正确,这是两件完全不相关的事。

---

## 2. ⚙️ 逼它真正跑起来:一个用完就扔的 touch commit

发现"从没跑过"之后,Alex 没有去改测试框架,也没有去写单元测试模拟 GitHub Actions 的行为——那测的是"我以为它会怎么跑",不是"它真的怎么跑"。谁在乎你以为。

他的做法更直接、也更笨:开一个新分支,对一个真实镜像的 `pyproject.toml` 做一次纯版本号的 touch commit(`0.1.0` → `0.1.1`,没有任何功能改动),让 `List modified images` 相信这个镜像"变了",从而把矩阵里对应的那一个 job,真正逼上跑道。

```bash
git checkout -b verify-ci-python-version-resolution develop
# sftp-ingest-core 依赖 paramiko/cryptography,是仓库里少数真的会产出
# 编译扩展的镜像之一——选它不是随便选的,选一个只有纯 Python 依赖的
# 镜像,新逻辑压根没有东西可测
sed -i '' 's/version = "0.1.0"/version = "0.1.1"/' images/sftp-ingest-core/pyproject.toml
git commit -am "touch sftp-ingest-core to exercise new CI python-version resolution"
git push
```

选哪个镜像去触发,才是这一步真正的技术含量所在——选错了,job 是跑了,但新逻辑没有任何东西可以校验(比如一个纯 boto3 依赖的镜像,根本不会产出任何编译扩展),又是一次"绿灯,但什么都没验证"。

这次它真的跑起来了。CI 立刻翻脸,变红:

```
Building sftp-ingest-core against Python 3.11 (derived from Dockerfile base image)
...
ERROR: Package 'platform-shared-lib' requires a different Python: 3.10.20 not in '<3.12,>=3.11'
```

没有一个字是演出来的。`sftp-ingest-core` 的 `Dockerfile` 当时真的是 `FROM python:3.10-slim`,而它依赖的 `platform-shared-lib`——一个没锁死版本、直接跟着 git HEAD 走的内部包——最新的要求是 `>=3.11,<3.12`。这个漂移,是仓库里本来就静静躺着的。新逻辑第一次真正执行,第一次就抓到了一个真实、自然生长出来的问题,报错信息直接可操作,连排查的力气都省了。

> **一句话哲学**:测试一段"检查漂移"的代码,最好的素材从来不是你脑子里编出来的场景,是仓库里本来就有、只是还没被人踩到的那个坑。

---

## 3. 🔍 第二次真实测试:朝相反的方向撞一次

第一次测试撞见的是"版本太旧"。Alex 想知道另一个方向——如果哪天有人为了打个安全补丁,顺手把某个镜像的 Dockerfile 从 3.11 升到 3.12,新逻辑拦不拦得住?

他挑了另一个真实存在、同样依赖 `platform-shared-lib` 的镜像 `report-refresh`,只改了 Dockerfile 的一行,`pyproject.toml` 一个字都没碰:

```diff
- FROM python:3.11-slim
+ FROM python:3.12-slim
```

结果:

```
Building report-refresh against Python 3.12 (derived from Dockerfile base image)
...
ERROR: Package 'platform-shared-lib' requires a different Python: 3.12.13 not in '<3.12,>=3.11'
```

版本推导本身完全正确——Dockerfile 说 3.12,CI 就真的拿 3.12 去构建。挡住这次升级的,是 `platform-shared-lib` 自己的版本上限。

这次测试真正的价值在于对比:**旧的 CI(写死 3.11)会怎么处理同样这次升级?** 答案是,它压根不会处理——不管 Dockerfile 写的是 3.10、3.11 还是 3.12,旧 CI 永远拿 3.11 去构建、去测试。一次真实的、有风险的基础镜像升级,会在没有任何人验证过依赖是否兼容 3.12 的情况下,大摇大摆地绿灯上线。新逻辑第一次,让"升级基础镜像"这个动作,真正经过了它本该经过的那一道关。

| | 旧 CI(写死 3.11) | 新 CI(从 Dockerfile 推导) |
|---|---|---|
| Dockerfile 升到 3.12 | 构建仍然用 3.11,升级本身**从未被验证** | 构建真的用 3.12,立刻撞见 `platform-shared-lib` 的版本上限 |
| 反馈时机 | 可能是生产环境的一次 `ModuleNotFoundError` | PR 阶段,一条能直接定位到哪个依赖的报错 |

---

## 4. 🧪 造一个还不存在的攻击:多阶段 Dockerfile

前两轮测试,用的都是仓库里真实存在的状态。第三轮,Alex 开始主动进攻——去找一个仓库里**目前一个镜像都没有**的模式:多阶段 Dockerfile。这是 Docker 里再正常不过的写法,今天没人用,不代表明天不会有人用。而新逻辑的推导脚本,长这样:

```bash
version="$(sed -nE 's|^FROM[[:space:]]+python:([0-9]+\.[0-9]+).*|\1|p' Dockerfile | head -1)"
```

`head -1`——只取文件里**第一条** `FROM python:` 行。单阶段 Dockerfile 里这没问题,全文只有一条。多阶段呢?

```dockerfile
FROM python:3.11-slim AS builder   # ← 第一条 FROM,head -1 会抓这个

FROM python:3.10-slim              # ← 最后一条才是真正要发布的镜像
RUN adduser --system --home /svc-python --group svc-python
...
```

Alex 把这个改动推上同一条测试分支,然后看着 CI 一步步走进那个陷阱:用 3.11 构建、测试、打包,再拿"期望的 ABI 是 cpython-311"去比对产物——而产物**确实**是用 3.11 编译的,两边严丝合缝。

**绿灯。**

漂亮,干净,而且是假的。真正会被发布出去的镜像,基础层是 `python:3.10-slim`,不是 3.11。校验逻辑用来"验证"的那个期望值,和产生构建产物的版本,来自**同一处错误的推导**——它们永远不可能互相矛盾,因为它们本来就是同一个错,只是照了两次镜子。

> **对称性破缺**:这个检查看起来像"两个独立信号互相印证"(推导出的版本 vs 实际编译出的产物),实际上是同一个 bug 投影出的两个影子。任何"自证"式的校验都要先问一句:这两个信号真的相互独立吗,还是共享同一个上游假设?

这是仓库今天完全没有的风险——所有镜像清一色单阶段。但"新逻辑今天没被这个模式坑过"和"新逻辑不会被这个模式坑"是两句完全不同的话。前一句是运气,后一句才是工程上的承诺。

---

## 5. 💥 abi3 地雷:一条自己都不知道自己错在哪的绿灯逻辑

到这一步,Alex 不太想再往 GitHub Actions 上推测试了——多阶段这一场,已经证明每次 CI 往返都在烧时间,很多假设本可以在本地更快、更干净地撞出来。他打开自己笔记本上的 Docker,几分钟之内,复现出了一个更深的坑。

新加的校验逻辑里,躺着这样一句注释:

```
Version-tagged .so files must carry the target ABI tag; abi3 (.abi3.so)
and pure-Python files are portable and skipped.
```

`abi3` 是 CPython 提供的稳定 ABI 子集——一个扩展只要不碰这个子集之外的东西,编译一次就能跨所有 3.x 小版本通用,不用为每个 Python 版本单独发 wheel。这句注释背后藏着一个假设:**abi3 文件永远安全,不用检查。**

这句话听起来完全合理,合理到没人会去质疑它。Alex 决定亲手撞一次:

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

崩溃的,恰恰就是那个被判定"永远安全"的 `abi3.so` 文件。原因是:`PyType_GetName` 这个 C API 符号,是 Python **3.11** 才被加进稳定 ABI 里的。`cryptography` 的 Rust 绑定编译时用到了它,于是这个 abi3 wheel 实际的最低可运行版本,就是 3.11——比它老的解释器,不管文件名标不标 `abi3`,一样会崩,毫无商量余地。

**abi3 保证的从来不是"跨所有版本通用",是"从编译时那个最低版本开始,向后、向着更新的版本通用"。** 它是单向的兼容性,不是对称的可移植性。把"跨小版本安全"简化成"文件名里带 abi3 就跳过检查",这个简化本身,就是漏洞。

| 文件 | 检查怎么处理它 | 实际情况 |
|---|---|---|
| `_cffi_backend.cpython-311-*.so` | 会被扫到,标签对不上就报错 | 正确处理 |
| `_rust.abi3.so`(cryptography) | 直接跳过,判定"天生安全" | **错的**——这次崩的就是它 |

### 一个太容易脱口而出的直觉,需要被纠正

看到这里,很难不冒出一个念头:"那把 Docker 基础镜像统一升到 3.12,不就一了百了了?"

不是。这次崩溃的根因是"运行的版本比编译产物需要的最低版本更老"(3.10 < 3.11 的 floor),不是"版本太旧"这个抽象概念本身——只要最终运行的版本 ≥ 3.11,不管是 3.11 还是 3.12,这个具体的 `abi3` 崩溃都不会再发生。

而"升到 3.12"这条路,在这个仓库里,已经被亲手证明是死路——第 3 节里 `report-refresh` 的那次测试已经说得很清楚:任何依赖 `platform-shared-lib` 的镜像,一升到 3.12 就会立刻撞上它自己 `<3.12` 的版本上限,报错和这次一字不差。升级版本,不是在修这个问题,是拿一个已知会炸的方案去换另一个。

真正的修法只有一条:**构建阶段和运行阶段的 Python 版本,永远保持同一个数字,不许有漂移。** 这条结论,在这篇文章里被一个和最初那次生产事故完全不同的失败模式,重新证明了一遍——两条完全不同的裂缝,通向的是同一堵墙。

---

## 收尾:五轮测试连起来看

| 轮次 | 测什么 | 素材 | 结果 |
|---|---|---|---|
| 1 | 新逻辑到底跑没跑 | 仓库真实的路径过滤规则 | 一次都没跑过 |
| 2 | 逼它真正执行,看它能不能接住真实漂移 | 仓库里本来就有的 3.10 vs `platform-shared-lib` 要求 | 接住了,报错清晰可操作 |
| 3 | 反过来测版本升级会不会被拦住 | 真实改一行 Dockerfile(3.11→3.12) | 接住了,而旧 CI 永远接不住 |
| 4 | 结构性盲区:版本解析逻辑本身的假设 | 手工构造的多阶段 Dockerfile(仓库里还不存在) | 假绿灯——校验逻辑和构建逻辑共享同一个错误假设 |
| 5 | 检查逻辑自己的假设是否成立 | 本地 Docker 复现,真实 `ImportError` | 假绿灯——"abi3 天生安全"这个假设本身是错的 |

前两轮测的是"这段代码能不能扛住真实世界"。后两轮测的是"这段代码信以为真的那个假设,到底站不站得住"。两种测试都做完,才轮得到你说这个安全网真正被检验过——不是"合并了就算数",是"逼它跑起来、逼它接一次真实的漂移、逼它去撞一个它自己都不知道自己会输的场景",全都撞完之后,才算数。

## 立刻可以做的事

1. 下次合并一个只改 CI 配置文件本身、不改任何业务代码的 PR 之前,先看一眼具体是哪些 job 真正执行了——`skipped` 和 `success` 长得很像,含义天差地别。
2. 如果你的 CI 用路径过滤触发矩阵构建,任何一次"只改 workflow 逻辑"的 PR,配一次专门的、用完即弃的 touch commit,强制至少一个真实分支跑一遍新逻辑,再合并。
3. 审查任何"跳过某类文件/某种标签"的安全检查逻辑时,把这句话当成必答题:这个跳过条件成立的前提,是不是"单向的",还是"只在特定范围内成立"?——`abi3` 这个词听起来像"通用",实际上是"以某个版本为起点,向后通用"。

---

*绿色对勾从来不是终点。它只是一个问题,悬在那里,等你回答:这个勾,到底是谁打的、验证了什么、又是在什么条件下,才被允许打上去的。*
