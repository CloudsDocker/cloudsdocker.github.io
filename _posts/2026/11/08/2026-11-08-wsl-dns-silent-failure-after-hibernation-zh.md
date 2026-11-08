---
title: 从「假性存活」到「透明自愈」——一次跨越虚拟化网络断层的深度复盘
header:
    image: /assets/images/jpa_camel_snake.png
date: 2026-11-08
tags:
 - 网络故障
 - 虚拟化
 - 自愈系统
permalink: /blogs/tech/zh/wsl-dns-silent-failure-after-hibernation
lang: zh
layout: single
category: tech
---
*从「假性存活」到「透明自愈」——一次跨越虚拟化网络断层的深度复盘*

同治年间，一位名叫杨引传的人在苏州的一个路边书摊偶然发现了一本手稿残卷。这本残卷篇幅虽短，却记录了沈复与芸娘的日常琐事。杨引传爱不释手，并将其刊印，这本小书《浮生六记》竟大受欢迎，成为文学经典。这让我想起了一次虚拟化网络中突如其来的断层，仿佛是现代科技版的意外之喜。周日上午 11:42，我给自己的 Telegram 机器人发了这条消息：

`/quote 。思想最好的归宿，永远不是被供奉，而是继续生长。`

没有回复。连着发了两次，屏幕那头依然是一片死寂。

没有回复。连着发了两次，屏幕那头依然是一片死寂。」

我第一反应是去查服务的状态。输入 `wsl_portal.sh status`，控制台弹出了一个看似完全健康的表格：

```
==========================================================================================
  awesome Portal Services Status (WSL2)
==========================================================================================
ID  NAME                 PORT    STATUS    PORT-CHECK   PID    CPU   MEM      RESTARTS  UPTIME  
--  -------------------  ------  --------  -----------  -----  ----  -------  --------  --------
0   awesome-portal         3000    🟢 online  🟢 LISTENING  14577  0.1%  64.1 MB  16        14h 41m 
1   portal-api           8002    🟢 online  🟢 LISTENING  14628  0.0%  15.0 MB  15        14h 41m 
2   hr-chatbot-api     8001    🟢 online  🟢 LISTENING  14633  0.0%  14.4 MB  14        14h 41m 
3   mcp-gateway          8800    🟢 online  🟢 LISTENING  14716  0.2%  45.7 MB  17        14h 41m 
-   portal-the-chat-bot  (poll)  🟢 online  N/A (bot)    15375  0.0%  32.7 MB  0         14:40:52
```

每一个指示灯都是绿的。`portal-the-chat-bot` 赫然显示着 `🟢 online`，PID `15375`，存活时间整整 14 小时 40 分钟。

然而，当我切进日志文件 `the-chat-bot.log` 时，眼前的景象却完全相反——屏幕被同一行报错淹没，整整刷了四个多小时：

```log
2026-11-08T07:34:00+1100 [the-chat-bot] WARNING: Polling error: [Errno -3] Temporary failure in name resolution (retrying in 3.0s)
2026-11-08T07:34:13+1100 [the-chat-bot] WARNING: Polling error: [Errno -3] Temporary failure in name resolution (retrying in 3.0s)
...
2026-11-08T11:42:06+1100 [the-chat-bot] WARNING: Polling error: [Errno -3] Temporary failure in name resolution (retrying in 3.0s)
```

从早上 7:34 笔记本唤醒的那一刻起，每隔 13 秒，它就遭遇一次 DNS 失败。它没有崩溃，没有触发系统的 `Restart=always`，只是在死循环里不停重试。

**进程还活着，端口没冲突，监控显示全绿，但它已经聋哑了四个小时。**

## 读完你会得到什么关键信息与技能提升点？这里为你总结几个核心收获点，让你更深入地理解复杂的系统行为和解决方法，避免常见的坑和误解。每个要点都结合实际经验，为你提供有价值的洞见和实用技巧。以下是几个关键收获点，按「最有用的先讲」排序，不按我当时的迂回顺序——我走过的弯路，你直接跨过去就好。这不仅能够让你更有效地解决实际问题，还能帮助你深入理解背后的原因，避免类似的问题再次发生。这些收获点不仅适用于当前的问题，还具有广泛的应用价值。以下是我们将讨论的关键收获点：

