---
title: "面对1966次崩溃重启，如何构建更坚固的系统"
header:
    image: /assets/images/hd_nodejs_faq.png
date: 2026-11-04
tags:
 - devops
 - debugging
 - reliability
 - observability
permalink: /blogs/tech/zh/pm2-max-restarts-is-not-a-budget
lang: zh
layout: single
category: tech
---

> 改变温度很难，但是改变温度计就容易多了；改变体重很难，但是改变体重秤就简单多了。

# `max_restarts: 5` 没拦住 1966 次重启

*从「进程还活着」到「服务真的能用」——中间隔着一整套会说谎的仪表*

早上九点，我在 MacBook 上打开 `http://100.124.38.9:3000/notes`，白屏。换另一个 IP，还是白屏。

我的第一反应和你大概一样：Tailscale 又抽风了。

然后我 SSH 进 WSL，敲了 `pm2 list`：

```
│ id │ name         │ status │ restarts │
│ 0  │ toddy-portal │ online │ 1966     │
```

`online`。

但 `ss -tlnp | grep :3000` 什么都没返回。端口是空的。

**1966 次重启**——而配置里明明白白写着 `max_restarts: 5`。

这篇文章不是「我修好了一个 bug」。是我花了二十分钟才意识到：从昨晚 22:56 到今早 09:10，整整十个小时，这个服务一直在以每 15 秒一次的节奏自杀，而我的三套监控——PM2 的状态、PM2 的重启上限、我自己写的冒烟测试——**全都在报绿**。

## 读完你会得到

- **一个可验证的直觉**：`max_restarts` 不是「最多重启 N 次」，它是「崩溃检测器只武装 `min_uptime × max_restarts` 毫秒」——这是时间窗，不是计数预算。
- **一条反直觉的结论**：你配的指数退避（`exp_backoff_restart_delay`）会**主动花掉**那个检测窗口。退避越礼貌，崩溃保护越确定不会触发。
- **一把尺子**：判断一个健康检查是在测体重，还是在测体重秤。

下面按「最有用的先讲」排序，不按我当时的排查顺序——我当时的顺序里有二十分钟是浪费在 Tailscale 上的。

---

## 一、先把三个说谎的仪表摆在一起

排查的起点不该是「哪里坏了」，而是「我手上哪些信号是可信的」。把这次的信号列出来：

| 仪表 | 它说什么 | 真相 | 为什么它不算撒谎 |
|---|---|---|---|
| `pm2 list` → `online` | 进程活着 | 进程确实刚被 fork 出来，0.15 秒后会死 | PM2 报告的是**进程状态**，从来不是服务状态 |
| `restarts: 1966` 但 `max_restarts: 5` | 上限失效了 | 上限的语义不是「次数」 | 见第三章，这是本文的主菜 |
| `wsl_portal.sh test` → 全绿 | 服务健康 | 它只 curl `127.0.0.1`，而我的问题是**远程**打不开 | 它测的东西确实是好的，只是跟我的问题无关 |

三个仪表，零个说谎，而我被彻底误导了十个小时。

> 一个信号的价值，不取决于它准不准，而取决于它和你要回答的问题之间的距离。

### 五个为什么

```
Mac 上打不开 portal
  └─ 为什么？端口 3000 没有监听
      └─ 为什么？Next.js 进程启动后 0.15 秒就退出了
          └─ 为什么？app.prepare() reject：找不到 production build
              └─ 为什么？.next/ 目录在，但里面没有 BUILD_ID
                  └─ 为什么？这个目录是 turbopack dev 模式留下的残骸
```

真正的根因在第五层。而第一层给我的提示是「网络问题」。

---

## 二、`.next/` 存在 ≠ 构建存在

PM2 的错误日志里，这行重复了 1966 次：

```text
[DEBUG] after next(), before prepare()
[DEBUG] prepare() REJECTED: Error: Could not find a production build in
        the '.next' directory. Try building your app with 'next build'
        before starting the production server.
```

而当时 `.next/` 目录是**存在**的：

```bash
$ ls .next/
cache/  diagnostics/  server/  static/  types/  lock  package.json  turbopack
$ cat .next/BUILD_ID
cat: .next/BUILD_ID: No such file or directory
```

这是整件事里第一个假阳性，也是最容易复发的一个：**Next.js 的 dev 模式和 production 模式共用同一个 `.next/` 目录名，但写进去的是两套完全不同的东西。**

