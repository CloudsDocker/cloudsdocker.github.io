---
title: 别再给 Windows 配端口转发了：把 WSL2 变成独立的 Tailnet 节点
header:
    image: /assets/images/bg/adfasdfasdf.jpg
date: 2026-09-26
tags:
 - wsl2
 - tailscale
 - ollama
 - gpu
 - networking
permalink: /blogs/tech/zh/wsl2-ollama-tailscale-gpu-inference
lang: zh
layout: single
category: tech
---
# 别再给 Windows 配端口转发了：把 WSL2 变成独立的 Tailnet 节点

*绕过宿主机网络中转与防火墙，直连 WSL2 中的 GPU 进行远程模型推理。*

```text
100.85.1.56     gpu-box-wsl         linux   active
100.124.38.9    gpu-box-win         windows active
100.121.102.62  laptop-air          darwin  active
```

同一台配了 RTX 5080 的物理机，在 Tailscale 管理后台里出现了两个并排的节点：一个是 Windows 宿主机，另一个是它腹中的 WSL2。

在很多人的直觉里，WSL2 只是 Windows 的一个子进程网络，想从外部笔记本访问 WSL2 里的服务，就得在 Windows 上装 Tailscale，再通过 `netsh interface portproxy` 建立端口映射，最后在 Windows 防火墙上凿个洞放行入站流量。这套方案链路冗长、极其脆弱，宿主机每次休眠或 IP 变化，端口转发就容易失灵。

**只要在开启了 systemd 的 WSL2 内部单独跑一个 Tailscale 守护进程，WSL2 就是 Tailnet 里的一等公民节点。**

读完本文，你能彻底拆掉 Windows 侧脆弱的端口转发桥，直接让 MacBook 等远程设备穿透到 WSL2 中调用 Ollama 进行本地 GPU 推理；同时避开一个让无数人白耗两小时的 systemd 极隐蔽静默配置陷阱。

---

### 🏗️ 两种拓扑：不要把简单问题做成俄罗斯套娃

远程调用 WSL2 服务有两种网络模型。大多数搜索出来的中文教程还在教前一种，而现代 WSL2 早就支持第二种：

| 对比维度 | 方案 A：宿主机中转（传统模式） | 方案 B：WSL2 独立节点（原生推荐） |
| :--- | :--- | :--- |
| **Tailscale 部署位置** | Windows 宿主机 | WSL2 实例内部独立运行 |
| **数据包路径** | Client → Win Tailscale → Win NAT/Portproxy → WSL2 vEthernet | Client → WSL2 `tailscale0`（端到端直连） |
| **依赖项** | `netsh interface portproxy`、Windows 防火墙出入站规则 | WSL2 开启 systemd、安装 `tailscale` |
| **维护成本** | 宿主机网络重置或休眠后端口映射频繁挂死 | 零中转配置，与普通 Linux 服务器无异 |
| **网卡可见性** | 服务只能感知宿主机转发过来的 NAT 虚拟 IP | 服务直接绑定在真实的 Tailscale 虚拟网卡上 |

当 WSL2 拥有独立的 Tailnet 身份后，MacBook 发出的推理请求直接穿透到 WSL2 内部的虚拟网卡 `tailscale0`。Windows 宿主机完全退化为硬件底座，不承担任何网络路由职责，根本不需要配置任何 `netsh` 规则。

---

### 🛠️ 监听所有接口与一个致命手滑

Ollama 默认仅监听 `127.0.0.1:11434`。要让 Tailnet 上的其他机器访问，必须将其监听地址扩大至全网卡。

在 WSL2 终端执行：

```bash
sudo systemctl edit ollama
```

在打开的 override 文件中补充配置：

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

保存后重载并重启服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

此时请立即运行验证命令：

```bash
ss -tlnp | grep 11434
```

正常情况下，输出应该由 `127.0.0.1:11434` 变成 `*:11434`。

