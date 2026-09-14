## 现象

`uv run blogs_client.py` 跑起来:

```
=== staring ....
======staring loop-=====
.... loaded mcpclient...
 Errors found Connection closed
```

client 端只有这四行,没有任何 traceback。`Connection closed` 就是 fastmcp Client 能给的全部信息。

## 排查思路(核心方法论,以后遇到同类问题直接照做)

`fastmcp.Client` 用 stdio transport 时,server 是一个子进程(`uv run --project ... mcp_server.py`)。如果子进程在**导入阶段**就崩溃退出,client 收到的只是"管道被关闭"——因为握手(initialize)还没发生,server 端的异常压根没机会序列化成 MCP 消息传回来。

所以永远不要对着 client 的报错猜。第一步永远是**绕开 client,直接手动跑 server 命令**,看它自己能不能干净启动:

```bash
cd ai/mcp/servers/output-learn-agent
uv run --project . mcp_server.py
```

这一步立刻暴露真实的 Python 报错(这次是 `AttributeError`)。

## 根因

[utils.py](ai/mcp/servers/output-learn-agent/utils.py) 里:

```python
from enum import StrEnum, auto
class BLOG_LANGUAGES(StrEnum):
    EN: auto()   # 这是类型标注 (annotation),不是赋值!
    CN: auto()
```

`EN: auto()` 是 `name: type` 的变量类型标注语法,不是 `name = value` 赋值。Python 不会把它当成枚举成员创建——`BLOG_LANGUAGES` 类实际上一个成员都没有。

而 `mcp_server.py` 里一个工具的签名:

```python
def list_published_files_n(n:int=5, lang:BLOG_LANGUAGES=BLOG_LANGUAGES.CN):
```

**在模块导入时**就要访问 `BLOG_LANGUAGES.CN` 作为默认值参数——这个属性不存在,直接 `AttributeError`。整个 `mcp_server.py` 在被 `uv run` 启动的瞬间就崩溃退出。

链条:
```
StrEnum 用标注代替赋值
  → 枚举类没有任何成员
    → 函数签名里的默认值 BLOG_LANGUAGES.CN 求值失败 (AttributeError)
      → mcp_server.py 导入阶段直接崩溃退出
        → stdio 管道关闭,client 只看到 "Connection closed"
```

## 修复

```python
class BLOG_LANGUAGES(StrEnum):
    EN = "en"
    CN = "zh"
```

`CN` 的值取 `"zh"` 而不是 `"cn"`,是为了跟仓库里已有的命名惯例对齐——`post_publisher.py` 的 `LANGUAGES = ("en", "zh")`,发布出来的文件名后缀也是 `-zh.md`/`-en.md`,不是 `-cn.md`。

## 验证

两步确认修好了:
1. `uv run --project . mcp_server.py` 直接跑,干净启动,无报错。
2. 完整跑 `uv run blogs_client.py`,日志里出现 `Connected to MCP server`。

## 可以提炼的原则

- **Python 的 `name: type` annotation 和 `name = value` assignment 长得像,后果天差地别**——尤其在 Enum/dataclass 这类"类体本身就是数据定义"的场景,少打一个 `=` 不会报语法错误,只会悄悄不创建你以为创建了的东西。
- **stdio 类型的 RPC 传输,握手前的异常是黑洞**——凡是子进程模式的协议(不只是 MCP),第一反应永远是脱离 client 单独跑 server 命令,拿到未经协议层过滤的原始报错,而不是在 client 的报错文字里找线索。

> 待验证/未想清楚:fastmcp 的 stdio transport 为什么设计成完全吞掉 server 端的 traceback,而不是至少把 stderr 的最后几行原样透传给 client 展示出来?这是协议规范本身的取舍,还是 fastmcp 这个实现的欠缺?没看过源码,不确定。
