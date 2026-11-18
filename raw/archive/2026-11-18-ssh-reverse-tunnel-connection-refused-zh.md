---
title: 最后一行在撒谎——一次 SSH 反向隧道 Connection refused 的根因追踪
header:
    image: /assets/images/hd_linux_tips.jpg
date: 2026-11-18
tags:
 - ssh
 - reverse-tunnel
 - networking
 - 排障
 - wsl
permalink: /blogs/tech/zh/ssh-reverse-tunnel-connection-refused
layout: single
category: tech
---

> "当你排除了一切不可能,剩下的无论多么不可思议,都是真相。" —— 柯南·道尔《四签名》,夏洛克·福尔摩斯

# 最后一行在撒谎——一次 SSH 反向隧道 Connection refused 的根因追踪

*从"报错喊在哪里"到"根因藏在哪里"——这是资深和 Principal 之间,读一屏日志就能分出来的那条线。*

我把一条一直手动开着的 `autossh` 隧道关了。几分钟后,在 MacBook 上敲 `ssh home-wsl`,终端吐出几十行 `debug1:`,最后停在这么一行:

```
kex_exchange_identification: Connection closed by remote host
Connection closed by UNKNOWN port 65535
```

`kex_exchange_identification`——密钥交换阶段握手失败。如果你照着最后一行去搜,会被引到一堆"服务器 SSH 版本不兼容""算法协商失败""MTU/防火墙切断握手"的帖子里,然后花一个晚上去调 `KexAlgorithms`、抓包看 MTU。

**全错了。** 真正的故障发生在这段日志中间偏下的一行,而且它根本不是一个"故障"——是我自己亲手造成的、设计之内的结果。

这篇文章就讲这一屏日志。读完你会带走三个东西:

- **一个读日志的硬口诀**:从上往下找第一个 `failed`,最后一行通常是连锁反应的"尸检报告",不是凶手。
- **一个架构直觉**:反向隧道的那个监听端口,它的生命周期**绑定在一个进程上**——进程没了,端口就没了,这不是 bug。
- **一条资深 vs Principal 的分界线**:能手动跑起来的东西,和"会自己活着"的东西,中间差一个 `systemd` service。

> 说明:下文的公网 IP 一律用文档保留地址 `203.0.113.10` 代替真实地址,架构是通用的反向 SSH 隧道模式。

---

## 先把地形画出来:一条命令,两段连接,三台机器

我的处境很常见:公司笔记本只放行出站 443,不让装 VPN;家里的开发机是 WSL,藏在 NAT 后面,没有公网 IP。中间我租了一台有公网 IP 的云主机当跳板机(下文叫 `spring-board`)。目标是:在任何只有 443 的网络里,敲一句 `ssh home-wsl` 就像本地一样落进家里的 WSL。

```
公司笔记本 ──443──▶  spring-board (203.0.113.10)  ──反向隧道──▶  家里 WSL (sshd:2222)
  ssh home-wsl          公网跳板, sshd 监听 :443          WSL 主动外拨, 把入口顶上去
  (ProxyJump)
```

这里有一个最容易被忽略的细节:**流量的方向和隧道建立的方向是相反的。**

- 用的时候:笔记本 → 跳板机 → WSL,流量往"里"走。
- 建的时候:是**家里的 WSL 主动拨出去**,在跳板机上开了一个"回家的入口"。NAT 后面的机器没法被外部直连,但它能主动往外连——这就是"反向"的全部含义。

那个"回家的入口",具体就是跳板机上的 `127.0.0.1:2200`。谁负责把它顶在那儿?一条跑在家里 WSL 上的命令:

```bash
autossh -M 0 -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
  -i ~/.ssh/id_ed25519_tunnel \
  -R 127.0.0.1:2200:localhost:2222 -p 443 tunnel@203.0.113.10
```

记住这一行,尤其是 `-R 127.0.0.1:2200:localhost:2222`。等会儿所有的因果都收束到它身上。

> 一句话:反向隧道不是"跳板机连回家",是"家主动把一扇门钉在跳板机的内墙上"。门由谁钉,门就跟谁同生共死。

---

## 把日志读成三幕:大部分字都是来打掩护的

`ssh home-wsl -v` 的输出有四五十行,但它其实是**两个 ssh 进程**各自在说话,拼在一起。为什么是两个?因为 `ProxyJump` 的本质是嵌套:

```
debug1: Setting implicit ProxyCommand from ProxyJump: ssh -W '[%h]:%p' usdream-jump
debug1: Executing proxy command: exec ssh -W '[127.0.0.1]:2200' usdream-jump
```

**外层 ssh**(你敲的那个)不自己连跳板机,它 fork 出一个**内层 ssh**,让内层去"连跳板机、认证、再从跳板机的视角拨 `127.0.0.1:2200`",然后把这根管子当成自己的裸 socket。所以日志里两次 `OpenSSH_10.5p1` banner、两次读 config——不是刷屏,是两个进程各打印了一遍。