- **一种识破「监控假象」的第一性直觉**：为什么 `kill -0 $PID` 是最懒惰也是最危险的健康检查方法？
  - **深入理解为什么 `kill -0 $PID` 不是理想的选择**：`kill -0 $PID` 的主要问题是它只会检查进程是否存在，而不会检查进程是否真的健康运行。进程可能存在，但是可能因为各种内部错误或资源不足而陷入无法响应的状态。因此，这种健康检查方法可能会产生误报或漏报，导致系统无法及时发现和处理问题。这种简单的检查方法在面对复杂的应用程序时可能无法提供足够的信息来判断业务状态。
  - **业务状态必须锚定在核心反馈环上**：要更准确地监控业务状态，应将健康检查的焦点放在应用的核心反馈环上，如HTTP请求、数据库查询响应时间、API接口响应时间等。通过监控这些关键指标，可以更准确地判断应用的健康状况，及时发现并处理潜在问题。
- **一张剖析 WSL2 跨边界网络的 X 光片**：彻底搞清为什么宿主机休眠后 NAT 路由毫发无损，却唯独把 UDP 53 割裂成了黑洞。
  - **深入了解 WSL2 的网络机制**：WSL2 的网络配置使得宿主机和子系统之间可以通过虚拟的网络接口进行通信。然而，当宿主机休眠后，NAT 路由虽然依然存在，但由于网络接口被关闭，导致 UDP 53 无法正常通信，形成了一个「黑洞」。
  - **如何避免 UDP 53 的问题**：可以通过配置宿主机的网络服务，确保在休眠状态下依然能够提供 DNS 解析服务，以避免 UDP 53 被割裂。
- **一套零外部依赖的 Python 应用级自愈解法**：如何在不等待 glibc 超时、不依赖宿主机 DNS 的情况下，用纯标准库实现透明 fallback，并避开 `anyio` 传入 `bytes` 的隐蔽暗坑。
  - **实现 Python 应用级自愈的零外部依赖方法**：通过使用 Python 的标准库实现一个透明的 fallback 机制，可以在不依赖外部库的情况下，处理 DNS 解析失败的情况。这种方法不仅避免了 glibc 的超时等待，还绕过了依赖宿主机 DNS 的限制。
  - **避开 `anyio` 的暗坑**：在使用 `anyio` 时，需特别注意传入的类型。确保传入的类型与接口定义一致，以避免潜在的错误。
- **两个「以为修好了却没修好」的经典陷阱**：为什么改完 `wsl.conf` 不重启等于白改，为什么 `systemd=true` 会让 DNS 修复功亏一篑。
  - **`wsl.conf` 修改不重启的陷阱**：在修改 `wsl.conf` 后，如果不重启 WSL，所做的修改可能不会生效，这会导致问题依然存在。
  - **`systemd=true` 带来的 DNS 问题**：当设置 `systemd=true` 后，如果 DNS 配置不当，可能会导致 DNS 解析问题，使得修复效果大打折扣。

## 一、最隐蔽的崩溃不是 Crash，而是「假死」

在软件可靠性工程里，挂掉的进程（Dead Process）从来不是最可怕的。Crash 会产生核心转储，会触发 systemd 或 supervisor 的自动拉起，会立刻让报警器炸响。

最可怕的是**僵尸服务（Zombie Service）**：它的心跳还在（PID 存活），内存占着，OS 调度着它，但它的有效吞吐量已经跌到了零。

把两个观测源摆在一起：

| 观测维度 | 表面看到的信号 | 背后的真相 | 结论 |
| --- | --- | --- | --- |
| **OS 进程表** (`ps`) | PID `15375` 存活 14h 40m | 进程在执行死循环 `sleep(3.0)` | 误判为健康 |
| **状态工具** (`status_table.py`) | `🟢 online` | 只测了 `kill -0 15375` | 假阳性（False Positive） |
| **真实业务** (`get_updates`) | 连续 4 小时无响应 | `api.telegram.org` 域名解析失败 | **业务已死** |

这就是典型的**对称性破缺（Symmetry Breaking）**：**「进程存在」与「服务可用」之间的对称性被打破了。**