| | dev（turbopack） | production（`next build`） |
|---|---|---|
| 写 `cache/` `server/` `static/` | ✅ | ✅ |
| 写 `BUILD_ID` | ❌ | ✅ |
| `next start` 认不认 | ❌ | ✅ |

所以任何形如 `if [ -d .next ]` 的检查都是**结构性错误**的。`next start` 真正去找的文件是 `BUILD_ID`，你的检查就必须找同一个文件：

```bash
[ -f "${PORTAL_DIR}/.next/BUILD_ID" ]
```

> **面试拿分点**：当你要检查「某个产物是否就绪」，正确的做法不是找一个「看起来相关」的路径，而是去读消费方的源码，找它**实际会打开的那个文件**。目录是约定，文件才是契约。

---

## 三、`max_restarts` 不是重启预算（本文的主菜）

这是我最想写下来的一章，因为它让我对「我以为我懂的配置项」重新谦虚了一次。

我的 `ecosystem.wsl.config.js` 里有这么一段，当初写它的时候，我自认为是在做防御性设计：

```js
const restartGuard = {
  autorestart: true,
  min_uptime: "10s",
  max_restarts: 5,
  exp_backoff_restart_delay: 2000,
};
```

我当时的心智模型是：「如果一个应用崩了 5 次，PM2 就放弃，别把机器拖死。」

**这个心智模型是错的。** 去读 PM2 的源码（`lib/God.js`，v6 分支）：

```js
var min_uptime   = typeof(proc.pm2_env.min_uptime)   !== 'undefined' ? proc.pm2_env.min_uptime   : 1000;
var max_restarts = typeof(proc.pm2_env.max_restarts) !== 'undefined' ? proc.pm2_env.max_restarts : 16;

if ((Date.now() - proc.pm2_env.created_at) < (min_uptime * max_restarts)) {   // ← 外层：时间窗
  if ((Date.now() - proc.pm2_env.pm_uptime) < min_uptime) {                   // ← 内层：本次存活
    proc.pm2_env.unstable_restarts += 1;
  }
}

if (proc.pm2_env.unstable_restarts >= max_restarts) {
  proc.pm2_env.status = cst.ERRORED_STATUS;   // 只有走到这里，PM2 才会放弃
  overlimit = true;
}
```

请盯着外层那个 `if` 看三秒钟：

```js
(Date.now() - created_at) < (min_uptime * max_restarts)
```

`max_restarts` 在这里**不是被当作次数用的，它是乘数**。它和 `min_uptime` 相乘，算出来的是一段**墙上时钟时间**。我的配置：

```
10,000 ms × 5 = 50,000 ms = 50 秒
```

**PM2 只在应用诞生后的头 50 秒内，才会去数不稳定重启。** 50 秒一过，外层 `if` 永远为假，`unstable_restarts` 再也不会 +1，那个 `>= max_restarts` 的判断就永远不可能成立——**崩溃保护被永久地、静默地卸载了**。

### 更反直觉的部分：退避在吃掉你的检测窗口

现在把 `exp_backoff_restart_delay: 2000` 叠进来。同样是 `God.js`：

```js
proc.pm2_env.prev_restart_delay = Math.floor(Math.min(15000, proc.pm2_env.prev_restart_delay * 1.5))
```

每次重启等待时间 ×1.5，上限 15 秒。于是在那宝贵的 50 秒侦测窗口里，PM2 大部分时间在**睡觉**：

| 崩溃序号 | 累计时刻 | 退避等待 | 窗口剩余 |
|---|---|---|---|
| #1 | 0.15 s | 2.0 s | 49.8 s |
| #2 | 2.3 s | 3.0 s | 47.7 s |
| #3 | 5.5 s | 4.5 s | 44.5 s |
| #4 | 10.1 s | 6.75 s | 39.9 s |
| #5 | 17.0 s | 10.1 s | 33.0 s |
| #6 | 27.3 s | 15.0 s（封顶） | 22.7 s |

两个条件是 **AND** 的关系，任何一个不成立，计数器就不动：

- **外层**：必须在头 50 秒内。退避把崩溃事件稀释了，很容易撑不到第 5 次就出窗。
- **内层**：本次进程必须活不过 10 秒。这条在空闲机器上成立（实测崩溃耗时 **0.153 秒**），但那天晚上 WSL 正扛着一整套 Airflow 容器和 60 个 MCP 进程，内存 95%、swap 吃掉 10GB、IO 压力 `full avg10=14%`——而 `server.js` 启动时要去 `/mnt/c/Users/.../toddy_backup.db` 打开一个跨 9P 挂载的 SQLite。在那种负载下，单次启动超过 10 秒完全是常态。

