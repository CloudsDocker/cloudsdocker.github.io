---
title: CUI ? GUI? pm2 在 Windows 上疯狂弹窗？问题不在配置，在可执行文件的 PE 头
header:
    image: /assets/images/hd_nodejs_faq.png
date: 2026-10-31
tags:
 - devops
 - python
 - windows
 - fastapi
 - debugging
permalink: /blogs/tech/zh/pm2-windows-crash-loop-pythonw
lang: zh
layout: single
category: tech
---

> "问题永远不是你看到的那个。" —— 理查德·费曼

# 你的 pm2 在 Windows 上疯狂弹黑窗口，关掉又打开——别急着怪 pm2

*从端口冲突到 PE 文件头——一次三层调试揭示的 Windows 进程本质*

傍晚六点半，我在 toddy_portal 项目上跑了一句 `pm2 start ecosystem.config.js`，然后桌面就炸了。

黑色终端窗口像弹幕一样涌出来，一秒一个，关掉立刻又弹。任务栏上十几个黑框堆叠闪烁，鼠标都来不及点。第一反应是 pm2 出 bug 了，第二反应是 Windows 中毒了。两个都不对。

读完这篇你会拿到三个东西：

- **为什么 pm2 的 crash-loop 在 Linux 上无感，在 Windows 上是视觉灾难**——这不是 pm2 的 bug，而是操作系统进程模型的根本差异
- **`windowsHide: true` 为什么治不了这个病**——以及什么才能治
- **一套可以直接抄的 `restartGuard` 模板**，让你的 ecosystem.config.js 在任何平台都不再出现无限重启风暴

## 1. 第一层：一个端口冲突引爆无限重启

pm2 日志里疯狂重复同一条错误：

```
ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8002):
       [winerror 10048] only one usage of each socket address
       (protocol/network address/port) is normally permitted
```

原因很简单：之前为了临时测试手动跑了一个 `python -m portal_api.main`，占着 8002 没杀。uvicorn 启动 → 绑端口失败 → 进程退出 → pm2 默认立即重启 → 又失败 → 又重启……

| 维度 | 默认行为 | 后果 |
|---|---|---|
| `autorestart` | `true` | 退出就拉起 |
| `max_restarts` | 无上限 | 永远不放弃 |
| 重启延迟 | 0 | 一秒一个 |
| 退出到重启间隔 | ~100ms | 每次弹一个窗口 |

这在 Linux 上完全无感——子进程共享父终端，没有新窗口可弹，你最多在 `pm2 ls` 里看到 restart 次数飙升。但 Windows 不是这么玩的。

> 同一行配置，跨平台之后行为可以天差地别。诊断问题之前，先问一句：我真的理解这行代码在目标平台上意味着什么吗？

## 2. 第二层：为什么每次重启都弹一个窗口——Windows 控制台子系统

杀掉占端口的进程后，crash-loop 停了。两个 Python 服务稳定运行了。

但窗口还在。

两个黑色终端窗口安安静静地待在桌面上，一个是 `portal-api`（8002），一个是 `bank-chatbot-api`（8001）。关掉？pm2 认为服务挂了，又拉起来，窗口又回来。

这才是真正有意思的地方。

Windows 的每一个可执行文件（PE 格式）在文件头里都有一个 `Subsystem` 字段：

| PE Subsystem | 常量值 | 行为 |
|---|---|---|
| `IMAGE_SUBSYSTEM_WINDOWS_CUI` | 3 | **Console 子系统**——系统一定给你分配一个控制台窗口 |
| `IMAGE_SUBSYSTEM_WINDOWS_GUI` | 2 | **GUI 子系统**——不自动创建控制台窗口 |

`uv.exe`、`python.exe`、`cmd.exe` 全都是 CUI 子系统。当 pm2（一个 node 进程）通过 `child_process.spawn` 拉起这些 exe 时，Windows 发现子进程需要 console 但父进程（node）本身可能没有可用 console，于是——**必须新建一个**。

这不是 pm2 的 bug。这是 Windows 的 CreateProcess 规则：**CUI 程序没有 console 可继承时，系统一定会给它新建一个。**

那 pm2 的 `windowsHide: true` 呢？它应该往 `CreateProcess` 的 `dwCreationFlags` 里传 `CREATE_NO_WINDOW`。但实际测试发现，当配置为 `interpreter: "none"`（直接执行外部 exe）时，这个标志不会被可靠地传递。可能是 pm2 的 fork 模式实现问题，也可能是 node 的 `child_process` 在 Windows 上的行为差异——总之，**`windowsHide` 是一个不可靠的解决方案**。