当我们把健康检查简化为一个系统调用 `kill -0` 时，我们测量的实际上只是「操作系统还记得这个进程号」，而不是「这个进程还在为人类工作」。

> **第一性原则**：永远不要监控进程的呼吸，要监控进程的吞吐。如果一个轮询服务连续 N 次无法完成握手，它在语义上就已经死了。

这揭示了一个重要的问题：**监控心跳并不能确保服务的健康状态**。心跳仅能表明进程是否仍然存在，而不能证明其执行功能是否正常。因此，在设计健康检查时，必须考虑到这一点，确保监控的是服务的实际业务状态，而不仅仅是进程的存在状态。

## 二、扒开虚拟网络黑盒：为什么休眠唤醒只丢了 DNS？

为了搞清楚真相，我在 WSL 里做了一组经典的层级排查。通过这种分层排查的方法，我们能够逐步定位问题的核心，从网络的底层到应用层层层剥开，以期找到 DNS 解析失败的真正原因。

### 第一步：测 L3 路由与外网连通性
```bash
$ ping -c 1 8.8.8.8
64 bytes from 8.8.8.8: icmp_seq=1 ttl=109 time=13.2 ms
```
**结果**：ICMP 正常，外网 IP 直连延迟只有 13ms。这表明底层的虚拟 NAT 交换机工作正常。

### 第二步：测 L4/L7 与 Telegram 服务器直连
既然无法解析域名，那绕过 DNS 直接用 Telegram 的官方公网 IP 发起 TLS 连接呢？
```bash
$ curl -I --resolve api.telegram.org:443:149.154.166.110 https://api.telegram.org
HTTP/2 302 
server: nginx/1.30.1
location: https://core.telegram.org/bots
```
**结果**：瞬时响应（sub-100ms），证书校验完美通过！这证明：
1. 宿主机与外网的 TCP/HTTPS 畅通无阻；
2. TLS SNI 证书协商毫无问题；
3. **唯一的断点，百分之百卡死在域名解析（DNS）这一环。**

### 第三步：对比查询系统默认 DNS 与公网 DNS

先看系统的 `/etc/resolv.conf`：
```
nameserver 10.0.0.1
```
这是 WSL2 启动时自动生成的虚拟网关地址，指向 Windows 宿主机的 Hyper-V 虚拟交换机。

分别对两个 DNS 发起查询：
```bash
# 1. 查宿主机虚拟代理：
$ dig @10.0.0.1 google.com +time=2 +tries=1
;; communications error to 10.0.0.1#53: timed out

# 2. 查公网 DNS：
$ dig @8.8.8.8 google.com +time=2 +tries=1
;; Query time: 8 msec
;; SERVER: 8.8.8.8#53(8.8.8.8) (UDP)
google.com.  IN  A  172.217.25.174
```

真相大白了：**`10.0.0.1:53` 彻底失联了，而 `8.8.8.8:53` 只需要 8 毫秒。**

