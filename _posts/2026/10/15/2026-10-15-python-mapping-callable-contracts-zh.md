---
title: "你真的懂 Python 类型映射吗？还是只是在滥用 Dict？"
header:
    image: /assets/images/docker-commands-bible.jpg
date: 2026-10-15
tags:
 - python
 - typing
 - software-engineering
 - architecture
permalink: /blogs/tech/zh/python-mapping-callable-contracts
lang: zh
layout: single
category: tech
---

> “欲变世界，先变其身。” —— 圣雄甘地


## 引言：微观包工头 vs 大局观老板

想象你要预测一个球沿着过山车轨道滚下来的轨迹。

**牛顿的解法：苦逼的“微观包工头”**

- 你必须盯着这个球的每一个瞬间。
- 你需要画出它受到的重力、轨道的支持力、摩擦力，并且把这些力全部拆解到 X 轴和 Y 轴上。
- 最让人抓狂的是，因为过山车轨道是弯曲的，那个支持力的方向每一毫米都在变。你就像一个微观包工头，必须死死盯住每一个细节，算错一个角度，整道题就全错了。

**拉格朗日的解法：聪明的“大局观老板”**

- 拉格朗日根本不关心球每一秒到底受了什么方向的力，他甚至不画受力分析图。他只看两个宏观指标：**动能**（跑得多快，记作 $T$）和**势能**（在什么高度，记作 $V$）。
- 他把这两个能量相减，创造了一个终极指标——拉格朗日量：

$$L = T - V$$

- 接着，他利用了宇宙里最酷的一条潜规则：**大自然极其“懒惰”**（物理学叫“最小作用量原理”）。球从起点到终点有无数种可能的跑法，但大自然一定会自动规划出一条让“总折腾程度”最小的路线。你只要把能量公式套进一个固定的数学方程里，它就会自动吐出球的运动轨迹。

**为什么这是降维打击？**

- **消灭了方向：** 能量是纯数字（标量），没有方向。你再也不用管什么正交分解、不需要算夹角的正弦余弦了。
- **无视了支持力：** 牛顿力学里最烦的就是轨道的支持力、绳子的拉力。拉格朗日力学从根本上把它过滤掉了。

在软件工程中，我们经常面临同样的抉择：你是选择做那个死磕每一个实现细节的“微观包工头”，还是做那个依靠抽象契约、掌控全局的“大局观老板”？

如果你在写代码时，总是纠结于具体的 `dict` 是如何存储数据的，或者在写函数时，必须绑定死具体的字典或函数实例，那你可能还在用牛顿式的微观思维在“搬砖”。

而 Python 的**抽象基类（ABC）**，尤其是 `Callable` 和 `Mapping`，正是拉格朗日式的“降维打击”。它们不关心你内部怎么实现，它们只定义**契约**：只要你符合这个契约，系统就能稳定运转。

## 一、这句话做了什么

它从标准库模块 `collections.abc` 中导入两个**抽象基类**（ABC，Abstract Base Class）：

- **`Callable`**：表示“可以被调用的东西”，也就是能写成 `x(...)` 的对象。
- **`Mapping`**：表示“只读的键值映射”，也就是像字典一样能用 `x[key]` 取值的对象。

它们主要有三种用途：

1. **类型注解**（最常见）：告诉读代码的人和类型检查器（mypy、Pyright）参数应该是什么形状。
2. **运行时检查**：配合 `isinstance()` 判断对象类型。
3. **作为父类**：继承它们来实现自定义容器，只写几个核心方法，其余方法自动获得。

## 二、为什么从 `collections.abc` 导入，而不是 `typing`

你可能见过旧写法：

```python
from typing import Callable, Mapping   # 旧写法
```

从 Python 3.9 起（PEP 585），`collections.abc` 里的类可以直接加方括号写泛型，比如 `Mapping[str, int]`。`typing.Callable` 和 `typing.Mapping` 已经变成**弃用的别名**。

