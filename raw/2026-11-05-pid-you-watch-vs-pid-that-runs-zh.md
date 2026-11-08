---
title: 你盯的 PID 不是干活的那个：PM2 + uv + interop 的双重错位
header:
    image: /assets/images/hd_containers.png
date: 2026-11-05
tags:
 - devops
 - debugging
 - wsl
 - pm2
 - reliability
permalink: /blogs/tech/zh/pid-you-watch-vs-pid-that-runs
lang: zh
layout: single
category: tech
---

> 你无法管理你没有测量的东西——但更危险的是，你在测量一个你以为是它、其实不是它的东西。

# 你的 gateway 崩溃了 865 次，但它从没真正重启过

*从「进程被管着」到「管的就是跑的那个」——一次跨越 WSL / Windows 边界的双重错位复盘*

这篇是上一篇 [`max_restarts 不是重启预算`](/blogs/tech/zh/pm2-max-restarts-is-not-a-budget) 的续集。同一个 `ecosystem.wsl.config.js`，同一个 PM2，但这次的雷不在配置的**语义**里，而在配置指向的**进程本身**——我盯着的那个 PID，根本不是真正在干活的那个。

起因很普通：我的 MCP gateway（一个常驻 HTTP 服务，监听 `127.0.0.1:8800`）又一次出现在故障列表里。`pm2 list` 给我的画面是这样的：

```
│ id │ name        │ status │ restarts │ uptime │
│ 1  │ mcp-gateway │ online │ 865      │ 16s    │
```

重启 865 次，当前存活 16 秒。典型的 crash-loop。我几乎要条件反射地去翻日志、看端口冲突。

但在动手之前，我多问了一句，然后 curl 了一下这个服务自己的健康端点：

```bash
$ curl -s http://127.0.0.1:8800/health
{"status":"ok","uptime_s":16187, ...}
```

**`uptime_s: 16187`。四个半小时。**

一个进程，PM2 说它活了 16 秒、崩了 865 次；它自己说它一口气活了 4.5 小时。两个数字不可能同时为真——除非，**PM2 盯的那个进程，和响应我这个 curl 的进程，压根不是同一个。**

这篇文章讲的就是这道裂缝：它为什么会出现，怎么跨越操作系统边界把它追出来，以及为什么它的根治方法只有一句话——**让你管的那个，就是跑的那个。**

## 读完你会得到

- **一个一眼识破影子进程的直觉**：当一个服务出现两个互相矛盾的「年龄」，不要去调和它们，要去数「到底有几个进程」。
- **一条反直觉的结论**：`uv run` 是开发期的好工具，但把它放进任何长期进程监督器的启动位，几乎总是在亲手制造孤儿。
- **一张追踪进程血缘跨越 WSL / Windows 边界的地图**，以及 interop 到底是什么、为什么它既是便利也是裂脑的温床。

下面按「最有用的先讲」排序，不按我当时的排查顺序——我当时绕的弯，没必要让你也绕。

---

## 一、一个进程不可能有两个年龄

排查的第一性问题从来不是「哪里坏了」，而是「我手上这两个信号，哪个在描述我真正关心的东西」。

把两个数字摆在一起：

| 信号 | 它说什么 | 它在描述谁 |
|---|---|---|
| `pm2 list` → `uptime 16s`, `restarts 865` | 一个每 15 秒自杀一次的进程 | **PM2 亲手 fork 出来的那个进程** |
| `/health` → `uptime_s 16187` | 一个稳定活了 4.5 小时的服务 | **真正 bind 了 :8800、响应请求的那个进程** |

两个信号都没撒谎。它们只是在描述**两个不同的进程**。PM2 在监控一个不断重生、不断夭折的东西；而真正服务我的，是另一个它根本不认识、已经在后台独活了 4.5 小时的进程。

> 当一个实体出现两个不可能共存的度量值，答案几乎从不是「其中一个错了」，而是「你以为的一个，其实是两个」。

这就是本文的脊柱，我给它起个名字叫**监督对齐性**：任何进程监督器（PM2、systemd、supervisord……）能提供的全部价值，都建立在一个契约上——**它盯着的 PID，必须就是真正干活的那个 PID。** 这个契约一旦破裂，监督器报告的一切——状态、重启次数、CPU、内存——全都是在描述一个影子。