```mermaid
flowchart LR
    subgraph WSL2 [

## 三、不要把应用的命悬在 /etc/resolv.conf 上

很多人的解决思路在这里就停了：通过修改 `/etc/wsl.conf`，禁用 `generateResolvConf`，然后手动将 `/etc/resolv.conf` 写死为 `8.8.8.8`。这种做法看似直接解决了问题，但作为系统架构师，我们还需要更深入地思考：

> **如果一个服务跑在无法随意修改系统配置的沙箱环境、容器、或者被运维管控的机器上，宿主机 DNS 崩了，你的应用就只能跟着陪葬吗？**

答案是：**在应用层建立自治的逃生通道。**

### 纯 Python 实现的透明 DNS 自愈层

我们设计并注入了一个零外部依赖的弹性 DNS 拦截器：[`dns_resilience.py`](file:///home/you/ws/main/repo/src/one-llm-based-app/services/portal_api/dns_resilience.py)。

其逻辑极为克制与精密，旨在确保 DNS 请求在各种异常情况下仍能成功。该拦截器通过以下步骤来实现其目标：

1. **协议层后备**：使用 Python 标准库 `socket` 构造 raw UDP DNS 查询包，直接发往 `8.8.8.8` 和 `1.1.1.1`；
2. **内存解析**：手写 15 行二进制 unpack 逻辑，解析 DNS Answer 区域的 A 记录与 CNAME 链条；
3. **静态兜底映射**：硬编码核心服务（如 `api.telegram.org` -> `149.154.166.110`）作为绝对防线；
4. **透明 Hook**：在运行时包装 `socket.getaddrinfo`，对业务代码完全无感。

核心的拦截机制如下：

```python
def resilient_getaddrinfo(host: Any, port: Any, family: int = 0, type: int = 0, proto: int = 0, flags: int = 0) -> Any:
    global _system_dns_failing_until
    now = time.time()

    # 规范化主机名（处理 bytes 与 str）
    if isinstance(host, bytes):
        host_str = host.decode("ascii", errors="ignore").strip().rstrip(".")
    elif isinstance(host, str):
        host_str = host.strip().rstrip(".")
    else:
        host_str = str(host or "").strip()

    is_named_host = (
        bool(host_str)
        and not host_str.replace(".", "").isdigit()
        and host_str not in ("localhost", "127.0.0.1", "::1")
    )

    # 1. 快速熔断降级：若系统 DNS 刚挂过，直接走后备 DNS，绝不被 glibc 拖慢 10 秒
    if is_named_host and now < _system_dns_failing_until:
        ips = resolve_fallback(host_str)
        if ips:
            try:
                return _orig_getaddrinfo(ips[0], port, family, type, proto, flags)
            except Exception:
                pass

    # 2. 正常路径：优先相信系统 DNS
    try:
        res = _orig_getaddrinfo(host, port, family, type, proto, flags)
        _system_dns_failing_until = 0.0  # 系统 DNS 恢复，清除故障标记
        return res
    except socket.gaierror as exc:
        if is_named_host:
            logger.warning("System DNS failed for %s (%s). Engaging fallback DNS...", host_str, exc)
            _system_dns_failing_until = now + 60.0  # 开启 60 秒快速后备通道
            ips = resolve_fallback(host_str)
            if ips:
                return _orig_getaddrinfo(ips[0], port, family, type, proto, flags)
        raise exc
```

### 一个藏得很深的暗坑：`anyio` 传入的不是 `str`

在开发这个自愈模块时，我遇到了一个极具启发性的技术细节：

我们在单元测试中使用 `requests` 或 `urllib` 进行测试时，一切看似完美。但一旦将代码迁移到基于 `httpx.AsyncClient` 的 Telegram 机器人中，依然会抛出 `ConnectTimeout` 错误。经过深入的断点追踪 `httpcore` 和 `anyio` 的源码，我发现了这道暗流：

现代异步库 `anyio` 在调用 `getaddrinfo` 之前，执行了如下代码：

```python
encoded_host = idna2008_resolve(host) if isinstance(host, str) else host
```

它为了支持国际化域名，在底层将域名编码成了 **`bytes`**（即 `b'api.telegram.org'`）！如果在拦截器中只是简单地检测 `host` 是否为 `str`，则所有现代异步 HTTP 框架（如 `httpx`、`fastapi`、`httpcore`）的请求都会直接绕过拦截逻辑，继续陷入系统 DNS 10 秒超时的困境。

```python
if isinstance(host, str):  # ❌ 对于 anyio 永远是 False！
```

因此，健壮的底层网络工具必须**防御性地同时接纳 `bytes` 与 `str`**，以确保在所有场景下都能正常工作。

## 四、把谎言从状态面板中抹去

解决了自愈问题后，我们还必须解决那个致命的「假阳性监控」。这种监控让问题隐藏在表面上的正常状态之下，导致我们无法及时采取行动。原有的 `status_table.py` 判断逻辑简单粗暴，只是简单地检查进程是否存活，而不是真正理解服务的实际状态。

原有的代码如下所示：

```python
# 旧代码：只要 PID 活着，就盖章 🟢 online
tg_status = "🟢 online" if tg_running else "🔴 stopped"
```

这种判断逻辑的问题在于，它只关注了进程的存活状态，而忽略了进程是否正常运行。当进程存在但服务出现问题时，这种判断逻辑无法提供有效的信息。

我们把它改造成了真正感知业务脉搏的探针，通过深入探测日志中的真实轮询心跳来判断服务状态。这样，我们就能更准确地了解服务的实际状态，而不是仅仅依赖于进程是否存活。

新的代码如下所示：

```python
# 新代码：深入探测日志中的真实轮询心跳
if tg_running:
    # 提取最后 4KB 日志
    recent_errs = [l for l in lines[-10:] if "Polling error:" in l]
    if recent_errs:
        last_err = recent_errs[-1]
        if "Temporary failure in name resolution" in last_err:
            tg_status = "⚠️ degraded"
            tg_port_check = "🔴 NO DNS"
            tg_warning_note = "⚠️ Telegram Bot cannot resolve api.telegram.org (WSL DNS failure)."
    else:
        tg_port_check = "🟢 POLLING"