所以现在推荐：

```python
from collections.abc import Callable, Mapping   # 新写法，推荐
```

同理，`list[int]`、`dict[str, int]` 也不再需要 `typing.List`、`typing.Dict`。

---

## 三、`Callable` 详解

### 1. 基本语法

```python
Callable[[参数类型1, 参数类型2, ...], 返回类型]
```

| 写法 | 含义 |
|---|---|
| `Callable[[int, str], bool]` | 接收 (int, str)，返回 bool |
| `Callable[[], None]` | 无参数，无返回值 |
| `Callable[..., Any]` | 任意参数，任意返回值（`...` 是字面量省略号） |
| `Callable[[str], bool]` | 接收一个 str，返回 bool，比如“检查器” |

### 2. 什么算 Callable

函数、lambda、类本身（调用类就是创建实例）、绑定方法、定义了 `__call__` 的对象实例、`functools.partial` 对象都算。

```python
from collections.abc import Callable

class Greeter:
    def __call__(self, name: str) -> str:
        return f"Hi {name}"

print(isinstance(len, Callable))         # True
print(isinstance(lambda: 1, Callable))   # True
print(isinstance(Greeter, Callable))     # True（类本身）
print(isinstance(Greeter(), Callable))   # True（有 __call__）
print(isinstance(42, Callable))          # False
```

日常判断其实直接用内置的 `callable(x)` 更简洁，效果相同。

### 3. 使用场景一：回调函数 / 策略函数

```python
from collections.abc import Callable

def apply_discount(price: float, strategy: Callable[[float], float]) -> float:
    return strategy(price)

def ten_percent_off(p: float) -> float:
    return p * 0.9

print(apply_discount(100, ten_percent_off))      # 90.0
print(apply_discount(100, lambda p: p - 15))     # 85
```

调用方可以把“怎么打折”作为参数传进来，函数本身不需要知道具体逻辑。

### 4. 使用场景二：返回函数（工厂 / 闭包）

```python
from collections.abc import Callable

def make_multiplier(n: int) -> Callable[[int], int]:
    def multiply(x: int) -> int:
        return x * n
    return multiply

triple = make_multiplier(3)
print(triple(5))   # 15
```

### 5. 使用场景三：装饰器（SME 级别：`ParamSpec`）

普通写法 `Callable[..., Any]` 会让类型检查器丢失原函数的参数信息。用 `ParamSpec` 可以完整保留签名：

```python
import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"调用 {func.__name__}，参数 {args} {kwargs}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    return a + b

add(1, 2)        # 调用 add，参数 (1, 2) {}
# add("x", 2)    # mypy 会报错，因为签名被保留了
```

Python 3.12+ 可以用更简洁的语法：`def log_calls[**P, R](func: Callable[P, R]) -> Callable[P, R]:`。

### 6. `Callable` 的局限

`Callable` 无法描述**关键字参数名**、默认值或重载。如果需要，就改用 `Protocol`：

```python
from typing import Protocol

class Formatter(Protocol):
    def __call__(self, text: str, *, upper: bool = False) -> str: ...
```

---

## 四、`Mapping` 详解

### 1. 基本语法

```python
Mapping[键类型, 值类型]
```

例如 `Mapping[str, int]` 表示“键是 str、值是 int 的只读映射”。

### 2. `Mapping` 与 `dict` 的区别（核心概念）

| | `dict` | `Mapping` |
|---|---|---|
| 本质 | 具体类 | 抽象接口 |
| 可读 | 是 | 是 |
| 可写（`m[k] = v`、`del`、`update`） | 是 | **接口里没有** |
| 能接受的对象 | 仅 dict 及其子类 | dict、OrderedDict、MappingProxyType、自定义映射等 |

需要可写的抽象接口时，用 `MutableMapping`。

### 3. 使用场景一：函数参数（最重要的用法）

经验法则是：**参数尽量宽松（用 `Mapping`），返回值尽量具体（用 `dict`）**。

