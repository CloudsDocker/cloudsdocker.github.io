---
title: "LLMOps 实战 04：它卡在哪一步了？——跨进程的实时调用栈"
date: 2026-11-10
categories: [engineering, ai, observability]
tags: [tracing, sse, event-sourcing, reducer, jsonl, agent]
---

# LLMOps 实战 04：它卡在哪一步了？

> 我唯一知道的就是自己一无所知。——苏格拉底

给 bot 发了条消息，它显示「正在输入」已经四十秒了。此刻它在干什么？在等模型吐字？在等某个工具超时？在第三轮工具调用里打转？还是已经挂了？

项目里本来有 trace：每一轮对话结束时写一条完整记录，包含 prompt、每一步耗时、工具调用链。很完善——**前提是这一轮结束了。** 对一个正卡着的请求，它提供的信息量恰好是零。

这篇讲怎么让「进行中」的事情可见。

---

### 1. 🎯 30 秒版本

- 事后的 trace 回答「刚才发生了什么」；实时事件回答「**现在**在发生什么」。两者都要。
- 采集器在每个 span 开始和结束时各发一个小事件，追加写入一个 **JSONL 文件**。
- API 用 SSE 把这个文件的新增内容推给浏览器。
- 「当前状态」不存储，由事件**折叠**（reduce）出来。服务端和浏览器用同一个 reducer。
- 选文件而不是内存队列，只因为一个事实：**bot 和 API 是两个进程。**

一轮真实运行的时间线（另一个进程里的 agent，本地模型；节选，父 span 写成了名字方便阅读）：

```
+ 0.00s trace_start   Read the file pyproject.toml and tell me...
+ 0.01s span_start    guardrail:input
+ 0.01s span_end      ok 0ms
+ 0.01s span_start    llm_round_0
+12.86s span_end      ok 12856ms
+12.86s span_start    tool:read_file
+12.86s span_start    guardrail:tool_call      parent=tool:read_file
+12.87s span_start    guardrail:tool_result    parent=tool:read_file
+12.87s span_end      ok 2ms
+12.87s span_start    llm_round_1
+17.84s span_end      ok 4972ms
+17.84s trace_end     ok
```

一眼就能看出：18 秒里有 12.9 秒花在第一次模型调用上，工具本身 2 毫秒。在第 3 秒去看，会看到状态 `running`、当前位于 `llm_round_0`。

---

### 2. ⚙️ 底层原理

#### 2.1 关键决策：为什么是一个文件

最自然的实现是进程内的发布订阅：采集器往一个 `asyncio.Queue` 里塞事件，SSE 端点从里面读。干净、快、零 IO。

它在这个项目里是错的。Telegram bot 是独立进程，agent 循环跑在 bot 进程里；SSE 端点在 API 进程里。内存队列跨不了进程，于是面板上永远只有网页端发起的对话，而最需要观察的 bot 那边一片空白。

可选方案：

| 方案 | 跨进程 | 新增依赖 | 重启后还在 |
|---|---|---|---|
| 进程内队列 | ✗ | 无 | ✗ |
| Redis pub/sub | ✓ | 一个服务 | ✗ |
| OpenTelemetry + collector | ✓ | SDK + collector + 后端 | ✓ |
| **追加写 JSONL + tail** | ✓ | 无 | ✓ |

单机、两个进程、每秒几个事件。这个量级下，一个追加写的文件就是最简单的消息总线。

> 经验：**设计先问部署拓扑。** 「有几个进程、在几台机器上」这个问题的答案，比任何架构偏好都更能决定方案。

#### 2.2 写入端：绝不能影响业务

```python
def emit(event_type: str, trace_id: str, **fields) -> None:
    """追加一个事件。永不抛异常：可观测性不能弄坏对话。"""
    try:
        path = log_path()
        if path.exists() and path.stat().st_size > MAX_LOG_BYTES:
            path.replace(path.with_suffix(".jsonl.1"))
        record = {"ts": time.time(), "type": event_type, "trace_id": trace_id, **fields}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:
        logger.debug("live event dropped: %s", exc)
```

整个函数包在 `try` 里，失败只记 debug 日志。磁盘满了、目录没权限，损失的是一条观测事件，不是用户的这一轮对话。测试也只有一句话：把 `log_path` 换成一个必然抛异常的函数，调用 `emit`，不炸就算过。

#### 2.3 读取端：三个必须处理的边界

```python
def read_from(offset: int):
    path = log_path()
    if not path.exists():
        return [], 0
    size = path.stat().st_size
    if offset > size:          # 文件被轮转了
        offset = 0
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read()
    end = data.rfind(b"\n") + 1  # 只消费完整的行；写入方可能正写到一半
    events = []
    for line in data[:end].splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events, offset + end
```

tail 一个别人正在写的文件，有三件事会咬人：

1. **半行。** 你读的瞬间对方刚写了半条 JSON。所以只消费到最后一个换行符为止，偏移量也只前进到那里，下次从半行的开头重读。
2. **轮转。** 文件被改名重建后，你手里的偏移量比新文件还大。检测到就归零。
3. **坏行。** 单行解析失败跳过，不能让一行脏数据卡死整个流。

偏移量按**字节**算、文件按二进制打开，是因为内容有中文：按字符 seek 会落在一个 UTF-8 字符中间。

#### 2.4 状态是算出来的，不是存出来的