```

通过这个新的逻辑，我们可以更准确地判断服务的状态，当 DNS 故障发生时，控制台再也不会粉饰太平，而是会诚实地红灯示警，帮助我们及时发现并解决问题。

现在，当 DNS 故障发生时，控制台会显示以下信息：
```
-   portal-the-chat-bot  (poll)  ⚠️ degraded  🔴 NO DNS     15375  0.0%  44.1 MB  0  14:52:51
⚠️ Telegram Bot cannot resolve api.telegram.org (WSL DNS failure).
💡 Troubleshooting: Run 'wsl_portal.sh logs bot' or restart via 'portal-restart bot'.
```

同时，当自愈机制生效后，状态将明确显示为：
```
-   portal-the-chat-bot  (poll)  🟢 online    🟢 POLLING    70022  0.0%  93.7 MB  0  03:01
```

通过这样的改进，我们可以确保服务状态的透明性和准确性，从而更好地应对各种故障和问题。

## 五、「改了 wsl.conf 就万事大吉？」——两个让你功亏一篑的陷阱

如果你只看到前面的分析就急着去改配置，很可能会踩进我亲历的两个坑。这两个陷阱相互咬合，你必须同时理解才能一次修好。

### 陷阱一：改了 wsl.conf 却没重启 WSL——等于什么都没改

在我的第一轮修复中，我在 `/etc/wsl.conf` 中加入了：

```ini
[network]
generateResolvConf = false
```

然后直接删掉了 `/etc/resolv.conf` 这个 symlink，手动创建了一个写死公共 DNS 的静态文件：

```
nameserver 8.8.8.8
nameserver 1.1.1.1
nameserver 10.0.0.1
```

看起来完美。然而几分钟后再次 `cat /etc/resolv.conf`，发现它又被覆盖回了老样子：

```
# This file was automatically generated by WSL. To stop automatic generation of this file...
nameserver 10.0.0.1
```

**原因**：`wsl.conf` 是 WSL 实例**启动时**读取的配置文件。当前正在运行的 WSL 实例仍然使用的是旧配置——`generateResolvConf` 实际上还是 `true`。WSL 的内部守护进程在运行过程中会持续维护 `/etc/resolv.conf` 的状态，你手动改了它，它就给你改回来。

**解法**：修改 `wsl.conf` 之后，必须在 **Windows 端** 执行一次完整关闭：

```powershell
wsl --shutdown
```

等待 3-5 秒后再重新启动 WSL 实例。此时 `generateResolvConf = false` 才会真正生效，WSL 不再自动生成 `/etc/resolv.conf`。

### 陷阱二：`systemd=true` 的夺权——你以为交给了你，其实交给了 systemd-resolved

当我在 `wsl.conf` 中同时启用了 `systemd=true`（现代 WSL2 发行版的标准配置），第二个意外出现了。

`wsl --shutdown` 后重新启动 WSL，检查 `/etc/resolv.conf`：

```bash
$ ls -la /etc/resolv.conf
lrwxrwxrwx 1 root root 39 Nov  8 21:18 /etc/resolv.conf -> ../run/systemd/resolve/stub-resolv.conf

