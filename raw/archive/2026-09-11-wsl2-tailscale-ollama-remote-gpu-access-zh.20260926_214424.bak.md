# 把 WSL2 里的 Ollama 通过 Tailscale 暴露给 MacBook（远程用 GPU 跑推理）

目标：Windows 11 + WSL2 这台机器上装了 RTX 5080，想从同一个 tailnet 里的
MacBook Air 直接远程调用 WSL2 里跑的 Ollama，用上这块 GPU 的算力。

## 关键前提：WSL2 自己就是一个 tailnet 节点

这台 WSL2 通过 systemd 跑了**自己独立的 Tailscale 节点**，跟 Windows 宿主机
的 Tailscale 节点是分开的两个 IP：

```
100.85.1.56     aidra-studio-wsl     (WSL2，这台)
100.124.38.9    aidra-studio         (Windows 宿主机，同一台物理机)
100.121.102.62  toddzhangs-macbook-air
```

因为 WSL2 是 tailnet 里独立的一等公民节点，所以完全不需要：

- `netsh interface portproxy`（Windows 到 WSL2 的 NAT 端口转发桥）
- Windows 防火墙的入站规则

Mac 那边的流量是直接打到 WSL2 内部的 `tailscale0` 网卡上的。这跟大多数教程
默认假设的"Tailscale 只装在 Windows 上，WSL 在它后面走 NAT"是不同的、更简单
的架构 —— 前提是你在 WSL2 里也单独装了 Tailscale（现在的 WSL2 支持 systemd
之后才好搞）。

## 怎么修

Ollama 默认只绑定 `127.0.0.1:11434`。需要改成 `OLLAMA_HOST=0.0.0.0:11434`
让它监听所有网卡（包括 tailnet 那张）：

```bash
sudo systemctl edit ollama
```

在 `[Service]` 块里加一行（跟已有的 `Environment=` 行放一起，比如
`OLLAMA_FLASH_ATTENTION`、`OLLAMA_KV_CACHE_TYPE` 这些）：

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

验证：

```bash
ss -tlnp | grep 11434
# 期望看到: *:11434   （不是 127.0.0.1:11434）
```

## 排障：一个会被 systemd 悄悄吞掉的手滑错字

第一次改完重启，`ss` 还是显示 `127.0.0.1:11434`，没生效。原因：手滑把
`Environment=` 打成了 `Engironment=`。

**systemd 对 `.service.d` override 文件里认不出来的指令 key，不会报错，
只会悄悄忽略那一行。** `systemctl status ollama` 照样显示
`active (running)`，什么异常都不提示。这就是坑所在：状态显示正常，
不代表配置真的生效了。

真正靠谱的验证方式，是把"你写的文件内容"和"systemd 实际生效的环境变量"
对比着看：

```bash
cat /etc/systemd/system/ollama.service.d/override.conf   # 你写的
systemctl show ollama -p Environment                      # 实际生效的
```

如果你刚加的变量没出现在 `systemctl show` 的输出里，说明这个 override
根本没被正确解析 —— 回去逐字检查文件有没有拼错，不要闷头再重启一遍。

改对拼写 -> `daemon-reload` -> `restart` -> `ss` 终于显示 `*:11434`。

## 在 Mac 那边测试之前，先在本机自证一遍

在 WSL 这台机器上，直接 curl 它自己的 tailnet IP（不是 localhost），先证明
它是真的在那张网卡上监听，而不是"理论上监听所有网卡"：

```bash
curl -s http://100.85.1.56:11434/api/tags
```

拿到了模型列表的 JSON —— 在碰 Mac 之前，先确认了 tailnet 那一侧没问题。
这一步很便宜，但能把"Ollama 是不是真的暴露出去了"和"是不是 Mac 那边的
问题"这两件事分开排查。

## Mac 客户端这边

```bash
curl http://100.85.1.56:11434/api/tags     # 先自查一下
export OLLAMA_HOST=http://100.85.1.56:11434
ollama run <模型名>
```

或者把任何兼容 Ollama API 的客户端（Open WebUI、LM Studio 等）的 base URL
指向 `http://100.85.1.56:11434`。

## GPU 显存的坑

RTX 5080 是 16GB 显存。`qwen2.5:32b` 这种模型大概要 19.4GB，装不下，会把
超出部分卸载到 CPU 上跑，非常慢。想要从 Mac 远程调用时体验流畅，模型规模
最好控制在 14B 左右，或者用更激进的量化版本。（这跟本周早些时候诊断出的
Ollama 超时问题根因一致 —— 都是这个显存溢出导致的。）

## 还没验证的点：重启后能不能自动恢复

还没完整测过"Windows/WSL 整个重启一遍"这条链路能不能自动跑通。应该查一下：

```bash
systemctl is-enabled tailscaled
```

如果 `tailscaled` 不是 `enabled` 状态，WSL2 重启后这个 tailnet IP 不会自动
起来，整套配置会在没人注意到的情况下悄悄失效，直到有人发现连不上再手动
重启。

> 待验证 / 未想清楚：还没有真正测过一次完整的重启循环（Windows 重启 ->
> WSL 冷启动 -> tailscaled 是否自动起 -> 是否拿到同一个 IP -> ollama.service
> 起来的时候 override 是否还在生效）。目前只是看 unit 状态是 `enabled`
> 就假设没问题，并没有端到端验证过。
