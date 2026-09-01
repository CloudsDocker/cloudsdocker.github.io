### 1. 🎯 30秒版本

我今天打开一个项目的 `.gitignore`，1000 行。其中 938 行是同一件事：某个 `.venv` 目录里的文件被**逐个**列了出来。

```
src/jobs/xxx/.venv/bin/pip
src/jobs/xxx/.venv/bin/pip3
src/jobs/xxx/.venv/bin/pip3.11
src/jobs/xxx/.venv/lib/python3.11/site-packages/certifi/cacert.pem
... 再来 934 行
```

第一反应是「能不能写个正则一次性排掉」。**不能** —— `.gitignore` 里没有正则，从来没有。它用的是 glob。

但你也不需要正则。这 938 行的正确写法是一行：

```
.venv/
```

结果：1000 行 → 63 行，`git status` 和 `git ls-files` 前后**完全一致**（我做了 diff 对比），没有任何文件因此掉出忽略范围。

而且新写法还多管了一个之前**漏掉**的 venv —— 因为 glob 有条关键性质，我猜大多数人没意识到：

> 模式里**没有斜杠**（或只有结尾斜杠）时，它在**任意深度**匹配。

`.venv/` 不是「根目录下的 .venv」，是「**任何地方**的 .venv」，包括你明年才会建的那个。

---

### 2. ⚙️ 底层原理

本文所有结论都在 git 2.54.0 上实测过，命令和输出都贴了原样。

#### 2.1 为什么是 glob 不是正则

`man gitignore` 原话是：

> See fnmatch(3) and the FNM_PATHNAME flag for a more detailed description.

`FNM_PATHNAME` 这个 flag 是理解一切的钥匙，它的含义是：**通配符不跨越 `/`**。

实测：

```bash
$ printf 'src/*.py\n' > .gitignore
$ git check-ignore -v src/t.py src/sub/t.py
.gitignore:1:src/*.py   src/t.py
                        ← src/sub/t.py 没有输出，即未被忽略
```

`src/*.py` 匹配 `src/t.py`，但**不**匹配 `src/sub/t.py`。在正则里 `.*` 会毫不犹豫地吃掉那个斜杠，glob 的 `*` 不会。这是两套语言最根本的分歧点。

顺带把最容易混淆的几个符号对照一下：

| 写法 | 在 glob 里 | 如果你按正则理解 |
|---|---|---|
| `*` | 任意字符，但不含 `/` | ~~任意个前一字符~~ |
| `?` | 恰好一个字符（不含 `/`） | ~~前一项可选~~ |
| `.` | 就是一个普通的点 | ~~任意字符~~ |
| `**` | 跨目录层级（git 扩展，非标准 fnmatch） | 无此概念 |
| `!` | 取消忽略（只在行首） | ~~否定~~ |

`*.pyc` 之所以能用，纯属巧合 —— 它在两套语法里碰巧都能工作，这大概也是误解的源头。

#### 2.2 斜杠决定锚定：唯一需要背的规则

| 模式 | 锚定行为 | 实测 |
|---|---|---|
| `foo.txt` | 无斜杠 → **任意深度** | 同时匹配 `foo.txt` 和 `deep/foo.txt` |
| `a/b/` | 含斜杠 → **锚定到 .gitignore 所在目录** | 匹配 `a/b/f.txt`，不匹配 `x/a/b/f.txt` |
| `/foo.txt` | 前导斜杠 → **只在根** | 不匹配 `deep/foo.txt` |
| `foo/` | 结尾斜杠 → **只匹配目录** | 同名文件不受影响 |

实测第二行那个反直觉的点：

```bash
$ printf 'a/b/\n' > .gitignore
$ git check-ignore -v a/b/f.txt x/a/b/f.txt
.gitignore:1:a/b/   a/b/f.txt
                    ← x/a/b/f.txt 逃掉了
```

**中间只要出现一个斜杠，整条模式就被锚死了。** 这就是为什么 `src/jobs/xxx/.venv/bin/pip` 那种写法既啰嗦又脆弱 —— 目录一改名，938 行集体失效。

反过来，`.venv/` 里的斜杠在结尾，不触发锚定，所以它满仓库通吃。**斜杠在中间是锚，在结尾是「限定为目录」，两个作用完全不同。**

#### 2.3 优先级：最后匹配者胜

```bash
$ printf '*.log\n!keep.log\n' > .gitignore
$ git check-ignore -v logs/keep.log
.gitignore:2:!keep.log   logs/keep.log    ← 第2行赢，文件保留

$ printf '!keep.log\n*.log\n' > .gitignore     # 仅仅调换顺序
$ git check-ignore -v logs/keep.log
.gitignore:2:*.log       logs/keep.log    ← 第2行赢，文件被忽略
```

同样两条规则，顺序一换结论就反了。所以 `!` 的例外**必须写在被它推翻的那条规则之后**。

#### 2.4 那个会让人怀疑人生的陷阱

```bash
$ printf 'logs/\n!logs/keep.log\n' > .gitignore
$ git check-ignore -v logs/keep.log
.gitignore:1:logs/   logs/keep.log        ← 白写了，第1行仍然赢
```

按 2.3 的规则，第 2 行在后面，应该赢才对。但它没有。

原因是：**git 排除了一个目录之后，根本不会走进去。** 目录级别的排除是剪枝，不是逐文件判断 —— 里面的文件从未被枚举过，你的 `!` 自然没有生效对象。这已经不是优先级问题了，是它压根没参与比较。