$ cat /etc/resolv.conf
nameserver 127.0.0.53
options edns0 trust-ad
```

文件变成了一个**全新的 symlink**——不再指向 WSL 的 `/mnt/wsl/resolv.conf`，而是指向 `systemd-resolved` 的 stub 配置文件。nameserver 变成了 `127.0.0.53`，这是 systemd-resolved 的本地 stub resolver 地址。

发生了什么？当 `generateResolvConf = false` 生效后，WSL 自己不再管 `/etc/resolv.conf`。但如果你同时开了 `systemd=true`，systemd 的初始化流程会启动 `systemd-resolved` 服务，而 **systemd-resolved 有自己的一套 DNS 管理机制**，它会把 `/etc/resolv.conf` 重新链接到自己的 stub 文件。

此时检查 resolved 的上游配置：

```bash
$ resolvectl status
Global
         Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
  resolv.conf mode: stub

Link 2 (eth0)
    Current Scopes: none
         Protocols: -DefaultRoute ...
```

**没有任何上游 DNS 服务器被配置。** `systemd-resolved` 启动了，接管了所有 DNS 查询，但它不知道该往哪里转发——所有发往 `127.0.0.53` 的查询都坠入了黑洞。

这就形成了一条完美的故障链条：

```
你手动写的 resolv.conf（8.8.8.8）
    ↓ wsl.conf 没重启，被 WSL 覆盖回 10.0.0.1
    ↓ wsl --shutdown 后重启
    ↓ WSL 不再生成 resolv.conf（generateResolvConf=false 生效了）
    ↓ 但 systemd-resolved 接管，创建新 symlink → 127.0.0.53
    ↓ resolved 没有上游 DNS → 所有查询超时
    ↓ DNS 依然是坏的，只是换了一种死法
```

**解法**：不要对抗 systemd-resolved——配置它。创建一个 drop-in 配置文件，告诉它使用公共 DNS 作为上游：

```bash
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo tee /etc/systemd/resolved.conf.d/public-dns.conf << 'EOF'
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=8.8.4.4 1.0.0.1
EOF

sudo systemctl restart systemd-resolved
```

验证：

```bash
$ resolvectl status | head -6
Global
           Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
    resolv.conf mode: stub
         DNS Servers: 8.8.8.8 1.1.1.1
Fallback DNS Servers: 8.8.4.4 1.0.0.1

$ dig google.com +short
172.217.25.174  ✅
```

这个 drop-in 文件会在每次 WSL 启动时被 systemd-resolved 自动加载，不会被覆盖，也不需要每次手动配置。

## 六、三层防御体系总结

构建高可靠系统不是追求「永不发生故障」，而是在层层设防中把故障的影响半径压缩至最小。这种体系不仅确保系统在复杂环境中的稳定运行，还能够在故障发生时迅速隔离并修复问题。

### 第一层：系统底座

通过系统底座，我们从根本上解决了对Windows虚拟代理的依赖问题，避免了单一故障点对整个系统的影响。

| 防御层次 | 发生位置 | 解决什么问题 | 关键机制 |
|---|---|---|---|
| **第一层：系统底座** | `/etc/wsl.conf` + `resolved.conf.d/` | 彻底切断 WSL 对 Windows 虚拟代理的单一依赖 | `generateResolvConf = false` + systemd-resolved 上游配置 |

通过在 `/etc/wsl.conf` 和 `resolved.conf.d/` 中设置 `generateResolvConf = false`，并使用 systemd-resolved 上游配置，我们消除了 WSL 对 Windows 虚拟代理的依赖，确保了 DNS 查询的独立性。

### 第二层：应用自愈

即使在系统底座失效的情况下，关键服务也能够迅速恢复运行。通过拦截 `getaddrinfo` 调用并采用 Raw UDP 查询，我们在60秒内迅速熔断故障服务，确保了服务的高可用性。

| 防御层次 | 发生位置 | 解决什么问题 | 关键机制 |
|---|---|---|---|
| **第二层：应用自愈** | `dns_resilience.py` | 即使系统底座崩塌，关键服务也能脱困 | 拦截 `getaddrinfo` + Raw UDP 查询 + 60s 快速熔断 |

`dns_resilience.py` 脚本通过拦截 `getaddrinfo` 调用，能够迅速切换到 Raw UDP 查询，从而在 WSL DNS 配置失效时，依然能够完成 DNS 查询。

### 第三层：真实观测

真实的观测机制能够拒绝欺骗性监控，通过穿透检查核心循环日志，揭示真正的故障状态，而不是被表面的正常信号所迷惑。

| 防御层次 | 发生位置 | 解决什么问题 | 关键机制 |
|---|---|---|---|
| **第三层：真实观测** | `status_table.py` | 拒绝欺骗性监控，暴露隐蔽故障 | 穿透检查核心循环日志，呈现 `🟢 POLLING` / `🔴 NO DNS` |

`status_table.py` 脚本通过穿透检查核心循环日志，确保了监控的真实性和准确性，及时暴露隐蔽故障。这种机制不仅能够快速发现故障，还能够通过 `🟢 POLLING` / `🔴 NO DNS` 的实时状态更新，提供明确的故障指示。

通过以上三层防御体系，我们能够在复杂多变的环境中，确保系统的高可靠性和稳定性。

## 立刻可以做的事

**在你的 WSL 里执行这条命令验证一下**：

```bash
 dig @10.0.0.1 google.com +time=2 +tries=1
