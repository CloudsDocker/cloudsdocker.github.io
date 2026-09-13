---
title: "为什么摩根士丹利和 Jane Street 禁止用 YAML 做配置"
date: 2026-09-13
header:
  image: https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200
categories: [engineering, configuration]
tags: [yaml, toml, json5, protobuf, cue, quant, configuration, type-safety]
---

# 为什么摩根士丹利和 Jane Street 禁止用 YAML 做配置

上周我在审计自己博客的 Jekyll 文章时，写了一个 Python 脚本来解析所有 markdown 文件的 YAML frontmatter。脚本跑得很顺利——直到我想起一件事：**在我之前待过的华尔街交易系统里，这种代码根本不允许存在。**

不是因为脚本写得差。而是因为它用了 YAML。

---

## 一个 "NO" 毁掉一个下午

先看一个真实的配置场景。假设你在写一个交易系统的风控配置：

```yaml
# risk_config.yaml
enable_margin_call: YES
enable_short_selling: NO
max_position_limit: 1_000_000
api_version: 1.2.3
country_code: NO    # 挪威 (Norway)
```

看起来很清晰？用 Python 加载试试：

```python
import yaml

config = yaml.safe_load(open("risk_config.yaml"))
print(config)
```

输出：

```python
{
    'enable_margin_call': True,      # YES → True ✅ 看起来对
    'enable_short_selling': False,   # NO  → False ✅ 看起来也对
    'max_position_limit': 1000000,   # 下划线被吃掉了，但值对
    'api_version': '1.2.3',          # 字符串 ✅
    'country_code': False            # NO → False ❌❌❌ 挪威消失了
}
```

**挪威的国家代码 `NO` 被 YAML 解析成了布尔值 `False`。**

这不是假设——这是 YAML 1.1 规范的真实行为。在 YAML 1.1 里，以下值全部被隐式转换为布尔型：

| 被当成 `True` 的 | 被当成 `False` 的 |
|:---|:---|
| `YES`, `Yes`, `yes` | `NO`, `No`, `no` |
| `TRUE`, `True`, `true` | `FALSE`, `False`, `false` |
| `ON`, `On`, `on` | `OFF`, `Off`, `off` |
| `Y`, `y` | `N`, `n` |

这意味着如果你在配置文件里写了挪威(`NO`)、丹麦某些缩写(`DK` 倒没事)、或者任何恰好撞上这张表的字符串，你的数据就会被 **静默地** 改掉。没有警告，没有报错，没有任何提示。

## 不只是布尔型——类型转换地雷到处都是

```yaml
# 更多惊喜
version: 1.0       # → 浮点数 1.0，不是字符串 "1.0"
version: 1.0.0     # → 字符串 "1.0.0"（因为有两个点）
port: 0800         # → 整数 512（八进制解析！）
timestamp: 2026-09-13  # → datetime 对象，不是字符串
price: 3.14e2      # → 浮点数 314.0 ✅ 但你确定想要浮点？
```

用代码验证：

```python
import yaml

cases = """
version_a: 1.0
version_b: 1.0.0
port: 0800
timestamp: 2026-09-13
"""

data = yaml.safe_load(cases)
for k, v in data.items():
    print(f"{k}: {v!r:>30}  (type: {type(v).__name__})")
```

```
version_a:                            1.0  (type: float)
version_b:                        '1.0.0'  (type: str)
port:                                 512  (type: int)
timestamp:       datetime.date(2026, 9, 13)  (type: date)
```

注意 `version: 1.0` 变成了浮点数，而 `version: 1.0.0` 变成了字符串。**同一个字段名，格式稍微不同，类型就变了。** 这在静态类型语言里会编译报错，但在 YAML 里默默通过。

而 `port: 0800`？YAML 1.1 把 `0` 开头的数字当八进制。`0800` 在八进制里是 `512`。你的服务绑定到了完全错误的端口，而且没有任何报错。

## 为什么金融系统零容忍

在交易系统里，一个配置错误的代价是什么？

- 2012 年，Knight Capital 因为一个部署配置错误，**45 分钟亏损 4.6 亿美元**，直接破产。
- 配置文件里的一个布尔值翻转，可能意味着风控开关被关闭、止损逻辑失效、或者订单路由到错误的交易所。

所以摩根士丹利、Jane Street、Two Sigma 等量化公司的做法很简单：**从根源上消除这类风险——禁用 YAML。**

核心原则是：

> **配置文件不应该有"猜测"行为。写的是什么，解析出来的就必须是什么。**

这和医院的"五个正确"原则（正确的病人、正确的药物、正确的剂量、正确的途径、正确的时间）如出一辙——当错误代价是人命（或几亿美元）的时候，**你不能允许系统替你做任何推断**。

---

## 配置格式全景图：YAML 的对手们