而这个契约，有两种崩法。先看第一种。

---

## 二、纵向错位：`uv run` 的双 fork 孤儿

我的 `ecosystem.wsl.config.js` 里，gateway 这一段当初是这么写的：

```js
{
  name: "mcp-gateway",
  script: "uv",
  args: "run python gateway.py",
  cwd: "~/ws/project/ai/mcp/gateway",
}
```

看起来天经地义：用 `uv run` 跑 Python，环境、依赖都由 uv 搞定。但请盯着「PM2 到底 spawn 了谁」这个问题看。

PM2 的监督模型极其朴素：它 `spawn` 一个子进程，**记下那个子进程的 PID**，然后盯着这个 PID 的死活、向这个 PID 发信号、按这个 PID 统计重启。一切都绑在「它亲手 fork 的那个 PID」上。

而 `uv run python gateway.py` 实际发生的是：

```
PM2 spawn ──► uv (PID 1654)          ← PM2 以为「app = 1654」，盯着它
                 │  uv 准备好环境（定位 venv、同步依赖、设 PATH）
                 └──► python3 gateway.py (PID 3841)   ← 真正 bind :8800 的是它
```

`uv run` **不会把自己 exec 替换掉**，而是另起一个子进程跑你的命令，自己留在上面当父进程。于是永远是两层：`uv(1654)` 当父，`python(3841)` 干活。PM2 认识 1654，但占着 :8800 的是 3841。

错位就此埋下。引爆它的是任何一次重启：

| 步骤 | 发生了什么 |
|---|---|
| 1 | PM2 要重启 → 对它记录的 PID 1654（uv）发 SIGTERM |
| 2 | uv 死了，但子进程 3841（python）**没跟着死**，被过继给 PID 1，成了**孤儿**，继续死攥 :8800 |
| 3 | PM2 看见 1654 没了 → 判定 app 死了 → `spawn` 新的 uv → 新 uv 拉起新 python |
| 4 | 新 python 想 bind :8800 → **`EADDRINUSE`**（被孤儿 3841 占着）→ 立刻崩溃 |
| 5 | PM2 又判定挂了 → 再重启 → 再撞孤儿 → **无限 crash-loop** |

865 次重启，就是这么烧出来的。而那个「活了 4.5 小时」的 `/health`，正是步骤 2 里那个最早逃逸、至今没被杀掉的孤儿在应答。两个年龄的谜底，到这里闭合了。

> 「双 fork」本是守护进程**故意**用来脱离父进程、挂到 init 下的经典手法。`uv run` 并非存心 daemonize，但「包装器 → 子进程」这一层间接，恰好复刻了同样的效果：真正要紧的那个孙子进程，逃出了监督器的视野和信号范围。

**普通人的看法**：uv run 跑得好好的，手动起服务完全正常，所以配置没问题。
**资深工程师的洞察**：「手动跑正常」和「被监督器托管正常」是两回事。前者你就是那个父进程，你眼里有子进程；后者监督器是父进程，而它眼里只有 uv 这层壳。

根治方法只有两行，让 PM2 直接 spawn 真正的解释器：

```js
{
  name: "mcp-gateway",
  script: ".venv/bin/python3",   // 原来是 "uv"
  args: "gateway.py",            // 原来是 "run python gateway.py"
  cwd: "~/ws/project/ai/mcp/gateway",
}
```

`.venv/bin/python3` 本就是这个 venv 的解释器，依赖、site-packages 天然在里面——运行时根本不需要 uv 再兜一层。uv 的价值在**开发期的装/锁依赖**，不在**生产期的进程常驻**。用对层级，错位消失。

改完之后，我做了一次对齐验证：

```bash
$ 端口属主 pid = 41960
$ PM2 记录 pid = 41960   ✅ 一致
```

**PM2 盯的，就是占端口的那个。** 契约第一次真正成立。这是我的第一个立场：**把 `uv run` 放进 PM2 / systemd 的 script 位，几乎总是错的——它是装依赖的工具，不是进程运行时。**

---

## 三、插曲：interop 是什么，以及它凭什么让第二个管家钻进来