```

如果你看到 `timed out`，说明你的开发环境同样遭遇了 DNS 悬空的困扰。这种状况通常是由于 WSL 内部的 DNS 缓存未能及时更新，导致 DNS 查询失败。

**永久固定 WSL DNS（需要一次 sudo + 一次重启）**：

**Step 1**：首先，你需要修改 `wsl.conf` 配置文件，以阻止 WSL 自动生成 `resolv.conf`，从而确保 DNS 配置不会被意外覆盖。

```bash
sudo tee /etc/wsl.conf << 'EOF'
[network]
generateResolvConf = false
[interop]
enabled=true
appendWindowsPath=true
[boot]
systemd=true
EOF
```

**Step 2**：这一步至关重要，必须重启 WSL 以确保配置生效。在 PowerShell 中运行以下命令：

```powershell
wsl --shutdown
```

**Step 3**：重启后，进入 WSL 并为 systemd-resolved 配置上游 DNS。

```bash
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo tee /etc/systemd/resolved.conf.d/public-dns.conf << 'EOF'
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=8.8.4.4 1.0.0.1
EOF
sudo systemctl restart systemd-resolved
```

**Step 4**：验证配置是否成功。运行以下命令检查 DNS 服务器是否正确配置。

```bash
resolvectl status | grep "DNS Servers"
# 应显示：DNS Servers: 8.8.8.8 1.1.1.1

dig google.com +short
# 应返回 IP 地址
```

> ⚠️ **不要跳过 Step 2 直接做 Step 3**。如果 WSL 没有重启，`generateResolvConf = false` 未生效，WSL 内部守护进程会持续覆盖 `/etc/resolv.conf`，你的所有修改都会被静默回滚。同时，如果跳过 Step 3，`systemd=true` 环境下 systemd-resolved 会接管 DNS 但没有上游服务器，DNS 会以另一种方式失败。

**顺手修一下 Windows 宿主机的 DNS**：

如果你的路由器 DNS 也不稳定，建议在 Windows 的网络设置中把以太网和 WLAN 的 DNS 服务器手动改为 `8.8.8.8`（首选）和 `1.1.1.1`（备用）。路由器 DNS 缓存带来的那点局域网加速，远不值得承担它挂掉时全家断网的风险。

**审视你现有系统中的进程探针**：

检查你的 Supervisor、PM2 或 Kubernetes 的 Liveness 探针，它测量的究竟是进程表里的一个整数（PID），还是能代表业务价值的数据回环？

例如，如果你的应用程序在 Kubernetes 中运行，Liveness 探针应该不仅仅检查 PID 是否存活，更应该验证应用程序的健康状态。这可以通过设置更复杂的探针逻辑来实现，确保应用程序在面对 DNS 问题时能够自我修复。

```yaml
livenessProbe:
  exec:
    command: ["curl", "-f", "http://localhost:8080/health"]
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

通过这种方式，可以确保你的应用程序在 DNS 问题发生时能够及时检测到并采取相应措施，而不是仅仅依赖 PID 是否存活来判断应用的健康状况。