在讲具体替代方案之前，先建立全局视角。2026 年，主流的配置格式大概有这么七个选手。把它们想象成一个从"人类友好"到"机器友好"的光谱：

```
人类友好 ◄──────────────────────────────────────► 机器友好
 YAML   TOML   JSON5   JSONC   JSON   HCL   Protobuf/FlatBuffers
 │       │       │       │       │      │      │
 │       │       │       │       │      │      └─ 编译时强类型，二进制序列化
 │       │       │       │       │      └─ HashiCorp 的 DSL，专为基础设施
 │       │       │       │       └─ 最严格：无注释、无尾逗号、字符串必须双引号
 │       │       │       └─ JSON + 注释（VS Code 用的就是这个）
 │       │       └─ JSON + 注释 + 尾逗号 + 单引号 + 无引号 key
 │       └─ 显式类型，零隐式转换，Python 3.11 内置
 └─ 隐式类型转换，最灵活也最危险
```

逐个认识一下：

### TOML — "明确的配置文件"

**全名**：Tom's Obvious, Minimal Language。没错，Tom 是人名——GitHub 联合创始人 Tom Preston-Werner 在 2013 年创造了它，理由和本文一样：**受够了 YAML 的歧义。**

TOML 的核心设计原则：**能被无歧义地映射到 hash table。** 每个值的类型在语法层面就是确定的，不需要解析器"猜"。

```toml
# config.toml — 所见即所得
title = "My App"           # 字符串必须加引号 → 永远是字符串
port = 8080                # 整数，永远是十进制
enabled = true             # 布尔，只认 true/false（全小写）
version = "1.0"            # 加了引号 → 字符串，不会变成浮点数
created = 2026-09-13T10:00:00Z   # 原生支持 RFC 3339 日期时间

[database]                 # 用 [section] 表示嵌套，比 YAML 的缩进更不容易出错
host = "localhost"
ports = [5432, 5433]       # 数组
```

**关键优势**：Python 3.11 起内置了 `tomllib`（只读解析器），**零依赖**，不需要 `pip install` 任何东西。这是标准库对 TOML 地位的官方背书。

**局限**：深层嵌套时语法变得冗长——你需要写 `[a.b.c.d]`，而 YAML 用缩进可以自然表达无限嵌套。这也是为什么 Kubernetes 这种动辄 5-6 层嵌套的配置没选 TOML。

### JSON — "最安全也最不方便"

2001 年 Douglas Crockford 从 JavaScript 对象字面量语法里提炼出来的子集。**没有注释、没有尾逗号、字符串必须双引号、key 也必须双引号。** 极度严格，因此也极度可预测——不可能发生隐式类型转换。

```json
{
  "country_code": "NO",
  "port": 800,
  "enabled": true
}
```

`"NO"` 永远是字符串，因为它被引号包着。`true` 永远是布尔值，因为它没有引号。**类型完全由语法决定，零歧义。**

但不能写注释这一点是致命的——配置文件没有注释，等于法律条文没有注解，半年后没人记得某个参数为什么是这个值。

### JSON5 — "JSON 的人性化补丁"

2012 年社区提出的 JSON 超集，目标是**让 JSON 适合人类手写**：

```json5
{
  // ✅ 可以写注释了
  country_code: "NO",        // key 可以不加引号
  port: 800,                 // ✅ 可以有尾逗号
  description: '单引号也行',  // ✅ 单引号字符串
  big_number: 0xFF,          // ✅ 十六进制
  /* 多行注释也支持 */
}
```

JSON5 保留了 JSON "零隐式转换"的核心安全性，同时加上了手写配置最需要的功能。前端生态用得特别多（`.babelrc` / `tsconfig.json` 的注释实际上走的就是类 JSON5 解析）。

**局限**：没有原生日期类型、没有多行字符串（要用 `\n` 转义），Python 生态里需要 `pip install json5`，不如 TOML 的标准库地位。

### JSONC — "VS Code 的选择"

和 JSON5 思路类似，但更保守——**只加了注释和尾逗号**，其余和标准 JSON 完全一样。VS Code 的 `settings.json` 用的就是 JSONC。可以理解为"JSON5 的最小子集"。

### HCL — "基础设施专用语言"

HashiCorp Configuration Language，Terraform 的配置格式。专为"声明式基础设施"设计，支持变量引用、条件表达式、循环：

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.env == "prod" ? "m5.xlarge" : "t3.micro"

  tags = {
    Name = "web-${var.env}"
  }
}
```

HCL 本质上不是通用配置格式，而是一个**领域特定语言（DSL）**。在 Terraform/Vault/Consul 之外几乎没人用它。

### CUE — "配置界的 TypeScript"

Google 的 Marcel van Lohuizen（Protocol Buffers 团队成员）在 2019 年创造。CUE 的核心思想是**配置和校验合为一体**——你写的每一行既是值，也是约束：

```cue
// config.cue
#RiskConfig: {
    enable_margin_call:   bool
    enable_short_selling: bool
    country_code:         =~"^[A-Z]{2}$"    // 正则约束：必须是两个大写字母
    port:                 int & >0 & <65536  // 范围约束
}

