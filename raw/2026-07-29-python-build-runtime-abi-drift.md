---
title: "构建期 3.11,运行期 3.10:一个潜伏五个月的 _cffi_backend 事故"
date: 2026-07-29
categories: [engineering, python]
tags: [python, docker, cffi, abi, ci-cd, incident, packaging]
---

生产批处理挂了。日志里只有一句:

```
ImportError: no module named _cffi_backend
_cffi_backend is either missing, uninstalled, or compiled for a different version of Python
```

第一反应是"依赖装漏了"。查完 lock 文件,`cffi` 好好地躺在那儿。再查镜像,`site-packages` 里 `cffi` 也在。

问题不在"装没装",在于**装它的那个 Python,和跑它的那个 Python,不是同一个**。

这篇讲清楚这类 bug 的完整机理:为什么它只在特定的构建模式下出现,为什么偏偏是 `cffi` 而不是 `cryptography` 报错,以及为什么它能潜伏五个月才爆。

---

## 1. 🎯 30秒版本

某个镜像的 Dockerfile 长这样:

```dockerfile
FROM python:3.10-slim
COPY build /app/build          # ← 注意:没有 RUN pip install
ENV PYTHONPATH=/app/build
```

依赖不是在容器里装的,是在 CI runner 上装好、再 `COPY` 进去的:

```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.11'      # ← runner 的解释器
- run: pip install ./dist/*.whl --target ./build
```

`pip` 跑在 3.11 上,于是它下载 3.11 的 wheel,解出这么个文件:

```
build/_cffi_backend.cpython-311-x86_64-linux-gnu.so
```

这个目录被搬进了一个 **3.10** 的镜像。3.10 的解释器不认 `-311-` 后缀的扩展模块,于是 `import` 时**根本看不见这个文件**——报的不是"加载失败",是"不存在"。

一句话:**`RUN pip install` 天然保证装和跑是同一个解释器;把 pip 挪到 Docker 外面,这个保证就没了,只能靠人去维护。**

---

## 2. ⚙️ 底层原理

### 2.1 正常的 Dockerfile 为什么不会出这个问题

绝大多数项目是这么写的:

```dockerfile
FROM python:3.10-slim
COPY requirements.txt .
RUN pip install -r requirements.txt   # ← 在容器"里面"执行
```

关键在 `RUN`。它在容器内部执行,执行它的 `pip` 就是镜像里那个 3.10 的 pip。pip 挑 wheel 时看到的解释器,**就是将来真正跑代码的那个解释器**。

装的人和跑的人是同一个人。想错都错不了。

这就是为什么你在别的项目里从来没遇到过这个坑——不是你运气好,是这个约束由构造保证,压根没机会出错。

### 2.2 `pip install --target` 不知道你要干什么

一旦改成外部安装:

```bash
pip install ./dist/*.whl --target ./build
```

`--target` 只是说"把包解到这个目录"。pip **不知道**这个目录将来会被搬进一个别的 Python 版本的容器。它只知道一件事:

> 我现在跑在 3.11 上,那我就下 3.11 的 wheel。

它做的完全正确。错的是外面那个没人维护的假设。

### 2.3 为什么 `.so` 换个 Python 版本就废了

纯 Python 的 `.py` 文件无所谓,3.10 和 3.11 都能读。但**编译出来的 C 扩展不行**。

`.so` 里是机器码,直接链接了 CPython 的内部 ABI:对象内存布局、引用计数宏、C API 符号表。这些东西在小版本之间**会改**。3.10 编译的扩展塞给 3.11,轻则符号找不到,重则内存布局对不上直接段错误。

CPython 的处理办法很干脆:**把版本写进文件名,然后只认自己那个后缀**。

3.10 的解释器 import 一个扩展模块时,只找这三种文件名:

| 文件名形态 | 含义 | 3.10 能否加载 |
|---|---|---|
| `foo.cpython-310-x86_64-linux-gnu.so` | 为 3.10 编译 | ✅ |
| `foo.abi3.so` | 稳定 ABI,跨小版本通用 | ✅ |
| `foo.so` | 无标签,老式命名 | ✅ |
| `foo.cpython-311-x86_64-linux-gnu.so` | 为 3.11 编译 | ❌ **视而不见** |

注意最后一行:不是"报错说版本不对",是**这个文件对它来说不存在**。解释器扫描目录时按后缀白名单匹配,`-311-` 不在白名单里,直接跳过。

所以最终的报错才是那句含糊的 `is either missing, uninstalled, or compiled for a different version` ——库自己也分不清是哪种情况,因为它拿到的信息就是"没有"。

> 打个比方:文件名上的 `cpython-311` 就像插头的制式。3.10 的解释器是个只认国标插座的接线板——你把英标插头怼上去,它不会"报错说电压不对",它会说"我这儿没插着东西"。

### 2.4 为什么偏偏是 cffi 报错,而不是 cryptography

这是最容易看漏的一层,也是定位这类问题最快的抓手。

同样是 C 扩展,同样被 3.11 装、被 3.10 跑,结果却不一样:

| 包 | 发布的 wheel 标签 | 跨小版本 |
|---|---|---|
| `cryptography` | `cp39-abi3` | ✅ 能用 |
| `bcrypt` / `pynacl` | 多为 abi3 | ✅ 基本能用 |
| **`cffi`** | **`cp310-cp310` / `cp311-cp311`** | ❌ **不能** |

**Py_LIMITED_API / 稳定 ABI** 是 CPython 提供的一个子集:只用这个子集里的 API,编出来的扩展就能标成 `abi3`,一次编译跨所有 3.x 小版本通用。`cryptography` 这类库为了少发几十个 wheel,基本都走了 abi3。

而 `cffi` **不能**走。它的整个工作就是在运行时构造 C 类型、调 C 函数、操作 CPython 对象内部结构——它用的正是稳定 ABI 之外的那部分。**给别人做 ABI 桥的东西,自己必须绑死 ABI。**

所以在一条 `paramiko → cryptography → cffi` 的依赖链上,前两个都相安无事,只有最底下那个 `cffi` 炸了。看到这个报错组合,基本可以直接跳到"版本错配"的结论。

### 2.5 这个模式换来了什么

把 pip 挪到 Docker 外面,不是有人拍脑袋决定的。它有真实收益:

| 维度 | 换来的 | 代价 |
|---|---|---|
| 构建速度 | 多个镜像共用一份 runner 的 pip 缓存,不用每个都起 docker build 装一遍 | — |
| 镜像体积 | 最终镜像只有一个 `COPY` 层,很薄 | — |
| 安全面 | 镜像里不装 pip、不装编译工具链,攻击面小 | — |
| **一致性** | — | **构建期与运行期的解释器绑定被切断,只能靠约定维持** |

它把一个**由构造保证**的约束,降级成了一个**靠人记住**的约束。

### 2.6 潜伏五个月:为什么当时没炸

这才是这类事故真正阴险的地方。

时间线大致是这样:

```
2 月:  有人把 CI 的 setup-python 从 3.10 改成 3.11
       顺手改了 3 个镜像的 Dockerfile,漏了 21 个
       ✅ CI 全绿,没有任何告警

3~6 月:那 21 个镜像一次都没被改过
       CI 只重建"有改动"的镜像,所以它们从没被重新构建
       生产上跑的还是 2 月之前构建的好镜像
       ✅ 一切正常

7 月:  一个格式化 PR 动了所有镜像的 pyproject.toml
       → 21 个镜像全部重建 → 全部带着错版本的 .so 上线
       💥 第二天早上,第一个批处理任务炸了
```

三个放大因素叠在一起:

1. **CI 全绿。** 单元测试是在 runner 的 3.11 上跑的,那里的扩展**天生是对的**。测试永远发现不了这个问题——这不是测试写得差,是单元测试在原理上就测不到"产物搬进另一个解释器还能不能 import"。
2. **增量构建把爆炸延后了。** 改动和事故之间隔了五个月,中间几百次提交。没有任何人会想到去看 2 月那个 PR。
3. **触发它的改动毫无信息量。** 最后点火的是一行代码格式化配置,功能上什么都没变。事故报告上写"格式化改动导致生产故障",听起来像天方夜谭。

