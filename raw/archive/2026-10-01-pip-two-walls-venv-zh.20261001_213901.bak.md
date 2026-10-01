---
title: "pip 装不上的那一晚：Ubuntu 24.04 的两堵墙，和一个 venv 的破解"
date: 2026-10-01
categories: [engineering, python, linux]
tags: [pip, venv, PEP668, ubuntu, ensurepip, pipenv]
---

# pip 装不上的那一晚：Ubuntu 24.04 的两堵墙，和一个 venv 的破解

任务本来小到不值一提：改好了几个仓库的 `Pipfile`，把包源指向公司内网的 Nexus 代理，剩下只要在有 VPN 的机器上跑一句 `pipenv lock` 重新生成锁文件就收工。

结果这一句命令，像推倒了第一张多米诺骨牌：

```text
$ pipenv lock
command not found: pipenv

$ python3 -m pip install --user pipenv
/usr/bin/python3: No module named pip

$ python3 -m ensurepip --upgrade
ensurepip is disabled in Debian/Ubuntu for the system python.
```

装个 pipenv 而已，怎么会一路塌方到「连 pip 都没有、连 ensurepip 都被禁用」？而且——**这是公司给我电脑上的锁吗？为什么我以前从来没遇到过？**

这篇就把那一晚的坑、原理、和「一句 venv 破两墙」的真相，从源码层面讲透。

---

### 1. 🎯 30秒版本

- 现代 Ubuntu（24.04）的**系统 Python** 前面立了**两堵墙**，专门拦住你往系统 Python 里装包：
  - **墙 1 — PEP 668**：解释器旁边放了一个 `EXTERNALLY-MANAGED` 标记文件，pip 一看到它就罢工，报 `externally-managed-environment`。
  - **墙 2 — Debian 禁用 ensurepip**：`ensurepip` 被下游打了补丁，在系统 Python 里直接 `sys.exit(1)`。
- `--user` **救不了你**——它装的还是系统解释器那套包，照样撞墙 1。
- 两堵墙其实**由同一个开关决定**：`sys.prefix != sys.base_prefix`。只要你站在 venv 里，这个条件成立，两堵墙**同时失效**。
- 所以解法就是那四行 venv：进了 venv，pip 自带、没有标记文件、ensurepip 也放行。
- 这**不是公司锁的**，是 Ubuntu 的发行版默认策略；你以前没遇到，多半因为老机器是 22.04、或你一直在用 pyenv/conda/docker 绕开了系统 Python。

---

### 2. ⚙️ 底层原理

#### 两堵墙，拦的是同一件事

每一条失败的命令，撞的都是 Debian/Ubuntu 给**系统** Python 加的守卫。它们问的是同一个问题：**「你是不是想动系统 Python 本身？」**

| 你跑的命令 | 撞上的墙 |
|---|---|
| `pip install --user … pipenv` | **墙 1** — PEP 668 的 `EXTERNALLY-MANAGED` 标记 |
| `python3 -m ensurepip --upgrade` | **墙 2** — Debian 打补丁禁用的 `ensurepip` |
| `/usr/bin/python3 -m pip …`（第一次报错） | 系统 Python 根本没装 pip（Debian 把它拆出去了） |

#### 墙 1：PEP 668 的 `EXTERNALLY-MANAGED`

自己读一眼：

```bash
cat /usr/lib/python3.12/EXTERNALLY-MANAGED
```

它**不是代码**，是一个纯 INI 文件。它**存在**这件事本身就是信号。pip 启动时会检查「这个解释器的标准库目录旁边有没有 `EXTERNALLY-MANAGED`」，有就拒绝，并原样打印文件里的 `Error=` 文案。

背后的理由（PEP 668，2022 年）：在一台 `apt`/`dpkg` 拥有 `/usr/lib/python3/...` 的发行版上，再让 pip 往里写，等于两个包管理器抢同一批文件，迟早把系统工具搞坏。所以发行版丢下这个标记，对 pip 说：**「这台 Python，别碰。」**