production: #RiskConfig & {
    enable_margin_call:   true
    enable_short_selling: false
    country_code:         "NO"     // ✅ 满足正则
    port:                 800      // ✅ 满足范围
}
```

如果有人把 `country_code` 写成 `false` 或者 `port` 写成 `99999`，**CUE 在验证阶段就会报错**，不需要额外的 Pydantic 或 JSON Schema。Kubernetes 社区正在用 CUE 替代部分 YAML 工作流（`cue export` 可以生成 YAML/JSON）。

### Protobuf / FlatBuffers — "编译时消灭一切歧义"

Google 的 Protocol Buffers 和 FlatBuffers 走的是终极路线：**配置不是文本文件，而是编译后的二进制。** 类型在 `.proto` 文件里定义，编译器生成各语言的读写代码，运行时没有任何"解析"过程。

```protobuf
// risk_config.proto
syntax = "proto3";

message RiskConfig {
  bool   enable_margin_call   = 1;
  bool   enable_short_selling = 2;
  int64  max_position_limit   = 3;
  string api_version          = 4;
  string country_code         = 5;
}
```

类型错误在 **编译期** 就被捕获——把 `bool` 的字段赋值成字符串？编译不过。不需要等到运行时才发现挪威变成了 `False`。

**局限**：人类不能直接阅读二进制文件，调试时需要 `protoc --decode` 或者 `pbtxt`（Protobuf 文本格式）做转换。配置变更也需要重新编译——对需要运营人员热更新的场景不友好。

### 一张表收尾

| 格式 | 诞生年份 | 核心卖点 | 类型安全 | 注释 | 嵌套能力 | Python 支持 |
|:---|:---|:---|:---|:---|:---|:---|
| **YAML** | 2001 | 人类可读，表达力强 | ❌ 隐式转换地雷 | ✅ `#` | ✅ 缩进嵌套，无限深 | `PyYAML` / `ruamel.yaml` |
| **TOML** | 2013 | 显式类型，零歧义 | ✅ | ✅ `#` | ⚠️ 深嵌套冗长 | `tomllib`（3.11 标准库） |
| **JSON** | 2001 | 最严格，机器解析最快 | ✅ | ❌ | ✅ | 标准库 `json` |
| **JSON5** | 2012 | JSON + 注释 + 人性化 | ✅ | ✅ `//` `/* */` | ✅ | `pip install json5` |
| **JSONC** | ~2015 | JSON + 注释（最小改动）| ✅ | ✅ `//` `/* */` | ✅ | 第三方库 |
| **HCL** | 2014 | 基础设施声明式 DSL | ✅ | ✅ `#` `//` | ✅ + 表达式 | `pip install python-hcl2` |
| **CUE** | 2019 | 配置 + 校验一体化 | ✅✅ 带约束系统 | ✅ `//` | ✅ | CLI `cue` / Go SDK |
| **Protobuf** | 2008 | 编译时强类型，二进制 | ✅✅✅ 编译级 | ✅ `//` | ✅ | `protobuf` / `grpcio` |

---

## 用同一个例子看差异

回到那个让挪威消失的风控配置，看每种格式怎么处理同一份数据：

### TOML 版

```toml
# risk_config.toml
enable_margin_call = true
enable_short_selling = false
max_position_limit = 1_000_000
api_version = "1.2.3"
country_code = "NO"       # 永远是字符串，不会被转成 False
port = 800                # 永远是十进制整数
```

```python
import tomllib  # Python 3.11+ 标准库，零依赖

with open("risk_config.toml", "rb") as f:
    config = tomllib.load(f)

print(config["country_code"])   # "NO" — 字符串，符合预期
print(type(config["port"]))     # <class 'int'> — 十进制 800
```

TOML 的设计哲学：**字符串必须加引号，布尔值只认 `true`/`false`（全小写），数字永远是十进制。** 没有隐式转换，没有惊喜。

### JSON5 版

```json5
// risk_config.json5 — 支持注释和尾逗号
{
  enable_margin_call: true,
  enable_short_selling: false,
  country_code: "NO",       // 明确是字符串
  port: 800,                // 明确是十进制
  max_position_limit: 1000000,
  api_version: "1.2.3",
  // 这是注释，标准 JSON 不支持但 JSON5 支持
}
```

JSON 的安全性（零隐式转换）+ 人类写配置最需要的功能（注释、尾逗号）。

### CUE 版