> 面试拿分点：如果有人问"Windows 上进程为什么会弹终端窗口"，答 PE 头的 Subsystem 字段，而不是"系统设置"或"控制台属性"。这是二进制级别的行为决定，在编译的那一刻就定了。

## 3. 第三层：真正的解法——pythonw.exe

Python 安装包里自带两个可执行文件：

| 文件 | Subsystem | 窗口行为 | 功能 |
|---|---|---|---|
| `python.exe` | CUI (Console) | 一定有终端窗口 | 完整的 Python 解释器 |
| `pythonw.exe` | GUI (Windows) | 不创建终端窗口 | **完全一样的** Python 解释器 |

它们的区别**只有一个**：PE 头里的 Subsystem 字段值不同。运行能力完全相同——能跑脚本、能跑模块、能跑 uvicorn。而 pm2 通过管道捕获 stdout/stderr，不依赖子进程有没有控制台窗口，所以日志完全不受影响。

### 修改前

```js
{
  name: "portal-api",
  script: "C:\\...\\uv.exe",                    // CUI → 弹窗
  args: "run uvicorn portal_api.main:app --host 127.0.0.1 --port 8002",
  interpreter: "none",
}
```

### 修改后

```js
{
  name: "portal-api",
  script: path.join(__dirname, "services", "portal_api",
                    ".venv", "Scripts", "pythonw.exe"),  // GUI → 无窗口
  args: "-m uvicorn portal_api.main:app --host 127.0.0.1 --port 8002",
  interpreter: "none",
}
```

窗口彻底消失。pm2 日志、健康检查、流量代理一切正常。

## 4. 完整的 restartGuard 模板——直接抄

不管你用不用 pythonw，这套重启护栏都应该加上。它把 crash-loop 从"无限风暴"降级为"试几次就放弃"：

```js
const restartGuard = {
  autorestart: true,
  min_uptime: "10s",                  // 10 秒内退出才算崩溃
  max_restarts: 5,                     // 崩 5 次就放弃
  exp_backoff_restart_delay: 2000,     // 退避：2s → 4s → 8s → 16s → 32s
  windowsHide: true,                   // 聊胜于无
};
```

| 参数 | 没设时的行为 | 设了之后 |
|---|---|---|
| `min_uptime` | 任何退出都触发重启 | 正常运行超过 10s 后退出，reset 重启计数 |
| `max_restarts` | 无限 | 5 次后标记 errored，不再重启 |
| `exp_backoff_restart_delay` | 0ms | 指数退避，最慢约 30 秒一次 |

即使在 Linux 上，裸配 pm2 的 crash-loop 也会产生 CPU 空转和日志爆炸。加上 guard 是基本卫生。

## 回顾：三层调试的完整路径

| 层 | 现象 | 根因 | 修法 |
|---|---|---|---|
| 1. crash-loop | 窗口疯狂弹出 | 端口 8002 被占 → uvicorn bind 失败 → pm2 无限重启 | 杀掉占端口的进程 + 加 restartGuard |
| 2. 常驻窗口 | 服务稳定但桌面上有两个黑窗口 | `uv.exe` 是 CUI 子系统，Windows 必须给它分配 console | 认清 `windowsHide` 不可靠 |
| 3. 根治 | — | PE 头的 Subsystem 决定一切 | 用 `pythonw.exe`（GUI 子系统）替代 `uv.exe` |

> 第一性原理：不要在应用层修补系统层的行为。Windows 给 CUI 进程分配 console 是操作系统的硬性规则——你想绕过它，就不能还站在 CUI 的地盘上。换一个 Subsystem 才是跟系统用同一种语言说话。

## 立刻可以做的事

1. **`grep -r 'interpreter.*none' ecosystem.config.js`** — 看看你的 pm2 配置里有没有直接执行 `.exe` 的 app。如果有且在 Windows 上跑，检查那个 exe 是什么子系统。
2. **给每个 app 加 restartGuard** — 把上面的模板抄进去。这 10 秒钟的投入能省你几十分钟的 crash-loop 诊断时间。
3. **Windows 上 Python 服务一律用 `pythonw.exe` 启动** — 不只是 pm2，任何进程管理器（supervisord, NSSM, Windows Service wrapper）都适用这个原则。


---

*你看到的窗口不是 bug，是操作系统在用它唯一会说的语言告诉你：你启动的程序类型不对。*