关键结论：**`--user` 没用**。`pip install --user` 装的仍然是**系统**解释器那套包集合，标记照样生效。所以你那次 `--user` 被拒，天经地义。

#### 墙 2：Debian 禁用的 `ensurepip`

```bash
sed -n '8,40p' /usr/lib/python3.12/ensurepip/__init__.py
```

打印那段错误的函数长这样：

```python
if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
    return                       # 在 venv 里？早早返回，不拦你

# 只有在「系统 Python」里才会走到这：
print('''ensurepip is disabled in Debian/Ubuntu for the system python. ...''')
sys.exit(1)
```

**这一行就是全部秘密。** Debian 不是一刀切禁掉 ensurepip，而是**只在 `sys.prefix == sys.base_prefix` 时**才禁。

#### 真正的开关：`sys.prefix` vs `sys.base_prefix`

- `sys.base_prefix` = **真正**的 Python 装在哪（`/usr`）。
- `sys.prefix` = **当前激活**的环境在哪。

系统 Python 里两者相同；进了 venv，`sys.prefix` 变成 venv 目录，而 `base_prefix` 还指向 `/usr`。我在机器上现场验证过：

```text
系统 Python：   prefix=/usr             base_prefix=/usr            → 相同  → 两墙都生效
venv 里：        prefix=/tmp/demo-venv   base_prefix=/usr            → 不同  → 两墙都退场
```

那句 `prefix != base_prefix` **字面上**就是 ensurepip 决定「要不要退场」的判据；而 venv 目录里**根本没有 `EXTERNALLY-MANAGED` 文件**，于是 pip 的墙 1 检查也扑空。**同一个「进 venv」的动作，把两堵墙一起拆了**——不是靠某个 flag，不是靠 `sudo`，也不是靠 `--user`。

#### 那四行解法，逐行拆

```bash
sudo apt-get install -y python3-venv
```
Debian 把标准库拆成了多个包。`venv` 模块用来**引导 pip 的 wheel**被单独放在 `python3-venv` / `python3-pip-whl` 包里，不在基础 Python 里。缺了它，`python3 -m venv` 造出来的 venv **里面没有 pip**。这行保证 wheel 在场。

```bash
python3 -m venv ~/.venvs/lock && source ~/.venvs/lock/bin/activate
```
- `python3 -m venv ~/.venvs/lock` 造一个新环境：一个指回 `/usr/bin/python3.12` 的 `bin/python`、一个记着 `home = /usr/bin` 的 `pyvenv.cfg`（这正是让 `base_prefix` 指向 `/usr` 的原因），并且——因为 wheel 在场——它跑自己**内部**的 ensurepip 把 `pip` 放进 venv。而这个内部 ensurepip 正好命中那句 `prefix != base_prefix` 的早返回，于是放行。造完你就能看到：全新 venv 里已经自带 `bin/pip`、`bin/pip3`。
- `source .../activate` 只是把 venv 的 `bin/` 塞到 `$PATH` 最前面（并设 `$VIRTUAL_ENV`），于是 `python`、`pip` 都解析到 venv 自己的那份，而不是 `/usr/bin` 的。

```bash
pip install --index-url https://nexus.qantasloyalty.io/repository/pypi-all/simple pipenv
```
- 这个 `pip` 是 venv 的 pip → 没有 `EXTERNALLY-MANAGED` 墙 → 顺利安装。
- `--index-url` 为**这一次安装**把默认的 `https://pypi.org/simple` **替换**成公司内网 Nexus 代理。因为防火墙很可能挡掉了 pypi.org，这步必须走 Nexus；而 Nexus 的 `pypi-all` 是透明代理，拿到的包和哈希跟 PyPI 一样。