把它切成三幕,信号立刻清晰:

**第一幕 · 外层把活儿交出去(前几行)**
`%h/%p` 被 config 里的 `HostName 127.0.0.1 / Port 2200` 填进去。注意这个 `127.0.0.1` 是**在跳板机上**解析的地址,不是你 Mac 的本地回环。外层到此就去等一根管子了。

**第二幕 · 内层连跳板机、认证——全绿**

```
debug1: Connecting to 203.0.113.10 port 443.   →   Connection established.
debug1: Host '[203.0.113.10]:443' is known and matches the ED25519 host key.
debug1: Server accepts key: .../id_ed25519_usdream_wsl
Authenticated to 203.0.113.10 ([203.0.113.10]:443) using "publickey".
```

TCP 通了、host key 对上了、公钥认证过了。**跳板机这一层,从网络到身份,一个毛病都没有。** 这一幕的价值不在于它成功了,而在于它**替你排除了一大片假设**:不是 443 被墙、不是密钥不对、不是跳板机宕了、不是 host key 变了。福尔摩斯那句话此刻生效——这些不可能被划掉之后,根因只可能在下游。

**第三幕 · 真凶登场(致命四行)**

```
debug1: channel_connect_stdio_fwd: 127.0.0.1:2200
channel 0: open failed: connect failed: Connection refused     ← 第一个 failed,真正的根因
stdio forwarding failed
kex_exchange_identification: Connection closed by remote host
Connection closed by UNKNOWN port 65535                        ← 你一开始盯着的那行
```

内层认证成功后,代表你向跳板机发出 `-W` 请求:"帮我连你本机的 `127.0.0.1:2200`。" 跳板机的内核去 `connect(127.0.0.1:2200)`,**瞬间**回了一个 RST,因为那个端口上**没有任何进程在监听**。于是:`Connection refused`。

后面三行全是尸检报告:管子一塌 → 内层退出 → 外层那根"裸 socket"断了 → 外层还没来得及做自己的密钥交换就发现对端没了,于是喊 `kex_exchange_identification: Connection closed`。`UNKNOWN port 65535` 是因为对端是个 pipe 不是真 socket,拿不到真实端口号,ssh 填了个占位值。

| 你看到的日志行 | 它在说什么 | 该不该信 |
|---|---|---|
| `Connection refused`(第一个 failed) | 到了主机,但端口没人听 | **信它,这是凶手** |
| `stdio forwarding failed` | `-W` 管道建不起来 | 直接后果 |
| `kex_exchange_identification: Connection closed` | 外层 ssh 发现管子是死的 | 连锁反应,**别信** |
| `Connection closed by UNKNOWN port 65535` | 对端是 pipe,拿不到端口号 | 占位噪声,**别信** |

> **第一个 failed 定律**:一屏报错里,从上往下第一个 `failed`/`refused` 才带信息量,它下面的每一行都在复述"因为上面那个,所以我也挂了"。读日志是考古,不是读新闻——别从最后一条头条倒推。

---

## 为什么"关掉 autossh"必然导致这个结果

现在把第三幕的 `127.0.0.1:2200 refused` 和第一节那条 `autossh -R ...` 接上。

`-R 127.0.0.1:2200:localhost:2222` 的语义是:**让跳板机监听它自己的 `127.0.0.1:2200`,任何连上来的流量,顺着这条已经建好的反向隧道,回灌到家里 WSL 的 `localhost:2222`(也就是 WSL 自己的 sshd)。**

关键在于:**这个监听,是 autossh 进程开出来的。** 它不是跳板机的常驻服务,不写在 `/etc/` 里,不随跳板机开机。它是一个客户端连接的副产品——

> autossh 进程活着,`127.0.0.1:2200` 就 `LISTEN`;
> autossh 进程一死,这个监听**同一时刻**从跳板机上消失。

我手贱关掉的那条命令,正是"回家那扇门"的唯一钉子。门钉一拔,墙上连个洞都不剩。所以跳板机去 `connect(2200)` 时,内核诚实地告诉它:这儿没人。`Connection refused` 不是故障,是**我自己把入口拆了之后,系统给出的唯一正确答复**。

这里还藏着一个"诚实放大器":命令里的 `-o ExitOnForwardFailure=yes`。它的意思是"如果反向端口没成功建起来,autossh 宁可自杀也不装活着"。好处是永远没有"进程在跑、端口却是空的"这种半死不活的中间态——但反过来也提醒你:**这条隧道的健在,是一个 all-or-nothing 的状态,不存在'开着但没用'。**

```
Mac ──443──▶ spring-board:443 (sshd, 认证 OK)
                 │
                 └─ 需要连 127.0.0.1:2200 ──┐
                                            这个监听谁提供?
家里 WSL ──autossh -R 127.0.0.1:2200:localhost:2222──▶ 就是它(被我关了)
```

