---
title: "LLMOps 实战 01：别让一个 14B 大模型干所有活——小模型路由与可降级后端"
date: 2026-11-10
categories: [engineering, ai, llmops]
tags: [small-models, bge, reranker, fastembed, design-patterns, fallback]
---

# LLMOps 实战 01：别让一个 14B 大模型干所有活

> 黄金，不会埋在人人路过的地方。

人人路过的地方是：「有 GPU，上个大模型，所有问题都丢给它。」判断是不是注入？问 LLM。找哪段文档相关？问 LLM。这个字段是不是人名？还是问 LLM。

我家里那台 5080 很能打，但这个系列要讲的项目（一个带 MCP 工具的 agent 后端）最后是这么分工的：**大模型只负责写最后那段话，其它判断全部下沉给小模型或纯代码。** 这是系列第一篇，先讲地基：小模型路由。

系列目录：

1. 小模型路由与可降级后端（本篇）
2. Guardrail：agent 循环上的四个检查点
3. Prompt 是发布物，不是字符串常量
4. 跨进程的实时调用栈
5. 混合检索 RAG：BM25 + 向量 + RRF + rerank
6. 评测、Quality Gate 与闭环
7. 工程手感：那些没写进设计文档的修法

---

### 1. 🎯 30 秒版本

- 把系统里每一种「判断」抽象成一个 **slot**（槽位）：向量化、精排、分类、实体抽取、语种识别。
- 每个 slot 有两个后端：**真实小模型**（装了才有）和**确定性降级实现**（纯 Python，永远可用）。
- 调用方只认接口，不知道背后是谁。CI、冷启动的笔记本、没网的机器全都能跑。
- `profile()` 报告每个 slot 实际解析到了哪个后端，写进 trace 和评测报告——否则你永远说不清「这个分数是谁跑出来的」。

| Slot | 小模型 | 降级实现 | 谁在用 |
|---|---|---|---|
| embedder | bge-small（ONNX，CPU） | 字符 n-gram 特征哈希 | RAG 召回、注入分类器 |
| reranker | jina reranker | 查询词覆盖率 | RAG 精排 |
| classifier | few-shot 最近邻 | 关闭（只走规则） | 改写型注入 |
| entities | GLiNER | 关闭（只走正则） | 没有固定形状的 PII |
| language | — | Unicode 文字系统启发式 | 语种路由 |

---

### 2. ⚙️ 底层原理

#### 2.1 接口先行：Protocol 而不是基类

```python
class Embedder(Protocol):
    id: str
    semantic: bool  # False => 只有词法相似度；语义分类器必须保持关闭

    def embed(self, texts: list[str]) -> list[Vector]: ...
```

两个细节值得抄：

**`id` 是身份证。** 索引里每个文档都记了「我是被哪个 embedder 向量化的」。换模型后 `id` 变了，增量同步自动判定全部过期、重新向量化。不记这个字段，你会得到一个混着两种向量空间的索引，检索结果诡异但不报错——最难查的那种 bug。

**`semantic` 是诚实标记。** 降级用的哈希 embedder 也能算余弦相似度，数字看起来一样正经，但它只懂「字面像不像」。如果拿它去驱动「这句话是不是注入攻击」的判定，就是在用噪声做安全决策。所以接口上强制每个后端自报家门，消费方一行代码把关：

```python
if not getattr(embedder, "semantic", False):
    return  # 词法降级后端：这里的相似度没有意义
```

> 经验：**降级实现最危险的地方不是「效果差」，而是「看起来一样」。** 让能力差异在类型上可见。

#### 2.2 降级后端：穷但是确定

```python
class HashingEmbedder:
    id = "hashing-ngram-256"
    semantic = False
    dim = 256

    def embed(self, texts):
        out = []
        for text in texts:
            vec = [0.0] * self.dim
            low = f" {' '.join(text.lower().split())} "
            for n in (2, 3):
                for i in range(len(low) - n + 1):
                    h = int.from_bytes(hashlib.blake2b(low[i:i+n].encode(), digest_size=4).digest(), "big")
                    vec[h % self.dim] += 1.0 if (h >> 31) & 1 else -1.0
            out.append(_normalize(vec))
        return out
```

这是经典的 **feature hashing**（哈希技巧）：把字符 2-gram、3-gram 哈希到 256 个桶里，符号位决定加还是减（减少碰撞偏差），最后 L2 归一化。零依赖、零下载、同样输入永远同样输出。

为什么用 `blake2b` 而不是内置 `hash()`？因为 Python 的 `hash()` 对字符串每个进程随机加盐，同一句话两次运行得到不同向量，索引直接作废。**凡是要落盘、要跨进程比较的哈希，都不能用 `hash()`。**

#### 2.3 解析后端：一个函数管住所有失败