我没有当晚逐次的计时日志，**无法断定是哪一个条件先失效**。但这恰恰是我想强调的：**这两个条件都是时间性的，都会在你不知情的时候失效，而失效的表现完全一样——一个标称「最多 5 次」的保护，跑出了 1966 次。**

> 这就是「对称性破缺」的典型形态：`max_restarts` 这个名字承诺了一个计数语义，实现给的却是一个时间语义。名字和机制之间的这道裂缝，就是所有「我以为它会拦住」类故障的温床。

### 算一笔账

```
1966 次 × 15 秒（退避封顶） ≈ 8.19 小时
```

加上每次 node 冷启动的开销，正好填满从昨晚 22:56 到今早 09:10 的那十个小时。数字对得上，故事就闭环了。

---

## 四、`created_at` 会活过 WSL 重启

还有一个零件要装上去，不然上一章的机制解释不了「为什么它从第一次崩溃起就没在数」。

PM2 在 `God.executeApp()` 里这样处理 `created_at`：

```js
if (!env_copy.created_at)
  env_copy['created_at'] = Date.now();
```

**只在它为空时才赋值。** 而崩溃后的自动重启走的正是 `God.executeApp(proc.pm2_env)` 这条路——`created_at` 被原样带过去，不刷新。只有手动 `pm2 restart` 才会走 `God.resetState()`：

```js
God.resetState = function(pm2_env) {
  pm2_env.created_at = Date.now();
  pm2_env.unstable_restarts = 0;
  pm2_env.prev_restart_delay = 0;
};
```

更要命的是，`pm2 save` 会把 `created_at` 原封不动写进 `~/.pm2/dump.pm2`：

```
dump.pm2 存盘于     2026-11-03 22:56:34
  created_at        2026-11-03 22:56:31
  unstable_restarts 1
```

于是 `pm2 resurrect` 之后，应用的「年龄」是从**上辈子**继承来的。如果 dump 里那个 `created_at` 已经是几小时前，那么应用一复活，50 秒的侦测窗口**早就过期了**——崩溃保护出生即死亡。

| 触发路径 | `created_at` | 崩溃检测器 |
|---|---|---|
| 手动 `pm2 restart` | 刷新 | 重新武装 50 秒 |
| 崩溃后自动重启 | 继承 | 继续倒计时 |
| `pm2 resurrect`（开机/`wsl --shutdown` 之后） | **从 dump 继承** | **可能一上来就是过期的** |

对任何用 `pm2 save` + `pm2 startup` 做开机自启的人，最后一行是个真实的坑：**你以为重启机器等于重置状态，实际上 PM2 把时间也一起存盘了。**

---

## 五、冒烟测试测 `127.0.0.1`，等于没测

我那个脚本里的 `test` 子命令，三项全绿：

```bash
curl -s -f -m 3 http://127.0.0.1:3000
curl -s -f -m 3 http://127.0.0.1:8002/healthz
curl -s -m 3 http://127.0.0.1:8800/health
```

但我的故障是「**Mac 上**打不开」。回环地址对这个问题的信息量是**零**：它既不经过网卡绑定（`127.0.0.1` vs `0.0.0.0`），也不经过 Tailscale，也不经过防火墙。

顺带说，我在 Tailscale 上还踩了两脚，都是同一类错误——**把两个节点当成一个**：

```
100.85.1.56     aidra-studio-wsl     linux     ← portal 跑在这里
100.124.38.9    aidra-studio         windows   ← 另一台机器，没人监听 3000
100.104.0.40    todd-macbook-pro     macOS     offline, last seen 107d ago
```

WSL 和 Windows 宿主机在 tailnet 上是**两个独立节点、两个独立 IP**。我试的第二个 URL 指向 Windows 那个节点，它永远不会通。

而最后一行更彻底：我的 MacBook **已经 107 天没上过这张 tailnet 了**。就算服务是好的，也连不通。

> 分布式系统的调试里，最贵的时间往往花在「两个东西其实是两个东西」上。

---

## 六、把部落知识变成工程产物

修复本身是两行 `npm run build`，没什么可说的。值得说的是：**这次故障暴露的每一个认知，如果只留在我脑子里，三个月后一定会重演。**

所以真正的交付物是把它们编码进脚本：

