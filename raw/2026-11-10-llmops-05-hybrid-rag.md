---
title: "LLMOps 实战 05：一个说得清每一步的 RAG——BM25 + 向量 + RRF + rerank"
date: 2026-11-10
categories: [engineering, ai, rag]
tags: [rag, bm25, rrf, reranker, chunking, citations, sqlite]
---

# LLMOps 实战 05：一个说得清每一步的 RAG

> 凡是可以说的，都可以清楚地说；凡是不能说的，就应该沉默。——维特根斯坦

这句话几乎是 RAG 的需求文档：知识库里有的，带着出处说清楚；知识库里没有的，闭嘴。

多数 RAG demo 是三行：切块、塞向量库、拼 prompt。跑起来像那么回事，直到有人问一个工单号。向量检索对 `SN-23295` 这种标识符基本无能为力——在向量空间里它和 `SN-23296` 几乎是同一个点。

这篇拆一个每个环节都能解释、都能单独调试的检索管线。

---

### 1. 🎯 30 秒版本

```
markdown ─按标题分块─▶ SQLite 索引（按文件哈希增量更新）
query ─▶ BM25（精确词、编号、中文）─┐
      ─▶ 向量（bge-small）         ─┴▶ RRF 融合 ─▶ reranker 精排
      ─▶ top-k 段落 ─[丢掉带注入的段落]─▶ LLM
      ─▶ 带 [n] 引用的回答 ─[引用校验]─▶ grounded / 不 grounded
```

- **双路召回**：BM25 管字面，向量管语义，互补。
- **RRF 融合**：只看名次不看分数，两路不需要对齐量纲。
- **reranker**：对融合后的短名单重新排序，这是最后的质量来源。
- **引用校验**：回答里的 `[n]` 必须指向真实给过的段落。
- 检索结果里每条都带 `bm25_rank / dense_rank / score`——「为什么没搜到」可以被回答。

---

### 2. ⚙️ 底层原理

#### 2.1 分块：别让一段话失去主语

```python
def chunk_markdown(text, source, max_chars=1200, overlap=150):
    """按标题切，再把段落装箱到 max_chars。
    一个 chunk 不会跨标题，并且带着自己的标题路径。"""
    ...
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else _HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            path[:] = [(lv, h) for lv, h in path if lv < level] + [(level, m.group(2))]
        else:
            body.append(line)
```

三个决定：

**标题路径拼进 chunk 正文。** 一段「设成 30 即可。」单独拿出来毫无意义。前面加上 `Telegram Bot > Configuration` 它才是一条知识。这一行改动对检索质量的提升，通常大于换一个更贵的 embedding 模型。

**代码块里的 `#` 不是标题。** shell 注释 `# 进入目录` 会被朴素的正则当成一级标题，把一个章节腰斩。所以要跟踪是否在围栏内。这个 bug 我是看语料目录时发现的：一份文档的「标题列表」里混着一堆 shell 注释。

**维护标题栈。** 遇到 `##` 时，弹掉所有同级和更深的，再压入自己。`path[:] = [...]` 原地改，是因为外层闭包 `flush` 持有同一个列表。

#### 2.2 索引：增量，且认得自己的 embedder

```python
def sync(self, files):
    known = {row[0]: (row[1], row[2]) for row in self._db.execute("SELECT source, sha, embedder FROM docs")}
    for source in set(known) - set(files):
        self._delete(source)                      # 文件删了，索引跟着删
    for source, path in sorted(files.items()):
        sha = hashlib.sha256(text.encode()).hexdigest()
        if known.get(source) == (sha, self.embedder.id):
            continue                              # 内容没变，且是同一个模型算的
        ...重新分块、向量化、写入
```

跳过条件是 `(内容哈希, embedder 的 id)` 这个二元组。只比内容哈希是不够的：换了 embedding 模型，文件一个字没动，但旧向量全部作废。把模型身份放进缓存键，换模型后重建是自动发生的。

> 经验：**缓存键要包含所有会改变结果的输入**，模型版本尤其容易被漏掉。

向量用 `array.array("f").tobytes()` 存成 BLOB，一个 384 维向量 1.5KB，不需要 numpy。

#### 2.3 BM25：自己写，二十行

```python
def _bm25(self, query, tfs, df, avgdl, k1=1.5, b=0.75):
    n = len(tfs)
    terms = set(tokenize(query))
    idf = {t: math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) for t in terms if df.get(t)}
    scores = []
    for tf in tfs:
        dl = sum(tf.values())
        scores.append(sum(
            w * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avgdl))
            for t, w in idf.items() if tf.get(t)))
    return scores
```

读懂它只要记住三件事：词越稀有权重越高（idf）；同一个词出现多次，收益递减（`k1` 控制饱和）；长文档天然词多，要打折（`b` 控制长度归一）。

中文没有空格，分词器的处理是**字符二元组**：

```python
def tokenize(text):
    low = text.lower()
    tokens = _WORD_RE.findall(low)                       # 拉丁词
    for run in _CJK_RE.findall(low):                     # 连续的中日韩字符
        tokens.extend(run[i:i+2] for i in range(len(run) - 1)) if len(run) > 1 else tokens.append(run)
    return tokens
```

`滚动日志` → `滚动 / 动日 / 日志`。不需要分词库，召回够用，而且查询和文档用的是同一个函数——**索引时和查询时的分词必须完全一致**，这比分词本身准不准重要得多。

