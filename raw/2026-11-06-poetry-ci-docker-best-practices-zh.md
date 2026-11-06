---
title: "Poetry 在 CI/Docker 里的最佳实践：从三连检查到生产级部署"
date: 2026-11-06
categories: [engineering, python, devops]
tags: [poetry, docker, ci-cd, github-actions, python-packaging, best-practices]
---

# Poetry 在 CI/Docker 里的最佳实践：从三连检查到生产级部署

最近在整理 CI 流水线时，重新梳理了一遍 Poetry 的使用姿势。从一条看似简单的 pre-commit 检查命令开始，一路深挖到 Docker 多阶段构建和 CI 缓存策略。记录如下。

---

## Part 1: 一条三连检查命令的拆解

```bash
git branch --show-current && poetry check --lock && git -c core.whitespace=cr-at-eol diff --check
```

用 `&&` 串起来三个检查，前一个成功才跑下一个，任何一步失败就停止。这是一个典型的 **pre-commit 前置卫生检查**。

### 逐段解释

**`git branch --show-current`** — 打印当前分支名，纯输出无副作用，常用于脚本里动态获取分支名。

**`poetry check --lock`** — 检查 `poetry.lock` 和 `pyproject.toml` 是否一致。如果你改了依赖但忘了 `poetry lock`，这步就会报错。防止"本地能跑，CI 炸了"的经典场景。

**`git -c core.whitespace=cr-at-eol diff --check`** — 检查 git diff 里有没有空白符错误（多余尾部空格、混用 tab 等），但允许 Windows 的 `\r\n` 换行。`-c core.whitespace=cr-at-eol` 是临时设置，跨平台项目的保命符；`diff --check` 只检查不改，发现问题返回非零退出码。

### `&&` 串联的意义

> 确认我在对的分支上 → 锁文件没漏 → 代码没有脏空白

全过才放行，典型的防呆设计。

---

## Part 2: Poetry 三兄弟 — check vs lock vs install

一句话总结：**check 是验货员，lock 是采购清单员，install 是搬货工。**

| | `poetry check` | `poetry lock` | `poetry install` |
|---|---|---|---|
| **做什么** | 只看不动手，检查配置 | 解析依赖，写锁文件 | 真正装包到虚拟环境 |
| **改文件吗** | ❌ 不改 | ✅ 写/更新 `poetry.lock` | ❌ 不改配置，但装东西到 `.venv` |
| **联网吗** | ❌ 纯本地 | ✅ 要查 PyPI | ✅ 要下载包 |
| **速度** | 毫秒级 | 可能很慢 | 取决于包数量 |
| **CI 用途** | 门禁检查 | 一般不在 CI 跑 | 装环境 |

### `poetry check`

检查 `pyproject.toml` 格式，加 `--lock` 验证锁文件同步性。不装东西，不联网，纯静态检查。

### `poetry lock`

根据 `pyproject.toml` 约束，解析所有依赖（包括传递依赖）的精确版本，写入 `poetry.lock`。

- `poetry lock` → 重新解析，可能升级版本
- `poetry lock --no-update` → 只补缺的，已有的不动（更安全）

### `poetry install`

读 `poetry.lock`，把包装到虚拟环境。

- `poetry install` → 装所有依赖 + 项目本身
- `poetry install --no-root` → 只装依赖，不装项目（CI 常用）
- `poetry install --sync` → 严格同步，多余的包也删掉（CI 推荐）

### 经典工作流

```
改了 pyproject.toml
    ↓
poetry lock          # 重算锁文件
    ↓
poetry install       # 装到本地环境
    ↓
git add pyproject.toml poetry.lock   # 两个一起提交！
    ↓
CI: poetry check --lock → poetry install --sync
```

**黄金法则：`pyproject.toml` 和 `poetry.lock` 永远一起提交，像情侣一样，分开就出事。**

---

## Part 3: `poetry install --sync` 在 CI/Docker 里的最佳实践

### 为什么必须用 `--sync`？

不加 `--sync` 的翻车场景：

```
上次装了 pandas 2.0
→ 从 pyproject.toml 删了 pandas
→ poetry install
→ pandas 还在环境里！代码照跑！
→ 推到生产 → 💥
```

`--sync` 是洁癖模式：**环境严格等于锁文件，多的删，少的补。**

### Docker 最佳实践

```dockerfile
FROM python:3.12-slim

# 1. 装 poetry，容器里不需要虚拟环境
ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

# 2. 先只复制依赖文件 → 利用 Docker 层缓存
COPY pyproject.toml poetry.lock ./

# 3. 只装依赖，不装项目本身
RUN poetry install --sync --no-root --only=main \
    && rm -rf $POETRY_CACHE_DIR

# 4. 再复制代码（代码变了不用重装依赖）
COPY . .

# 5. 装项目本身
RUN poetry install --only-root
```

**关键技巧：**

- `VIRTUALENVS_CREATE=false` — 容器本身就是隔离层，不需要嵌套虚拟环境
- 先 COPY 锁文件，再 COPY 代码 — Docker 层缓存大杀器，依赖没变就不重装
- `--no-root` — 先不装项目本身，等代码进来再说
- `--only=main` — 不装 dev 依赖（pytest、black 生产不需要）
- 清理缓存 — 镜像瘦身

### GitHub Actions 最佳实践

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Cache poetry
        uses: actions/cache@v4
        with:
          path: |
            ~/.local
            .venv
          key: poetry-${{ hashFiles('poetry.lock') }}
      
      - name: Install poetry
        run: pipx install poetry
      
      - name: Install deps
        run: |
          poetry config virtualenvs.in-project true
          poetry check --lock
          poetry install --sync
      
      - name: Test
        run: poetry run pytest
```

**CI 关键点：**

- `virtualenvs.in-project true` — `.venv` 在项目里，方便被 actions/cache 缓存
- `hashFiles('poetry.lock')` 做缓存 key — 锁文件变了才重装
- `check --lock` 在 `install` 前 — 先验货再搬货，锁文件没同步直接失败

### 常见翻车总结

| 坑 | 症状 | 解法 |
|---|---|---|
| 忘了 `--sync` | 删掉的包还在，幽灵依赖 | 永远加 `--sync` |
| Docker 里开了虚拟环境 | 镜像多 100MB+，路径混乱 | `VIRTUALENVS_CREATE=false` |
| COPY . . 在装依赖前 | 改一行代码就重装所有依赖 | 锁文件先 COPY |
| CI 没缓存 | 每次 3 分钟装依赖 | cache on `poetry.lock` hash |

---

## 总结口诀

> Docker 关虚拟环境，CI 开 in-project；锁文件先进场，代码后进场；`--sync` 永远带上，幽灵依赖见光死。