```bash
cd edr-pgp && pipenv lock
```
- `pipenv lock` 读仓库的 `Pipfile`，解析整张依赖图，写出带版本和哈希的 `Pipfile.lock`。它的索引地址取自 **`Pipfile` 的 `[[source]]`**（你早就改成了 Nexus），**不是**上面那个 `--index-url`（那个只管「装 pipenv 这个工具」）。这是你的 PR 真正需要重新生成的那个产物。

> 🔑 **一个 recipe 里两个 index URL，干的是两件事**：`--index-url` 这个 flag 负责**装 pipenn 工具本身**；`Pipfile` 的 `[[source]]` 负责**锁项目依赖**。把两者混为一谈，就是经典的「我明明设了 index，锁文件却还指向 pypi」的坑。

---

### 3. 🔬 面试官追问链

**Q1：为什么 `pip install --user` 在新 Ubuntu 上也被拒？不是说 `--user` 装到用户目录、很安全吗？**
因为真正的分界线**不是「用户级 vs 全局」，而是「系统解释器 vs venv 解释器」**。`--user` 装的东西仍然挂在**系统**解释器的包集合上，PEP 668 的标记照样生效。很多人栽在这个直觉上。

**Q2：venv 到底凭什么能绕过？它是复制了一份 Python 吗？**
不是复制。venv 是一层**很薄的重定向**：一个 `pyvenv.cfg` + 几个符号链接，把 `sys.prefix` 改成 venv 目录，而 `base_prefix` 仍指向真身。两堵守卫恰恰都建立在这个 `prefix != base_prefix` 的区别上，所以一句便宜的 `python3 -m venv` 就能同时解除两道封锁。

**Q3：这是我公司给电脑上的安全锁吗？**
不是。用 `dpkg -S` 查文件归属就知道：
```bash
dpkg -S /usr/lib/python3.12/EXTERNALLY-MANAGED   # libpython3.12-stdlib
dpkg -S /usr/lib/python3.12/ensurepip/__init__.py # python3.12-venv
```
两个文件都属于**原版 Ubuntu 包**，不是公司加的工具。公司在你这条链路里**唯一**的贡献是**网络侧**——防火墙 + Nexus 代理（所以才需要 `--index-url`）。Python 这边是标准的 Ubuntu 24.04 行为，全世界的 24.04 都一样。

**Q4：那为什么我以前从来没遇到过？**
因为 **PEP 668 的强制执行很新**，而你大概率一直在用「不碰系统 Python」的环境：
- Ubuntu **20.04 / 22.04 LTS** → **没有标记**，`pip install --user` 直接能用（很多公司 WSL 镜像到 2024 年前都还是 22.04）。
- Debian 12 bookworm（2023.6）、Ubuntu 23.04 → 第一批带标记。
- Ubuntu **24.04 LTS（2024.4）** → 带标记，而这是多数 IT 团队把新 WSL 镜像统一过去的 LTS。**你刚好经历的就是这次跳版**。
- 另外，**pyenv / conda / docker** 用的都是「非 apt 管理」的 Python，自然没有标记——你本机的 pyenv `3.11.5` 我查过，旁边就**没有** `EXTERNALLY-MANAGED`。你以前的习惯一直在悄悄替你挡着。

**Q5：遇到任何「公司电脑把我卡住了」，怎么快速判断是公司锁还是发行版默认？**
`dpkg -S <文件>`。如果文件归属于一个发行版包（像上面的 `libpython3.12-stdlib`），那就是上游策略，你在家里的笔记本上照样会遇到；只有归属不明/公司自己铺的文件，才是「公司侧」。把「发行版默认」和「公司加固」分清楚，是在受控环境里排障不内耗的第一刀。

---

**一句话收尾**：那一晚并没有发生什么玄学，也没有被公司单独上锁——我只是跨过了 Ubuntu 22.04 → 24.04 那条线，撞上上游 Python 终于开始强制执行的 PEP 668，而我平时的 pyenv / 老 LTS 习惯，一直在替我把这堵墙挡在视线之外而已。