> **休眠故障的引爆点,永远不是根因。** 找根因时要问的是"**构建产物**什么时候变的",不是"代码什么时候变的"。

---

## 3. 🛠 怎么修

### 3.1 三个选项,只有一个是对的

| | 方案 | 评价 |
|---|---|---|
| A | 把所有 Dockerfile 改成 3.11 | 一次动几十个镜像的运行时,测试面爆炸。**一次只动一个变量**的原则不允许 |
| B | 把 CI 改回 3.10 | 能止血,但那几个真的是 3.11 的镜像会反向踩雷。而且这个数字还是有两个来源 |
| **C** | **让版本只有一个来源** | ✅ **唯一从结构上消除问题的做法** |

A 和 B 都在回答"这个数字该填几",但真正的病是**这个数字有两个地方可以填**。

### 3.2 单一真相来源

让 CI 从 Dockerfile 里**推导**出解释器版本,而不是自己再写一遍:

```yaml
- name: Resolve target Python version from Dockerfile
  id: target_python
  working-directory: images/${{ matrix.image }}
  run: |
    set -euo pipefail
    version="$(sed -nE 's|^FROM[[:space:]]+python:([0-9]+\.[0-9]+).*|\1|p' Dockerfile | head -1)"
    if [ -z "$version" ]; then
      echo "::error::Could not resolve 'FROM python:<major>.<minor>' from Dockerfile."
      exit 1
    fi
    echo "version=${version}" >> "$GITHUB_OUTPUT"

- uses: actions/setup-python@v4
  with:
    python-version: ${{ steps.target_python.outputs.version }}
```

注意两个细节:

- **推不出来就 `exit 1`,绝不猜。** 一个 fallback 默认值会让这个 bug 以更隐蔽的形式回来。
- **不做版本映射表。** 不维护"镜像 A 用 3.10、镜像 B 用 3.11"这种清单——清单本身就是第二个真相来源。

改完之后,`Dockerfile` 的 `FROM` 成了唯一真相。谁改 Dockerfile,构建自动跟着走;谁想改 CI 的版本——改不了,那里已经没有数字可填了。

> 把"两个地方要一致"变成"只有一个地方"。这是消除这类 bug 的通用手法,比加多少检查都管用。

### 3.3 兜底:校验产物本身

单一来源挡住了**这次**的错配方式。但挡不住下次那个你没想到的。

所以再加一层:构建完成后、**上传产物之前**,扫一遍编译出来的扩展,ABI 标签对不上就直接失败。

```bash
set -euo pipefail
expected="cpython-$(echo "${TARGET_PY}" | tr -d '.')"    # 3.10 -> cpython-310

mismatched="$(find ./build -name '*.so' \
  | sed 's|.*/||' \
  | grep -E '\.cpython-[0-9]+' \
  | grep -v "\.${expected}[-.]" || true)"

if [ -n "$mismatched" ]; then
  echo "::error::Native extensions target the wrong Python (expected ${expected}):"
  echo "$mismatched"
  exit 1
fi
echo "All native extensions match ${expected}."
```

几个设计要点:

- **`grep -E '\.cpython-[0-9]+'` 先筛出带版本标签的。** `abi3.so` 和纯 Python 文件本来就可移植,不该被误报——漏报比误报可怕,但一个天天误报的检查等于没有检查。
- **放在上传产物之前。** 坏产物根本传不出去,后面的 docker build 拿不到东西,坏镜像**进不了 registry**。断在源头,而不是断在部署。
- **零依赖。** 纯 shell,不需要在构建机上跑 docker。

如果构建环境允许跑 docker,还有一个更强的版本——直接拿目标镜像 import 一遍:

```bash
docker run --rm -v "$PWD/build:/b" -e PYTHONPATH=/b \
  python:${TARGET_PY}-slim python -c "import cffi, cryptography, paramiko"
```

这个最接近真相,因为它就是生产环境要做的事。

---

## 4. 🔍 自查清单

如果你的项目符合下面任意一条,现在就去查:

- [ ] Dockerfile 里**没有** `RUN pip install`,依赖是 `COPY` 进去的
- [ ] CI 里有 `pip install --target` / `pip install --prefix` / 打 zip 传 Lambda Layer
- [ ] `setup-python` 的版本和 `FROM python:` 的版本**写在两个文件里**
- [ ] 用 Lambda / Glue / 任何"上传一个依赖包"的托管运行时
- [ ] 在 macOS 上装依赖、丢进 Linux 容器跑(这个还会额外撞上平台 tag)

一行命令自查(在放依赖的目录下跑):

```bash
find . -name '*.so' | sed 's|.*/||' | grep -oE 'cpython-[0-9]+' | sort -u
```

输出应该**只有一个版本**,并且等于运行时的 Python 版本。出现两个,或者和运行时对不上,就是这个问题。

---

## 5. 🔬 常见追问

**Q: 为什么 CI 全绿还能把这种东西推上生产?**

A: 测试跑在 CI runner 的解释器上,那里的扩展是有效的——测试**证明不了**产物换个解释器还能 import。这是覆盖率的结构性盲区,不是测试写得不够。唯一能证明的办法是校验产物本身,或者真的在目标镜像里 import 一次。

**Q: 那把所有东西都升到最新 Python 不就完了?**

A: 那是在回答"该填几",而病在"有两个地方可以填"。今天对齐到 3.11,明天有人升 3.12,同样的事再来一次。而且一次性改几十个镜像的运行时,等于同时动几十个变量——出了问题你分不清是谁的锅。**先让版本只有一个来源,再单独安排升级。**

**Q: 换成 `pip install --platform manylinux --python-version 3.10` 行不行?**

A: 能解决单次问题,但那是**第三个**写死版本的地方——问题更严重了。真要用交叉安装,那些参数也必须从 Dockerfile 推导出来。

**Q: 为什么 `cryptography` 没事,`cffi` 有事?**

A: `cryptography` 发的是 `abi3` wheel(稳定 ABI,跨小版本通用),`cffi` 发的是版本绑定的 `cp3XX` wheel。`cffi` 用的正是稳定 ABI 之外的那部分 CPython 内部结构,没法走 abi3。看到"依赖链上只有最底层的 cffi 报错",基本就能锁定版本错配。

**Q: `deregister` 掉坏的部署版本能救急吗?**

A: 如果编排层引用的是"最新版本"而不是固定版本号,可以——删掉最新的,自动回落到上一个。但有两个前提必须先验:一是镜像 tag 是**不可变**的(如果是 `:latest` 这种可变 tag,回滚版本号没用,旧版本指向的还是被覆盖过的同一个镜像);二是要确认**有几个坏版本**——如果连着几次部署都是坏的,只删最新那个,回落到的还是坏的。

**Q: 怎么防止它再来一次?**

A: 三层,缺一不可。
1. **单一真相来源**——版本只有一个地方可填,结构上无法漂移。
2. **产物校验**——挡住你没想到的那种错配。
3. **发布路径上要有一道非生产环境的闸**。这次事故里,合并主干直接同时部署到预发和生产,中间没有任何一层能先撞上这个错误。版本错配是根因,但**没有闸的发布路径才是把它送进生产的那只手**。

---

## 收尾

这个 bug 本身很小——一个数字写在了两个地方。

但它有教科书级的三个特征:**改动和爆炸隔了五个月**、**CI 全程绿灯**、**点火的是一行格式化配置**。这三条凑齐,任何靠"经验直觉"的排查都会失效。

真正能救你的只有一件事:**别让同一个事实在系统里存在两份。**

下次 review 到"这里也要记得改一下"这种注释时,停一下——那句注释就是一个还没爆的雷。