#### 2.4 RRF：不比分数，只比名次

BM25 的分数可能是 12.7，余弦相似度是 0.63。它们没法相加，归一化又很脆弱（一个离群值就把其它分数压扁）。

Reciprocal Rank Fusion 绕开了整个问题：

```python
rrf = {
    i: (1 / (RRF_K + bm25_rank[i]) if i in bm25_rank else 0.0)
     + (1 / (RRF_K + dense_rank[i]) if i in dense_rank else 0.0)
    for i in set(bm25_rank) | set(dense_rank)
}
```

每一路只贡献 `1/(60+名次)`。两路都排前面的文档得分最高；只在一路靠前的也能入围。常数 60 是原论文的经验值，作用是让第 1 名和第 2 名的差距不至于太悬殊。没有需要调的参数，这是它最大的优点。

还有个小细节：BM25 那一路只收分数大于零的（一个词都没匹配上就别来凑数），向量那一路不设这个限制。

#### 2.5 reranker：把最贵的计算留给最少的候选

embedding 是「各算各的再比较」（双塔），快，但查询和文档没有真正交互。cross-encoder 把查询和文档拼在一起过模型，准得多，也慢得多。

所以顺序是：两路各取 20 → 融合成至多 20 条短名单 → 只对这 20 条跑 reranker → 取前 5。**召回阶段要全，精排阶段要准，贵的模型只看少量候选。**

实测：纯降级后端 hit@1 是 0.95，换成 bge-small + jina reranker 到 1.0。语料很小，这个数字只说明方向。

#### 2.6 生成：文档也是不可信输入

```python
for h in hits:
    checked = guard.check_tool_result("knowledge_base", h.chunk.text)
    if any(f.category == "injection" for f in checked.findings):
        continue                      # 带指令的段落，丢
    if any(f.category == "secret" for f in checked.findings):
        h.chunk = Chunk(..., checked.text)   # 带密钥的段落，打码
    safe.append(h)
```

知识库是别人能写的地方。一篇文档里藏一句「忽略以上规则」，就是一次不需要接触用户的攻击。所以检索回来的段落要过和工具返回同一个 guardrail 检查点。

#### 2.7 引用校验：结构上的 groundedness

```python
def check_citations(answer, n_passages):
    cited = sorted({int(n) for n in _CITATION_RE.findall(answer)})
    invalid = [n for n in cited if not 1 <= n <= n_passages]
    abstained = ABSTAIN.lower()[:40] in answer.lower()
    return {..., "grounded": abstained or (bool(cited) and not invalid)}
```

只给了 3 段，回答里出现 `[7]`——编造的引用。一个引用都没有——无法溯源。这两种都判为不 grounded。

这是**结构校验**，不是语义校验：它不能保证 `[1]` 那句话真的被第 1 段支持。那是评测里 LLM 评审（faithfulness 打分）的工作。但它便宜、确定、每次请求都能跑，能挡住最离谱的那一类。

---

### 3. 🧭 为什么选它，不选别的

**为什么 SQLite + 线性扫描，不用向量数据库？**
语料是几十到几千个 chunk。纯 Python 扫一遍，从几毫秒到几十毫秒。向量库解决的是百万级的近似最近邻，在这个规模上它只带来一个要运维的服务。代码里写明了边界：超过几千 chunk，把 `_dense` 换成 pgvector 或 HNSW，管线其余部分不动。**先写清楚方案在什么规模失效，比一开始就上重型方案更负责。**

**为什么不用 LangChain / LlamaIndex？**
整条管线三百行，每个阶段的输入输出我都能打印出来看。检索质量的调试几乎全是「看中间结果」，框架恰恰把中间结果藏起来了。

**为什么不靠分数阈值让它拒答？**
reranker 的分数量纲随模型而变，降级后端是 0 到 1 的覆盖率，jina 输出的是 logit。写死一个阈值换个模型就错。于是拒答交给 prompt 里的明确规则，加上引用校验兜底；只有「什么都没检索到」这一种情况在调模型之前直接短路。

---

### 4. 🔬 常见追问

**Q：怎么调试「明明文档里有，就是搜不到」？**
调 `POST /rag/search`，看目标段落的 `bm25_rank` 和 `dense_rank`。两路都没进前 20，是分块或分词的问题；进了但最终被挤掉，是 reranker 的问题。分阶段看名次，比盯着最终结果猜有效得多。

**Q：英文问、中文文档答，行不行？**
词法检索做不到。我有一条这样的评测题，起初在降级后端下也通过了，后来新加一篇英文文档它就挂了——之前只是碰巧有词重叠。现在这条题声明了 `requires: ["semantic_embedder"]`。

**Q：重叠（overlap）有必要吗？**
答案恰好横跨两个 chunk 的边界时有用。150 字符是个保守值。更重要的是「不跨标题」这条规则，它保证了每个 chunk 主题单一。

---

### 5. 🛠 自己动手

1. 写一个按标题分块的函数，用一份含 shell 代码块的文档测它。
2. 手写 BM25，用三篇小文档验证：稀有词的文档排第一。
3. 给一个只有向量检索的系统加上 BM25 和 RRF，用带编号的查询对比前后。
4. 实现 `check_citations`，喂它一个编造引用的回答。
5. 在知识库里放一篇带注入语句的文档，确认它不会进入发给模型的上下文。