```python
def _load(slot, factory, fallback):
    if settings.small_models_mode == "off":
        return fallback
    try:
        return factory()
    except ImportError:
        logger.info("small_models: %s backend not installed; using fallback", slot)
    except Exception as exc:  # 比如离线时模型下载失败
        logger.warning("small_models: %s backend failed to load (%s); using fallback", slot, exc)
    return fallback

@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return _load("embedder", lambda: FastEmbedEmbedder(settings.embed_model), HashingEmbedder())
```

三种失败被区别对待：

- **显式关闭**（`PORTAL_SMALL_MODELS=off`）：测试和 CI 用，安静返回降级。
- **没装**（`ImportError`）：正常情况，info 级别。
- **装了但加载失败**：warning。这是要人看的。

`lru_cache(maxsize=1)` 是最便宜的懒加载单例：第一次调用才加载模型，之后复用。配一个 `reset()` 清缓存，测试才不会互相污染。

#### 2.4 分类器：先别急着微调

```python
class FewShotClassifier:
    def __init__(self, embedder, examples: dict[str, list[str]]):
        self.embedder = embedder
        self._examples = {label: embedder.embed(texts) for label, texts in examples.items() if texts}

    def scores(self, text: str) -> dict[str, float]:
        vec = self.embedder.embed([text])[0]
        return {label: max(cosine(vec, ex) for ex in vecs) for label, vecs in self._examples.items()}
```

每个标签给十几条例句，判定时看「离哪一类最近的那条例句有多近」。没有训练循环，没有 LLM 调用，加一条例句就是改一行 YAML。

这不是真正的 SetFit（SetFit 会对比学习微调 embedding 再训练分类头）。但它占住了同一个接口位置：等标注样本够多了，换一个微调过的头进来，调用方不用改。**先用最笨的办法把接口立住，再用数据决定要不要上更重的方案。**

---

### 3. 🧭 为什么选它，不选别的

**为什么不全用大模型？**

| 维度 | 大模型判定 | 小模型 / 规则 |
|---|---|---|
| 延迟 | 秒级，占 GPU | 毫秒级，CPU |
| 确定性 | 同样输入可能不同输出 | 确定 |
| 可测试 | 需要 live 评测 | 普通单测 |
| 被攻击面 | 判定本身可被注入 | 正则不听人话 |
| 成本 | 每轮多一次调用 | 约等于零 |

最后一行最关键：**用 LLM 判断「这段话是不是在骗 LLM」，等于让被告当法官。**

**为什么是 fastembed，不是 sentence-transformers？**
fastembed 走 ONNX Runtime，不依赖 torch。装上之后环境多几十 MB，而不是两个 G；CPU 上跑得够快，而且不和大模型抢显存。部署目标是一台同时跑 LLM 的机器，这点决定性。

**为什么语种识别只做了 Unicode 启发式？**
它只能分出中文、日文、拉丁这种「文字系统」，分不出英语和法语。但我此刻的需求只是「这段是不是中文」，为这个引入一个编译依赖不值。接口留着，需求真来了再换。

---

### 4. 🔬 常见追问

**Q：降级实现效果差，CI 用它跑评测还有意义吗？**
有，但要分清它在测什么。规则、流程、接线这些与模型无关的行为，降级后端测得一样准。与模型质量相关的用例，用 `requires: ["semantic_embedder"]` 声明依赖，降级环境下显示为 skipped——**跳过要显式可见，不能悄悄算通过。**

**Q：真实踩到的坑？**
bge-small-**en** 对中文几乎没有区分力。我把评测集每条输入的相似度打出来看，中文良性句子对「攻击例句」的相似度高达 0.79–0.82，和真正的英文攻击混在一起。原因很朴素：英文模型看所有中文都差不多。修法不是调阈值，而是**路由**：

```python
if cfg.get("scripts") and small_models.detect_script(text) not in cfg["scripts"]:
    return  # 按语种路由：这个 embedder 没学过这种文字
```

这正是语种识别 slot 存在的意义——小模型组合的精髓不在「多」，在「谁该上场」。

**Q：怎么知道线上到底用的哪个后端？**
`GET /ops/status` 调 `profile()`。评测报告的 `profile` 字段也是它，基线按 profile 分开存，两套后端的分数不会互相比较。

---

### 5. 🛠 自己动手

1. 给一个你现有的项目找出三处「其实不需要 LLM」的判断，各写一个 Protocol。
2. 为其中一个写降级实现，要求：无第三方依赖、同输入同输出。
3. 加一个能力标记（类似 `semantic`），并找到一处必须检查它的调用点。
4. 故意把模型名写错，确认系统降级而不是崩溃，并且日志级别是 warning。
5. 换一个 embedder，观察你的索引是否自动识别出「需要重建」。不能的话，补上 `id`。