```python
def apply_event(runs, ev):
    run = runs.setdefault(ev["trace_id"], {"status": "running", "spans": {}, "stack": [], ...})
    kind = ev["type"]
    if kind == "span_start":
        run["spans"][ev["span_id"]] = {"name": ev["name"], "parent_id": ev.get("parent_id"), "status": "running", ...}
        run["stack"].append(ev["span_id"])
    elif kind == "span_end":
        run["spans"][ev["span_id"]].update(status=ev["status"], duration_ms=ev["duration_ms"], ...)
        run["stack"].remove(ev["span_id"])
    elif kind == "trace_end":
        run.update(status=ev["status"], latency_ms=ev["latency_ms"], stack=[])
```

没有任何地方存着「这一轮当前的状态」。状态 = 把事件按顺序喂给这个纯函数的结果。`stack` 里剩下的 span 就是「现在卡在哪」。

这就是事件溯源的最小形态，它带来两个好处：

**快照和流用同一套逻辑。** 浏览器打开时调一次 `/traces/live`（服务端折叠最近 2MB 事件，返回状态 + 当前偏移量），然后从那个偏移量接上 `/traces/stream`。前端的 JS 里有一个和上面逐行对应的 `applyEvent`。因为两边 reducer 相同，「快照 + 增量」拼出来的状态和「从头回放」一致，不会在衔接处丢事件或重复。

**崩溃的进程自然显形。** 一个 `trace_start` 之后再没有任何事件——进程死了。不需要心跳机制，折叠时看一眼最后事件时间，超过阈值标成 `stale` 而不是永远 `running`。

#### 2.5 调用栈：一个列表就够

```python
step = ExecutionStep(..., parent_id=self._open_stack[-1] if self._open_stack else None)
self._open_stack.append(step_id)
```

开始一个 span 时，栈顶就是它的父亲。工具执行期间跑的 guardrail 检查，自动挂在那个工具 span 下面。面板按 `parent_id` 缩进，就是调用栈。

#### 2.6 SSE 与一个浏览器的限制

```python
async def events():
    position, idle = start, 0
    while not await request.is_disconnected():
        batch, position = await asyncio.to_thread(live.read_from, position)
        for ev in batch:
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        idle = 0 if batch else idle + 1
        if idle >= 30:                 # 约 15 秒没动静：发个注释行保活
            idle = 0
            yield ": keepalive\n\n"
        await asyncio.sleep(0.5)
```

三个细节：文件 IO 丢进线程（`to_thread`），别阻塞事件循环；每轮检查客户端是否断开，否则连接泄漏；空闲时发 SSE 注释行，防止中间的代理因超时掐断。

前端没有用 `EventSource`，因为它**不能自定义请求头**，而 API 用请求头做鉴权。改用 `fetch` 读流、自己按 `\n\n` 切帧，二十行代码。

---

### 3. 🧭 为什么选它，不选别的

**为什么不上 OpenTelemetry？**
OTel 是对的方向，等有多台机器、多个服务时一定会换。但现在引入它意味着 SDK、collector、存储后端、一个看图的 UI。而我要回答的问题只是「它卡在哪一步」。span 的数据模型（id、父 id、类型、起止）和 OTel 是同构的，将来加一个导出器即可，采集点不用动。**数据模型向标准靠拢，基础设施按当前规模选。**

**为什么轮询文件而不是用 inotify？**
半秒一次 `stat` 的开销可以忽略，而且在 macOS、Linux、WSL 上行为一致。文件监听在 WSL 的跨文件系统场景下并不可靠。

**事件日志和最终 trace 是不是重复了？**
用途不同。事件小而多，面向「进行中」；trace 大而全（完整 prompt、工具返回），面向「事后分析」。事件日志到 16MB 就轮转，可以随时丢；trace 是审计记录。

---

### 4. 🔬 常见追问

**Q：两个进程同时追加写同一个文件，会不会写花？**
以追加模式打开时，每次 `write` 都落在文件末尾，小于一个管道缓冲区大小的单次写入在本地文件系统上实际是整条落盘的。每个事件一次 `write`、远小于这个量级，所以不需要锁。真到了多机或高并发，就该换掉这个方案了，而不是给它加锁。

**Q：测试时事件写到哪？**
一个 autouse 的 fixture 把 `log_path` 指到临时目录。我在这里踩过一脚：最初直接放进了测试自己的 `tmp_path`，结果另一个测试在同一目录里 glob `*.jsonl` 当评测数据集，把事件日志读了进去，报了一个莫名其妙的 `KeyError: 'id'`。后来改用独立的临时目录。**测试隔离的对象不只是生产数据，还有别的测试。**

**Q：评测回放 agent 时也会产生一堆事件吗？**
不会。回放时把 `live.emit` 临时换成空函数，把 trace 存储换成一个不落盘的一次性实例。评测不该污染生产观测数据。

---

### 5. 🛠 自己动手

1. 列出你的系统有几个进程。你现有的日志/trace 能不能告诉你一个进行中的请求卡在哪？
2. 定义四种事件，写 `emit`，保证它在磁盘只读时也不抛异常。
3. 写 `read_from`，用测试逼出半行、轮转、坏行三种情况。
4. 写 reducer，再用另一种语言（前端）照着写一遍，确认两边对同一串事件得到相同状态。
5. 启动一个会 sleep 的假任务，中途 `kill -9`，看面板是否最终显示 `stale`。