解法是排除**目录内容**而不是目录本身：

```bash
$ printf 'logs/*\n!logs/keep.log\n' > .gitignore
$ git check-ignore -v logs/keep.log logs/drop.log
.gitignore:1:logs/*        logs/drop.log
                           ← keep.log 无输出，成功捞回
```

一个字符的差别（`logs/` → `logs/*`），行为完全不同：前者剪掉整棵子树，后者只排除孩子、目录本身仍然被遍历。

#### 2.5 那 938 行，其实从来就没生效过

这是整件事最讽刺的地方。改之前我先查了一下到底是哪条规则在起作用：

```bash
$ git check-ignore -v src/jobs/xxx/.venv/bin/pip
src/jobs/xxx/.venv/.gitignore:2:*    src/jobs/xxx/.venv/bin/pip
```

生效的不是根目录那 938 行里的任何一行，而是 **`.venv` 目录内部自带的一个 `.gitignore`**。

`uv`、`python -m venv` 这类工具在建虚拟环境时，会顺手在里面写一个只有 `*` 的 `.gitignore`。git 的规则查找是**从文件所在目录逐级向上**的，越深的 `.gitignore` 优先级越高。所以 venv 一建好就已经自我屏蔽了，根本不需要你在外面管。

那 938 行是纯噪音 —— 看起来像是某次 `git status --porcelain >> .gitignore` 的手滑产物。**它们不是「冗余的保险」，而是从第一天起就没被查询到过的死代码。**

#### 2.6 已跟踪的文件，`.gitignore` 完全管不着

```bash
$ git add tracked.log && git commit -m x     # 先跟踪
$ printf '*.log\n' > .gitignore              # 事后再加规则
$ echo v2 >> tracked.log
$ git status --porcelain tracked.log
 M tracked.log                               ← 照常显示
```

`.gitignore` 只对 **untracked** 文件起作用。文件一旦进了索引，再怎么写规则都拦不住它。要真正甩掉：

```bash
git rm --cached <file>     # 从索引移除，保留工作区文件
```

这里还有个诊断上的坑，实测：

```bash
$ git check-ignore -v tracked.log
$ echo $?
1                                            ← 什么都没输出

$ git check-ignore -v --no-index tracked.log
.gitignore:1:*.log   tracked.log             ← 加了 --no-index 才看得见
```

`check-ignore` **默认会跳过已跟踪文件**。所以当你「明明写了规则却不生效」跑去 check-ignore 排查、它却一言不发时 —— 那个沉默本身就是答案：**这文件已经被跟踪了，问题不在你的规则上。** 想验证规则本身写得对不对，加 `--no-index`。

---

### 3. 🔬 常见追问

**Q: 我就是想用正则，有没有什么开关？**

A: 没有。`.gitignore` 只认 glob，无配置项可改。不过 git 的其他地方是有正则的 —— `git log -G<regex>` 搜索改动内容、`git grep -E`、`git branch --list` 的部分场景。只是路径匹配这一块，从 `.gitignore` 到 `.gitattributes` 到 pathspec，统一都是 glob。

**Q: 那 `**` 什么时候是必须的？**

A: 比你以为的少得多。`**` 只在需要「锚定 + 跨层级」**同时**成立时才有意义，例如 `src/**/test/`（限定在 src 下，但 test 可以在任意深度）。

而 `**/foo` 和 `foo` 是等价的 —— 前者纯属多余，因为无斜杠模式本来就匹配任意深度。所以 `**/.env` 大可以直接写成 `.env`。

**Q: 我加了规则，文件还是出现在 git status 里。**

A: 按这个顺序查，基本一次命中：

1. 文件是不是已经被跟踪了？→ `git ls-files --error-unmatch <file>`，是的话用 `git rm --cached`（见 2.6）
2. 是不是被后面某条规则用 `!` 推翻了？→ `git check-ignore -v` 看到底哪行赢了（见 2.3）
3. 模式里是不是有中间斜杠、被意外锚定了？（见 2.2）
4. 是不是想在已排除的目录里捞文件？（见 2.4）

**Q: 怎么知道到底是哪条规则在起作用？**

A: `git check-ignore -v <path>` —— 输出格式是 `规则文件:行号:模式<TAB>路径`。它会明确告诉你**哪个文件的哪一行**赢了，这就是 2.5 里揪出「元凶其实是 venv 内部的 .gitignore」的方法。养成习惯：先 check-ignore，再动手改。

**Q: 938 行会拖慢 git 吗？**

A: 我没测，所以不编数字。直觉上 git 有 pattern 预编译和目录级剪枝，这个量级大概率无感。

但性能从来不是重点。**重点是那 1000 行里没有一行能被人读懂在干什么** —— 下一个来维护的人（很可能是三个月后的你自己）无从判断哪条重要、哪条能删，于是谁都不敢碰，只能继续往后追加。63 行的版本是可以一屏读完、可以推理、可以放心修改的。

---

**动手清单**：现在就 `wc -l .gitignore` 看一眼。超过 100 行的话，`grep -c '\.venv\|node_modules\|__pycache__' .gitignore` 大概率能解释掉大半。改之前先跑 `git status --porcelain > /tmp/before`，改完再 diff 一次 —— 这个对比只要 10 秒，能让你放心大胆地删。