修好纵向错位，我以为结束了。结果端口又被抢。而追凶的过程，逼着我把 WSL 的一个底层机制彻底搞明白——**interop**。先讲清楚它，第四章的「横向错位」才看得懂。

**Interop（Windows-Linux 互操作）= WSL2 和 Windows 之间互相调用对方可执行程序的能力。** 它是双向的：

- 你在 WSL（Linux）里，能直接敲 `powershell.exe`、`schtasks.exe`、`wsl.exe` 这些 **Windows 的 .exe**，它们真的在 Windows 侧跑起来，输出回传到 Linux 终端。
- 反过来，Windows 里 `wsl.exe -d Ubuntu -- <命令>` 能钻进 Linux 跑东西。

Linux 里敲 `powershell.exe` 为什么会「魔法般」跑起来？靠的是内核的 **`binfmt_misc`** 机制：它注册了一条规则——「遇到 `.exe` 文件，交给一个叫 `/init` 的进程，转发到 Windows 执行」。这个 `/init` 就是 interop 的**边界翻译官**。

还记得上一次你追进程血缘，`ps` 一路往上爬，突然撞到一堆 `/init` 就断了吗？那不是进程树坏了——**那就是你撞到了 OS 边界的路标。** `/init` 意味着：这个进程的真正发起方，不在 Linux 这边，在 Windows 那边。

> 这正是我称为**信息单向性**的东西：每一道上下文边界（宿主↔客户机、前端↔后端、ORM↔SQL），都会按自己那侧的假设重写信息。跨过 `/init` 这道边界，Linux 的 `ps` 就再也看不清上游了——语义还在，但得换一侧的工具（Windows 的进程表）才能读出来。

记住这一点：**当进程链撞到 `/init`，你要换到 Windows 侧继续追。** 第四章就是这么破案的。

---

## 四、横向错位：一台机器上的两个 PM2

端口再次被抢，但这次 WSL 里的 PM2 明明是干净的。我追 :8800 属主的血缘：

```
python3 gateway.py (占 :8800)
  ← uv run --directory ~/ws/project/.../gateway python gateway.py
      ← /init        ← 撞到边界了！发起方在 Windows 侧
```

按第三章的教训，换到 Windows 侧继续追。我在 WSL 里直接调 `powershell.exe` 查 Windows 进程表，找命令行里带 `gateway` 的进程：

```powershell
ProcessId   : 24040
Name        : wsl.exe
CommandLine : "C:\Program Files\WSL\wsl.exe" -d Ubuntu -u <you> --
              zsh -lc "... exec uv run --directory
              ~/ws/project/ai/mcp/gateway python gateway.py"
```

一个 Windows 上的 `wsl.exe`，反向钻进 WSL 来启动我的 gateway。那它的父进程是谁？继续往上追：

```
wsl.exe (24040)
  ← node  ...\pm2\lib\ProcessContainerFork.js  (PID 45564)   ← 一个 PM2 app 的 worker
      ← node  ...\pm2\lib\Daemon.js            (PID 70044)   ← PM2 守护进程本体
```

真相大白：**那个「Windows 侧启动器」从来不是什么神秘任务，它就是第二个 PM2——只不过装在 Windows 上。**

我这台机器上有**两个 PM2**。我查了一下 Windows 那个的 app 列表：

```
name              pm_id  restart_time
toddy-portal      0      0
mcp-gateway       1      99     ← 靠 launcher.js → wsl.exe 钻进 WSL 跑，占 :8800
bank-chatbot-api  2      156
portal-api        3      2693   ← 疯狂 crash-loop，抢不到 :8002
```

它跑着一整套**和 WSL 侧几乎重复**的 stack。两个监督器，各自以为自己独占这些端口，于是永远在抢：

| | WSL PM2 | Windows PM2 |
|---|---|---|
| 它以为自己管着 | gateway + 另外三个 | gateway + 另外三个 |
| :8800 实际归谁 | 抢不到就 crash-loop | 这次它赢了，占着 |
| :8002 实际归谁 | 它赢了 | 抢不到 → portal-api 重启 2693 次 |
| 症状 | 跨会话随机崩溃 | 后台默默烧 CPU |