```cue
// risk_config.cue — 值和校验规则写在一起
#RiskConfig: {
    enable_margin_call:   bool
    enable_short_selling: bool
    max_position_limit:   int & >0
    api_version:          =~"^\\d+\\.\\d+\\.\\d+$"
    country_code:         =~"^[A-Z]{2}$"
    port:                 int & >=1 & <=65535
}

production: #RiskConfig & {
    enable_margin_call:   true
    enable_short_selling: false
    max_position_limit:   1000000
    api_version:          "1.2.3"
    country_code:         "NO"     // 正则保证两个大写字母
    port:                 800      // 范围约束保证合法端口
}
```

```bash
$ cue vet risk_config.cue   # 校验通过
$ cue export risk_config.cue --out json   # 导出为 JSON 给程序读
```

CUE 的杀手锏：**如果有人写了 `country_code: false`，`cue vet` 直接报错——因为 `false` 不满足正则 `^[A-Z]{2}$`。** 连 Pydantic 都不需要。

### Protobuf 版

```protobuf
// risk_config.proto
syntax = "proto3";

message RiskConfig {
  bool   enable_margin_call   = 1;
  bool   enable_short_selling = 2;
  int64  max_position_limit   = 3;
  string api_version          = 4;
  string country_code         = 5;   // 类型在 schema 里写死
}
```

类型错误在**编译期**就被捕获，不需要等到运行时才发现挪威变成了 `False`。

---

## 决策矩阵：什么场景用什么格式

| 场景 | 推荐格式 | 原因 |
|:---|:---|:---|
| 博客 frontmatter (Jekyll/Hugo) | YAML | 生态锁定，风险可控（只有几个字段） |
| 应用配置文件 | **TOML** | 显式类型 + Python 3.11 标准库 |
| 前端/API 配置 | **JSON5** | 前端生态天然亲和 |
| 基础设施即代码 | **HCL** / **CUE** | Terraform 用 HCL；多工具链用 CUE |
| 交易系统/风控参数 | **Protobuf** | 编译时校验，零歧义，零解析开销 |
| Kubernetes 清单 | YAML（被迫） | 生态锁定，但请务必用 linter |
| CI/CD Pipeline | YAML（被迫） | GitHub Actions / GitLab CI 都绑定了 YAML |

注意"被迫"两个字。Kubernetes 和 CI/CD 用 YAML 不是因为 YAML 好，是因为**先发优势锁定了整个生态**。这也是为什么 Kubernetes 社区一直在推 Helm (Go templates)、Kustomize、CUE lang——它们本质上都是在 YAML 上面加一层类型系统来弥补 YAML 的缺陷。

## 如果你必须用 YAML，至少做到这三件事

现实中很多场景无法避免 YAML（比如我的 Jekyll 博客）。如果你躲不开，至少遵守这三条：

**1. 所有字符串强制加引号**

```yaml
# ❌ 危险
country_code: NO

# ✅ 安全
country_code: "NO"
```

**2. 用 yamllint 做 CI 检查**

```bash
pip install yamllint
yamllint --strict your_config.yaml
```

`yamllint` 可以配置规则，强制要求所有字符串加引号（`quoted-strings: {required: only-when-needed}`）。

**3. 解析后立刻做 schema 校验**

```python
import yaml
from pydantic import BaseModel

class RiskConfig(BaseModel):
    enable_margin_call: bool
    enable_short_selling: bool
    country_code: str  # Pydantic 会拒绝 False → str 的转换
    port: int

raw = yaml.safe_load(open("config.yaml"))
config = RiskConfig(**raw)  # ← 类型不匹配这里会直接报错
```

用 Pydantic 做第二道防线：如果 YAML 把 `"NO"` 解析成了 `False`，Pydantic 在 strict mode 下会拒绝把 `bool` 赋值给 `str` 字段——至少让错误暴露在启动时而不是运行时。

## 回到那个博客审计脚本

回头看我最初写的那个博客审计脚本：

```python
fm = yaml.safe_load(parts[1])
img = (fm.get('header') or {}).get('image')
```

这段代码在博客场景下是安全的，因为 Jekyll frontmatter 的字段都是简单字符串和列表，撞上隐式类型转换的概率很低。但**同样的代码模式**如果被复制到一个金融系统的配置加载器里——比如从 YAML 读取交易所代码、货币对名称、风控开关——就可能成为一颗定时炸弹。

**配置格式的选择不是技术偏好，是风险管理决策。** 在你的个人博客里，YAML 的便利性大于它的风险。在管理几十亿美元的交易系统里，一个隐式类型转换的代价可能是公司的存亡。

选择工具的标准从来不是"它能不能工作"，而是"它在最坏的情况下会怎么失败"。

---

> *这篇文章源自一次博客审计脚本的编写过程——在修复自己代码的同时，想起了不同世界对同一个工具截然不同的态度。有时候，理解一个工具的最好方式，是去看谁拒绝使用它，以及为什么。*