🩸 **血泪提醒**：如果你的输出仍然是 `127.0.0.1:11434`，千万不要盲目反复重启。systemd 对 `.service.d` override 文件中无法识别的 key（例如手滑写成 `Engironment=`）**绝不报错，而是静默忽略整行**。此时 `systemctl status ollama` 依然会显示绿色正常的 `active (running)`，让你误以为配置已加载。

**配置生效的唯一标准不是服务有没有起来，而是系统实际认领了什么。**

验证 systemd 实际变量最靠谱的方法，是用系统内核读取值与文件原文对比：

```bash
# 检查你写的文件内容
cat /etc/systemd/system/ollama.service.d/override.conf

# 检查 systemd 进程真正认领的上下文变量
systemctl show ollama -p Environment
```

如果 `systemctl show` 的输出里根本没有 `OLLAMA_HOST`，说明那一行的 key 必定拼错了，回去逐字核对文件，而不是怀疑网络链路。

---

### 验证链路：在碰客户端之前先做本地回环

别急着跑去 MacBook 上发请求。分段排查的第一原则是：**在本地用远端 IP 自证**。

在 WSL2 本机直接 curl 自己的 Tailscale 内部 IP（以 `100.85.1.56` 为例）：

```bash
curl -s http://100.85.1.56:11434/api/tags
```

如果立刻返回了包含模型清单的 JSON 数据，证明两件事：
1. Ollama 正确监听了包含 `tailscale0` 在内的所有接口。
2. WSL2 内的 Tailscale 数据平面工作正常。

这时再打开远端的 MacBook，直接验证连通性：

```bash
# 1. 验证网络穿透
curl http://100.85.1.56:11434/api/tags

# 2. 设置临时环境变量，终端直连远程 GPU
export OLLAMA_HOST=http://100.85.1.56:11434
ollama run qwen2.5:14b
```

任何第三方 UI 客户端（如 Open WebUI 或 LM Studio），只要把 API Base URL 改为 `http://100.85.1.56:11434`，便能无感借助远程台式机的 GPU 算力跑推理。

---

### 🧠 显存容量与掉速的真相

网络通了，不代表推理体验就一定丝滑。

以这块消费级旗舰 RTX 5080 为例，其板载显存为 16GB。很多开发者在远程连通后兴冲冲地加载 `qwen2.5:32b`，紧接着就会遭遇吞吐骤降甚至连接超时。

> 📌 **本节要点**：32B 模型完整加载通常需要约 19.4GB 显存；当显存被撑爆，推理运行时会强行将剩余层卸载到系统内存与 CPU 上计算。由于系统内存带宽与 PCIe 传输开销，整体生成速度会断崖式下跌两到三个数量级。

要保证远端调用的流畅度：
- 优先选择 **14B** 规模的模型，能在 16GB 显存内实现全层加载与完整 KV Cache 驻留。
- 若必须使用 32B，请选择激进量化版本（如 Q4_K_M 或更低），把总内存需求压进 16GB 的安全线以内。

---

### 未经验证的边界：冷启动自愈

这套架构非常轻盈，但有一个边界情况目前尚未经过完整端到端验证：**宿主机经历完整的冷重启时，服务链是否能无干预自愈**。

请在 WSL2 中检查：

```bash
systemctl is-enabled tailscaled
```

虽然 `tailscaled.service` 处于 `enabled` 状态，但 WSL2 本质上是在 Windows 启动后按需拉起的子系统。如果 Windows 重启后没有开机自动唤起 WSL2，或者唤起顺序导致 `tailscaled` 慢于 `ollama` 启动，Tailnet IP 是否能稳定续租、监听端口是否会有竞态，依然需要一次真正的物理重启循环来进行破坏性验证。

你的 WSL2 实例在物理机重启后，Tailscale 会稳定保活，还是需要你手动连进去敲一次 `wsl` 才能唤醒？如果你有更优雅的冷启动拉起实践，欢迎交流你的自动化脚本。