**普通人的看法**:"`ssh home-wsl` 连不上,肯定是跳板机或者 Mac 配置坏了。"
**资深工程师的洞察**:日志已经证明跳板机和 Mac 全对;连不上恰恰说明**链路里那个'靠进程续命'的环节断了**,而反向隧道里只有一个这样的环节——家里那条 autossh。方向唯一,不用猜。

---

## 修复:30 秒验证根因,然后把它变成"不用管的东西"

**第一步 · 证明因果(家里 WSL 跑一条):**

```bash
# 家里 WSL:把隧道重新拉起来
autossh -M 0 -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
  -i ~/.ssh/id_ed25519_tunnel \
  -R 127.0.0.1:2200:localhost:2222 -p 443 tunnel@203.0.113.10 &

# 任意能登跳板机的机器上,确认监听回来了:
ssh spring-board 'ss -tlnp | grep 2200'   # 期望:127.0.0.1:2200 ... LISTEN
```

看到 `LISTEN`,Mac 上 `ssh home-wsl` 立刻就通——**不用动 Mac 的任何配置**,这反过来再次证明第二幕的判断:笔记本端一直是对的。

这里插一个你能在面试里拿分的点:`Connection refused` 和 `Connection timed out` 是两种完全不同的病。

| 现象 | 内核层面 | 含义 | 该查哪儿 |
|---|---|---|---|
| **瞬间** `Connection refused` | 收到了 RST | 包到了主机,但端口没人听 | 服务/监听进程 |
| **卡住再** `timed out` | 什么都没收到 | 包被丢了,主机没回应 | 防火墙 / 安全组 / 路由 |

我这次是**瞬间 refused**,所以根因一步锁死在"监听没了",连安全组和 443 都不用看。能第一时间分清这两者,就省掉了半个晚上的抓包。

**第二步 · 把"部落知识"升级成"工程产物":**

真正的问题不是"隧道断了",而是"**这条隧道的存活,依赖我记得去手动开它**"。这是典型的部落知识——只活在我脑子里、靠肌肉记忆维持的运维动作。它迟早会因为一次重启、一次手贱、一次睡眠而断掉,而且断了没人知道。

Principal 的解法是把它钉死成一个会自愈的 `systemd` service:

```ini
# 家里 WSL: /etc/systemd/system/reverse-tunnel.service
[Unit]
Description=Reverse SSH tunnel to spring-board
After=network-online.target
Wants=network-online.target

[Service]
User=phray
ExecStart=/usr/bin/autossh -M 0 -N -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new \
  -i /home/phray/.ssh/id_ed25519_tunnel \
  -R 127.0.0.1:2200:localhost:2222 -p 443 tunnel@203.0.113.10
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now reverse-tunnel
ssh spring-board 'ss -tlnp | grep 2200'   # 验证:监听自动回来
```

`Restart=always` + `ServerAliveInterval` 这组合解决的,正是我今天踩的坑:开机自动起、断网/睡眠后靠探活自动重连,我再也不需要"记得手动开一条、手动关一条"。

但这里有个 WSL 专属的暗礁必须点破:**WSL 只在 Windows 把它拉起来的时候才活着。** 你的 `systemd` service 写得再漂亮,如果 WSL 发行版本身没醒,它就是一纸空文。要真正开机即通,还得在 Windows 任务计划里加一个登录时 `wsl.exe -d <distro> ...` 把发行版拉起来的任务。**自愈链条的强度,等于它最弱那一环;而最弱那环往往在你没留意的宿主层。**

> 这篇是我那篇《一次 SSH 登录失败,让我重新理解 Linux 权限设计哲学》的姊妹篇。上次栽在**权限**(文件权限的设计哲学),这次栽在**生命周期**(监听端口到底依附于谁)。SSH 这东西,每次打你的地方都不一样,但每次都在教同一件事:别只看表象那行报错。

---

## 三句话收束

| 层次 | 今天学到的那一句 |
|---|---|
| 读日志 | 从上往下找第一个 `failed`,最后一行多半是尸检报告 |
| 懂架构 | 反向隧道的监听端口,生命周期绑在那个 autossh 进程上,进程死即端口亡 |
| 做运维 | 手动能跑 ≠ 搭好了;`Restart=always` 的 service 才算工程产物 |

### 立刻可以做的事

1. 去数一下你自己环境里,有多少个"靠我记得手动开"的进程(隧道、端口转发、`kubectl port-forward`、临时 `ssh -L`)——每一个都是一颗会在你最忙的时候掉链子的雷。
2. 挑最关键的那一个,今天就把它写成 `systemd` service 或等价的自愈机制,顺手补一条 `ss -tlnp | grep <port>` 的验证命令进你的 runbook。
3. 下次再看到一屏 SSH 报错,先别搜最后一行——用 `-v` 跑一遍,从上往下找第一个 `failed`,圈出来,再决定查哪儿。


*报错喊得最响的那一行,往往离真相最远;真相通常安安静静地待在上游,等一个愿意从头读的人。*