```python
from collections.abc import Mapping

def total_score(scores: Mapping[str, int]) -> int:
    return sum(scores.values())

print(total_score({"Alice": 90, "Bob": 85}))   # 175
```

把参数写成 `Mapping` 有两个好处：

- 它向调用方承诺“我不会修改你的字典”。如果函数内部写了 `scores["x"] = 1`，类型检查器会报错。
- 调用方可以传任何映射类型，不必非要是 `dict`。

### 4. 使用场景二：真正的只读配置（`MappingProxyType`）

类型注解只是“约定”，运行时并不阻止修改。要在运行时真正只读，就用 `types.MappingProxyType`：

```python
from collections.abc import Mapping
from types import MappingProxyType

_raw = {"timeout": 30, "retries": 3}
CONFIG: Mapping[str, int] = MappingProxyType(_raw)

print(CONFIG["timeout"])                 # 30
print(isinstance(CONFIG, Mapping))       # True
print(isinstance(CONFIG, dict))          # False

CONFIG["timeout"] = 99   # TypeError: 'mappingproxy' object does not support item assignment
```

### 5. 使用场景三：继承 `Mapping` 实现自定义容器

只需实现三个抽象方法：`__getitem__`、`__iter__`、`__len__`。下面这些方法会**自动获得**：`get`、`keys`、`values`、`items`、`__contains__`（`in`）、`__eq__`。

```python
from collections.abc import Iterator, Mapping

class CaseInsensitiveMap(Mapping[str, str]):
    """键不区分大小写的只读映射"""

    def __init__(self, data: Mapping[str, str]) -> None:
        self._data = {k.lower(): v for k, v in data.items()}

    def __getitem__(self, key: str) -> str:
        return self._data[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

headers = CaseInsensitiveMap({"Content-Type": "json"})
print(headers["CONTENT-TYPE"])     # json
print("content-type" in headers)   # True（自动获得）
print(headers.get("x", "无"))      # 无（自动获得）
print(dict(headers.items()))       # {'content-type': 'json'}
```

少实现一个抽象方法时，实例化会直接报 `TypeError: Can't instantiate abstract class...`，这就是 ABC 的保护作用。

### 6. 使用场景四：运行时判断“像不像字典”

```python
from collections.abc import Mapping

def flatten(obj, prefix=""):
    if isinstance(obj, Mapping):          # 比 isinstance(obj, dict) 更通用
        for k, v in obj.items():
            yield from flatten(v, f"{prefix}{k}.")
    else:
        yield prefix.rstrip("."), obj

print(dict(flatten({"db": {"host": "x", "port": 5432}})))
# {'db.host': 'x', 'db.port': 5432}
```

---

## 五、综合案例：两者结合，构建高扩展性的注册表模式

实际项目中很常见 `Mapping[str, Callable[...]]` 这种组合，也就是“名字 → 处理函数”的**注册表**模式：

```python
import re
from collections.abc import Callable, Mapping
from types import MappingProxyType

_HIGH_RISK = re.compile(
    r"\b(?:approve|approved|pay(?:ing)? (?:me|my|out)|how much will (?:i|you)|decline[ds]?|"
    r"reject(?:ed)?|settle(?:ment)?|will you cover my claim|is my claim (?:approved|accepted))\b",
    re.I,
)

Check = Callable[[str], bool]   # 类型别名：一个“检查器”

RULES: Mapping[str, Check] = MappingProxyType({
    "high_risk_claim": lambda t: bool(_HIGH_RISK.search(t)),
    "too_long":        lambda t: len(t) > 2000,
    "has_email":       lambda t: "@" in t,
})

def run_checks(text: str, rules: Mapping[str, Check] = RULES) -> list[str]:
    """返回所有被触发的规则名"""
    return [name for name, check in rules.items() if check(text)]

print(run_checks("Is my claim approved? email me at a@b.com"))
# ['high_risk_claim', 'has_email']
```