```bash
check_build() {
    # 一个 '.next' 目录可能只是 dev/turbopack 跑过的残骸。
    # BUILD_ID 才是 'next start' 实际会去找的文件，所以检查它——
    # 否则 PM2 会安静地崩溃循环在 prepare() 上。
    if [ ! -f "${PORTAL_DIR}/.next/BUILD_ID" ]; then
        echo "❌ No production build found (${PORTAL_DIR}/.next/BUILD_ID missing)."
        echo "   Run 'npm run build' in ${PORTAL_DIR} first."
        exit 1
    fi
}
```

以及给冒烟测试补上那条真正对应故障场景的检查：

```bash
# 4. Tailscale —— 回环通了，对远程访问零信息量
TS_IP=$(tailscale ip -4 2>/dev/null | head -1)
if [ -z "${TS_IP}" ]; then
    echo "4. Tailscale UI reachability... ⏭️  SKIPPED (no tailscale0 in this WSL)"
else
    echo -n "4. Testing Toddy Portal UI over Tailscale (http://${TS_IP}:3000)... "
    if curl -s -f -o /dev/null -m 5 "http://${TS_IP}:3000"; then
        echo "✅ OK"
    else
        echo "❌ FAILED (port 3000 may be bound to 127.0.0.1 only)"
    fi
fi
```

改完之后，把 `BUILD_ID` 挪走做了一次反向验证——守卫确实拦住了，退出码 1，而且在 PM2 被调用**之前**就拦住了：

```
$ ./scripts/wsl_portal.sh restart
❌ No production build found (/home/phray/.../.next/BUILD_ID missing).
   Run 'npm run build' in /home/phray/... first.
exit=1
```

然后是全绿，而且这次的「全绿」是有意义的：

```
1. Testing Toddy Portal UI (http://127.0.0.1:3000)... ✅ OK
2. Testing portal-api Health (http://127.0.0.1:8002/healthz)... ✅ OK
3. Testing mcp-gateway Health (http://127.0.0.1:8800/health)... ✅ OK
4. Testing Toddy Portal UI over Tailscale (http://100.85.1.56:3000)... ✅ OK
```

> Senior 修好这个 bug，Principal 让这个 bug 下次在三秒内自报家门。差别不在于谁更懂 PM2 源码，而在于谁愿意把刚学到的东西从脑子里搬到仓库里。

---

## 把三章缝起来

这次故障里三个独立的组件骗了我，但它们犯的是**同一个错误**：

| 仪表 | 它测的（体重秤） | 应该测的（体重） |
|---|---|---|
| `pm2 list` → `online` | 进程被 fork 出来了 | 端口在监听、能返回 200 |
| `max_restarts: 5` | 头 50 秒内的崩溃密度 | 这个应用到底能不能起来 |
| `wsl_portal.sh test` | 回环可达 | 我真正访问的那条路径可达 |
| `ls .next/` | 目录存在 | `BUILD_ID` 存在 |

每一行左边那列都**便宜、好测、好实现**——这正是它们成为默认值的原因。右边那列贵，所以工具默认不给你。

**所以这是我的立场：任何你没有亲手验证过「它在故障时会变红」的健康检查，都应该默认当它是绿色噪音。** 一个从未失败过的检查项，和一个 `echo "✅ OK"` 的硬编码，在信息量上是等价的。

---

## 立刻可以做的事

1. 翻出你自己的 `ecosystem.config.js`，把 `min_uptime × max_restarts` 乘出来。那个秒数就是你的崩溃保护**全部的有效期**。如果你同时配了 `exp_backoff_restart_delay`，再问一句：在这段时间里，退避会让它睡掉多少？
2. `pm2 jlist | jq '.[] | {name, restart_time, unstable_restarts}'`——任何 `restart_time` 三位数以上而 `unstable_restarts` 是 0 的应用，都值得你去看一眼日志。那是「保护已失效」的特征信号。
3. 给每个 `*_service.sh start` 加一条前置断言，检查**消费方实际会打开的那个文件**（`BUILD_ID`、`.jar`、`dist/index.js`），而不是它所在的目录。
4. 把你的冒烟测试里所有 `127.0.0.1` 过一遍：如果用户是从别的机器访问的，这条检查对真实故障的覆盖率是 0。至少补一条走真实路径的。
5. 做一次「反向验证」：故意把产物挪走，确认你的守卫真的会红。没红过的守卫不算守卫。

---

*监控的本质不是知道系统活着，而是知道自己什么时候该停止相信仪表。*