这就是**横向错位**，也叫裂脑（split-brain）：两个 supervisor 持有几乎相同的 app 清单，抢同一批资源。谁先启动谁绑上，另一个永远 crash-loop。它比纵向错位更隐蔽——因为**表面上总有一个在正常跑**，代价全在后台空转里。

```
★ 为什么 interop 是帮凶 ──────────────────────
正因为 interop 双向打通，Windows 的 PM2 才能通过 wsl.exe
反向伸手进 WSL 占端口。没有 interop，两个 OS 的进程各管各的，
裂脑根本无从发生。interop 是把双刃剑：它消除了「跨 OS 跑命令」
的摩擦，也消除了「谁在管什么」的清晰边界。
────────────────────────────────────────────
```

根治横向错位，和纵向一样，只有一个原则：**一个服务，只能有一个管家。** 我选择让 WSL PM2 独管（这才符合「WSL 内统一管理」的初衷），于是把 Windows PM2 的四个 app 全部删掉：

```powershell
pm2 delete all
pm2 save --force
```

`delete` 停掉并移除，`save --force` 把它们从开机自动恢复清单里抹掉——它们重启后不会再回来。那个烧 CPU 的 `portal-api` 2693 次重启，也随之消失。

> 这是我的第二个立场：**一个服务被两个监督器管，比被零个监督器管更糟。** 零个管，它死了你立刻知道；两个管，它永远「看起来活着」，而你永远不知道信任哪一个的读数。

---

## 五、把两种错位缝起来

这次故障的两个病灶，长得完全不同——一个是进程包装器，一个是跨 OS 的第二个守护进程——但它们犯的是**同一个错误**：

| | 错位发生在 | 监督器盯的 | 真正干活的 | 修法 |
|---|---|---|---|---|
| **纵向**（uv 孤儿） | 一个进程内部的父/子层级 | uv 包装器 (1654) | python 解释器 (3841) | 让 PM2 直接 spawn 解释器 |
| **横向**（裂脑） | 两个 OS 的两个监督器之间 | 各自以为的那份 | 实际抢到端口的那个 | 砍到只剩一个监督器 |

两种错位，一个脊柱：**监督的对齐性。** 纵向是「你管的那层，不是干活的那层」；横向是「管它的，不止你一个」。只要「管」和「跑」没有严格一一对应，监督器给你的所有读数，都是在描述影子。

而这，恰好接上了上一篇的主题。上一篇讲的是仪表的**语义**会骗你（`max_restarts` 是时间窗不是计数）；这一篇讲的是仪表盯错了**对象**（它盯的 PID 不是干活的 PID）。前者是「体重秤的刻度被改了」，后者是「你称的根本是另一个人」。两篇合起来才是完整的一句话：

> 一个健康检查要可信，既要度量对的**量**，也要度量对的**那个东西**。

---

## 立刻可以做的事

1. 对你每一个被 PM2 / systemd 托管的服务，做一次**对齐核对**：`监督器记录的 PID` 是否等于 `实际 bind 端口的 PID`（`ss -ltnp` 看属主）？不相等，你就在监督一个影子。
2. 翻出你的 ecosystem / service 文件，看 `script` 位是不是 `uv run` / `npm run` / `poetry run` 这类**包装器**。是的话，换成它最终 exec 的那个真实可执行文件（`.venv/bin/python3`、`node`、具体的 binary）。
3. 当一个服务报出**两个矛盾的「年龄」或「状态」**，别去调和数字——先 `pgrep -af <name>` 数一数到底有几个进程。影子进程藏在数量里。
4. 如果你同时用 WSL 和 Windows：在**两侧**都跑一次 `pm2 list`（Windows 侧用 `powershell.exe pm2 list`）。确认同一个服务没有被两个 PM2 各管一份。
5. 学会一个追凶动作：`ps` 往上爬时一旦撞到 `/init`，立刻换到 Windows 侧用 `powershell.exe Get-CimInstance Win32_Process` 继续追。`/init` 不是终点，是边界。

---

*监督器能告诉你的，永远只是「我盯着的那个还在不在」。它说不了的那句话——「我盯的是对的那个吗」——才是你自己要负责回答的。*