这个设计的好处有三点：

1. **可扩展**：新增规则只需往字典里加一行，`run_checks` 不用改。
2. **可测试**：测试时可以传一个只含假规则的 `Mapping`，无需任何 mock 工具。
3. **安全**：`MappingProxyType` 防止其他模块在运行时偷偷篡改全局规则表。

---

## 六、SME 进阶要点

**1. 参数化泛型不能用于 `isinstance`**

```python
isinstance(f, Callable)               # 可以
isinstance(f, Callable[[int], str])   # TypeError
```

运行时 Python 无法检查函数签名，方括号里的信息只给类型检查器看。

**2. 型变（Variance）：为什么参数要用 `Mapping` 而不是 `dict`**

`Mapping` 对**值类型是协变的（Covariant）**，而 `dict` 是**不变的（Invariant）**：

```python
from collections.abc import Mapping

def f(m: Mapping[str, float]) -> None: ...
def g(m: dict[str, float]) -> None: ...

data: dict[str, int] = {"a": 1}
f(data)   # mypy 通过：只读，int 当 float 读完全合法
g(data)   # mypy 报错：g 可能往里写 float，会污染 dict[str, int]
```

这正是“只读接口类型更宽松”的理论依据。

**3. `Callable` 对参数是逆变的（Contravariant）**

需要 `Callable[[int], object]` 的地方，可以传入 `Callable[[float], str]`（能接受更宽的输入参数、返回更具体的结果类型）。反过来则不行。

**4. 注解不影响运行效率**

Python 不会在运行时强制检查类型注解，也不会因此拖慢执行性能。要让类型约束发挥作用，需要在 CI 门禁中运行 mypy 或 Pyright。

---

## 七、练习题

1. 写出这个函数参数的类型注解：接收一个 `str` 和一个 `int`，什么都不返回。
2. `isinstance(str, Callable)` 的结果是什么？为什么？
3. 一个函数只读取配置字典，参数应该注解为 `dict[str, str]` 还是 `Mapping[str, str]`？
4. 继承 `Mapping` 至少要实现哪三个方法？
5. `x: Mapping[str, int] = {"a": 1}` 之后执行 `x["b"] = 2`，运行时会报错吗？mypy 会报错吗？

### 参考解答

1. `Callable[[str, int], None]`。
2. `True`。因为 `str` 本身是一个类，在 Python 中调用类即可构造实例对象，因此任何类都是可调用的。
3. 应该注解为 `Mapping[str, str]`。这向调用方表达了“只读契约”，并且接受任何符合映射协议的容器。
4. `__getitem__`、`__iter__`、`__len__`。
5. 运行时**不会**报错，因为 `x` 底层依然是一个普通的内置 `dict`，类型注解在运行时被忽略；但 **mypy 会在静态检查阶段直接报错**，阻止写入非法属性。如果需要在运行时彻底防篡改，应当包裹 `MappingProxyType`。

---

## 八、一句话总结与回响

- **`Callable`** 描述“能调用的东西”，用于回调、策略、工厂和装饰器。
- **`Mapping`** 描述“只读的字典式对象”，用于函数参数、只读配置和自定义容器。
- **从 `collections.abc` 导入**是 Python 3.9+ 的现代规范。
- **参数宽松、返回具体**：注解给工具看，运行时保护靠 `MappingProxyType` 等具体手段。

回到开头微观包工头与大局观老板的比喻：与其在每一个函数的每一行代码里死磕对象是不是一个底层的 concrete `dict`、内部怎么哈希存储（像牛顿力学一样算尽每一个瞬间的微观支持力），不如用 `Callable` 与 `Mapping` 定义清晰的契约边界（像拉格朗日那样，只看宏观约束与作用量）。

契约一旦立住，系统的复杂度自然降维。下次当你在函数签名写下 `def process(data: dict)` 时，不妨问问自己：你真的需要一个随时可能被修改污染的具体字典，还是只需要一个稳固的只读键值契约？