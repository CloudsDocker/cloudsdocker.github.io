### 1. 🎯 30秒版本

`create_agent()` 返回的不是一个"会调工具的函数"，而是一张**编译好的状态图（compiled StateGraph）**：一个 `agent` 节点（调 LLM，决定要不要调工具）和一个 `tools` 节点（真正执行工具），来回循环直到 LLM 不再要求调工具为止。`astream()` 就是这张图的**流式执行入口**——每跑完一个节点就把当前状态 `yield` 出来一次，让你能实时看到"LLM 决定调了什么工具 → 工具返回了什么 → LLM 最终写了什么"，而不是像 `ainvoke()` 那样等全部跑完才拿到一坨最终结果。这也是本地 Ollama 模型跑 MCP 工具调用时，能在终端里逐步打印进度日志的原因。

代码语境：本地 MCP + Ollama 的一个 agent 实现，用来控制一个 Next.js 服务的启停（`portal_start`/`portal_stop`/`portal_status`）。

```python
async def build_agent():
    llm = build_llm()
    client = MultiServerMCPClient({
        "aidra": {
            "command": "uv",
            "args": ["run", "--directory", str(AIDRA_DIR), "python", "server.py"],
            "transport": "stdio",
            "env": dict(os.environ),
        }
    })
    tools = await client.get_tools()
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
```

---

### 2. ⚙️ 底层原理

#### 2.1 MultiServerMCPClient：协议转换层

MCP（Model Context Protocol）本身是独立协议，server 和 client 用 stdio 或 HTTP/SSE 交换 JSON-RPC 消息（`tools/list`、`tools/call`）。LangChain 的 agent 只认识自己的 `BaseTool` 接口。`MultiServerMCPClient` 是中间的适配层：

- 构造函数接收一个字典，key 是 server 名字，value 是连接配置（`command`/`args` 告诉它怎么把 MCP server 当子进程拉起来，`transport` 指定用 stdio 还是别的方式）
- `await client.get_tools()` 内部会启动子进程、完成 MCP 的 `initialize` 握手、调用 `tools/list`，把拿到的每个工具 schema 包装成 LangChain 的 `Tool` 对象
- 字典里可以放多个 server，`get_tools()` 会把所有 server 的工具合并成一个列表——这就是 "Multi" 的含义：一个 agent 可以跨多个 MCP server 调工具，不用关心每个工具具体来自谁

#### 2.2 create_agent：一张 ReAct 循环图

`create_agent(model=llm, tools=tools, ...)` 在底层用 LangGraph 搭了一张标准的 ReAct 模式循环图：

```
        ┌─────────────┐
   ┌───▶│  agent 节点  │  调用 LLM，决定要不要调工具
   │    └──────┬──────┘
   │           │
   │     有 tool_calls?
   │      是 │      否
   │         ▼       ▼
   │   ┌──────────┐  END（返回最终答案）
   │   │ tools 节点│  真正执行工具（比如调 MCP 的 portal_status）
   │   └─────┬────┘
   └─────────┘
```

每跑一次这张图，状态（`{"messages": [...]}`）就更新一次。`checkpointer=InMemorySaver()` 负责按 `thread_id` 把每次对话的消息历史存起来，这样同一个 `thread_id` 下的多轮对话能共享上下文（REPL 模式固定用 `"repl-session"`，one-shot 模式每次用 `"one-shot"`，所以没有跨次记忆）。

#### 2.3 astream：流式跑图

```python
async for state in agent.astream(
    {"messages": [{"role": "user", "content": prompt}]},   # 输入：这一步要处理的新数据
    {"configurable": {"thread_id": thread_id}},              # 配置：告诉 checkpointer 用哪个会话历史
    stream_mode="values",
):
    ...
```

- `ainvoke()`：一次性异步执行整个图直到结束，只返回最终结果，中间过程不可见
- `astream()`：图每跑完一个节点就 `yield` 一次，可以实时拿到中间进度

`stream_mode` 决定每次 yield 出来的数据形状：

| 模式 | 含义 |
|---|---|
| `"values"` | 每次 yield **完整的当前状态**（累积到目前为止的整个消息列表），需要自己用计数器去重取新增部分 |
| `"updates"` | 每次只 yield **这个节点新产生的增量**，按节点名取值，结构更细但要多一层解析 |
| `"messages"` | 更细粒度，连 LLM token 级别的流式输出都能拿到，适合做打字机效果 |

选 `"values"` 是因为逻辑最简单：拿到完整列表后用一个 `seen` 计数器切片，只挑出新增的消息去打日志：

```python
async def ask(agent, thread_id: str, prompt: str) -> str:
    final_state = None
    seen = 0
    async for state in agent.astream(
        {"messages": [{"role": "user", "content": prompt}]},
        {"configurable": {"thread_id": thread_id}},
        stream_mode="values",
    ):
        final_state = state
        seen = _log_new_messages(state.get("messages", []), seen)
    if not final_state or not final_state.get("messages"):
        return ""
    return final_state["messages"][-1].content
```

`_log_new_messages` 只处理 `messages[seen:]`（上次没打印过的那部分），这就是终端里能看到：

```
[aidra] LLM → tool `portal_status`({})
[aidra] tool `portal_status` finished (214 chars)
[aidra] LLM writing final answer…
```

这种实时进度日志的来源——分别对应"agent 节点跑了一次决定调工具" → "tools 节点跑了一次真正执行" → "agent 节点又跑了一次，这次没有 tool_calls，图判断该结束了"。循环结束后，`final_state["messages"][-1]` 就是最终那条 `AIMessage`，取它的 `.content` 作为文字答案返回。

---

### 3. 🔬 常见追问

**Q1: 为什么 `build_llm()` 是同步函数，`build_agent()` 却要 `async def`？**
A: `ChatOllama(...)` 只是构造一个 Python 对象，即便 `validate_model_on_init=True` 会去 ping 一下 Ollama，LangChain 内部也是用阻塞式 HTTP 调用实现的，没有 `await`。而 `build_agent()` 里的 `client.get_tools()` 需要真正 spawn 子进程、做 MCP stdio 握手、等待 `tools/list` 回包——这是货真价实的异步 I/O，库把它实现成 `async def`，Python 规则决定了：只要函数体里出现 `await`，这个函数本身就必须声明为 `async def`（不能在普通 `def` 函数里用 `await`）。

**Q2: `stream_mode="values"` 每次都拿完整消息列表，会不会随对话变长而越来越浪费？**
A: 会有一定开销（每次 yield 的 payload 随历史线性增长），但在单次问答只有几轮工具调用的场景下可以忽略。如果关心极致效率，可以换成 `stream_mode="updates"`，只处理增量，代价是要多写一点按节点名解析的逻辑。

**Q3: 为什么 `thread_id` 要分 `"one-shot"` 和 `"repl-session"` 两种？**
A: `InMemorySaver` 是进程内存里的 checkpointer，按 `thread_id` 隔离每次对话的历史。one-shot 模式（命令行传参直接问一句就退出）不需要记忆，随便传个固定值即可；REPL 模式要在同一个交互会话里维持上下文，所以固定用一个 `thread_id`，让 `astream()` 每次都能从 checkpointer 里捞出之前的消息拼接进去。注意这是**进程内存**，一旦 agent 进程退出，历史就没了——生产场景要跨进程持久化记忆，得换成 SQLite/Redis 之类的 checkpointer 实现。
