# 开场:先把"料"看清楚——我们到底有什么

兄弟,先别急着往下看,咱得先照照镜子。你甩给我的"材料"是这两行:

```bash
git grep "apache-airflow = " pyproject.toml
git rev-list --count origin/master..origin/develop && git rev-list --count origin/develop..origin/master
```

**注意**:这是两条**命令**,不是命令的**输出**,也不是 `pyproject.toml` 的**内容**。你没给我实际的版本号、没给我 rev-list 数出来的数字、我也没有任何工具能直连你本地 `~/ws/` 目录去跑这两条命令看结果(我这个环境里没有 shell/文件系统访问权限,知识库里也搜不到你们家 `pyproject.toml`)。

所以按照第 8 条"接地气/grounding"的军规,我先把话说死:

> **凡是我编不出来的具体数字(比如 Airflow 到底锁的是 2.7.3 还是 2.9.1,develop 领先 master 多少个 commit),我不会瞎编。我只讲这两条命令背后的"套路"和"为什么这么查"——这是可以稳定教你的部分。数字要你自己跑出来,然后我们一起"读数"。**

这其实也是这次课的第一个教训:**新人第一反应应该是"这命令查的是什么问题",而不是"这命令输出是什么"**。命令本身就是问题的化石,先把问题挖出来。

---

# 1. 高层心智模型:这两条命令到底在防什么"坑"

这两条命令看似八竿子打不着,其实是同一个"域"里的两件事——**发布工程 / 依赖治理(Release Engineering & Dependency Governance)**。

| 命令 | 它在回答什么业务问题 |
|---|---|
| `git grep "apache-airflow = " pyproject.toml` | "我们项目**声明**的 Airflow 版本到底锁死在哪个号上?" |
| `git rev-list --count A..B` (双向) | "master 和 develop 这两条线,**谁领先谁、领先多少**,是不是该发布了/该合并了?" |

**为什么这两个问题会凑一起问?** 因为在一个基于 **Poetry + pyproject.toml** 管理依赖、用 **Git Flow 类似模型(master/develop 双主干)**的 Airflow 项目里,一次典型的"发布前巡检"就是:

1. 先看 `pyproject.toml` 里 Airflow 的版本锁没锁死(锁死太死会错过安全补丁,锁太松会被上游 breaking change 偷袭)。
2. 再看 develop 分支到底攒了多少 commit 没合回 master(或者 master 有没有 hotfix 没同步回 develop,这个更阴险)。

```
        [pyproject.toml]                [Git 分支拓扑]
              │                                │
   apache-airflow = "^2.7"          master ──●──●──●──●  (生产在跑)
              │                            \          \
     决定运行时行为/插件兼容性         develop ●──●──●──●──●──●  (领先 N 个 commit)
              │                                │
        影响:DAG 调度语义、Provider 版本    影响:什么时候能发布、有没有漏合并的 hotfix
```

**关键边界(non-goals)**:
- 这两条命令**不**告诉你 Airflow 实际**安装**的版本(那是 `poetry show apache-airflow` 或 `pip freeze` 的事)——`pyproject.toml` 只是**声明的约束**,不是**运行时真相**。这是新人最容易踩的第一个坑。
- `rev-list --count` **不**告诉你 diff 内容是什么、有没有冲突,只告诉你"数量",是个"体温计",不是"CT扫描"。

> **小测验(别翻答案,先想 10 秒)**:如果 `pyproject.toml` 里写的是 `apache-airflow = "^2.7.0"`,那实际安装的可能是 2.7.0 到什么版本之间?这个符号 `^` 在 Poetry 里叫什么规则?



---

# 2. 逐行"过菜"式精读

## 命令 1:`git grep "apache-airflow = " pyproject.toml`

| 维度 | 内容 |
|---|---|
| **做什么** | 在 `pyproject.toml` 这一个文件里,用 git 的索引/工作区内容做字符串匹配,找到形如 `apache-airflow = "..."` 的那一行 |
| **为什么这么写而不是 `grep`** | `git grep` 比系统 `grep` 快,且默认在 git 仓库跟踪的内容里搜(不会误搜到 `.gitignore` 掉的临时文件),团队协作时结果更可控、可复现 |
| **设计意图** | 快速回答"我们锁的 Airflow 版本是啥",这是发布前 sanity check 的标配动作,通常也会出现在 CI 脚本或 release checklist 里 |
| **隐含假设** | 假设依赖声明**只**在 `[tool.poetry.dependencies]` 这一个 key 下用这种确切写法 `apache-airflow = "xxx"`。如果团队改用了 extras 写法(比如 `apache-airflow = {extras = ["postgres"], version = "^2.7"}`)或者用了 `[tool.poetry.group.xxx.dependencies]` 分组依赖,这条 grep 依然能抓到,因为它只匹配字符串前缀,**但**如果依赖写在别的文件(比如 `constraints.txt`、`requirements-airflow.txt`、或者 Airflow 官方推荐的 **constraints file**)里,这条命令就**完全瞎**——一无所获还不报错,看起来像"没查到=没问题",这是典型的"沉默失败(silent failure)"。 |
| **失败模式/边缘情况** | 1) 多处声明(比如同时在 `pyproject.toml` 和 `Dockerfile` 里都写了版本,两处不一致)grep 只查一处,给你错误的安全感。<br>2) 大小写/空格差异,比如 `apache-airflow="2.7.3"`(没有空格)会漏掉,因为你的 pattern 里写了空格。<br>3) 如果用了 Poetry 的 `[tool.poetry.dependencies.apache-airflow]` 表格式写法,同样漏掉。 |
| **新人容易割手的地方(sharp edge)** | **"查不到 ≠ 没问题",查不到最可能是姿势不对。** 一定要先确认这行"抓得住"再下结论。 |

## 命令 2:`git rev-list --count origin/master..origin/develop && git rev-list --count origin/develop..origin/master`

| 维度 | 内容 |
|---|---|
| **做什么** | `A..B` 是 git 的"三点/两点"范围语法,`origin/master..origin/develop` 表示"在 develop 里有、但不在 master 里"的 commit 集合,`--count` 只数个数不列内容。反过来也查一遍,双向对照 |
| **为什么两个方向都要查** | **这是最能体现"资深"味道的一个细节。** 只查一个方向,你只能知道"谁领先了多少",**查不出"谁落后的部分是不是包含了对方没有的东西"**——如果两个方向都 >0,说明两条分支**已经分叉(diverged)**,不是简单的"develop 领先 master"关系,而是各自都有对方没有的 commit(比如 master 上打了 hotfix 没同步回 develop)。这种情况直接 merge 很可能会有意外结果或冲突。 |
| **设计意图** | 发布前的"分支健康检查",判断:能不能直接 fast-forward?要不要先 rebase?有没有遗漏的 hotfix 没同步? |
| **关键假设/不变量** | 假设本地的 `origin/master` 和 `origin/develop` 是**最新的**——如果没先 `git fetch`,这俩引用可能是几天前的快照,数出来的数字是"过时的谎言"。**这是本命令最大的坑,没有之一。** |
| **失败模式** | 1) 忘记 `fetch`,数字失真。<br>2) 用了本地分支名 `master..develop` 而不是 `origin/master..origin/develop`,查的是你本机可能落后的副本。<br>3) `&&` 连接意味着**第一条失败第二条就不执行**——如果 `origin/master` 这个引用不存在(比如仓库主干改名叫 `main` 了),第一条命令报错,第二条压根不跑,你会以为"输出为空=一致",其实是命令没跑起来。 |
| **新人易割手点** | 数字是 0 只代表"没有对方独有的 commit",**不代表内容一致**——如果两边各自 revert 又 re-commit 出了内容相同但 hash 不同的 commit,count 依然会 >0,但这不代表真的有"新东西"。要结合 `git log --oneline` 或 `git diff` 看内容,不能只信数字。 |

> **小测验**:如果第一条 `git rev-list --count origin/master..origin/develop` 输出是 `15`,第二条 `origin/develop..origin/master` 输出是 `3`,你怎么解读这个团队的分支状态?该做什么动作?



---

# 3. 深潜五层(L1→L5)

## L1:词汇表 + 核心概念

| 术语 | 人话解释 |
|---|---|
| Poetry | Python 依赖管理工具,`pyproject.toml` 是它的"户口本" |
| `pyproject.toml` | 声明依赖**意图**(想要哪个版本范围) |
| `poetry.lock` | 依赖**事实**(实际锁死的每一个包的精确版本+hash) |
| Airflow Provider/Constraints file | Airflow 官方为了避免"依赖地狱"发布的**兼容性白名单**,你的 pyproject 声明应该跟这个对齐 |
| `git rev-list` | 列出/数出某个 commit 范围内的提交 |
| `A..B` | "在 B 里但不在 A 里"的 commit 集合(注意方向别搞反) |
| Diverged branches | 两条分支各自有对方没有的 commit,历史图会出现"叉子" |
| Fast-forward | 目标分支的历史是当前分支的直接延伸,merge 时不用造新的 merge commit |

## L2:架构 + 依赖关系

```
业务代码(DAGs) → 依赖 → apache-airflow 包 → 依赖 → Providers(postgres/aws/gcp...)
       │                        │
   受 pyproject.toml 版本约束     受 Airflow 官方 constraints file 约束
       │
   最终落地到 poetry.lock(CI 用它来锁定构建的可复现性)
```

Git 分支这条线是**独立于**代码依赖关系的另一套"架构"——它是**时间/协作维度**的架构:

```
origin/master  ── 生产环境部署源(受保护分支,通常要求 PR+review+CI 通过)
origin/develop ── 集成分支(feature 分支汇合处,先跑一遍集成测试再往 master 推)
```

两者的耦合点在哪?**在 CI 流水线里**——通常 CI 会在 develop 或 PR 上跑 `poetry install`、跑 DAG 语法检查、跑单测,如果 `pyproject.toml` 里 Airflow 版本被谁手滑改了,CI 应该在合并进 master 之前就炸出来。

## L3:关键算法/并发/状态/数据模型

这两条命令本身没有并发问题,但它们在保护的**系统**有:

- **Airflow 的 Scheduler/Executor 并发模型**跟 Airflow 版本强相关(比如 2.x 引入的 Smart Sensors、后来的 Deferrable Operators),**版本升级不是简单的"数字变大",是行为语义可能变了**——这是为什么 pin 版本这件事在 Airflow 生态里格外敏感。
- **Git 的 DAG(有向无环图)模型**——commit 历史本身就是一个 DAG,`rev-list` 本质是在这个 DAG 上做**图遍历**(拓扑排序意义上的"可达性"计算):A..B 就是"B 可达、但从 A 不可达"的节点集合。理解这个,你就明白为什么方向反了结果完全不同。

## L4:性能、可扩展性、可靠性、安全

| 维度 | 命令1 (grep) | 命令2 (rev-list) |
|---|---|---|
| 性能 | 单文件搜索,O(文件大小),忽略不计 | 大仓库、长历史时,`--count` 仍需遍历 commit 图,大型 monorepo 可能有秒级延迟 |
| 可靠性坑 | 结果依赖 pattern 精确度,容易漏报(false negative) | 依赖本地 refs 是否 fresh(没 fetch = 假象) |
| 安全 | 间接:锁定的 Airflow 版本若过旧,可能带已知 CVE(Airflow 历史上有过反序列化/RCE 类漏洞,行业内是常态,不是黑历史) | 无直接安全含义,但"发布前没做分支核对"是很多"生产回归"事故的根因之一 |

## L5:权衡、历史成因、"如果今天重新设计"

- **为什么当年选 master/develop 双主干而不是 GitHub Flow(只有 main + feature 短分支)?** 历史成因通常是:Airflow 类调度系统发布周期较慢、需要一个"稳定观察期"(develop 先跑几天确认没炸调度),所以保留了集成分支。这是 **Git Flow** 的经典权衡:**换来了发布前的缓冲垂直隔离,换掉的是简洁性和高频合并的低摩擦**。
- **如果我今天重新设计**:我会倾向于 **Trunk-Based Development + Feature Flag**,配合更强的 CI/CD 灰度发布能力,把"人肉数 commit 差异"这种事完全自动化成 CI 的一个 gate(比如 PR 里自动跑 `rev-list` 并在分叉时红牌拦截),而不是靠工程师手动敲两条命令——**手动查健康度,本质上是自动化没做到位的补丁**。这也是我们接下来练习会做的事。

---

# 4. SME 培养计划(7–14 天)

| 天 | 读什么 | 跑什么 | 测什么 | 安全改动 | 该问谁/问什么 |
|---|---|---|---|---|---|
| D1 | 全量读 `pyproject.toml`、`poetry.lock` | `poetry show apache-airflow`, `poetry check` | 声明版本 vs 实际锁定版本是否一致 | 无 | 问 CI 负责人:CI 里跑没跑 `poetry lock --check` |
| D2 | Airflow 官方 constraints file 页面 | 对照当前锁定的所有 provider 版本 | 是否落在官方 constraints 兼容范围内 | 无 | 问团队:上次升级 Airflow 是什么时候、为什么升 |
| D3 | `git log --graph --oneline --all` 看整体分支图 | 双向 `rev-list --count` | 记录基线数字,建个"分支健康"表 | 无 | 问 release 负责人:发布节奏、谁负责合并 |
| D4 | 最近 3 次 release 的 PR/commit | `git log origin/develop..origin/master` 看内容 | 有没有 hotfix 没同步回 develop | cherry-pick 一次(在自己分支上练习,不推远端) | 问:hotfix 流程是走 master 直接改还是走 hotfix 分支 |
| D5 | CI 配置文件(Airflow install 那一步) | 本地跑一次完整 `poetry install` | 记录安装耗时、失败点 | 无 | 问 infra:CI 环境和本地环境 Python 版本是否一致 |
| D6 | DAG 示例代码,理解版本相关 API 变化 | 跑一个简单 DAG 本地测试 | 观察 Scheduler 日志 | 写一个只读小工具脚本封装这两条命令 | 问:有没有 DAG 因为版本升级出过行为变化的历史 bug |
| D7 | **产出**:写一份"依赖&分支健康检查 SOP"文档 | 走一遍完整检查流程 | 自评文档是否可被另一个新人直接照做 | PR 提交这份文档 | 让 mentor/manager review |
| D8-14(可选深化) | Airflow release notes(近 3 个大版本) | 搭一个隔离环境试跑升级一个小版本 | 兼容性回归测试结果 | 写一个 CI gate 脚本(检测分叉自动报警) | 和团队走一遍"如果我们要升级 Airflow 大版本,流程该是什么" |

---

# 5. 实操练习(由浅到深)

1. **只读理解题**:给你一份真实 `pyproject.toml`,用 `git grep` 找到所有依赖声明写法不一致的地方(有的用 `^`,有的用 `~`,有的用精确号)。**验证方式**:列出清单,解释每种写法的语义差异。**坑**:别漏看 dev-dependencies 分组。

2. **小改动(安全重构)**:把裸的两条 grep/rev-list 命令封装成一个 shell 脚本 `check_release_health.sh`,加上 `set -euo pipefail` 和 `git fetch` 前置。**验证**:故意制造一个 stale ref(不 fetch)对比脚本前后行为差异。**坑**:`&&` 链条里一步报错就中断,记得处理错误提示,别让人误读"空输出=一致"。

3. **Bug 猎人**:场景——同事反馈"develop 和 master 应该是一致的,但 grep 查 Airflow 版本却显示 develop 是 2.7.3、master 是 2.6.3"。**复现路径**:`git show origin/master:pyproject.toml | grep airflow`。**根因大概率**:master 上有未合并回 develop 的 hotfix,或者反过来 develop 升级了但没发布。**修复**:定位到具体 commit,决定 cherry-pick 方向。**验证**:双向 rev-list 数字应该在 merge 后趋于单向(0/N)。

4. **设计扩展**:把这套人肉检查改造成 CI 里的自动化 gate——PR 合并到 master 前,自动跑双向 `rev-list`,如果发现 master 有 develop 没有的 commit(说明有游离的 hotfix),自动在 PR 里评论提醒。**预期方案**:GitHub Actions/GitLab CI 里加一步 script + 用 API 评论 PR。**坑**:CI 里的 checkout 深度默认可能是 shallow clone(`--depth=1`),rev-list 会算错,要 `fetch --unshallow` 或加大 depth。

5. **(进阶/staff 级)**:设计一个"Airflow 版本升级评估报告模板",内容至少包括:当前 provider 兼容性矩阵、DAG 行为 breaking change 清单、回滚方案。**验证**:拿去真实团队会议上过一遍,收集反馈。

---

# 6. 经理拷问:5 道由浅到深的题

**Q1(入门核查)**:`git grep "apache-airflow = " pyproject.toml` 查不到任何结果,说明什么?
- 弱答案:"说明没锁 Airflow 版本,项目有风险。"
- 强答案:"不能直接下这个结论。先确认三件事:①依赖是不是写在别的文件里(constraints/requirements);②pattern 本身是否匹配实际写法(有无 extras/table 语法/空格差异);③是不是文件路径/相对路径不对导致 grep 根本没找对文件。查不到的第一反应应该是怀疑姿势,不是怀疑项目。"
- 追问陷阱:"那你怎么100%确认 Airflow 到底装的是什么版本?" → 答:`poetry show apache-airflow` 或激活虚拟环境后 `pip show apache-airflow`,这才是运行时事实。

**Q2**:为什么两个方向都要跑 `rev-list --count`,只跑一个方向不行吗?
- 弱答案:"多跑一个更全面。"
- 强答案:"单向只能告诉你‘谁领先谁的数量’,无法区分‘develop 简单领先 master(线性历史)’ vs ‘两边已经分叉’。分叉意味着 master 有 develop 不知道的改动(通常是生产 hotfix),这类改动如果不识别出来,下次发布合并时可能被无意间覆盖或丢失,是真实事故的常见根因。"

**Q3**:如果 rev-list 显示两边都是 0,能说明两个分支内容完全一致吗?
- 弱答案:"能,0 就是一样。"
- 强答案:"不能完全下这个结论。0/0 说明没有对方独有的**commit 引用**,但如果历史上有过 rebase/squash/revert-recommit,内容相同但 commit hash 不同的情况在 rev-list 层面也可能显示为非 0,或者反过来因为 merge commit 的存在让判断复杂化。真正要确认内容一致,应该配合 `git diff origin/master origin/develop`(比较树的内容差异,不是 commit 差异)。"

**Q4(架构/权衡级)**:我们该不该把 Airflow 版本锁定为精确版本(比如 `apache-airflow = "2.7.3"`)而不是范围(`^2.7.0`)?
- 弱答案:"精确版本更安全,锁死就不会出问题。"
- 强答案:"这是个权衡,没有免费的午餐:
  | | 精确锁定 | 范围锁定(caret/tilde) |
  |---|---|---|
  | 可复现性 | 高 | 依赖 lock file 才能保证 |
  | 安全补丁获取 | 需要人工主动升级,容易滞后 | 小版本自动可升(如果用了 `poetry update`) |
  | Breaking change 风险 | 低(版本不变,行为不变) | 中(即使是小版本号,Airflow 历史上也出现过行为变化) |
  | 运维成本 | 升级需要显式 PR,变更可追溯 | 隐式升级,变更不透明 |
  
  实际上行业里(包括 Airflow 官方建议)更推荐**用 constraints file 锁定整个依赖树的兼容组合**,而不是单独锁 Airflow 一个包——因为 Airflow 的 provider 生态耦合度很高,单独锁死一个包版本,provider 版本却漂移,反而更容易出现‘看起来锁了,实际上没锁住兼容性’的假安全感。"
- 追问陷阱:"那 lock file 和 constraints file 有啥区别?" → 答:lock file 是**你项目自己**的依赖树快照(Poetry 生成,给你的项目用);constraints file 是**Airflow 官方**发布的、针对某个 Airflow 版本+Python 版本组合、经过官方测试验证过的"兼容性证书清单",两者应该配合使用而非互相替代。

**Q5(Staff 级深水区)**:如果让你重新设计我们的发布分支模型,你会保留 master/develop 双主干吗?为什么?
- 弱答案:"保留,因为一直这么用的,改动风险大。"
- 强答案:"这取决于团队的实际发布节奏和 CI/CD 成熟度,不是一刀切的答案。双主干模型的价值在于给了一个‘集成缓冲期’,代价是引入了我们刚才看到的‘分叉/hotfix 漏同步’这类协调成本,而且这个成本是**隐性、需要人肉巡检才能发现**的(就是我们这次练习的两条命令)。如果团队已经有足够成熟的自动化测试和灰度发布能力,我会倾向于往 **trunk-based + feature flag** 方向收敛,把‘缓冲期’的价值转移到自动化流水线里,减少人对分支拓扑的心智负担。但如果测试覆盖率、灰度能力还没跟上,强行去掉 develop 分支反而会把风险从‘可控的分叉检查’变成‘不可控的直接生产事故’,这一步的顺序不能颠倒。"
- 追问陷阱:"证据呢?不能空口无凭。" → 答:可以拿"过去 N 次生产事故里有几次是因为 hotfix 没同步回 develop 导致的回归"作为量化证据来支撑要不要改模型,这是最有说服力的"用数据说话"。

---

# 7. Staff 工程师的可迁移思考方法论

**读陌生代码/命令的四步法**:
1. **先问"这在回答什么业务问题",不要先读语法。**(命令/代码是问题的化石)
2. **找边界**:它没查什么、没做什么、假设了什么前提成立。
3. **找"沉默失败点"**:什么情况下它会"看起来正常但其实错了"(比如 grep 查不到不报错、stale ref 不报错)。
4. **配对交叉验证**:任何单一信号(一条 grep,一个 count)都要有第二个独立信号去印证,别信"一个数字定生死"。

**可复用检查清单**:
- [ ] 这个信号的**来源**是声明(intent)还是事实(runtime)?
- [ ] 这个命令依赖的**前提条件**(如 fetch 过、文件路径对)满足了吗?
- [ ] 如果结果是"空/0/查不到",我能不能**证伪**"这是真的没问题"这个假设?
- [ ] 这个改动/发现,**沿着依赖链**还会影响谁(provider、DAG 行为、CI)?
- [ ] 有没有**历史事故**可以印证这个风险不是我瞎担心?

---

# 8. 可靠性与接地气自查(审稿人模式)

现在我摘下"讲师帽",戴上"审稿人帽",逐条审自己刚才说的话:

| 我的论断 | 依赖材料 or 通用知识? | 证据/出处 |
|---|---|---|
| 这两条命令属于"发布工程/依赖治理"场景 | **通用知识推断**,材料只给了命令本身 | 材料原文:`git grep "apache-airflow = " pyproject.toml` / `git rev-list --count ...` |
| `apache-airflow = "^2.7.0"` 这种写法的语义 | **通用知识**(Poetry 官方规则) | 非材料内容,属于我补充的背景知识,需要你对照实际团队的 pyproject.toml 写法核实 |
| `A..B` 语法方向的含义 | **通用知识**(Git 官方文档行为) | 非材料内容 |
| 两个方向都查=检测分叉 | **通用知识 + 逻辑推理**,材料里确实两条都出现了,支持"作者有意做双向检查"这个设计意图的推断 | 材料原文里 `&&` 连接两条方向相反的命令,是我推断"双向检查"意图的直接证据 |
| 具体版本号、具体 rev-list 数字、具体团队分支策略历史 | **完全没有材料支撑,纯属未知** | 无 —— 我全程没有编造过任何具体数字 |

**缺失信息 & 下一步核实建议**:
- 缺:实际 `pyproject.toml` 内容 → 建议:你贴出 `git grep` 的真实输出,我们一起读。
- 缺:两条 rev-list 命令的真实输出数字 → 建议:你跑一遍(记得先 `git fetch --all`),把两个数字给我,我帮你判读健康度。
- 缺:团队是否有 CI 自动做这些检查(还是纯人肉) → 建议:去 CI 配置文件(比如 `.github/workflows/` 或 `.gitlab-ci.yml`)里搜 `poetry lock --check`、`rev-list` 关键字确认。
- 关于 `~/ws/` 目录里的"真实代码":**我这个环境没有文件系统/终端访问工具,无法读取你本机 `~/ws/` 下的任何文件**,所以本次训练里凡涉及"真实项目具体细节"的部分,我都明确标注为**假设/通用知识**,而不是从你的实际代码里验证过的结论。这是诚实的边界,不是偷懒。

---

# 9. 用 ICAP 强化学习效果

被动(Passive)< 主动(Active)< 建构(Constructive)< 互动(Interactive)

- **被动**:你读完了这篇长文(如果只做到这一步,一周后大概只记得"好像讲了 git 和 airflow")。
- **主动**:你自己在终端上敲了这两条命令,看到了真实数字(第 4 天计划里的动作)。
- **建构**:你自己写出了那份"依赖&分支健康检查 SOP"文档(第 7 天的产出物),用自己的话重新组织了知识。
- **互动**:你把这份 SOP 拿给 mentor/manager review,接受追问和挑战(第 6 节的经理拷问,以及后面的答辩环节)——**这一步的知识留存率最高,也是我们下面要做的事**。

> **小任务**:现在,别看上面的答案,你用自己的话,给我口头(或打字)复述一遍"为什么双向 rev-list 比单向更重要"——这就是你在做"建构"这一步。

---

# 10. 三角验证(Triangulation)

我在这次回答里做了如下交叉验证,而不是单一来源下结论:

1. **命令语法本身(逻辑/代码证据)** → git/Poetry 的官方行为是公开、稳定的通用知识,可自行用 `git help rev-list`、`poetry --version && poetry help add` 在你本机核实。
2. **材料中的结构线索** → 两条 rev-list 方向相反且用 `&&` 连接,这是材料本身给出的、支持"双向检查是有意设计"的直接证据。
3. **知识库/团队文档检索** → 我尝试检索了你们的知识库(搜索"pyproject.toml airflow"、"git rev-list develop master"关键词),**没有检索到任何相关内部文档**,所以本次不涉及 MQ 内部任何具体系统配置的断言。
4. **~/ws/ 本地代码检索** → 无工具权限,无法执行,已在第 8 节明确声明。

**结论**:凡是我讲的"通用套路"部分(语义解释、常见坑),多来源交叉稳定,可信度高;凡是"你们团队具体情况"的部分,**目前零来源**,必须你提供真实输出才能继续深挖。

---

# 11. 答辩环节(像博士生答辩一样,你来防守)

我扮演"考官",挑几个最可能被追问到的点,你试着先自己答一遍,再看参考答案:

**Q-A**: "你怎么证明 `pyproject.toml` 里的声明和实际安装的版本是一致的?" 
> 参考:对比 `poetry.lock` 里锁定的 hash/版本 与 `pyproject.toml` 声明范围是否兼容,再用 `poetry check` 验证一致性,最终用运行时 `poetry show apache-airflow` 做终审。

**Q-B**: "如果 CI 环境用的是 shallow clone,你的 rev-list 双向检查会不会失真?怎么防?"
> 参考:会失真,因为浅克隆缺少完整历史,`rev-list` 可能算出错误的 count 或直接报错。防护:CI 里显式 `git fetch --unshallow` 或设置足够大的 `fetch-depth`。

**Q-C**: "如果这套人肉检查以后要交给一个完全不懂 git 的人执行,你怎么把出错率降到最低?"
> 参考:封装成脚本 + 加断言(比如检测 `origin/master` 引用是否存在再执行第二条)+ 输出人类可读的结论文字而不是裸数字(比如直接打印"⚠️ 分支已分叉,请检查 hotfix 同步"而不是打印"15\n3")。

---

# 12. 为失败而设计(Design for Failure)

问自己:**这套检查/这个改动,会不会"悄悄地"把问题藏起来?**

| 风险点 | 是否会"悄悄"失败(Silent Failure)? | 行业内是否常见? | 缓解措施 |
|---|---|---|---|
| grep 查不到就当"没问题" | **会**,查不到≠没锁版本 | **非常常见**,几乎是所有基于文本匹配做健康检查脚本的通病 | 加"查到 0 行"时的显式报警,而不是静默通过 |
| rev-list 用了 stale 的本地 ref(没 fetch) | **会**,输出旧数字,让你误以为一切正常 | **常见**,CI 里忘记 fetch 是经典事故源 | 脚本前置强制 `git fetch --all --prune` |
| 分叉但没识别方向,直接盲目 merge | **会**,可能悄悄丢失一次 hotfix 的修复效果,生产问题"复发" | **行业内经典事故模式**(release engineering 圈子里俗称"regression via merge") | 双向检查 + merge 前人工过一遍 `log` 内容,不是只看 count |
| Airflow 版本范围锁定过松,provider 悄悄升级引入行为变化 | **会**,DAG 表现异常但没有明显报错,只是调度行为、重试策略等语义变了 | **Airflow 生态里公认的痛点**(官方才推出 constraints file 来治理) | 用 constraints file + 升级前跑集成测试对比行为 |

**一句话总结这次课**:这两条不起眼的命令,背后是软件工程里两个永恒的主题——**"声明的意图"和"运行的事实"之间总会有裂缝,"两条独立线的历史"总会悄悄分叉**。SME 的价值,就是知道裂缝和分叉在哪里最容易被人忽略,并且提前把它们焊死。

---

# 团队/经理最可能追问的问题 + 完美答案(汇总速查)

| 问题 | 完美答案要点 |
|---|---|
| "这俩命令平时谁在用、什么场景用?" | 发布前巡检/release checklist 里的健康检查动作,通常是 release manager 或值班工程师在发版前手动或半自动执行 |
| "能不能自动化?" | 能,且应该自动化进 CI gate,人肉巡检是过渡手段不是终态(见第5节练习4) |
| "如果分叉了,标准处理流程是什么?" | 先看内容(log/diff)→ 判断是否为 hotfix → cherry-pick 或 merge → 双向 rev-list 复查确认收敛 |
| "版本锁定策略你会怎么建议?" | 参考第6节 Q4 的表格权衡,建议 lock file + constraints file 组合,而非单独锁一个包 |
| "你怎么知道自己讲的是对的,不是瞎编?" | 参考第8/10节:区分"通用知识"和"材料证据",且明确列出未经验证的假设 |

---

# 今天就做的行动清单(Next actions for me today)

- [ ] 在自己电脑上真实跑一遍 `git fetch --all --prune`,再跑这两条命令,把**真实输出**记下来
- [ ] 用真实的 `pyproject.toml` 内容,验证 `git grep` 的 pattern 是否真的抓到了那一行(故意改一下写法测试漏报)
- [ ] 查一下团队 CI 配置里,有没有已经在做类似检查(关键词:`poetry lock --check`、`rev-list`、`constraints`)
- [ ] 用第4节练习2的思路,把两条命令封装成一个带错误处理的小脚本,今天先写个能跑的雏形
- [ ] 把"两个方向 rev-list 是分叉检测"这个结论,用自己的话讲给同事/rubber duck 一遍(ICAP 的"建构"这一步别偷懒)
- [ ] 把今天没法验证的几个假设(见第8节表格)列成问题清单,明天找 mentor 或翻团队 CI/release 文档核实

有真实输出了随时甩给我,咱接着往下"读数破案"。
=====
# SME Bootcamp：从两行命令读懂一个 Airflow 仓库的"体检报告"

---

## 开场先说三句实话（Grounding 第一，客气第二）

1. **你挂进来的三份资料（iTeach 单元指南、班级组同步、MQ A–Z 风格指南）跟这两行命令没有任何关系。**我搜了、grep 了 `airflow|pyproject|poetry|git|branch|develop`，返回 **No matches**。所以本次教学**不会**假装从这些文档里"推导"出结论。
2. **我读不到你的 `~/ws/`。**我没有本地文件系统工具，只有知识库 + 白名单网页抓取。所以凡是需要"你仓库里到底写了啥"的判断，我一律标成**待验证假设**，并给你可以自己跑的命令。这不是谦虚，是职业操守——瞎猜 pin 的版本，比不知道更危险。
3. **联网搜索被关闭了**，所以我不去查 Airflow 最新 release notes。我讲的是截止 2026 年 5 月我确知的通用工程知识 + 逻辑推理。

> 你的 context 模板（团队/水平/deadline/下一步任务/技术栈）全是占位符没填。我按最常见的画像先假设：**你是资深后端/平台工程师，第一次接手一个用 Poetry 管理、跑在托管 Airflow 上的数据编排仓库，走 git-flow 分支模型，下一步大概是 bugfix 或 upgrade/migration。**如果哪条不对，喊我一声，后面 4/5/6 节的剧本我给你换。

---

## 热身小测（先想，再往下看——这是 ICAP 的"建构"而不是"被动"）

别翻答案，先在脑子里回答，三十秒：

- **Q0.1** `git grep "apache-airflow = " pyproject.toml` 这条命令，如果仓库里写的是 `apache-airflow==2.9.3`，会不会有输出？
- **Q0.2** `git rev-list --count origin/master..origin/develop` 输出 `47`，`反向`输出 `0`，说明什么？如果是 `47` 和 `3` 呢？
- **Q0.3 反事实题**：如果我**不**跑 `git fetch` 就跑第二条命令，我看到的数字错在哪个方向？
- **Q0.4 介入题**：如果我把这两条命令塞进 CI 的 `set -e` 脚本里，会发生什么惨案？

答案在第 6 节和文末的答案区。想不出来也没关系——想不出来的那个点，正是你今天要学的东西。

---

# 1) 高层心智模型：先看地图，再走地形

## 这两行命令到底是什么

它不是"代码"，它是**仪式**。资深工程师接手一个陌生仓库的头十分钟，都会做两件事，古今中外一模一样：

| 命令 | 它在问的真正问题 | 类比 |
|---|---|---|
| `git grep "apache-airflow = " pyproject.toml` | **我站在哪个平台的哪个版本上？** | 考古学家先测碳十四定年代，再谈文物 |
| `git rev-list --count A..B` 双向 | **这个仓库的两条主干，分家多久了？血缘还认不认？** | 看族谱：两支分了 47 代，还能不能合宗 |

袁腾飞式的说法：第一条是**问朝代**，第二条是**问南北朝有没有正在打仗**。你不知道现在是唐还是宋，就别急着写变法奏章。

## 为什么偏偏是 Airflow 让"问朝代"变得生死攸关

这是这个 domain 最核心的一条 insight，你记住这一句今天就没白来：

> **Airflow 不是一个库（library），它是一个平台（platform）。**

普通库你 import 它，你是主人；Airflow 是**它 import 你**——你写的 DAG 文件被 scheduler 解析、被 worker 反序列化执行。所以：

- 你的代码和 Airflow 的版本是**强耦合**的，DAG 编写 API 在大版本间会变（operator 搬家到 provider 包、`schedule_interval` → `schedule`、TaskFlow API、2.x → 3.x 的一堆 breaking change）。
- Airflow 自己的依赖树是**出了名的巨大**，社区因此专门维护 **constraints 文件**（`constraints-2.x.y/3.x.y-python3.11.txt`）。这在依赖管理界是个异类：普通项目靠 lock，Airflow 生态多一层"官方约束文件"。
- **真正运行的 Airflow 版本，往往不在 `pyproject.toml` 里。**它在 Docker 镜像 tag 里、在 MWAA/Cloud Composer 的环境配置里、在 Astronomer 的 `Dockerfile` 里。`pyproject.toml` 那行经常只是**给本地开发和单测用的替身演员**。

这就是本 domain 的**头号静默故障（silent break）**：

```
pyproject.toml:  apache-airflow = "^2.9"     ← 单测在这里跑，绿
运行时镜像:       apache-airflow 2.7.3        ← DAG 在这里跑，红
                  ↑
        中间没有任何人报错，直到某个 operator 参数在 2.7 不存在
```

## Concept map（数据/控制流）

```
        ┌──────────────────── 你的仓库 (repo) ────────────────────┐
        │                                                          │
        │  pyproject.toml ──声明意图──► poetry.lock ──锁定事实──►   │
        │       │                            │                     │
        │       │                            ▼                     │
        │       │                    本地 venv / CI 单测            │
        │       │                                                  │
        │       └─────?????? （断层带 / 最易出事）                  │
        │                                                          │
        │  Dockerfile / requirements-mwaa.txt / image tag          │
        │       │                                                  │
        └───────┼──────────────────────────────────────────────────┘
                ▼
        ┌── 运行时 Airflow ──────────────────────────────┐
        │  webserver / scheduler / worker / triggerer    │
        │  + providers  + constraints  + Python 版本     │
        │             ▲                                  │
        │             │ 解析 & 执行                      │
        │        dags/ *.py                              │
        └────────────────────────────────────────────────┘

        分支拓扑（第二条命令测量的东西）：
                     merge-base
                          │
        origin/master  ───●───○───○  (M 个 commit：hotfix 走的路)
                          │
        origin/develop ───●───□───□───□ ... (N 个 commit：feature 走的路)
```

## 职责边界与 non-goals

| 是它的职责 | **不是**它的职责（别指望） |
|---|---|
| 告诉你**声明的** Airflow 版本约束 | 告诉你**实际安装/运行**的版本 |
| 告诉你两条远端分支的 commit 数量差 | 告诉你差异的**内容和风险** |
| 快速、只读、零副作用的侦察 | 依赖冲突分析、可升级性判断 |
| 基于**上次 fetch**的快照 | 实时的远端真相 |

### ✅ 本节回顾题
1. 用一句话解释"Airflow 是平台不是库"对你写代码的直接影响。
2. `pyproject.toml` 里的 Airflow 版本和线上跑的版本，为什么可以合法地不一致？谁是"真相之源"？

---

# 2) 逐行走查（Guided walkthrough）

## 第一行：`git grep "apache-airflow = " pyproject.toml`

**它做什么**：在 git 追踪的文件里做字符串搜索，路径限定为 `pyproject.toml`，模式是字面量 `apache-airflow = `（注意：`=` 两边各一个空格，末尾那个空格是"承重墙"）。

**设计意图**：找 `[tool.poetry.dependencies]` 段里那一行 Airflow 的声明。Poetry 的 TOML 风格恰好是 `name = "constraint"`，所以 `" = "` 这个模式是**为 Poetry 量身定制**的。

**隐含不变量（invariants）——这是新人最容易踩的地方**：

| 假设 | 一旦不成立会怎样 |
|---|---|
| 项目用 **Poetry**（`name = "ver"` 风格） | 若是 PEP 621 的 `dependencies = ["apache-airflow>=2.9"]` 数组 → **零输出** |
| 格式化风格是 `= ` 带空格 | 若有人写 `apache-airflow="2.9"` → **零输出** |
| 声明是**单行 inline** | 若是 `[tool.poetry.dependencies.apache-airflow]` 多行表 → **零输出** |
| `pyproject.toml` 在**当前工作目录** | monorepo 里 `services/etl/pyproject.toml` → **零输出**（pathspec 不带 glob 时不递归） |
| 声明写在 `pyproject.toml` 里 | 若在 `requirements.txt` / `Dockerfile` / `constraints.txt` → **零输出** |
| 只想要 airflow 本体 | `apache-airflow-providers-x = "1.0"` **不会**匹配（因为要求紧跟 ` = `）；但 `apache-airflow = {version="^2.9", extras=[...]}` **会**匹配 |

**故障模式清单（Failure modes）**：

- **假阴性（最危险）**：零输出。新人的反应是"哦，这个项目不依赖 Airflow"——错，是你的正则太脆。零输出应该触发**扩大搜索**，而不是下结论。
- **退出码陷阱**：`git grep` 无匹配时 **exit code = 1**。在 `set -e` 的脚本里，这一行会直接把整个 CI 干掉，而且报错信息毫无线索。
- **只搜 working tree**：不带 revision 的 `git grep` 搜的是工作区（已追踪文件）。想看别的分支得写 `git grep <pattern> origin/develop -- pyproject.toml`。这一点极其实用——**你想对比 master 和 develop 的 Airflow 版本，就靠它。**

**更稳的版本（我平时真用的）**：

```bash
# 1) 找所有 pyproject（monorepo 友好）
git ls-files '*pyproject.toml'

# 2) 宽松匹配，大小写/下划线/空格都不怕，且看行号
git grep -n -i -E 'apache[-_]airflow\s*[=<>~^"]' -- '**/pyproject.toml' '**/requirements*.txt' '**/*.cfg' 'Dockerfile*'

# 3) 跨分支对比（真相往往在这里）
for r in origin/master origin/develop; do
  echo "== $r"; git grep -n -E 'apache[-_]airflow' $r -- '**/pyproject.toml' || echo "  (no match)"
done

# 4) 锁文件里的"事实"（Poetry lock 用 name = "apache-airflow" 的形式）
git grep -n -A3 'name = "apache-airflow"' -- poetry.lock | head -40

# 5) 运行时的"终极真相"（如果你能进容器/环境）
airflow version && python -c "import airflow, sys; print(airflow.__version__, sys.version)"
```

## 第二行：`git rev-list --count origin/master..origin/develop && git rev-list --count origin/develop..origin/master`

**它做什么**：`A..B` 的含义是**"在 B 里、但不在 A 里"的 commit 集合**（严格说：可从 B 到达、不可从 A 到达）。`--count` 只要个数。两条合起来，就是经典的 **ahead / behind**。

**设计意图**：一秒钟判断分支模型的健康度。这是 git-flow（`master` = 生产，`develop` = 集成）仓库的标准体检。

**为什么用 `&&` 而不是 `;`**：作者想要"前一条成功才跑后一条"。这里其实无所谓——`rev-list` 数出 0 也是 exit 0。但把它和第一行连起来写就会出事（`git grep` 无匹配 exit 1 → 后面全不执行）。**这是个真实的、我见过不止一次的坑。**

**读数字的解释表**：

| ahead (master..develop) | behind (develop..master) | 含义 | 你的下一步 |
|---|---|---|---|
| 0 | 0 | 完全同步。刚发过版，或者仓库已死 | 看最后一次 commit 日期，区分"健康"和"停摆" |
| N > 0 | 0 | **健康的 git-flow**：develop 领先，master 可 fast-forward | 正常提 PR 到 develop |
| 0 | M > 0 | **危险信号**：master 有 develop 没有的东西（hotfix 没回灌） | 先问：为什么没 back-merge？我的改动会不会把 hotfix 覆盖掉？ |
| N > 0 | M > 0 | **两支分家**（最常见也最需要小心） | 搞清楚那 M 个是什么，评估 release 合并时的回归风险 |

**故障模式与"利刃"**：

- **`origin/*` 是缓存，不是真相。**这两个 ref 只在你 `git fetch` 时更新。你要是三周没 fetch，这数字讲的是三周前的故事。**永远先 `git fetch --all --prune`。**
- **`--count` 数的是 commit，不是变更量。**47 个 commit 可能是 47 次 `fix typo`，也可能是一次架构重写。数量 ≠ 风险。
- **squash merge / rebase 会虚增数字。**同一份改动在两边有不同 SHA，`rev-list` 会重复计数。要看"内容层面的真实差异"，用 patch-id：
  ```bash
  git cherry -v origin/master origin/develop   # 行首 '+' = 内容真的只在 develop；'-' = 内容两边都有
  ```
- **`master` 未必存在。**很多仓库改名 `main` 了。ref 不存在时 `rev-list` 报 `unknown revision` 并 exit 128 —— 又一个静默杀死脚本的点。
- **分支名假设了 git-flow。**如果团队其实是 trunk-based（只有 `main` + 短命 feature 分支），这条命令的前提就不成立，答案没有意义。

**升级版侦察脚本**：

```bash
git fetch --all --prune

# 一行拿到 behind/ahead（顺序是：左边独有  右边独有）
git rev-list --left-right --count origin/master...origin/develop   # 注意三个点

# 分家点在哪、多久以前
git merge-base origin/master origin/develop | xargs git show -s --format='merge-base: %h %ad %s' --date=short

# master 上有什么 develop 没有（回灌漏了啥）
git log --oneline --no-merges origin/develop..origin/master

# 两边的 Airflow 声明差异（把两条命令串起来的杀手级用法）
git diff origin/master origin/develop -- pyproject.toml poetry.lock
```

### ✅ 本节回顾题
1. `A..B` 和 `A...B` 差在哪？为什么 `--left-right --count` 要用三个点？
2. 为什么"零输出"比"输出一行"更需要你紧张？
3. 举一个"数字看着很健康、实际很危险"的场景。

---

# 3) 深潜 L1 → L5

## L1：术语表（背下来，开会不怯场）

| 术语 | 人话解释 |
|---|---|
| **DAG** | 有向无环图。在 Airflow 里就是"一条流水线的定义"，是 Python 代码，不是配置。 |
| **Operator / Task** | Operator 是模板（"发个 HTTP 请求"），Task 是它的一个实例。 |
| **Provider package** | Airflow 2.0 把 AWS/GCP/Snowflake 等集成从本体**拆出去**独立发版。这是版本地狱的主要来源：本体和 provider 各有版本轴。 |
| **Constraints 文件** | Airflow 官方发布的"这一版 Airflow 已知可工作的全套依赖精确版本"。它**不是** lock 文件，是 pip 的 `-c` 约束。 |
| **Caret pin `^2.9`** | Poetry 语法：`>=2.9.0, <3.0.0`。对 Airflow 这种平台，这个范围**太宽**了。 |
| **poetry.lock** | 事实层。pyproject 是"我想要什么"，lock 是"上次解出来是什么"。 |
| **Executor** | Local/Celery/Kubernetes。决定 task 在哪跑、依赖装在哪。 |
| **merge-base** | 两条分支最近的共同祖先。所有 ahead/behind 都是相对它算的。 |
| **ahead / behind** | 见上表。面试和 standup 高频词。 |
| **git-flow** | master(生产) + develop(集成) + release/hotfix 分支的老派模型。第二条命令是为它写的。 |

## L2：架构与依赖

```
声明层   pyproject.toml  [tool.poetry.dependencies]
              │  poetry lock
事实层   poetry.lock
              │  poetry install / pip install -c constraints
镜像层   Dockerfile (FROM apache/airflow:X.Y.Z-pythonA.B)  ← 常常是真正的老大
              │
平台层   MWAA / Cloud Composer / Astronomer / 自建 K8s      ← 有时连镜像都由它定
              │
执行层   scheduler 解析 dags/ → worker 执行 task
```

**关键依赖关系（你要问团队的第一个问题）**：
> "我们的 Airflow 版本**真相之源**是哪一个文件？pyproject、Dockerfile，还是托管环境配置？谁保证它们一致？"

如果没人答得上来，恭喜你，你入职第一个可交付成果找到了。

## L3：算法 / 状态 / 数据模型

**`git rev-list` 的本质**：从起点 commit 出发在 DAG 上做遍历，用"可达性"做集合减法。`A..B` = reachable(B) − reachable(A)。它是**拓扑**运算，不看 diff 内容，所以 rebase/squash 后同内容不同 SHA 就被算成不同 commit。要做"内容等价"判断，得用 **patch-id**（对 diff 做规范化哈希），这就是 `git cherry` / `git log --cherry-mark` 干的事。

**`git grep` 的本质**：遍历 index（或指定 tree），按 pathspec 过滤，逐 blob 做字符串/正则匹配。因为走 index 而不是 `find`，所以在大仓库上比 `grep -r` 快得多，还天然跳过 `.gitignore` 的垃圾（`node_modules`、`.venv`）。

**版本约束求解**：Poetry/pip 的依赖解析本质是 SAT 求解，NP-hard。Airflow 依赖树 hundreds of packages，这就是为什么"随便 `poetry add` 一个包"能让 lock 跑二十分钟然后失败——以及为什么社区要发 constraints 文件来把搜索空间钉死。

## L4：性能 / 可靠性 / 安全

| 维度 | 要点 |
|---|---|
| 性能 | `git grep` 在 index 上跑，O(tracked files)；避免 `grep -r`。大 monorepo 用 `-- '**/pyproject.toml'` 收窄 pathspec。 |
| 可靠性 | 两条命令都是只读、幂等、可安全重跑。唯一的"状态"是本地 fetch 快照的新鲜度。 |
| 可靠性（Airflow 侧） | 版本漂移是**静默**的：单测绿、DAG 运行时炸。防御手段是"同一份约束贯穿单测和运行时"。 |
| 安全 | 宽松 pin（`^2.9` / 无上界）= 供应链暴露面。lock + 哈希校验 + 私有 index 优先，防 dependency confusion。 |
| 安全（信息泄露） | 把 `git grep` 结果贴到工单里时注意别把内网 index URL、token 一起贴出去——`pyproject.toml` 的 `[[tool.poetry.source]]` 段里经常藏着凭据 URL。 |

## L5：权衡与"今天重新设计我会怎么做"

| 抉择 | 选项 A | 选项 B | 我的判断 |
|---|---|---|---|
| Airflow pin 策略 | 精确 `==2.9.3` | 范围 `^2.9` | **平台依赖用精确 pin**。Airflow 是宿主，宿主不能"大概" |
| 一致性保障 | 人工同步多处版本 | CI 断言 pyproject == 镜像 tag | **B**，写成一个 5 行的测试，比一页 wiki 有用 |
| 分支模型 | git-flow | trunk-based + feature flag | trunk-based 更适合 Airflow（DAG 发布本身就是持续的）；但**别在入职第一周提这个改革** |
| 依赖工具 | Poetry lock | pip + 官方 constraints | Airflow 生态里 constraints 是一等公民，理想是 **lock 生成时喂 constraints** |
| 侦察方式 | 手敲 grep | 仓库里存一个 `make doctor` | **B**：把你今天学的两条命令变成脚本，是你能留下的第一份资产 |

**历史原因（为什么现状会这么丑）**：git-flow 出自 2010 年，那个年代发版是季度级事件，`master`/`develop` 分家几十个 commit 很正常。Airflow 从 1.10 到 2.0 的 provider 大拆分，又强行给所有仓库塞进一次"版本大迁徙"。你现在看到的 `pyproject` + `Dockerfile` + 托管环境三处版本，基本都是**地质沉积层**，不是有人故意设计的。理解这一点，你在 code review 里的语气会好很多。

### ✅ 本节回顾题
1. constraints 文件和 lock 文件，本质区别是什么？
2. 为什么我说"平台依赖要精确 pin"，而普通库可以用范围？
3. `git cherry` 解决了 `rev-list --count` 的什么缺陷？

---

# 4) SME 培养计划（10 天，每天 ≤2 小时）

| Day | 读什么 | 跑什么 | 量什么 | 安全改什么 | 问队友什么 | 交付物 |
|---|---|---|---|---|---|---|
| 1 | `README`、`pyproject.toml`、`poetry.lock` 头部 | 上面那 5 条加固版 grep | 有几个 pyproject？Airflow 声明在几处？ | 什么都别改 | "Airflow 版本的真相之源是哪个文件？" | 一页 `docs/repo-map.md` |
| 2 | `Dockerfile` / 部署配置 / CI yaml | `git diff origin/master origin/develop -- pyproject.toml poetry.lock` | 声明版本 vs 镜像 tag 是否一致 | — | "谁保证这两个一致？出过事吗？" | **版本漂移矩阵表**（本节的杀手交付物） |
| 3 | git 历史 | `git log --oneline --no-merges origin/develop..origin/master` | 有多少 hotfix 没回灌 | — | "上一次 release 是怎么合的？" | 分支健康快照 |
| 4 | `dags/` 里最简单的 1 个 DAG | 本地起 Airflow（`LocalExecutor` / breeze / astro dev） | 冷启动到 DAG 出现要多久 | — | "本地环境标准姿势是什么？" | 本地起环境的 runbook |
| 5 | Airflow 官方 upgrade check / deprecation 文档 | 跑仓库现有测试套件 | 测试耗时、覆盖率、有没有 DAG import 测试 | — | "有 DAG 完整性测试吗？" | 测试现状小结 |
| 6 | Poetry 文档的 constraint 语法 | 写 `scripts/repo-doctor.sh`（把 D1–D3 的命令固化） | 脚本运行时间 | **加脚本，不改逻辑** | "能进 CI 吗？" | PR #1（纯新增，零风险） |
| 7 | 团队的 provider 使用面 | `git grep -n 'apache-airflow-providers'` | 用了几个 provider、各自版本 | — | "哪个 provider 最容易出事？" | provider 清单 |
| 8 | — | 加 **DAG import 冒烟测试**（遍历 DagBag 断言 0 import error） | 新测试执行时间 | 加测试 | "为什么以前没加？" | PR #2 |
| 9 | — | 加 **版本一致性断言测试**（pyproject 声明 vs 运行时 `airflow.__version__`） | — | 加测试 | "这个断言应该 fail 还是 warn？" | PR #3 |
| 10 | 复盘全部笔记 | 给团队做 20 分钟分享 | — | — | 收集反驳意见 | **一页 ADR：Airflow 版本管理与分支策略现状及建议** |

**为什么这个顺序**：前三天纯只读建立地图（ICAP 的"主动"），4–5 天动手跑（"建构"），6–9 天用**只增不改**的 PR 建立信誉（工程政治学：新人的第一个 PR 应该零风险且有用），第 10 天做分享（"互动"——被人质疑才是真学会）。

---

# 5) 动手练习（难度递增）

### 练习 1（只读 · 解释）
在你的仓库跑那两条原始命令，**然后写一段话解释输出**。要求这段话里必须包含：声明的版本、真相之源在哪、ahead/behind 各是多少、这两个数字对你下周提 PR 的影响。
- **预期做法**：先 `git fetch --prune`，再跑，再跑加固版交叉验证。
- **坑**：把 pyproject 的版本当成线上版本。
- **验证**：让队友看一眼你的结论，问"我漏了什么"。

### 练习 2（小改动 · 安全重构）
把两条命令写成 `scripts/repo-doctor.sh`，要求：
- 显式 `git fetch --all --prune`
- **无匹配时不能让脚本挂掉**（提示：`|| true`，或 `if ! git grep -q ...; then echo "WARN: ..."; fi`）
- 自动探测 `main` vs `master`（`git symbolic-ref refs/remotes/origin/HEAD`）
- 用 `--left-right --count ...`（三点）一次拿两个数
- **坑**：`set -euo pipefail` + `git grep` 的退出码 1；ref 不存在时 exit 128。
- **验证**：在一个**故意不含 airflow** 的空仓库里跑它，脚本必须优雅输出 WARN 且 `echo $?` 为 0。

### 练习 3（Bug hunt · 复现 + 修）
**造一个假阴性。**在测试仓库里把声明改成
```toml
[tool.poetry.dependencies.apache-airflow]
version = "2.9.3"
extras = ["celery"]
```
跑原命令 → 零输出。现在修你的 grep 让它抓得到。
- **坑**：只加 `-i` 不够；TOML 多行表根本不含 `apache-airflow = `。正解是匹配 `apache[-_]airflow` 再看上下文，或者干脆**别用 grep**——用 `python -c "import tomllib; ..."` 解析 TOML 才是正确解法。
- **教学点**：**"用正则解析结构化格式"是全行业最经典的静默 bug 之一**（跟"用正则解析 HTML/XML"同源）。这是本课最重要的一条 design-for-failure 教训。
- **验证**：把 inline 表、数组式 PEP 621、带注释、大小写混写四种写法都做成 fixture，跑你的解析器。

### 练习 4（Bug hunt 进阶 · 分支幻觉）
在测试仓库里：从 master 拉 develop，在 develop 提 3 个 commit，然后把这 3 个 **squash merge** 回 master。此时 `rev-list --count master..develop` 是多少？`develop..master` 是多少？内容上两边其实一致吗？
- **预期发现**：数字非零，但 `git cherry -v` 显示内容已经在对面了。
- **教学点**：拓扑差异 ≠ 内容差异。**很多团队的"分支永远合不干净"就是 squash merge 造成的假分家。**
- **验证**：`git diff master develop --stat` 应该接近空。

### 练习 5（设计扩展）
设计并实现一个 CI 检查：**声明的 Airflow 版本必须与运行时/镜像版本一致，不一致就红。**
- **预期做法**：解析 pyproject（tomllib）→ 解析 Dockerfile `FROM apache/airflow:X.Y.Z`（或托管环境配置）→ 比较；在容器内再断言 `airflow.__version__`。
- **需要先做的决策**（写在 PR 描述里）：不一致时是 **fail** 还是 **warn**？我的建议是**先 warn 两周收集噪声，再升级为 fail**——因为一上来就 fail 会拦住所有人的 PR，你会在入职第二周变成全组公敌。
- **坑**：镜像 tag 可能是 `latest`、`2.9.3-python3.11`、或 digest；托管服务的版本可能压根不在仓库里（那就承认"无法自动校验"并在 doc 里写明，这也是合格答案）。
- **验证**：故意改坏一边，CI 必须变色；两边一致时必须绿。

---

# 6) 主管拷问（Q1 → Q5，附标准答案）

### Q1（入职检查）"这两条命令是干什么的？"
- **弱答**："搜 Airflow 版本，数分支 commit。"
- **强答**："第一条从 Poetry 的声明里找 Airflow 的版本约束，第二条量 `master`/`develop` 的双向 ahead/behind。合起来是仓库侦察：我在哪个平台版本上，以及两条主干分家多远。**但两条都只是线索不是结论**——第一条可能假阴性，第二条依赖上次 fetch 的新鲜度。"
- **追问陷阱**："`A..B` 到底是哪边独有？" → **B 独有**（可从 B 到达、不可从 A 到达）。

### Q2 "命令返回空，你怎么办？"
- **弱答**："那就是没依赖 Airflow。"
- **强答**："空输出我先怀疑我的模式，不怀疑仓库。依次排查：① 是否 PEP 621 数组式声明；② 是否 `[tool.poetry.dependencies.apache-airflow]` 多行表；③ 是否 `=` 两侧无空格；④ 是否 monorepo 里的嵌套 pyproject（pathspec 不递归）；⑤ 是否根本不在 pyproject 而在 requirements/Dockerfile/托管配置。最终手段是 `tomllib` 解析而不是 grep——**用正则读结构化格式本身就是 bug 源**。"
- **追问**："那 `git grep` 的退出码呢？" → **无匹配是 1**，在 `set -e` 脚本里会静默杀掉后续步骤。

### Q3 "ahead 47 / behind 3，你的第一个 PR 该怎么提？"
- **弱答**："提到 develop，让 reviewer 看着办。"
- **强答**："behind 3 是红旗——master 上有 develop 没有的 commit，通常是没回灌的 hotfix。我会先 `git log --oneline origin/develop..origin/master` 看那 3 个是什么。如果碰我要改的文件，我先把 back-merge 这件事提出来（**由 owner 做，不是我做**），再基于最新 develop 开分支。同时用 `git cherry -v` 确认这 3 个是真差异还是 squash 造成的幻影。至于 47，那是数量不是风险，我关心的是 `git diff --stat` 和有没有触及我的代码路径。"
- **追问**："你会自己 back-merge 吗？" → 入职第一周**不会**。冲突解决需要业务上下文，我会主动提出并 pair。
- **拿证据辩护**：贴 `--left-right --count`、`merge-base` 日期、`git cherry -v` 三份输出。

### Q4 "pyproject 写 `^2.9`，线上跑 2.7.3。谁错了？影响是什么？"
- **弱答**："pyproject 写错了，改成 2.7.3。"
- **强答**："严格说没人'写错'，是**缺少一致性约束**这个系统性问题。影响是最坏的一类：**静默**。CI 在 2.9 上装依赖跑单测，全绿；DAG 在 2.7.3 上执行，一旦用了 2.8+ 才有的 operator 参数或 TaskFlow 特性，就在生产 runtime 报 `TypeError`/`ImportError`，而且往往是**某条低频 DAG 半夜跑到才炸**。修法分两步：短期把声明精确 pin 到运行时版本（**向下对齐，不是向上**，因为运行时不好改）；长期加 CI 断言 + 在同一容器镜像里跑测试，让'声明层'和'执行层'物理上同源。"
- **追问陷阱**："那为什么不干脆升级线上到 2.9？" → 那是独立的迁移项目：需要读 deprecation 列表、跑 upgrade check、评估 provider 兼容、准备回滚。**不能作为"修一致性 bug"的顺手动作。混淆这两件事是新人最常犯的判断错误。**

### Q5（Staff 级权衡）"设计一套机制，让这类版本/分支漂移不再靠人肉 grep 发现。给我方案和取舍。"
- **弱答**："写个脚本每天跑，发 Slack。"
- **强答**：分层设计，按"越早越便宜"排序：

| 层 | 机制 | 成本 | 抓到的时机 | 取舍 |
|---|---|---|---|---|
| L0 开发者本地 | `make doctor` / pre-commit | 极低 | 写代码时 | 会被 `--no-verify` 绕过，只能算提醒 |
| L1 CI（推荐主战场） | 版本一致性断言 + DAG import 冒烟测试 | 低 | PR 时 | 需要先跑 warn 期，否则拦住全组 |
| L2 构建产物 | 单一镜像同时用于测试和运行 | 中 | 构建时 | 最彻底，但要改 CI 架构 |
| L3 运行时 | 启动时上报 `airflow.__version__` 到 metrics，与期望值比对告警 | 中 | 部署后 | 最后一道网，抓托管环境静默升版 |
| L4 流程 | 分支漂移看板 + 定期 back-merge 节律，或直接转 trunk-based | 高（组织成本） | 持续 | 技术容易、人难；需要 owner 支持 |

  "如果只能做一件：**L1 的 DAG import 冒烟测试**。它便宜、无争议、能挡住绝大多数版本不兼容（因为 API 变更几乎都在 import/构造阶段就炸）。分支那边我先做**可观测性**（看板）而不是**强制**（policy），先让数据说话再谈改流程。"
- **追问陷阱**："如果托管服务被云厂商自动小版本升级了呢？" → 那 L0–L2 全部失效，只有 **L3 运行时上报**能发现。这正是为什么要分层，而不是指望一个 CI 检查。
- **怎么用证据辩护**：拿三样东西——① 一次真实漂移的事故时间线；② DAG import 测试的执行耗时（证明成本低）；③ warn 期收集的违规计数（证明该不该升级为 fail）。

### ✅ 本节回顾题
1. Q4 里为什么要"向下对齐"而不是升级线上？
2. Q5 里为什么"先 warn 再 fail"是政治上和工程上的双重正解？

---

# 7) 怎么像 Staff 一样思考（可复用方法论）

## 读陌生代码的四问法
```
1. WHERE  真相之源在哪？（哪个文件/系统是 authoritative）
2. WHAT   它声明了什么不变量？（invariants）
3. WHEN   什么时候会静默失败？（不是崩溃，是无声地错）
4. WHO    谁在维护这个假设？（有人？还是靠祈祷？）
```
默认心态：**"我看到的是线索，不是结论。"** 一条命令的输出永远要用第二条独立路径交叉验证（triangulation）。本课里的三角就是：`pyproject`（声明）× `poetry.lock`（解析结果）× `airflow.__version__`（运行时）。三点共线才叫知道。

## 建立正确性模型
- 写下**不变量**："声明版本 == 运行时版本"
- 写下**观测手段**：怎么在不改任何行为的前提下证明它成立
- 写下**违反后果**：崩溃（好）还是静默（坏）
- 只有**能观测**的不变量才是真不变量。写在 wiki 里没人测的，那叫许愿。

## 故障与可观测性推理
问三句：
1. 这个改动**能不能静默地**坏掉？（能 → 必须加断言/指标）
2. 坏掉后**多久**才会有人发现？（越久越该前置）
3. 这个坑**是不是行业通病**？（是 → 别自创方案，抄成熟做法）

**本 domain 的行业通病清单**（记在小本上）：
- 用正则解析结构化格式（TOML/YAML/JSON/HTML）→ 假阴性
- 声明层与运行时层版本漂移 → 静默生产故障
- 忘 `fetch` 就读 `origin/*` → 基于过期数据决策
- 脚本里忽略非零退出码 → CI 假绿
- squash merge 造成的分支假分家 → 永远合不干净
- 长命分支 + hotfix 不回灌 → release 时回归

## 可复用清单

**接手陌生仓库 · 10 分钟清单**
- [ ] `git fetch --all --prune`
- [ ] `git ls-files '*pyproject.toml' '*requirements*.txt' 'Dockerfile*'`
- [ ] 平台/框架版本：声明层、锁层、镜像层、运行时层，四处各是多少
- [ ] `git rev-list --left-right --count origin/<main>...origin/develop`
- [ ] `git merge-base` 的日期（分家多久了）
- [ ] 最近 20 个 commit 的作者分布（谁是真 owner）
- [ ] CI 配置：跑什么测试、在哪个环境跑
- [ ] 找出**一个**没人保证的假设，写下来 → 这就是你的第一个交付物

**改动前 · design-for-failure 清单**
- [ ] 这个改动会不会**静默**改变行为？
- [ ] 有没有测试会因此变红？（一个都没有 → 说明覆盖不足，本身就是发现）
- [ ] 失败时错误信息里有没有足够线索？
- [ ] 回滚方案是什么？
- [ ] 上下游谁依赖我改的这个不变量？

---

# 8) 可靠性与溯源自审（我换上 Reviewer 的帽子审我自己）

## 8.1 声明：本次回答的证据来源

| 说法 | 来源 | 置信度 |
|---|---|---|
| 提供的三份知识库文件与本题无关 | **已验证**：`grep` `airflow\|pyproject\|poetry\|git\|branch\|develop` 返回 "No matches"；语义检索命中的是"Changes from previous offerings"、MQ 风格指南 A–Z、班级组同步说明 | 高 |
| `git grep` 语义、pathspec 不递归、无匹配 exit 1 | 通用 git 知识 | 高 |
| `A..B` = B 独有；`--left-right --count` 需三点 | 通用 git 知识 | 高 |
| `git cherry` / patch-id 可识别 squash 造成的假分家 | 通用 git 知识 | 高 |
| Poetry `name = "ver"` 与 `^2.9` 语义 | 通用 Poetry 知识 | 高 |
| Airflow 有官方 constraints 文件、2.0 拆分 provider 包 | 通用 Airflow 生态知识（截至 2026-05） | 高 |
| **你的仓库实际用 Poetry / git-flow / 托管 Airflow** | **推断，未验证** | 低 — 见 8.3 |

## 8.2 我明确说"不知道"的地方
- **No.** 我读不到 `~/ws/`。我没有本地文件系统或 shell 工具，只有知识库检索和白名单网页抓取。所以我**没有**、也**不会假装**看过你的实际代码。
- **No.** 网络搜索被禁用，我不去核对 Airflow 最新版本号或具体某个 API 在哪个小版本引入。凡涉及"具体哪一版引入了什么"，你必须查官方 changelog。
- 我**没有**给出任何你仓库里的真实版本号、文件路径、CI 名称——因为我不知道，编出来就是害你。

## 8.3 假设清单 + 验证方式

| 假设 | 怎么验证（你跑一下就知道） |
|---|---|
| 用 Poetry（而非 uv/pip/PDM） | `git ls-files \| grep -E 'poetry.lock\|uv.lock\|requirements'` |
| 分支叫 `master`/`develop`，走 git-flow | `git branch -r`；`git symbolic-ref refs/remotes/origin/HEAD` |
| Airflow 是托管服务而非自建 | 找 `Dockerfile` / `.tf` / MWAA·Composer 配置 |
| pyproject 与运行时版本不一致 | `git grep -n airflow -- Dockerfile*` 对比 pyproject；容器内 `airflow version` |
| 单测在与生产不同的 Airflow 版本上跑 | 读 CI yaml 里的 install 步骤 |

## 8.4 缺什么材料（你补给我，我给你一版精确到行的分析）
1. `pyproject.toml` 全文（或至少 `[tool.poetry.dependencies]` 段）
2. `poetry.lock` 里 `name = "apache-airflow"` 附近 5 行
3. `Dockerfile` 或部署配置里的 Airflow 镜像/版本
4. CI 配置文件
5. `git branch -r` 和 `git rev-list --left-right --count` 的**实际输出**
6. `dags/` 的目录结构（不用内容）

**安全的下一步**（在缺料情况下也绝对不会出错的动作）：只跑只读命令、把输出记成文档、不改任何配置、把发现整理成问题清单去问 owner。

---

# 9) ICAP 加固（被动 < 主动 < 建构 < 互动）

| 层级 | 你要做的事 | 本课对应动作 |
|---|---|---|
| **被动** Passive | 读完上面这些 | 已完成（别停在这层，这层留存率最低） |
| **主动** Active | 在你的仓库真的敲那两条命令 + 加固版 | 今天 30 分钟 |
| **建构** Constructive | 画出**你自己**仓库的版本漂移矩阵 + 分支拓扑图，**不看我的模板** | 今天 45 分钟 |
| **互动** Interactive | 拿你画的图去找 owner 对质："我理解的真相之源是 X，对吗？"——被反驳的地方，才是你真正学到的地方 | 明天 20 分钟 |

**只做被动，你明天就忘。做到互动，你两周后是这个仓库的 SME。**这不是鸡汤，这是 Chi 的实证结论。

---

# 10) 论文答辩模式（Defence — 现在换你说，我提问）

规则：不许看上文，口头作答，每题 60 秒。答完对照标准答案。

| # | 问题 | 标准答案要点 |
|---|---|---|
| D1 | 为什么"零输出"不等于"没依赖 Airflow"？举三个具体原因 | PEP 621 数组式 / 多行 TOML 表 / `=` 无空格 / monorepo 嵌套路径 / 声明在别处 |
| D2 | ahead=0, behind=5 说明什么？危险在哪 | hotfix 没回灌；我的 PR 可能与 master 上的修复冲突或覆盖它；release 时会带回归 |
| D3 | 反事实：如果我**没有**先 fetch 就下结论，会怎样？ | 我基于本地过期快照决策；数字可能偏小甚至方向相反；结论可能已经过时数周 |
| D4 | 介入：如果我把 pyproject 从 `^2.9` 改成 `==2.9.3`，会发生什么？ | lock 重解、CI 依赖树变化、可能触发 provider 冲突；**但线上运行版本一点没变**——这只统一了声明层，没修根因 |
| D5 | 介入：如果我把 develop 直接 merge 进 master 让数字归零，会怎样？ | 那是发版行为，不是清理行为。绕过 release 流程、跳过 QA、可能上线 47 个未验证 commit。**数字是症状，不是要治的病。**（"为了让指标变绿而操作指标"是 Goodhart 定律的教科书案例） |
| D6 | 为什么我说"用正则解析 TOML 是 bug 源"？这个错误的通用形态叫什么 | 结构化格式有多种等价语法表示，正则只能覆盖你想到的那几种 → 系统性假阴性。同族："用正则解析 HTML/XML/CSV" |
| D7 | 如果只允许你加**一个** CI 检查来防这类问题，你加哪个？为什么 | DAG import 冒烟测试（DagBag 遍历断言 0 error）。理由：便宜、无争议、覆盖面大（API 不兼容几乎都在 import/构造期暴露） |
| D8 | 主管说"这不就两条命令吗，值得写一页文档？" | 值得。这两条命令编码了两个关键不变量（版本一致性、分支收敛性），而目前**没有任何自动化在守护它们**。文档只是第一步，真正的产出是把它变成 CI 断言 |

---

## 热身题答案（Q0.1–Q0.4）

- **Q0.1** 不会。模式要求 ` = `（空格-等号-空格），`==2.9.3` 不含它。**这就是假阴性。**
- **Q0.2** `47/0` = 健康的 git-flow，develop 领先，master 可 fast-forward。`47/3` = 双向分家，master 上那 3 个很可能是没回灌的 hotfix，红旗。
- **Q0.3** 数字**偏小**（你的本地 `origin/*` 停在过去，看不到新 commit），甚至可能方向错——你以为同步了其实早分家。
- **Q0.4** `git grep` 无匹配返回 exit 1 → `set -e` 直接终止脚本，且如果用 `&&` 串联，后面的 `rev-list` 根本不执行。**CI 会以一个语义不明的失败挂掉，或者更糟：后续检查被静默跳过而 CI 显示绿。**

---

# ✅ Next actions for me today（今天就做，别攒着）

- [ ] `git fetch --all --prune`，然后跑原始的两条命令，把输出**原样**记下来
- [ ] 跑加固版：`git ls-files '*pyproject.toml'` + 宽松正则 grep + `git rev-list --left-right --count origin/<main>...origin/develop`
- [ ] 用 `tomllib` 而不是 grep 解析一次 pyproject，对比两种方法结果是否一致（这一步会让你终身记住第 5 题的教训）
- [ ] 填一张 4 行的**版本漂移矩阵**：声明层 / 锁层 / 镜像层 / 运行时层，各是什么版本，空的地方写"未知"
- [ ] `git merge-base origin/<main> origin/develop` 看分家日期；`git log --oneline --no-merges origin/develop..origin/<main>` 看漏灌了什么
- [ ] 写下 **3 个要问 owner 的问题**，第一个必须是："Airflow 版本的真相之源是哪个文件，谁保证一致？"
- [ ] 起草 `scripts/repo-doctor.sh`（今天只要能跑，不追求漂亮），处理好 exit code 和 main/master 探测
- [ ] 把上面 6 项材料贴给我，我给你一版**精确到行号**的复盘 —— 现在这一版是方法论，那一版才是你仓库的真相

---

最后一句掏心窝的话：这两行命令看着像顺手一敲，其实它是一个成熟工程师的**条件反射**——先定位自己在时空中的坐标，再动手。刘邦入关中第一件事是"收秦丞相御史律令图书"，萧何抢的不是金银是档案。你今天抢的就是档案。

看到 `apache-airflow` 那行的时候，脑子里要同时闪过三个问题：**这是声明还是事实？谁在守护它？它坏掉的时候会不会有人知道？** 能条件反射地问出这三句，你就不是"会用 git 的人"，你是 SME。

有输出了就贴上来，我们过第二轮。
=====
# 第三条命令：`git merge-base origin/master origin/develop`

好，你继续往下敲了。这条命令是前面那条 `rev-list --count` 的**亲爹**——你之前数的 ahead/behind，全都是相对它算出来的。现在你算是从"看仪表盘"走到"看发动机"了。

**先说清楚**：你只给了命令，没给输出（我也跑不了你的仓库）。所以这一节我教的是**怎么读这个输出**，等你把那个 SHA 贴上来，我们再做具体判案。

---

## 开场三十秒小测（先想，别往下滑）

- **Q1** `merge-base` 输出的那个 SHA，如果**正好等于 `origin/master` 的 tip**，说明什么？你之前的 `behind` 数字应该是多少？
- **Q2** `git merge-base --all A B` 有可能吐出**两行**吗？如果真的吐了两行，意味着什么、你该紧张吗？
- **Q3 反事实题**：如果我拿 merge-base 那个 commit 的**日期**当作"两条分支分家的时间"，什么情况下这个推断是**错的**？

---

## 1) 它到底在干什么：一句话 + 一张图

> **merge-base = 两条分支最近的共同祖先（Lowest Common Ancestor, LCA）。**它是 git 一切"三方合并"的**基准点（base）**。

```
                       merge-base（就是它）
                            │
   ...──●──●──●──●──●───────●
                            │╲
              origin/master │ ╲───○───○───○      ← behind：master 独有
                            │
              origin/develop└───□───□───□───□    ← ahead：develop 独有
```

**为什么它是"发动机"**：`git merge` 干的活叫 **three-way merge（三方合并）**，三方是——

| 角色 | 是谁 |
|---|---|
| **base** | `merge-base` 的那个 commit（共同祖先） |
| **ours** | 你当前分支的 tip |
| **theirs** | 你要合进来的分支 tip |

git 拿 base 当参照系，分别算出 ours 和 theirs 各自"改了什么"，然后叠加。**base 选错，冲突就会莫名其妙。**你以后遇到"这个冲突根本不该冲啊"的时候，十有八九问题出在 base，不出在两边的代码。

这也是历史学的道理：判断南北两朝谁篡了谁，你得先找到最后一个**共同承认的正统**。找不到共同祖先，就没有"谁改了什么"这回事——只有两份互不相识的文本。

---

## 2) 怎么读输出：三种结局对照表

拿到那个 SHA，第一件事是跟两条分支的 tip **比对身份**。这是本节最实用的部分：

```bash
MB=$(git merge-base origin/master origin/develop)
echo "merge-base : $MB"
echo "master tip : $(git rev-parse origin/master)"
echo "develop tip: $(git rev-parse origin/develop)"
git show -s --format='%h %ad %an %s' --date=short "$MB"
```

| merge-base 等于 | 拓扑含义 | ahead/behind 应该是 | 你的动作 |
|---|---|---|---|
| **`origin/master` 的 tip** | master 是 develop 的**祖先**，历史线性 | behind = **0** | 最健康。master 可以 fast-forward 到 develop，发版无痛 |
| **`origin/develop` 的 tip** | develop 完全被 master 包含（develop 落后但没独有） | ahead = **0** | develop 停摆或刚被 reset；先问 owner 是不是分支废了 |
| **两个 tip 都不是** | **已分家（diverged）** | 两个都 > 0 | 红旗。先查 master 独有的那几个是什么 |
| 两个 tip **相等** | 完全同步 | 0 / 0 | merge-base 就是共同的 tip 本身 |

**这就是三角验证（triangulation）**：`rev-list --count` 给你**数量**，`merge-base` 给你**拓扑身份**。两个信号互相印证，你才敢下结论。单看数字，你只是"知道有差异"；加上 merge-base，你才"知道差异的形状"。

---

## 3) 逐个变体：真正干活的是这几个

原始命令只是入门款。下面这些是我平时真按的键：

| 命令 | 用途 | 关键细节 |
|---|---|---|
| `git merge-base A B` | 输出 LCA 的 SHA | 有多个 LCA 时**只吐一个**（任选），会骗你 |
| `git merge-base --all A B` | 吐出**所有** LCA | 输出 >1 行 = **criss-cross merge**，见下文 |
| `git merge-base --is-ancestor A B` | 判断 A 是不是 B 的祖先 | **不输出任何东西**，靠**退出码**：0=是，1=不是。写脚本必用 |
| `git merge-base --fork-point A B` | 猜"B 是从 A 的哪个点分出来的" | **依赖 reflog**，reflog 过期就失效或给错答案。**别在 CI 里用** |
| `git merge-base --octopus A B C` | 多分支的共同祖先 | 少见，release 合多个 feature 时偶尔用 |

**脚本里的正确写法**（比 grep SHA 字符串靠谱一万倍）：

```bash
if git merge-base --is-ancestor origin/master origin/develop; then
  echo "OK: master 是 develop 的祖先，可 fast-forward"
else
  echo "WARN: 已分家，master 上有 develop 没有的 commit"
  git log --oneline --no-merges origin/develop..origin/master
fi
```

注意这里的模式：**用退出码做判断，用日志做解释。**判断要机器可读，解释要人类可读。这个习惯你带到任何脚本里都成立。

---

## 4) 利刃（Sharp edges）—— 这几个坑我都亲手踩过

### ① `--all` 出现多行：criss-cross merge

```
   ...──●──A──────────●──────  master
         ╲  ╲        ╱
          ╲  ╳──────╱          ← 互相合过，形成交叉
           ╲╱  ╲
   ...──●──B────●───────────    develop
```
A 和 B **都是**合法的共同祖先，谁都不比谁"更近"。这时候 git 的默认策略（`ort`/`recursive`）会**递归地把多个 base 先合成一个"虚拟 base"**，然后再用它做三方合并。

**后果**：冲突内容会显得"很诡异"——因为参照系是一个**从来不存在过的虚拟 commit**。这就是那种"我明明没改这行，怎么冲突了"的经典来源。

**怎么发现**：`git merge-base --all` 输出多于一行。真遇到了，别硬合，先 `git log --graph --oneline` 看清拓扑，然后**找 owner pair**。这不是新人该单飞的场景。

### ② merge-base 的日期 ≠ 分家的日期（Q3 的答案）

如果 **master 自分家后一个 commit 都没动**，那 merge-base 就**等于 master 的 tip**。此时那个 commit 的日期是"master 最后一次更新"的日期，**不是**"develop 分出去"的日期——虽然数值上常常巧合地接近。

更阴的情况：**rebase 会重写 commit 的 author date/committer date**，`--fork-point` 依赖的 reflog 又是**本地的、会过期的**。所以：

> **merge-base 的日期是"参考坐标"，不是"法庭证据"。**要论证"这两条分支分家 N 个月了"，请用 `git log --oneline` 看实际 commit 序列，别只拿一个日期说事。

### ③ 忘记 fetch（老朋友了）

`origin/master`、`origin/develop` 都是**本地缓存的 ref**。没 fetch，merge-base 算的是历史剧。**每次都先 `git fetch --all --prune`**，这句话我这辈子会跟你说一百遍。

### ④ ref 不存在时静默炸

仓库改名 `main` 了？`git merge-base origin/master origin/develop` 报 `Not a valid object name` 并且**退出码非 0**。在 `set -e` 脚本里就是一声不响地终止。跟前面 `git grep` 的坑同源——**所有"读 ref"的命令，在脚本里都要先验证 ref 存在**：

```bash
git rev-parse --verify --quiet origin/master >/dev/null || { echo "no origin/master"; exit 2; }
```

### ⑤ 空仓库 / 无共同祖先

两条分支毫无血缘（比如 import 进来的孤立历史），`merge-base` **输出为空、退出码 1**。这时候合并需要 `--allow-unrelated-histories`——**看到这个 flag 出现在别人的 PR 里，你就该警觉了**，它意味着有人在缝合两段不相干的历史。

---

## ✅ 本节回顾题
1. `--is-ancestor` 为什么"没有输出"反而是设计得好？
2. 为什么我说 `--fork-point` **不能**进 CI？
3. `--all` 输出两行时，git 实际拿什么当 base？这会导致什么现象？

---

## 5) 动手练习（30 分钟，能造出来才叫懂）

### 练习 A（只读 · 三角验证）
在你的仓库跑这一套，把四个 SHA 摆在一起看：

```bash
git fetch --all --prune
MB=$(git merge-base origin/master origin/develop)
git show -s --format='%h %ad %s' --date=short "$MB"
git rev-parse --short origin/master origin/develop
git rev-list --left-right --count origin/master...origin/develop
git merge-base --all origin/master origin/develop | wc -l   # 期望是 1
```
**交付**：一句话结论，必须落在第 2 节那张表的某一行上。**如果落不进去，说明你读错了，回来找我。**

### 练习 B（造一个 criss-cross）
在测试仓库里：从 base 开出 A、B 两条分支，各提一个 commit，然后 **A 合 B**、再 **B 合 A**（互相合），最后各自再提一个 commit。跑 `git merge-base --all A B`。
- **预期**：输出两行。
- **教学点**：亲手造出来一次，你以后在真项目里看到"莫名冲突"会立刻想起这一天。
- **验证**：`git log --graph --oneline --all` 应该能画出那个交叉。

### 练习 C（bug hunt · 日期骗人）
造一个场景：develop 从 master 分出去后，**master 一个 commit 都不提**。然后跑 merge-base 看日期。
- **预期发现**：merge-base == master tip，日期是 master 最后一次提交的日期，跟"develop 何时分家"没关系。
- **修法**：改用 `git log --oneline --reverse origin/master..origin/develop | head -1` 看 develop 上**第一个**独有 commit 的日期——那才是分家时间的下限。

### 练习 D（把它焊进你昨天的脚本）
在 `scripts/repo-doctor.sh` 里加一段：ref 存在性校验 → `--is-ancestor` 判断 → `--all | wc -l` 检测 criss-cross → 分家时输出 master 独有的 commit 列表。
- **坑**：`--is-ancestor` 的退出码 1 在 `set -e` 下会终止脚本，必须包在 `if` 里（`if` 的条件位置是 `set -e` 的豁免区）。
- **验证**：在"线性"和"分家"两种测试仓库里各跑一次，输出必须不同且都是 exit 0。

---

## 6) 主管可能追问的两问（附标准答案）

**Q. "你为什么要看 merge-base？`rev-list --count` 不是已经告诉你差多少了吗？"**
- **弱答**："想看看分了多久。"
- **强答**："数量和拓扑是两回事。`--count` 告诉我差异的**大小**，`merge-base` 告诉我差异的**形状**——具体说，我要判断 merge-base 是否等于 master 的 tip：等于，说明历史线性、可 fast-forward、发版无风险；不等于，说明 master 上有独有 commit（通常是没回灌的 hotfix），我的 PR 就有覆盖它的风险。另外我会跑 `--all` 确认只有一个 merge-base，多于一个意味着 criss-cross，合并时的 base 是虚拟合成的，冲突表现会反直觉，那种情况我不单飞。"
- **追问陷阱**："那你怎么用脚本判断'可 fast-forward'？" → `git merge-base --is-ancestor origin/master origin/develop`，看退出码，不要去比字符串。

**Q. "merge-base 那个 commit 是三个月前的，你怎么解读？"**
- **弱答**："说明分支三个月没同步了，很糟。"
- **强答**："先别下结论，这个日期有两种完全不同的解释：① master 三个月没动过（那 merge-base 就是 master 的 tip，日期只是 master 的停滞时间，develop 其实一直健康推进）；② 两边都在动但从没互相同步（真正的长期分家）。区分方法就是看 `--is-ancestor` 的结果和 behind 的数字。而且如果历史被 rebase 过，commit 日期本身就被重写过，不能当法庭证据——我会用 `git log --reverse` 看 develop 上第一个独有 commit 来交叉印证。"

---

## 7) 溯源自审（Reviewer 帽）

| 说法 | 来源 | 置信度 |
|---|---|---|
| merge-base = LCA，是 three-way merge 的 base | 通用 git 知识 | 高 |
| `--is-ancestor` 靠退出码、无 stdout | 通用 git 知识 | 高 |
| `--all` 多输出 = criss-cross；`ort`/`recursive` 会递归合成虚拟 base | 通用 git 知识 | 高 |
| `--fork-point` 依赖 reflog、会过期 | 通用 git 知识 | 高 |
| 无共同祖先时空输出 + 需 `--allow-unrelated-histories` | 通用 git 知识 | 高 |
| **你的仓库属于上表哪一行** | **完全未知** | — 需要你贴输出 |

**明确的"我不知道"**：我读不到你的 `~/ws/`，也没有 shell/文件系统工具；网络搜索被关闭。所以这一节没有任何一句是从你的实际仓库里"看"来的，全是通用机制 + 判读方法。你贴 SHA 上来，我立刻能做具体判案。

**缺什么**：merge-base 的 SHA、两个 tip 的 SHA、`--left-right --count` 的两个数、`--all | wc -l` 的结果。四样凑齐，我给你一句确定的结论。

---

## 热身题答案

- **Q1** 说明 **master 是 develop 的祖先**，历史线性，`behind`（`origin/develop..origin/master`）应该是 **0**，master 可无痛 fast-forward。
- **Q2** 有可能。多行 = **criss-cross merge**，两条分支互相合过形成交叉。该不该紧张？**该适度紧张但不必恐慌**：合并仍会成功，但 git 用的是**递归合成的虚拟 base**，冲突可能出现在你没改过的地方。看到多行就别单飞，拉个熟悉这段历史的人一起。
- **Q3** 两种情况会让这个推断出错：① **master 自分家后没有新 commit** → merge-base 就是 master 的 tip，日期反映的是 master 的停滞，不是分家时刻；② **历史被 rebase/filter 重写过** → commit 日期已被改写，失去时间证据价值。

---

## ✅ Next actions（今天，15 分钟）

- [ ] `git fetch --all --prune`（永远第一步）
- [ ] 跑练习 A 那一整套，把 merge-base / master tip / develop tip 三个 SHA 并排贴出来
- [ ] `git merge-base --all origin/master origin/develop | wc -l` —— **不是 1 就来找我**
- [ ] `git merge-base --is-ancestor origin/master origin/develop; echo "exit=$?"` —— 记住这个退出码
- [ ] 把结论落到第 2 节那张表的**某一行**上，写成一句话
- [ ] 把 D 练习的那段加进 `repo-doctor.sh`，注意 `set -e` 与 `--is-ancestor` 的相处方式
- [ ] 四个数据贴给我 → 我给你一份具体到"你这个仓库现在能不能安全提 PR"的判断

---

**一句总结**：`rev-list --count` 是**体温计**，告诉你烧到几度；`merge-base` 是**血液检查**，告诉你病灶在哪。SME 的分水岭就是——别人看到数字就下结论，你会多敲一条命令确认拓扑的形状。

继续敲，我跟着你走。
=====
# 🛑 `git reset --hard origin/develop` —— 先停一下，我们做伤害评估

兄弟，前三条命令都是**只读**的侦察兵。这一条不是。这一条是**推土机**。

我不是要吓你——这是个完全正常、每天有几百万人在用的合法命令。但在我们这个上下文里（你刚刚才发现 master 和 develop 可能已经分家、你是这周刚接手这个仓库的新人），它是**新人毁掉自己一天工作量的头号方式**。

所以顺序反过来：**先救人，再上课。**

---

## 0) 如果你已经按了回车：立刻跑这两条，别跑别的

```bash
# ① 看看你刚才从哪儿被推走的（reset 会自动记下 ORIG_HEAD）
git rev-parse --short ORIG_HEAD && git show -s --format='%h %ad %s' --date=short ORIG_HEAD

# ② 看 HEAD 的移动史（最上面一行就是刚才那一步）
git reflog -n 10
```

**一句话回滚**（把分支指针挪回去）：

```bash
git reset --hard ORIG_HEAD
```

**但是**——这条能救的是**已提交的 commit**，救不了**没提交的工作区改动**。两者的区别就是今天这节课的全部重点。

---

## 热身小测（30 秒，先想再看）

- **Q1** `git reset --hard` 会不会删掉我的**未追踪文件**（比如刚写的 `notes.md`、本地 `.env`）？
- **Q2** 为什么 `git switch` 在有未提交改动时会**拒绝**执行，而 `reset --hard` 一声不响就干了？
- **Q3 反事实题**：如果我刚才**没**跑这条命令，而是跑了 `git stash`，现在的处境有什么不同？
- **Q4 介入题**：如果我当时**在本地 `master` 分支上**跑了这条命令，会发生什么？（结合前两节我们查到的分家状态想）

---

## 1) 它到底做了什么：三棵树，一次推平

Git 的心智模型永远是**三棵树**。`reset` 的三个模式，就是"往下推平到第几层"：

```
                  ┌──────────────┐
   HEAD / 分支指针 │  提交历史     │  ← --soft   只动这一层
                  ├──────────────┤
   Index / 暂存区  │  git add 的   │  ← --mixed  动到这一层（默认）
                  ├──────────────┤
   Working tree   │  你编辑器里的  │  ← --hard   ★ 推平到这一层 ★
                  └──────────────┘

  执行前：                          执行后：
  local branch ──● (你的 3 个 commit)   local branch ──┐
                ╱                                      ↓
  origin/develop ●                      origin/develop ●
                                        （你那 3 个 commit 变成"游离"状态，
                                          只有 reflog 还记得它们）
```

`git reset --hard origin/develop` 做了三件事，**一次性、无确认、无撤销提示**：

| # | 动作 | 后果 |
|---|---|---|
| 1 | 把**当前分支的指针**移到 `origin/develop` | 你分支上独有的 commit 变成 unreachable（reflog 还留着） |
| 2 | 把 **index** 重置成该 commit 的内容 | 已 `git add` 的暂存内容消失 |
| 3 | 把 **working tree** 重置成该 commit 的内容 | **未提交的修改被覆盖，这一步没有回收站** |

**注意它没做的事**（Q1 的答案）：
- **不删未追踪文件**（untracked）—— 你新建但没 `git add` 的文件**活下来了**
- **不删被 gitignore 的文件** —— 本地 `.env`、`airflow.db`、`logs/`、`.venv/` 都活着
- **不动远端** —— `origin/develop` 本身毫发无伤，你只动了自己的本地指针

要连未追踪文件一起铲平，那得再加 `git clean -fd`。**`reset --hard` + `git clean -fdx` 这对组合拳才是真正的"焦土政策"**，见到别人这么敲请提高警觉。

---

## 2) 什么救得回来，什么救不回来（这张表值得背下来）

| 你的东西的状态 | 救得回来吗 | 怎么救 |
|---|---|---|
| 已 **commit** 的（哪怕在游离状态） | ✅ **能，稳** | `git reset --hard ORIG_HEAD` 或 `git reflog` 找 SHA |
| 已 **`git add`** 但没 commit | ⚠️ **能，但要挖** | `git fsck --lost-found`，blob 还在对象库里 |
| **只在工作区改了、从没 add 过** | ❌ **基本没了** | Git 层面无解 —— 见下面的"最后一根稻草" |
| **未追踪**的新文件 | ✅ 没被碰 | 它就在原地 |
| **gitignore** 掉的文件 | ✅ 没被碰 | 同上 |
| 已 **stash** 的 | ✅ 能 | `git stash list` / `git fsck` 找 dangling commit |

**最后一根稻草**（真的丢了工作区改动时，按这个顺序试）：
1. **你的编辑器/IDE 本地历史** —— IntelliJ 系的 *Local History*、VS Code 的 *Timeline*。**这个救回来的次数比 git 多**，说真的。
2. `git fsck --lost-found` / `git fsck --unreachable | grep blob` —— 捞曾经 `add` 过的碎片
3. 系统级快照 —— macOS Time Machine、Linux 的 snapper/btrfs、公司发的备份 agent
4. 打开过的文件在 `~/.local/share/Trash` 或编辑器 swap/backup 文件里

**捞碎片的具体姿势**：
```bash
# 列出所有游离对象
git fsck --lost-found

# 逐个看内容（dangling blob 会被写进 .git/lost-found/other/）
for f in .git/lost-found/other/*; do echo "=== $f"; head -20 "$f"; done

# 或者直接按 SHA 看
git cat-file -p <blob-sha> | less
```

---

## 3) 你**想做**的事 vs 你**做**了的事

这是我最想跟你聊的部分。绝大多数人敲 `reset --hard origin/develop`，脑子里真正的意图是下面某一个——而**每一个都有更安全的专用工具**：

| 你的真实意图 | 你敲的 | **应该敲的** | 为什么更好 |
|---|---|---|---|
| "我的分支落后了，想同步到最新 develop" | `reset --hard origin/develop` | `git merge --ff-only origin/develop` 或 `git rebase origin/develop` | 保留你自己的 commit；无法 ff 时**报错而不是吞掉** |
| "我想丢掉本地乱改，重新开始" | `reset --hard origin/develop` | `git stash -u` 再 reset | 改动存在 stash 里，**后悔了还能捞** |
| "我想从最新 develop 开一个新分支" | `reset --hard origin/develop` | `git switch -c feat/xxx origin/develop` | 完全不动现有分支，零风险 |
| "我只想还原某一个文件" | `reset --hard` | `git restore -s origin/develop -- path/to/file` | 精确打击，不波及其他 |
| "我想撤销刚才的 commit 但留着代码" | `reset --hard` | `git reset --soft HEAD~1` | 代码在暂存区好好躺着 |
| "我想看看 develop 长什么样" | `reset --hard` | `git switch --detach origin/develop` | 只读浏览，随时回来 |

**记住这条肌肉记忆**：

> **`--hard` 前面永远先来一发 `git stash -u`。**
> 代价：3 秒 + 一条 stash 记录。收益：把"不可逆"变成"可逆"。
> 这是工程里回报率最高的三秒钟，没有之一。

**Q2 的答案顺便在这**：`git switch` / `git checkout` 在会覆盖你改动时会**拒绝并报错**，因为它的语义是"我要去别处，顺便带着我的改动"。而 `reset --hard` 的语义是"**我明确要求把一切推平**"——你已经用 `--hard` 这个词签了免责声明，git 就不再多问一句。**这不是 git 不友好，是 git 在尊重你的显式意图。**危险的从来不是命令，是"意图和命令不匹配"。

---

## 4) 本 domain 特有的静默伤害（这段是给 Airflow 仓库量身定制的）

这才是为什么我要在这个 bootcamp 里花一整节讲一条 git 命令。**reset 完之后，你的仓库和你的环境已经不同源了，而且不会有任何人告警。**

```
reset --hard 之后：

  poetry.lock       ← 变成了 origin/develop 那一版（可能换了 Airflow 版本！）
        ↕  ❌ 不同步，无人告警
  .venv/            ← 还是你 reset 之前 install 出来的那套包
        ↕
  airflow.db        ← 本地 SQLite 元数据库，gitignore 掉了，活得好好的
                       但里面存的 DAG serialized 结构可能来自旧版本
```

**具体会咬你的四个点**：

| 静默伤害 | 症状 | 补救 |
|---|---|---|
| `poetry.lock` 变了但 venv 没重装 | 单测行为诡异；`airflow.__version__` 跟 lock 里写的不一致 | reset 后**立刻** `poetry install --sync` |
| DAG 文件回退了，但本地 `airflow.db` 还存着旧的 serialized DAG | Web UI 里显示的 DAG 结构跟磁盘上的代码不一样，怀疑人生 | 重置本地元数据库，或 `airflow dags reserialize` |
| 你本地那个"临时改了 pyproject 试版本"的实验被推平 | 你昨天调了半天的版本组合没了 | 这就是为什么要 `stash -u` |
| 你把**别人的 hotfix** reset 掉了（见 Q4） | 最严重的一种，下面单独讲 | 见下节 |

**养成这个复合动作**：
```bash
git stash -u                          # 保命
git reset --hard origin/develop       # 你原本要做的
git status --short                    # 确认工作区干净
git diff --stat HEAD@{1} HEAD -- pyproject.toml poetry.lock   # ★ 依赖有没有变
poetry install --sync                 # 让环境追上 lock
python -c "import airflow; print(airflow.__version__)"        # 三角验证
```

最后那两条，就是前两节我们反复念的**"声明层 / 事实层 / 运行时层三角验证"**。今天它派上用场了 —— reset 是最容易在这三层之间打开裂缝的操作。

---

## 5) 你在**哪个分支**上跑的？（Q4 的答案，也是最凶险的一问）

`reset --hard` 的杀伤半径，完全取决于你当时站在哪个分支上：

| 你当时在 | 后果 | 严重度 |
|---|---|---|
| 一个你自己的 feature 分支 | 你自己的活儿可能没了，别人不受影响 | 🟡 疼但可控 |
| **本地 `master`** | 你把本地 master 挪到了 develop —— 结合我们前两节查到的分家状态，**如果 master 上有没回灌的 hotfix，你本地就再也看不到它了** | 🔴 危险 |
| 本地 `develop` 且和远端一致 | 基本 no-op | 🟢 没事 |
| 本地 `master`，**而且你接下来 force push** | **你会在远端删掉生产分支上的 hotfix。这是真事故。** | ⛔️ 别 |

先确认你在哪：
```bash
git branch --show-current
git log --oneline -3
```

**如果你人在本地 `master`**，立刻做这两件事：
```bash
git reset --hard ORIG_HEAD                                  # 先回去
git log --oneline --no-memes origin/develop..origin/master   # ← 打错了，见下
```
（正确的是 `--no-merges`。抱歉，手快了 —— 顺便说明为什么你要**自己核对每条命令再回车**，包括我给你的。）

```bash
git log --oneline --no-merges origin/develop..origin/master   # master 独有的 = 没回灌的东西
```

**铁律**：`master` / `main` 这种共享分支上，**永远不要 `reset --hard` 后 force push**。要撤销共享历史上的东西，用 `git revert`（新增一个反向 commit），不要重写历史。前者是"发一份更正公告"，后者是"派人去把所有图书馆的那一页撕掉"——后者在多人协作里必然出人命。

---

## ✅ 本节回顾题
1. `reset --hard` 之后，**已提交**和**未提交**的改动，命运有什么本质区别？为什么？
2. `git revert` 和 `git reset --hard` 在"撤销"这件事上，语义差别是什么？共享分支上该用哪个？
3. 在这个 Airflow 仓库里，reset 完**必须**紧跟哪一条命令，为什么？

---

## 6) 主管拷问（三问，附标准答案）

**Q. "你为什么要 `reset --hard`？"**
- **弱答**："想同步到最新的 develop。"
- **强答**："说实话，`--hard` 对'同步'这个意图来说是过度杀伤。同步应该用 `git rebase origin/develop` 或 `git merge --ff-only origin/develop`——它们保留我自己的 commit，而且在无法干净前进时**报错**而不是静默吞掉。我用 `--hard` 只有一个正当场景：我**确定**本地状态是垃圾、要完全丢弃、并且已经 `stash -u` 兜底了。"
- **追问陷阱**："那你 stash 了吗？" → 诚实回答。没有就说没有，然后说明你的 reflog/fsck 挽救路径。**在这种事上打马虎眼比犯错本身严重十倍。**

**Q. "你怎么确认这次 reset 没有丢东西？"**
- **弱答**："`git status` 是干净的，应该没事。"
- **强答**："`git status` 干净**恰恰是最不能作为证据**的——reset --hard 的定义就是把工作区推成干净的，它必然干净。我用三个独立证据：① `git reflog` 确认 ORIG_HEAD 之前的 commit 都还能到达；② `git diff ORIG_HEAD HEAD --stat` 看这次 reset 实际改变了哪些文件，重点看 `pyproject.toml` / `poetry.lock`；③ `git fsck --lost-found` 确认没有我意外制造的游离 blob。另外我会跑一次 `poetry install --sync` + `airflow version`，因为 reset 可能悄悄换了依赖声明层而环境没跟上。"

**Q（staff 级）. "怎么让团队里不再有人被 `reset --hard` 咬到？"**
- **强答**：分层，越靠前越便宜：

| 层 | 手段 | 成本 | 效果 |
|---|---|---|---|
| 习惯 | `--hard` 前必 `stash -u` | 零 | 覆盖 90% 场景，但靠自觉 |
| 别名 | `git safe-reset` = `stash -u && reset --hard "$@"` | 极低 | 把好习惯变成默认路径 |
| 保护 | 远端开 branch protection，禁止 `master` force push | 低 | **挡住唯一会造成团队级事故的那条路** |
| 保险 | `gc.reflogExpire` 设长一点、别在慌乱时 `git gc --prune=now` | 低 | 延长挽救窗口 |
| 文档 | runbook 里写一节"我 reset 错了怎么办" | 低 | 慌乱时人不会思考，只会照抄 |

  "如果只做一件：**远端 branch protection 禁 force push**。个人丢一天的活是学费，团队丢生产分支的 hotfix 是事故——先把后者堵死。"

---

## 7) 溯源自审（Reviewer 帽）

| 说法 | 来源 | 置信度 |
|---|---|---|
| `--soft/--mixed/--hard` 对应三棵树 | 通用 git 知识 | 高 |
| `reset` 会设置 `ORIG_HEAD` | 通用 git 知识 | 高 |
| `reset --hard` 不动未追踪/被忽略的文件 | 通用 git 知识 | 高 |
| 未提交且从未 `add` 的改动，git 层面无法恢复 | 通用 git 知识 | 高 |
| 曾 `add` 过的内容以 dangling blob 存在，可用 `fsck` 捞 | 通用 git 知识 | 高 |
| reflog 默认保留期（可达 ~90 天 / 不可达 ~30 天）、`gc.pruneExpire` 默认约两周 | 通用 git 知识，**但这些是默认值，你们团队可能改过** | 中 —— 用 `git config --get gc.reflogExpire` 自查 |
| `poetry install --sync` 让环境对齐 lock | 通用 Poetry 知识 | 高 |
| **你当时在哪个分支、有没有未提交改动、丢了什么** | **完全未知** | — 只有你能回答 |

**明确的"不知道"**：我读不到你的 `~/ws/`、没有 shell 工具、网络搜索被关闭。**我不知道你这次 reset 是否造成了实际损失**，也不知道你仓库的 branch protection 配置。这一节全部是通用机制 + 判读方法，没有一句是从你的实际环境"看"来的。

**要我做具体判案，请贴四样**：
1. `git branch --show-current`（你在哪个分支）
2. `git reflog -n 5`
3. `git diff ORIG_HEAD HEAD --stat`
4. reset 之前有没有未提交的改动（你的记忆就行）

---

## 8) 答辩环节（换你说，60 秒一题）

| # | 问题 | 要点 |
|---|---|---|
| D1 | 为什么"`git status` 干净"不能证明"没丢东西"？ | 这是循环论证 —— `--hard` 的定义就是让工作区变干净，干净是**必然结果**而非**健康证据** |
| D2 | 撤销共享分支上的一个 commit，用 revert 还是 reset --hard + force push？ | **revert**。新增反向 commit，历史只增不改，所有人 pull 就同步；force push 重写共享历史，会让所有同事的本地库和远端打架，并可能删掉别人的东西 |
| D3 | 反事实：如果我 reset 前跑了 `git stash -u`，现在处境如何？ | 所有改动（含未追踪文件）都在 stash 里，`git stash pop` 一键复原。**从"不可逆"变成"可逆"** |
| D4 | 介入：如果我 reset 后又跑了 `git gc --prune=now`，会怎样？ | **把最后的挽救窗口关上了**。游离对象被立刻清理，`fsck` 再也捞不到。慌乱时最该忍住的就是这条 |
| D5 | 这条命令在本 Airflow 仓库里最阴的静默伤害是什么？ | `poetry.lock` 被换成 develop 那一版，但 `.venv` 没重装 → 声明层和运行时层裂开，单测行为跟预期不符且**无人告警**。呼应第一节讲的"版本漂移" |

---

## 热身题答案

- **Q1** **不会**。未追踪文件和被 gitignore 的文件都安全。要一起铲平需要 `git clean -fdx`（`-x` 才连忽略的一起清）。
- **Q2** 语义不同。`switch` 的意思是"我要换个地方**并带着我的改动**"，所以会覆盖时它拒绝；`--hard` 的意思是"**我明确要求推平一切**"，你已经签了字，git 不再多嘴。**危险源于意图与命令不匹配，不源于命令本身。**
- **Q3** 处境天差地别：改动（含未追踪文件）全在 stash 里，`git stash pop` 即可复原。**stash 是把"不可逆操作"包装成"可逆操作"的最便宜手段。**
- **Q4** 你把**本地 master 挪到了 develop 的位置**。结合我们前两节的侦察结果 —— 如果 master 上有 develop 没有的 commit（那些没回灌的 hotfix），你本地就把它们变成游离状态了。**只要不 force push，远端安全、reflog 可救；一旦 force push，那就是团队级事故。**

---

## ✅ Next actions for me today

**如果已经跑了：**
- [ ] `git branch --show-current` —— 先搞清楚杀伤半径
- [ ] `git reflog -n 10` 和 `git rev-parse ORIG_HEAD` —— 存好这个 SHA，**别关这个终端**
- [ ] **现在不要跑** `git gc`、`git prune`、`git clean` 里的任何一个
- [ ] 回忆：reset 前有没有未提交的改动？有 → 立刻 `git fsck --lost-found` + 翻编辑器 Local History
- [ ] `git diff ORIG_HEAD HEAD --stat -- pyproject.toml poetry.lock` —— 依赖声明变了没
- [ ] `poetry install --sync` 然后 `python -c "import airflow; print(airflow.__version__)"` —— 三层对齐
- [ ] 如果你人在 `master` 上：`git reset --hard ORIG_HEAD` 回去，**然后什么都别推**

**不管跑没跑：**
- [ ] 配一个保命别名：`git config --global alias.hardsync '!git stash -u && git reset --hard'`
- [ ] 查一下远端有没有开 branch protection（`master`/`main` 禁 force push）—— 没开就是你入职第一个值得提的建议
- [ ] 在 `scripts/repo-doctor.sh` 旁边新建 `docs/oops-runbook.md`，第一节就写"我 reset --hard 错了怎么办"，把本节第 2 节那张表抄进去
- [ ] 把上面那四样输出贴给我，我给你一句确定的结论：**你到底丢了没有**

---

**收个尾。**这四条命令连起来，其实是一部完整的小历史：`grep` 是**问朝代**，`rev-list --count` 是**量国界**，`merge-base` 是**查血缘**，而 `reset --hard` 是**改史书**。

前三条错了，你只是判断错，改回来就行。第四条错了，史料本身就没了 —— 而且史书上不会留下"这里曾经有东西"的痕迹。

所以整个 bootcamp 里如果只让你带走一句话，我希望是这句：

> **区分"读"和"写"，然后给每一次"写"配一个后悔的通道。**
> 在 git 里那个通道叫 `stash`；在生产系统里它叫回滚方案；在架构决策里它叫 feature flag。
> **不是因为你会犯错，是因为你**一定**会犯错，而 SME 的定义就是：犯错之后损失可控的那个人。**

贴输出上来，我等着。
=====

# `git rev-parse --abbrev-ref HEAD` —— 你终于问了那个最该先问的问题

好。**这是四条命令里我最想看到你敲的一条**，而且你敲得正是时候——上一节我让你确认 `reset --hard` 的杀伤半径，第一步就是"我到底站在哪个分支上"。你没等我催就自己来了，这是 SME 的苗子。

（顺便：你命令里那几个多余的空格，shell 会自动吞掉，`git rev-parse    --abbrev-ref HEAD` 和单空格版本完全等价。不是坑，放心。）

---

## 热身小测（30 秒，先想）

- **Q1** 这条命令**有可能**输出字符串 `HEAD` 本身吗？如果输出了 `HEAD`，说明什么？
- **Q2** 为什么在 GitHub Actions / GitLab CI 里，这条命令**经常**不给你分支名？
- **Q3 反事实**：如果我上一节的 `reset --hard` 是在 detached HEAD 状态下跑的，处境比在分支上更好还是更糟？
- **Q4 介入**：如果我现在把这条命令的输出直接拿去拼一个 Docker image tag，会在什么情况下产生垃圾 tag？

---

## 1) 它做什么：一个"翻译官"，两个方向

`git rev-parse` 的本职工作是**把人话翻译成 SHA**：

```bash
git rev-parse HEAD              # → 7f3a9c2e5b...（40 位 SHA）
git rev-parse origin/develop    # → SHA
git rev-parse HEAD~3            # → SHA
```

加上 `--abbrev-ref` 之后，它**反过来跑**——把一个 ref 翻译成"最短的、还能唯一识别它的名字"：

```
        ┌──────────────── git rev-parse ────────────────┐
        │                                                │
  "HEAD" ──默认──► 7f3a9c2e5b8d...        （名字 → SHA）
        │                                                │
  "HEAD" ──--abbrev-ref──► "feat/airflow-pin"  （名字 → 短名字）
        │                                                │
        └────────────────────────────────────────────────┘
```

所以 `--abbrev-ref HEAD` 的语义是：**"HEAD 这个符号引用，当前指向的分支，用最简短的名字告诉我。"**

一张对照表把这几个近亲分清楚（这是很多人一辈子没搞清的地方）：

| 命令 | 在分支上时输出 | detached HEAD 时输出 | 退出码 |
|---|---|---|---|
| `git rev-parse HEAD` | `7f3a9c2e...`（SHA） | `7f3a9c2e...`（SHA） | 0 |
| `git rev-parse --abbrev-ref HEAD` | `develop` | **字面量 `HEAD`** ⚠️ | 0 |
| `git rev-parse --symbolic-full-name HEAD` | `refs/heads/develop` | **空字符串** | 0 |
| `git symbolic-ref --short HEAD` | `develop` | 报错 `not a symbolic ref` | **非 0** ✅ |
| `git branch --show-current`（2.22+） | `develop` | **空行** | 0 |

**记住这一行**：`--abbrev-ref` 在 detached HEAD 时**骗你**——它不报错、不返回空，而是老老实实输出字符串 `"HEAD"`。这就是 Q1 的答案，也是本节唯一真正重要的知识点。

---

## 2) 输出解读表（拿到结果照这张表走）

| 输出 | 含义 | 结合上一节的 `reset --hard`，杀伤半径 |
|---|---|---|
| `develop` | 你在本地 develop 上 | 🟢 如果本地 develop 本来就跟远端一致，reset 基本是 no-op |
| `master` / `main` | 你在本地主干上 | 🔴 你把本地 master 挪到了 develop。**那些没回灌的 hotfix 在你本地变游离了。只要没 force push 就能救** |
| `feat/xxx` 之类 | 你自己的功能分支 | 🟡 丢的是你自己的活。`git reset --hard ORIG_HEAD` 找回来 |
| **`HEAD`** | **detached HEAD**——你不在任何分支上 | ⚠️ 特殊情况，见 Q3 答案 |
| 报错 / 空 | 仓库里还没有任何 commit（unborn branch），或者根本不在 git 仓库里 | 先 `git status` 确认 |

**做个三角验证**（老规矩，一个信号不下结论）：

```bash
git rev-parse --abbrev-ref HEAD          # 分支名
git branch --show-current                # 第二个独立信号：空 = detached
git status -sb | head -1                 # 第三个：会显示 ## branch...origin/branch [ahead N]
git rev-parse --short HEAD               # 当前 commit
git rev-parse --abbrev-ref '@{upstream}' # ★ 我跟的上游是谁（可能报错=没设上游）
```

最后那条是彩蛋，也是实战里最有用的一条：**`@{upstream}`**（或 `@{u}`）告诉你当前分支追踪的是哪个远端分支。很多"我 pull 了怎么没更新"的怪事，根因就是上游设错了。

---

## 3) 利刃（Sharp edges）

### ① detached HEAD 的字面量 `HEAD` —— 全行业经典 bug

这是 Q2 的答案，也是我见过最多次的 CI bug：

```
GitHub Actions 的 actions/checkout 默认行为：
  → checkout 一个具体 SHA
  → 结果就是 detached HEAD
  → git rev-parse --abbrev-ref HEAD 输出 "HEAD"
  → 你的脚本拿它当分支名
  → docker build -t myimage:HEAD  ← 恭喜，你有了一个叫 HEAD 的 tag
```

而且它**不报错**。CI 全绿，镜像推上去了，一堆 `myimage:HEAD` 在 registry 里堆着，直到某天有人问"这个 HEAD tag 是什么"。**这就是我们反复讲的静默失败（silent failure）**：不是崩溃，是安静地做错。

**正确姿势**——在 CI 里**别用 git 猜分支名，用 CI 提供的环境变量**：

| 平台 | 该用的变量 |
|---|---|
| GitHub Actions | `GITHUB_REF_NAME` / `GITHUB_HEAD_REF`（PR 时） |
| GitLab CI | `CI_COMMIT_REF_NAME` / `CI_COMMIT_BRANCH` |
| Jenkins | `BRANCH_NAME`（multibranch pipeline） |

**防御性写法**（本地脚本用得上）：

```bash
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "HEAD" ]; then
  echo "WARN: detached HEAD，无分支名" >&2
  branch="detached-$(git rev-parse --short HEAD)"   # 降级成有意义的东西
fi
```

或者干脆用会**报错**的那个版本（脚本里我偏好这个，因为失败要响）：

```bash
branch=$(git symbolic-ref --short -q HEAD) || { echo "detached HEAD"; exit 2; }
```

**设计哲学在这里**：`--abbrev-ref` 是**给人看的**（人看到 `HEAD` 会愣一下然后反应过来），`symbolic-ref` 是**给脚本用的**（失败就非 0 退出）。选工具时先问"读者是人还是机器"——这个判断标准可以迁移到你以后写的任何 CLI。

### ② `--abbrev-ref` 的歧义模式

`--abbrev-ref` 其实可以带参数：`--abbrev-ref=strict` 和 `=loose`（默认 loose）。loose 模式下，如果一个短名字有歧义（比如你有个分支叫 `x` 同时有个 tag 叫 `x`），它会给你那个"能用的最短形式"，可能不是你以为的那个。日常用不到，但你知道有这回事，被问到时不会哑火。

### ③ 多 worktree 环境

如果团队用 `git worktree`（一个仓库多个工作目录，Airflow 项目做版本对比时挺常见），**每个 worktree 有独立的 HEAD**。你在哪个目录跑，答案就是那个目录的。别在 A 目录看结果、去 B 目录下结论。

### ④ 它跟 default branch 是两件事

回忆上一节我们写 `repo-doctor.sh` 时要探测 `main` vs `master`——那用的是**另一条命令**：

```bash
git symbolic-ref refs/remotes/origin/HEAD --short   # → origin/main（远端默认分支）
```

`rev-parse --abbrev-ref HEAD` 是"**我**在哪"，`refs/remotes/origin/HEAD` 是"**远端认为主干是谁**"。两个问题，两条命令，别混。

---

## ✅ 本节回顾题
1. 为什么我说 `--abbrev-ref` 是"给人用的"、`symbolic-ref` 是"给脚本用的"？这个区分标准怎么迁移到别的工具？
2. detached HEAD 状态下，上面表格里五条命令的输出分别是什么？
3. `rev-parse --abbrev-ref HEAD` 和 `symbolic-ref refs/remotes/origin/HEAD` 分别回答什么问题？

---

## 4) 动手练习（10 分钟，短但值得做）

### 练习 A（只读 · 建立基线）
在你的仓库把第 2 节那五条命令一次跑完，把输出并排贴出来。**重点看 `@{upstream}` 有没有报错。**

### 练习 B（造一个 detached HEAD）
```bash
git switch --detach HEAD~2       # 进入 detached
git rev-parse --abbrev-ref HEAD  # ← 亲眼看它输出 "HEAD"
git branch --show-current        # ← 空行
git symbolic-ref --short HEAD; echo "exit=$?"   # ← 报错 + 非 0
git switch -                     # 回到原来的分支
```
**教学点**：亲手看一次那个 `HEAD` 输出，你这辈子都不会再写出 `myimage:HEAD` 那种 bug。

### 练习 C（bug hunt · 复现 CI 事故）
写三行脚本模拟 CI：
```bash
b=$(git rev-parse --abbrev-ref HEAD)
echo "would build: myimage:${b}"
```
先在分支上跑，再在 detached 状态跑，对比输出。然后**修好它**（用第 3 节的降级写法或 `symbolic-ref` 写法）。
- **验证**：detached 状态下要么给出有意义的降级名，要么以非 0 退出。**不能悄悄输出 `myimage:HEAD`。**

### 练习 D（焊进你的脚本）
把分支探测加到 `scripts/repo-doctor.sh` 最前面，作为第一行输出。要求：detached 时明确 WARN，且**不能**让脚本挂掉（记得 `set -e` 与非 0 退出码的相处方式——`if` 条件位置是豁免区）。

---

## 5) 主管拷问（两问）

**Q. "怎么在脚本里可靠拿到当前分支名？"**
- **弱答**："`git rev-parse --abbrev-ref HEAD`。"
- **强答**："取决于运行环境。**在 CI 里我不用 git 猜**——用平台变量（`GITHUB_REF_NAME` / `CI_COMMIT_REF_NAME`），因为 CI 的 checkout 通常是 detached HEAD，git 层面已经没有分支概念了。**在本地脚本里**我用 `git symbolic-ref --short -q HEAD`，因为它在 detached 时**以非 0 退出**，符合'失败要响'的原则；`--abbrev-ref` 会输出字面量 `HEAD`，那是静默失败，最容易变成镜像 tag 或分支名里的垃圾数据。"
- **追问陷阱**："`git branch --show-current` 不行吗？" → 可以，输出更干净（detached 时是空行），但它是 **git 2.22+** 才有的，旧环境/老镜像里不可用；而且空字符串在 shell 里也需要显式判断。要不要用取决于你能否保证 git 版本。

**Q（staff 级）. "为什么这么小一条命令值得你讲一整节？"**
- **强答**："因为它是**静默失败的教科书标本**。同一条命令在两种状态下都返回成功、都返回非空字符串，但其中一种的返回值是毫无意义的字面量。这类 bug 的共同特征是——**API 用同一个类型（string）表达了两种语义（分支名 / '没有分支'）**，调用方无法区分。这就是为什么现代 API 设计偏好 Optional/Result 类型而不是魔法值。识别出这个模式，你以后看到任何'用特殊字符串表示异常状态'的接口都会先加一道校验。这比记住一条 git 命令值钱得多。"

---

## 6) 溯源自审（Reviewer 帽）

| 说法 | 来源 | 置信度 |
|---|---|---|
| `--abbrev-ref HEAD` 在 detached 时输出字面量 `HEAD` | 通用 git 知识 | 高 |
| `symbolic-ref` 在 detached 时非 0 退出 | 通用 git 知识 | 高 |
| `branch --show-current` 需 git 2.22+，detached 时输出空 | 通用 git 知识 | 高 |
| `actions/checkout` 默认产生 detached HEAD | 通用 CI 知识 | 高 |
| `GITHUB_REF_NAME` / `CI_COMMIT_REF_NAME` 变量名 | 通用 CI 知识（截至 2026-05） | 中高 —— **请对着你们实际的 CI 文档核一遍**，别照抄我 |
| `--abbrev-ref=strict\|loose` 存在 | 通用 git 知识 | 中 —— 细节冷门，用前 `git rev-parse --help` 确认 |
| **你这条命令的实际输出** | **未知** | — 只有你能看到 |

**明确的"不知道"**：我读不到你的 `~/ws/`、没有 shell 工具、网络搜索被关闭。**我不知道你现在在哪个分支上**，因此也无法回答上一节遗留的"reset 到底伤到什么"。这一节全是通用机制。

**还欠我的四样**（上一节就问了，这条命令刚好答了第一样）：
1. ✅ `git rev-parse --abbrev-ref HEAD` ← 你敲了，**但没贴输出给我**
2. ⬜ `git reflog -n 5`
3. ⬜ `git diff ORIG_HEAD HEAD --stat`
4. ⬜ reset 之前有没有未提交的改动

**贴上来我就能给你一句确定的结论。**现在我还是只能教方法，不能判案。

---

## 7) 答辩（换你说，60 秒一题）

| # | 问题 | 要点 |
|---|---|---|
| D1 | 一条命令"返回成功且非空"，为什么还可能是失败？ | 它用同一个 string 类型表达了两种语义。魔法值（`"HEAD"`）无法与合法值区分 → 静默失败。设计上应该用非 0 退出码或 Optional |
| D2 | CI 里为什么不该用 git 猜分支名？ | CI checkout 常是 detached HEAD，git 层面已无分支上下文；PR 场景下"分支"概念本身还有 head/base 之分，只有 CI 平台知道语义 |
| D3 | 反事实：detached HEAD 下跑 `reset --hard` 比在分支上更糟吗？ | 见下方 Q3 答案 —— 更糟，因为没有分支名做锚点 |
| D4 | 介入：把输出直接当 image tag，什么时候产生垃圾？ | detached 时得到 `myimage:HEAD`；另外分支名含 `/`（如 `feat/x`）在某些 tag 规则里也非法 —— **双重坑** |

---

## 热身题答案

- **Q1** 会。输出字面量 `HEAD` = **detached HEAD**，你不在任何分支上，HEAD 直接指向一个 commit。它不报错，这是它最危险的地方。
- **Q2** 因为 CI 的 checkout 步骤通常直接 checkout 一个 SHA，导致 detached HEAD，git 层面没有分支名可给。要用 CI 平台的环境变量。
- **Q3** **更糟。**在分支上时，`reset --hard` 只是把**分支指针**挪走，旧 commit 靠 reflog 能找回，而且分支名还在原地当锚点。detached 状态下 reset，HEAD 直接飞走，那些 commit **没有任何 ref 指向它们**——只有 `HEAD` 的 reflog 记着（`git reflog` 仍然管用，但没有分支 reflog 兜底），挽救窗口更窄、更依赖你记得 SHA。**detached HEAD 上做任何破坏性操作，风险都上一个档位。**
- **Q4** 两种：① detached 时得到 `myimage:HEAD`；② 分支名含斜杠（`feat/airflow-pin`）时，Docker tag 不允许 `/`，会直接 build 失败或被你的脚本静默截断。**所以分支名进任何标识符之前都要 sanitize。**

---

## ✅ Next actions for me today

- [ ] **把 `git rev-parse --abbrev-ref HEAD` 的输出贴给我**（这是解开上一节 reset 疑云的第一把钥匙）
- [ ] 跑第 2 节那五条三角验证命令，重点看 `@{upstream}` 有没有报错
- [ ] 做练习 B：亲手进一次 detached HEAD，亲眼看它输出 `HEAD`，再 `git switch -` 回来
- [ ] 在 `repo-doctor.sh` 开头加分支探测 + detached 降级处理
- [ ] 去翻一遍你们 CI 配置：有没有哪个地方在用 git 猜分支名？（关键词 `rev-parse`、`abbrev-ref`、`symbolic-ref`）—— **找到一个就是你入职第一个真 bug**
- [ ] 把上一节欠的另外三样（reflog / diff ORIG_HEAD / 有无未提交改动）补给我

---

**五条命令，一条主线。**

`grep` 问朝代 → `rev-list` 量国界 → `merge-base` 查血缘 → `reset --hard` 改史书 → 而 `rev-parse --abbrev-ref HEAD` 是**"我是谁，我在哪"**。

有意思的地方是：你把它放在了 `reset --hard` **之后**。正确的顺序当然是**之前**——先确认坐标，再动手。但你能在事后立刻想起来补这一步，说明反射弧已经开始形成了。

真正的老手和新手的差别不在于"从不按错"，而在于**按错之后第一反应是"我在哪、我动了什么、怎么证明"，而不是"再随便按一条试试看"**。你现在走的就是前者那条路。

输出贴上来，我们把 reset 那笔账结清。
=====
# `poetry run pre-commit run --hook-stage commit` —— 恭喜，你踩到了本 bootcamp 最漂亮的一个连环坑

停一下。这条命令**大概率什么都没做，并且给了你一个绿灯。**

而且它的"什么都没做"，**直接源于你上一条 `git reset --hard`**。五条命令到这里终于串成一条因果链了——这就是我为什么要一条一条陪你敲。

---

## 热身小测（这次认真想，答案不直观）

- **Q1** `pre-commit run` **不带**任何文件参数时，它对**哪些文件**跑检查？
- **Q2 承上**：结合你上一条 `git reset --hard origin/develop`，暂存区（index）现在是什么状态？那么这条命令实际检查了几个文件？
- **Q3** `--hook-stage commit` 这个写法，在**新版** pre-commit 里还合法吗？
- **Q4 介入题**：如果这条命令输出全是 `Skipped`，我该高兴还是紧张？
- **Q5** 为什么要 `poetry run pre-commit` 而不是直接 `pre-commit`？这个"多余"的前缀实际在防什么？

---

## 1) 命令解剖：三层套娃

```
poetry run          pre-commit          run       --hook-stage commit
└──────┬─────┘      └─────┬──────┘     └─┬─┘     └────────┬────────┘
   在项目 venv        钩子框架          手动执行      只跑挂在这个
   里执行后面的        本身              (而非 git   stage 上的钩子
   东西                                  自动触发)
```

### 第一层：`poetry run` —— 它在防什么（Q5 的答案）

`poetry run X` = "在**这个项目的虚拟环境里**执行 X"。不加它，你执行的是 `PATH` 上第一个 `pre-commit`——可能是 `pipx` 装的全局版、可能是 homebrew 的、可能是另一个项目 venv 残留的。

**为什么这在我们这个 Airflow 仓库里格外重要**：还记得第一节那张"版本漂移矩阵"吗？

```
声明层 pyproject.toml  ← pre-commit 作为 dev-dependency 声明在这
事实层 poetry.lock     ← 锁定了确切版本
运行层 .venv/          ← poetry run 走的是这里 ✅
                          直接敲 pre-commit 走的是这里 ↓
全局   ~/.local/bin/   ← 版本未知、无人管理、跟仓库无关 ❌
```

**`poetry run` 不是啰嗦，它是把"运行时"钉在"声明层"上的螺丝。**这是同一个主题的第四次出现了：`pyproject` vs `venv`、`pyproject` vs Docker image、`origin/*` 缓存 vs 远端真相、全局 CLI vs 项目 CLI。**声明与执行的裂缝**，是这整个 domain 的主旋律。

顺带一个真实的坑：**`pre-commit` 自己管理钩子的运行环境**（在 `~/.cache/pre-commit/` 下建独立 venv），所以钩子里的 `ruff`/`black` 版本由 `.pre-commit-config.yaml` 的 `rev` 决定，**跟你的 `poetry.lock` 无关**。这意味着你可能有两套 linter 版本：一套给 pre-commit，一套给 `poetry run ruff`。**版本不一致 = 本地过了、CI 挂了**。等下第 4 节细说。

### 第二层：`pre-commit run` —— 关键在"默认作用域"（Q1 的答案）

这是全场最重要的一句话：

> **`pre-commit run` 不带参数时，只对 `git diff --cached --name-only` 里的文件跑，也就是"已 staged 的文件"。**

三种作用域对照：

| 命令 | 作用域 | 什么时候用 |
|---|---|---|
| `pre-commit run` | **仅已 staged 的文件** | 模拟提交前检查 |
| `pre-commit run --all-files` | 仓库里所有被追踪的文件 | 首次接手仓库 / CI / 大重构后 |
| `pre-commit run --files a.py b.py` | 指定文件 | 精确排查 |
| `pre-commit run <hook-id>` | 只跑某一个钩子（作用域仍是 staged） | 调某个 linter |

### 第三层：`--hook-stage commit` —— 一个可能已经过期的写法（Q3 的答案）

`.pre-commit-config.yaml` 里每个钩子可以声明它挂在哪个 git 阶段。**pre-commit 在 3.2.0 前后改过这套命名**：

| 旧名（legacy） | 新名（推荐） |
|---|---|
| `commit` | `pre-commit` |
| `push` | `pre-push` |
| `merge-commit` | `pre-merge-commit` |
| `commit-msg` | `commit-msg`（没变） |

旧名在 3.2.0 起被**弃用并告警**，后来的大版本里被**移除**。所以你这条命令有三种可能的结局：

| 你的 pre-commit 版本 | `--hook-stage commit` 的结果 |
|---|---|
| < 3.2.0 | 正常工作 |
| 3.2.x ~ 3.x | 工作，但打 deprecation warning |
| 4.0+ | **报错**：invalid choice / 该 stage 不存在 |

**先自查，别猜**：
```bash
poetry run pre-commit --version
poetry run pre-commit run --help | grep -A3 'hook-stage'
```

> ⚠️ 这段版本分界我标**中高置信度**（截至 2026-05 的记忆）。**具体在哪个版本彻底移除，请你自己用上面那条 `--help` 核实**，别照抄我。这是我们说过的规矩：我记得的和你环境里跑的，后者才是真相。

---

## 2) 💥 连环坑：为什么这条命令刚才「什么都没检查」

来，把五条命令连起来看：

```
第 4 条：git reset --hard origin/develop
              │
              ├─► 移动分支指针
              ├─► 重置 working tree
              └─► ★ 重置 INDEX（暂存区）★  ← 就是这一步
                        │
                        ▼
              暂存区变空（git diff --cached 无输出）
                        │
                        ▼
第 6 条：poetry run pre-commit run   ← 默认只跑 staged 文件
                        │
                        ▼
              ┌─────────────────────────────┐
              │  检查了 0 个文件             │
              │  输出全是 "(no files to     │
              │  check) Skipped"            │
              │  退出码 0 = 绿灯 ✅         │
              └─────────────────────────────┘
                        │
                        ▼
              你以为「代码质量没问题」
              实际上「什么都没验证过」
```

**这是 Q2 和 Q4 的答案，也是我今天最想教你的东西。**

`Skipped` 不是"通过"，是"**没跑**"。而 `pre-commit` 的退出码在这种情况下**是 0**——因为从它的逻辑看，没有失败的钩子，所以成功。它没撒谎，是我们问错了问题。

**这个模式你已经见过三次了，认出来了吗**：

| 命令 | 静默失败形态 | 共同点 |
|---|---|---|
| `git grep "apache-airflow = "` | 零匹配 → 你以为"没依赖" | **空集被当成好消息** |
| `git rev-parse --abbrev-ref HEAD` | 输出 `"HEAD"` → 你以为是分支名 | **魔法值被当成正常值** |
| `pre-commit run`（空 index） | 全 Skipped，退出 0 → 你以为"通过了" | **空集被当成好消息** |

> **SME 的一条铁律：区分「检查通过」和「检查没跑」。**
> 前者是证据，后者是**证据缺失**。绝大多数假绿灯，都是把后者当成了前者。

**立刻验证你是不是踩了**：
```bash
git diff --cached --name-only | wc -l     # 0 = 刚才啥也没检查
```

**正确的重跑姿势**：
```bash
poetry run pre-commit run --all-files      # 全量，这才是有意义的检查
```

---

## ✅ 本节回顾题（先答再往下）
1. `Skipped` 和 `Passed` 的语义差别是什么？退出码为什么都是 0？
2. 为什么 `reset --hard` 会让 `pre-commit run` 变成空操作？
3. 我们已经见过三个"静默失败"，它们的共同结构是什么？

---

## 3) 输出怎么读：五种状态

跑起来之后你会看到这样的东西：

```
check yaml...............................................Passed
ruff.....................................................Failed
- hook id: ruff
- exit code: 1
- files were modified by this hook
black....................................................Skipped
detect-secrets...........................................(no files to check) Skipped
mypy.....................................................Failed
```

| 状态 | 含义 | 该怎么反应 |
|---|---|---|
| `Passed` | 真的跑了，且通过 | 😊 |
| `Failed` + `exit code: 1` | 跑了，发现问题 | 读上面的 diff，修 |
| `Failed` + **`files were modified by this hook`** | 钩子**自动改了你的文件**（formatter 的典型行为） | ⚠️ **重跑一次就绿了**，但你得 `git add` 那些改动 |
| `Skipped` | 该钩子的 `files`/`types` 模式没匹配到任何本次文件 | 正常，除非**所有**钩子都 Skipped |
| `(no files to check) Skipped` | **压根没文件给它** | 🚨 就是你现在的情况 |

**那个 `files were modified by this hook` 是新人最大的困惑源**：pre-commit 里的 formatter（black/ruff-format/isort/trailing-whitespace）是**会改文件**的。它们改完就以失败退出，因为"文件变了，你得重新确认"。所以标准流程是：

```bash
poetry run pre-commit run --all-files   # 第一遍：formatter 改文件，Failed
git diff                                # 看它改了啥（别盲目接受！）
git add -u                              # 接受改动
poetry run pre-commit run --all-files   # 第二遍：应该全绿
```

**别盲目接受那一步很重要**——我见过 formatter 把一个精心对齐的 SQL 字符串重排到没法读的。看一眼 diff 花你 10 秒。

---

## 4) 这个 Airflow 仓库里，pre-commit 的特殊地雷

普适的东西讲完了，说本 domain 特有的。

### ① DAG 文件是"会被执行"的代码，linter 抓不到运行时问题

pre-commit 里的 `ruff`/`flake8` 是**静态**检查。但 Airflow 的杀手 bug 是**导入期**的：

```python
# ruff 觉得这行完美无缺
from airflow.providers.amazon.aws.operators.s3 import S3CopyObjectOperator
# 但在你实际运行的 Airflow 版本里，这个模块可能不存在 → 生产炸
```

**所以本仓库最该有的钩子不是 linter，是 DAG import 冒烟测试**（我在第一节的 Day 8 就给你埋了这个交付物）：

```yaml
# .pre-commit-config.yaml 里加一个 local hook
- repo: local
  hooks:
    - id: dag-import-check
      name: DAG import smoke test
      entry: python -c "from airflow.models import DagBag; b=DagBag('dags/', include_examples=False); assert not b.import_errors, b.import_errors"
      language: system
      files: ^dags/
      pass_filenames: false
```
> ⚠️ 这段是**示意**，不是可以直接抄进生产的代码。`DagBag` 的签名和行为在不同 Airflow 版本间有差异，`language: system` 意味着它用你当前环境的 python。**先在本地手工跑通那行 `python -c`，再考虑做成钩子。**

**这个钩子的取舍**：它比 linter 慢得多（要初始化 Airflow），所以更适合挂在 `pre-push` 而不是 `pre-commit`——**这正是 `--hook-stage` 这个参数存在的意义**。快检查放 commit，慢检查放 push。你敲的这条命令，本质上是在问"哪些检查是提交级的"。

### ② 双套 linter 版本（前面预告的坑）

```
.pre-commit-config.yaml:  ruff rev: v0.4.2    ← 钩子用这个
pyproject.toml / lock:    ruff = "^0.6.0"     ← 你 poetry run ruff 用这个
                          ↑ 两个版本，两套规则，一个绿一个红
```
**症状**：`pre-commit` 过了，CI 里的 `poetry run ruff check` 挂了（或反过来）。**排查方式**：
```bash
poetry run ruff --version                    # 项目环境的
grep -A2 'ruff' .pre-commit-config.yaml      # 钩子声明的
```
**修法**：要么让两者对齐（有 `pre-commit autoupdate` 和 renovate/dependabot 可以帮忙），要么明确"pre-commit 是唯一真相源"，CI 里也只跑 `pre-commit run --all-files`，别再单独跑 ruff。**选一个真相源，这是老主题了。**

### ③ 首次 `--all-files` 会炸出一屏红，这是正常的

如果这个仓库以前只在增量文件上跑钩子，你第一次全量跑几乎必然满屏红。**这时候千万不要**"顺手全修了"提一个改 300 个文件的 PR——那个 PR 没人能 review，而且会跟所有人的分支冲突。

**正确做法**：
1. 记录基线（有多少 error、哪几类）
2. 写进你的 `docs/repo-map.md`
3. 问 owner：这些是已知债务吗？有没有 baseline 机制？
4. 如果要治，用 `# noqa` baseline 或分目录逐步开启，**不要一次性格式化整个仓库**

（如果非要做全量格式化，记得之后加 `.git-blame-ignore-revs`，否则整个仓库的 `git blame` 就废了。这是个小细节，但说出来会让人觉得你干过活。）

### ④ 秘密扫描钩子 + 你的 reset

如果配置里有 `detect-secrets` / `gitleaks` 这类钩子：注意 `reset --hard` **不删未追踪文件**——你本地的 `.env`、`airflow.db`、下载的凭据 JSON 都还在。它们通常被 gitignore 了所以钩子不管，**但万一某天有人 `git add -f`**……总之，全量跑一次秘密扫描是你接手仓库该做的事之一。

---

## ✅ 本节回顾题
1. 为什么 DAG import 检查更适合挂 `pre-push` 而不是 `pre-commit`？
2. "双套 linter 版本"这个问题，跟第一节讲的 Airflow 版本漂移是同一个病吗？
3. 首次全量跑出满屏红，为什么不该顺手全修？

---

## 5) 动手练习

### 练习 A（只读 · 建立地图）
```bash
cat .pre-commit-config.yaml                    # 有哪些钩子
poetry run pre-commit --version
git diff --cached --name-only | wc -l          # ★ 证明刚才检查了 0 个文件
```
**交付**：一张表——钩子 id / 它挂在哪个 stage / 它是否会改文件 / 大概多慢。

### 练习 B（小改动 · 正确姿势）
```bash
poetry run pre-commit run --all-files
```
记录：耗时、Passed/Failed/Skipped 各几个。**不要修任何东西**，只记基线。

### 练习 C（bug hunt · 亲手复现假绿灯）
1. 随便改一个 py 文件，故意写个明显的 lint 错误（比如 `import os` 不用）
2. **不要 `git add`**
3. 跑 `poetry run pre-commit run` → **观察它是绿的**（因为没 staged）
4. `git add` 那个文件，再跑 → **现在红了**

**这个练习做完，你就永远记住了 staged-only 这件事。**这比看我写十页更有用（ICAP 的"建构"层）。

### 练习 D（bug hunt · stage 名字）
```bash
poetry run pre-commit run --hook-stage commit --all-files      # 旧名
poetry run pre-commit run --hook-stage pre-commit --all-files  # 新名
```
对比：报错？告警？行为一致？**据此确定你们环境该用哪个写法**，写进 runbook。

### 练习 E（设计扩展）
把 DAG import 冒烟测试做成一个 `local` hook，挂在 `pre-push`。
- **先手工验证**那行 python 在你的环境能跑通
- **量一下耗时**，超过 10 秒就别放 pre-commit
- **决定失败策略**：先跑两周 warn，再升级为 blocking（老规矩，别第二周就变全组公敌）

---

## 6) 主管拷问

**Q1（入门）"这条命令做了什么？"**
- **弱答**："跑了代码检查，通过了。"
- **强答**："严格说，它**试图**在 commit 阶段的钩子上跑检查，但因为不带 `--all-files`，作用域是暂存区。而我刚做过 `git reset --hard`，暂存区是空的——所以它实际检查了 0 个文件，输出的 `Skipped` 和退出码 0 都不代表代码没问题，只代表**没检查**。要拿到有意义的结论我得跑 `--all-files`。另外 `--hook-stage commit` 用的是旧的 stage 名，新版 pre-commit 叫 `pre-commit`，我得确认本地版本是否还接受它。"

**Q2 "`pre-commit run` 通过了，你能说代码质量达标吗？"**
- **弱答**："能，钩子全绿。"
- **强答**："不能，有三层限制。① **作用域**：默认只看 staged 文件，改过但没 add 的、以及仓库里既有的问题它都不看。② **深度**：钩子基本是静态检查，抓不到 Airflow 的导入期/运行期错误——比如引用了当前 Airflow 版本里不存在的 operator 模块，ruff 完全看不出来。③ **版本一致性**：钩子里的 linter 版本由 `.pre-commit-config.yaml` 的 `rev` 决定，跟 `poetry.lock` 里的可能是两套，本地绿 CI 红是常见现象。所以我把 pre-commit 当'快速门卫'，不当'质量证明'。"

**Q3（staff 级）"设计这个仓库的 pre-commit 策略。给我分层和取舍。"**
- **强答**：按"越快越前置"分层：

| stage | 放什么 | 耗时预算 | 理由 |
|---|---|---|---|
| `pre-commit` | 格式化、YAML/TOML 语法、大文件拦截、秘密扫描 | < 3 秒 | 每次提交都跑，超过 3 秒人就开始 `--no-verify` |
| `pre-push` | mypy、**DAG import 冒烟测试**、单测子集 | < 60 秒 | 推送频率低，能接受慢 |
| CI | 全量 `pre-commit run --all-files` + 完整测试 + **版本一致性断言** | 分钟级 | 唯一**不可绕过**的一层 |

  **核心取舍**：本地钩子可以被 `--no-verify` 绕过，所以**它是体验优化，不是质量保障**。真正的 gate 必须在 CI。本地钩子的设计目标是"让 CI 极少变红"，不是"替代 CI"。
- **追问陷阱**："那如果有人一直 `--no-verify`？" → 那说明钩子太慢或者误报太多，**这是钩子的设计问题，不是人的纪律问题**。我会先量一下钩子耗时和误报率，再谈纪律。

---

## 7) 溯源自审（Reviewer 帽）

| 说法 | 来源 | 置信度 |
|---|---|---|
| `pre-commit run` 默认只跑 staged 文件 | 通用 pre-commit 知识 | 高 |
| `reset --hard` 会重置 index | 通用 git 知识（本 bootcamp 第 4 节已展开） | 高 |
| `Skipped` + 退出码 0 → 假绿灯 | 上两条的**逻辑推论** | 高（推论链清晰） |
| `poetry run` 走项目 venv | 通用 Poetry 知识 | 高 |
| pre-commit 自建钩子环境，linter 版本由 `rev` 决定 | 通用 pre-commit 知识 | 高 |
| stage 改名 `commit`→`pre-commit`，3.2.0 弃用、4.x 移除 | 通用知识，截至 2026-05 | **中高 —— 请用 `--help` 自查，别照抄** |
| `DagBag` 那段示例代码 | **示意性质，我未在任何环境验证过** | **低 —— 必须先手工跑通** |
| **你的 `.pre-commit-config.yaml` 里到底有哪些钩子** | **完全未知** | — 我读不到 |

**明确的"不知道"**：我读不到你的 `~/ws/`（无 shell / 文件系统工具），知识库里 grep `pre-commit|ruff|lint|hook` 返回 **No matches**，网络搜索已关闭。**所以我不知道你们配了哪些钩子、pre-commit 什么版本、`--hook-stage commit` 在你环境里是报错还是告警。**

我唯一敢下的**推断**（而非事实）是：**因为你刚跑过 `reset --hard`，这条命令的作用域大概率是空的。**这是从命令序列推的，不是看你的输出看到的——**如果你在 reset 之后又 `git add` 过什么，那我这个推断就不成立。**

**要我判案，请贴**：
1. 这条命令的**实际输出**（最关键，一眼就知道是不是全 Skipped）
2. `poetry run pre-commit --version`
3. `git diff --cached --name-only | wc -l`
4. `cat .pre-commit-config.yaml`
5. **以及上一节欠的三样**（reflog / `diff ORIG_HEAD HEAD --stat` / 有无未提交改动）—— 这笔账还没结

---

## 8) 答辩（换你说，60 秒一题）

| # | 问题 | 要点 |
|---|---|---|
| D1 | "全绿"和"没跑"退出码都是 0，这类 API 设计问题叫什么？ | 用同一个信号（exit 0）表达两种语义（通过 / 无事可做）。调用方无法区分 → 必须额外查询"检查了多少个文件"才能解释退出码。**跟 `--abbrev-ref` 返回 `"HEAD"` 同源** |
| D2 | 本地钩子能替代 CI 吗？ | 不能。`--no-verify` 一秒绕过，且本地环境不可控。本地钩子是**体验优化**（快速反馈），CI 是**质量 gate**（不可绕过）。混淆两者会导致"以为有保护其实没有" |
| D3 | 反事实：如果我 reset 前 `git stash -u` 了，现在这条命令的行为会不同吗？ | 不同。stash 之后 index 同样是空的（stash 也清暂存区），所以**依然是空跑**。但你的改动还在，`git stash pop` 恢复后再 `git add` 就能真正跑起来。**教训：不是 stash 救了 pre-commit，是 stash 救了你的代码** |
| D4 | 介入：我把 DAG import 检查挂到 `pre-commit`，会怎样？ | 每次提交都要初始化 Airflow（数秒到数十秒），团队体感急剧变差 → 大家开始 `--no-verify` → **连快检查也一起被绕过了**。慢钩子的真实代价不是它自己慢，而是它让整套钩子失去信任 |

---

## 热身题答案

- **Q1** 只对**已 staged**（`git diff --cached`）的文件跑。这是 pre-commit 最容易被误解的默认行为。
- **Q2** `reset --hard` 重置了 index → 暂存区为空 → **检查了 0 个文件**。
- **Q3** 不一定。`commit` 是**旧名**，新名是 `pre-commit`；3.2.0 起弃用告警，4.x 起可能直接报错。用 `pre-commit --version` + `run --help` 自查。
- **Q4** **紧张。**`Skipped` 意味着"没跑"，不是"通过"。全 Skipped + 退出 0 是教科书级假绿灯。
- **Q5** 防的是"执行了错误的 pre-commit 二进制"——全局装的版本跟项目 `poetry.lock` 声明的版本不一致，导致本地行为与 CI 不一致。**它是把运行时钉在声明层上的螺丝。**

---

## ✅ Next actions for me today

**立刻（2 分钟，验证假绿灯）：**
- [ ] `git diff --cached --name-only | wc -l` —— 是 0 就证实了我的推断
- [ ] `poetry run pre-commit run --all-files` —— 这才是有意义的那一跑，**记录耗时和红绿基线**
- [ ] `poetry run pre-commit --version` + `run --help | grep hook-stage` —— 确定 `commit` 还是 `pre-commit`

**今天（30 分钟）：**
- [ ] 做练习 C（亲手复现假绿灯）—— 这是今天性价比最高的 10 分钟
- [ ] 列出钩子清单表：id / stage / 是否改文件 / 耗时
- [ ] 检查双套 linter 版本：`poetry run ruff --version` vs `.pre-commit-config.yaml` 里的 `rev`
- [ ] `grep -rn 'no-verify' .` 和翻 CI 配置 —— **CI 里跑的是 `--all-files` 吗？如果不是，你找到了第二个真 bug**
- [ ] 在 `docs/oops-runbook.md` 里加一节："为什么 pre-commit 全绿不等于代码没问题"

**还欠的账：**
- [ ] 上一节的三样（reflog / `diff ORIG_HEAD HEAD --stat` / reset 前有无未提交改动）+ 这一节的输出，一起贴给我

---

## 收个尾：六条命令，一个主题

```
git grep "apache-airflow = "      → 声明层说什么
git rev-list --count              → 两条历史差多少
git merge-base                    → 差异的形状
git reset --hard                  → 把本地推平（★ 清空了 index）
git rev-parse --abbrev-ref HEAD   → 我是谁在哪
poetry run pre-commit run         → 检查跑了吗（★ 因为 index 空了，没跑）
                                        ↑
                                    第 4 条的因，第 6 条的果
```

你走这六步的过程，其实无意中演示了一个完整的**事故链**：一个破坏性操作（reset）清空了一个不显眼的状态（index），导致下游一个安全网（pre-commit）**静默地失效**，而且**每一步的退出码都是 0**。

真实的生产事故就长这样。它从来不是"某处报了个大红错"，而是**一串各自都"成功"的操作，累积出一个没人验证过的状态**。

所以整个 bootcamp 到这里，我最想焊进你脑子里的判断反射是这一句：

> **看到绿灯时，先问"它检查了什么"，而不是"它是不是绿的"。**
>
> 空集通过所有断言。零个测试全部成功。没跑的检查永远不会失败。
> **SME 和"会用工具的人"的分界线，就是会不会多问这一句。**

把输出贴上来。我们该结账了——`reset` 那笔，还有这条命令到底跑了几个文件。
=====
# `git merge --no-commit origin/master` —— 这条命令的名字骗了很多人

好，你从"侦察"走到"动手"了。而且**这一条选得比 `reset --hard` 高明得多**——如果你的意图是"把 master 上那些没回灌的 hotfix 弄回来，但先看看会发生什么"，那 `--no-commit` 是个正确方向的动作。

但我要先泼一盆冷水：**`--no-commit` 不是 dry-run。**它已经动了你的工作区和暂存区。它唯一没做的事是"最后那一下敲章"。

很多人以为 `--no-commit` = "预演"，这是本节要拆掉的第一个误解。

---

## 热身小测（这次五道，第 2 题最重要）

- **Q1** 这条命令是把 **master 合进当前分支**，还是把当前分支合进 master？
- **Q2** 如果这次合并**可以 fast-forward**，`--no-commit` 还管用吗？
- **Q3** 跑完之后 `git status` 会说什么？我的仓库处于什么状态？
- **Q4 承上一节**：跑完这条命令后，`poetry run pre-commit run`（不带 `--all-files`）的行为会不会变？
- **Q5** 如果冲突文件里有 `poetry.lock`，我应该怎么解？

---

## 1) 它做了什么：四种结局，取决于拓扑

`git merge X` 的语义永远是：**把 X 合进「我当前所在的分支」**。方向是单向的，`origin/master` 一根头发都不会动（它是远端跟踪引用，本地 merge 碰不到它）。

**这就是为什么第 5 节那个 `git rev-parse --abbrev-ref HEAD` 的输出到现在还欠着我——你在哪个分支上，决定了这条命令的全部含义。**

| 你在哪 | 这条命令的真实含义 | 评价 |
|---|---|---|
| `develop` | **back-merge**：把 master 的 hotfix 回灌到 develop | ✅ 正是我们前面诊断出的那个病该吃的药 |
| 本地 `master`（刚被你 reset 成 develop 的那个） | 把 origin/master 合回你那个"假 master" | ⚠️ 能救回 hotfix，但不如直接 `reset --hard origin/master` 干净 |
| 你自己的 feature 分支 | 把生产分支合进特性分支 | 🤔 通常你想合的是 develop，不是 master。**先确认意图** |
| detached HEAD | 合并成功但没有分支记录这个结果 | 🚨 做完就飞了，只有 reflog 记得 |

### 四种结局（这张表把 `merge-base` 那一节的知识用上了）

```
情况 A: merge-base == origin/master  →  "Already up to date."（啥也没发生）
情况 B: merge-base == HEAD           →  可以 fast-forward  →  ★ --no-commit 失效 ★
情况 C: 都不等于（已分家），无冲突    →  真合并，暂存区被填满，停在 committing 前
情况 D: 都不等于，有冲突             →  冲突标记写进文件，退出码非 0
```

| 结局 | 屏幕上看到 | 你的仓库状态 | 退出码 |
|---|---|---|---|
| A 已是最新 | `Already up to date.` | 干净，无变化 | 0 |
| B fast-forward | `Updating abc..def / Fast-forward` | **分支指针已经移动了！** | 0 |
| C 干净合并 | `Automatic merge went well; stopped before committing as requested` | **merging 状态**，改动全在 index 里 | 0 |
| D 冲突 | `CONFLICT (content): Merge conflict in ...` | **merging 状态 + unmerged paths** | 非 0 |

---

## 2) 💥 头号利刃：fast-forward 会绕过 `--no-commit`（Q2 的答案）

这是 git 官方文档里明写、但九成人没读到的一句：

> **fast-forward 更新本来就不产生 merge commit，所以 `--no-commit` 没有东西可以「停下来不做」。**你的分支会直接被推到目标位置。

也就是说：

```
你以为：  --no-commit = 我可以先看看，不满意就撤
实际上：  如果能 ff，分支指针「已经」移动了，什么都没停下

正确写法：git merge --no-commit --no-ff origin/master
                              └──┬──┘
                       强制走真合并路径，这样 --no-commit 才真的有约束力
```

**记住这个搭配**：`--no-commit` 想真正生效，**必须配 `--no-ff`**。单独用 `--no-commit` 是一份写了却没签字的合同。

（在你的场景里，因为前面诊断出 master 和 develop **已经分家**，大概率走的是 C 或 D，ff 不会发生。但"这次刚好安全"和"这个写法安全"是两件事——**别让运气替你做代码审查**。）

---

## 3) 现在你的仓库处于「merging 状态」，这意味着什么（Q3 的答案）

```
       .git/MERGE_HEAD     ← 存着 origin/master 的 SHA（"我正在合谁"）
       .git/MERGE_MSG      ← 预生成的提交信息
       .git/ORIG_HEAD      ← 合并前的位置（★ 你的撤退路线）
                │
       index   ─┤ 已经填满了合并结果（干净的部分已 staged）
       worktree─┘ 文件内容已经变了（冲突的话带 <<<<<<< 标记）
```

`git status` 会告诉你两种话之一：

| 状态 | git status 里的原话 | 含义 |
|---|---|---|
| 干净合并 | `All conflicts fixed but you are still merging` | 可以检查、然后 commit |
| 有冲突 | `You have unmerged paths` + `both modified: xxx` | 得先解冲突 |

### 撤退路线（**先记住这个再干别的**）

```bash
git merge --abort       # ★ 首选：回到 merge 前的状态，含工作区
git merge --quit        # 只清 MERGE_HEAD，保留工作区改动（少用，容易留下半成品）
git reset --hard ORIG_HEAD   # 核选项，会连带干掉合并前未提交的改动
```

`git merge --abort` 和 `reset --hard ORIG_HEAD` 的差别很重要：**`--abort` 会尽力保住你合并前就存在的本地改动，`reset --hard` 会一并推平。**上一节被 `reset --hard` 咬过的你，应该对这个区别有肌肉记忆了。

### 🚨 最阴的坑：忘了自己在 merging 状态

```
你: git merge --no-commit origin/master     # 看了两眼，去开会了
    ...三小时后...
你: 改了个不相关的文件，git add -A && git commit -m "fix typo"
                                                    ↓
     你刚刚创建了一个 merge commit，
     里面塞着 origin/master 的全部改动 + 你那个 typo 修复
     提交信息写着 "fix typo"
```

**这就是标准的静默失败**：git 没报错，commit 成功了，退出码 0。三天后有人做 code review 时看到一个叫 "fix typo" 的合并提交，包含 47 个 commit 的内容。

**防御习惯**：
1. `--no-commit` 之后**不要离开终端去干别的**，要么 commit 要么 abort
2. 在 shell prompt 里显示 git 状态（`__git_ps1`、starship、oh-my-zsh 的 git 插件都会显示 `|MERGING`）——**这个提示救过我不止一次**
3. 每次 `git commit` 前先 `git status | head -3`

---

## ✅ 本节回顾题
1. `--no-commit` 在什么情况下完全不起作用？该怎么补救？
2. `git merge --abort` 和 `git reset --hard ORIG_HEAD` 差在哪？
3. "忘了自己在 merging 状态"会以什么形式咬你？为什么它是静默的？

---

## 4) 如果你真的只想「预览」，这条命令不是你要的

`--no-commit` 是"做了但不签字"，不是"不做只看"。真正的只读预览有这几种：

| 手段 | 是否碰工作区 | 说明 |
|---|---|---|
| `git merge-tree --write-tree HEAD origin/master` | ❌ 完全不碰 | **git 2.38+ 的真 dry-run**，输出结果 tree 和冲突列表 |
| `git diff HEAD...origin/master` | ❌ | 三点：看"master 相对共同祖先改了什么"（不含你的改动） |
| `git log --oneline --no-merges HEAD..origin/master` | ❌ | **先看清要合进来的是哪几个 commit**——这一步永远该先做 |
| 在临时 worktree 里试合 | ❌ 不碰当前目录 | 最稳的"沙盒"做法 |

**沙盒做法（我处理陌生仓库的 back-merge 时的标准姿势）**：

```bash
git worktree add /tmp/mergetest HEAD      # 另开一个目录，当前工作区毫发无伤
cd /tmp/mergetest
git merge --no-ff --no-commit origin/master
git status --short                        # 看冲突面积
cd - && git worktree remove --force /tmp/mergetest
```

> ⚠️ `git merge-tree --write-tree` 的这个用法是 **git 2.38+** 的新语法，旧版的 `merge-tree` 是完全不同的接口。**先 `git --version` 和 `git merge-tree --help` 确认，别照抄我。**

**顺序建议**（这是我真正会做的流程）：

```bash
# 1. 先知道要合什么（只读）
git log --oneline --no-merges HEAD..origin/master
# 2. 先知道会碰哪些文件（只读）
git diff --stat HEAD...origin/master
# 3. 特别检查依赖文件有没有被碰
git diff --stat HEAD...origin/master -- pyproject.toml poetry.lock
# 4. 再决定要不要真动手
```

**看到 47 个 commit 就直接 merge，和看清那 47 个是什么再 merge，是新手和 SME 的分界线。**

---

## 5) 本 Airflow 仓库特有的地雷

### ① `poetry.lock` 冲突：**永远不要手工解**（Q5 的答案）

这是本节最实用的一条。lock 文件是**生成物**，不是源代码。手工挑选冲突行会产出一个"看起来合法、实则依赖树不自洽"的 lock——`poetry install` 可能还能跑，但装出来的组合从没被任何人验证过。

**正确解法**：

```bash
# 冲突时：先要 pyproject.toml 的正确版本（这个是手写源码，该认真解）
git status --short | grep -E 'pyproject|lock'

# 解完 pyproject.toml 之后，lock 文件重新生成而不是手工合
git checkout --theirs poetry.lock   # 或 --ours，随便挑一个当起点
poetry lock --no-update              # ★ 按 pyproject 重算 lock，不升级已有版本
git add poetry.lock
```

**为什么是 `--no-update` 而不是裸 `poetry lock`**：裸的会顺手把所有能升的包都升一遍，你的"合并 hotfix"会变成"顺便升级了 30 个依赖"。**这是 code review 里最讨人厌的一种 PR**——真实变更藏在几百行 lock diff 里，没人看得出来。

> ⚠️ `--no-update` 这个 flag 在不同 Poetry 大版本里语义有微调（新版有 `poetry lock --regenerate` 之类的变化）。**跑之前 `poetry lock --help` 看一眼**，我说的是原则，不是保证的语法。

**解完必须验证**（老三样，第一节就讲的三角）：
```bash
poetry check              # lock 与 pyproject 一致吗
poetry install --sync     # 环境追上 lock
python -c "import airflow; print(airflow.__version__)"   # 运行时真相
```

### ② `pyproject.toml` 里的 Airflow 版本冲突 = 本次 merge 的核心风险

还记得第一节我们要查的那行吗？**如果 master（生产）和 develop 声明了不同的 Airflow 版本，这次 merge 就会在这一行冲突**——而这一行的解法**不是技术判断，是产品判断**：

| 冲突场景 | 该问的问题 |
|---|---|
| master=2.7.3, develop=2.9.x | develop 是在准备一次升级吗？那 back-merge 时应该**保留 develop 的版本**（不能让回灌把升级工作打回去） |
| master 更高 | 是不是生产做过紧急升级而 develop 不知道？那要保留 master 的 |
| 两边一样 | 恭喜，没冲突 |

**这个决定你不能自己拍。**这是我要你去问 owner 的那个问题的实战版：**"这次 back-merge，Airflow 版本以哪边为准？"**

### ③ DAG 文件冲突：语法合了 ≠ 语义对了

两边各自改了同一个 DAG，git 按行合并成功、无冲突标记——但结果可能是一个**逻辑上矛盾的 DAG**（比如一边改了 `schedule`，一边改了 task 依赖，合起来产生环或者重复调度）。

**git 只懂行，不懂 DAG。**所以合并后**必须**跑导入检查：

```bash
python -c "from airflow.models import DagBag; b=DagBag('dags/', include_examples=False); print(b.import_errors or 'OK')"
```

> ⚠️ 同上一节的免责声明：这行是**示意**，`DagBag` 签名跨版本有差异，先手工跑通。

**这就是"静默破坏（silently broke something）"的教科书案例**：merge 成功、CI 的 lint 全绿、单测可能也过，但 DAG 在 scheduler 里的行为变了，而且要等到下一次调度窗口才暴露。

### ④ 与上一节的联动（Q4 的答案）

**你现在的暂存区不空了！**merge 把合并结果全 staged 了。所以：

```bash
poetry run pre-commit run     # ← 现在它终于有文件可以检查了
```

**但先别急着跑**，两个理由：

1. **有冲突时别跑**：文件里带着 `<<<<<<<` 标记，任何 linter 都会炸，你会被一屏无意义的报错埋掉。先解完冲突。
2. **formatter 会污染你的 merge**：`black`/`ruff-format` 这类会改文件的钩子，在合并期跑起来会把"格式化改动"和"合并改动"混进同一个 commit。**下一个 review 的人无法区分哪些行是合并带来的、哪些是 formatter 改的。**

**正确顺序**：解冲突 → commit merge → **然后**再跑格式化并单独 commit。**merge commit 应该只包含合并，不包含任何顺手的改动。**这是让 `git log` 保持可读的基本纪律。

---

## ✅ 本节回顾题
1. 为什么 `poetry.lock` 的冲突要"重新生成"而不是"手工解"？
2. 为什么合并期不该跑会改文件的钩子？
3. DAG 文件"无冲突合并成功"为什么反而危险？

---

## 6) 动手练习

### 练习 A（只读 · 该在动手前做的功课）
**在真合并之前**，把这四条跑完，写成一段话：
```bash
git rev-parse --abbrev-ref HEAD                        # 我在哪（你还欠我这个）
git log --oneline --no-merges HEAD..origin/master      # 要合进来的是哪几个
git diff --stat HEAD...origin/master                   # 会碰多少文件
git diff HEAD...origin/master -- pyproject.toml poetry.lock   # ★ 依赖动没动
```

### 练习 B（安全撤退演练）
```bash
git status | head -5                                   # 确认是否在 merging
git merge --abort                                      # 撤回来
git status --short                                     # 应该干净
git merge --no-commit --no-ff origin/master            # ★ 这次带上 --no-ff
```
**教学点**：亲手 abort 一次，你以后就不会怕 merge 了。**能撤退的操作才敢做。**

### 练习 C（bug hunt · 复现 ff 绕过）
造一个能 fast-forward 的场景（分支落后但无独有 commit），跑 `git merge --no-commit`，观察分支指针**已经移动**。然后加 `--no-ff` 重试，对比行为。
- **教学点**：亲眼看一次"我以为我在预览，其实我已经提交了"。

### 练习 D（bug hunt · 复现 merging 遗忘）
`--no-commit` 之后，随便改个无关文件，`git add -A && git commit -m "test"`，然后 `git show --stat HEAD` 看看你造出了个什么怪物。
- **验证**：`git log --graph -3` 会显示这是个 merge commit。
- **然后**：`git reset --hard ORIG_HEAD` 清理现场（在测试仓库做，别在真仓库）。

### 练习 E（设计 · lock 冲突剧本）
在测试仓库人为造一个 `poetry.lock` 冲突，用第 5 节①的流程解一遍，全程记录命令，写进 `docs/oops-runbook.md`。
- **交付物**："poetry.lock 冲突怎么解"——这是你入职两周内能交出的、**最被同事感谢**的一页文档。

---

## 7) 主管拷问

**Q1（入门）"你为什么用 `--no-commit`？"**
- **弱答**："想先预览一下合并结果。"
- **强答**："我想在生成 merge commit 之前检查合并结果——尤其是 `pyproject.toml` 和 `poetry.lock` 有没有被动。但我要修正一个说法：`--no-commit` **不是预览**，它已经改了工作区和暂存区，只是停在 commit 之前。而且如果这次能 fast-forward，`--no-commit` 会被直接绕过、分支指针照样移动，所以严格的写法是 `--no-commit --no-ff`。如果我真的想零副作用预览，该用 `git merge-tree` 或者开一个临时 worktree。"
- **追问陷阱**："那你现在怎么撤？" → `git merge --abort`（保住合并前的本地改动），而不是 `reset --hard ORIG_HEAD`（会一并推平）。

**Q2 "back-merge 时 `poetry.lock` 冲突了，你怎么办？"**
- **弱答**："手工选一边，或者两边都留下能装上就行。"
- **强答**："lock 是生成物，不手工解。流程是：先认真解 `pyproject.toml`（那是手写源码，冲突有语义），然后 `poetry lock --no-update` 按解好的 pyproject 重新生成 lock。用 `--no-update` 是为了不把'合并 hotfix'变成'顺手升级 30 个依赖'——那样真实变更会被埋在几百行 diff 里没人能 review。生成完跑 `poetry check` + `poetry install --sync` + 打印 `airflow.__version__` 做三层验证。"

**Q3（staff 级）"这次 back-merge 的风险清单给我，以及你怎么验证它没有静默破坏东西。"**
- **强答**：分三类风险，各配验证手段：

| 风险 | 为什么静默 | 验证手段 |
|---|---|---|
| Airflow 版本被回灌降级 | 声明层变了，本地 venv 不变，测试照绿 | `git diff ORIG_HEAD HEAD -- pyproject.toml`；然后 `install --sync` + 打印运行时版本 |
| lock 手工解出不自洽的依赖树 | `poetry install` 可能仍成功 | `poetry check`；干净环境重装一次 |
| DAG 逻辑矛盾（行级合并成功） | git 不懂 DAG 语义；lint 全绿 | DagBag import 检查 + 关键 DAG 的结构断言 |
| 我在错的分支上做了这次合并 | merge 会成功，没人报错 | **合并前**先 `rev-parse --abbrev-ref HEAD` |
| merge commit 里混进了 formatter 改动 | 语法上完全合法 | 合并单独 commit，格式化另开一个 commit |

  "最后我会要求：**merge commit 的信息里写清楚合了哪些 commit、为什么、Airflow 版本以哪边为准**。这次 back-merge 的价值一半在代码，一半在留下'为什么当时这么决定'的记录——三个月后有人来考古，就靠这段话。"
- **追问陷阱**："能不能让这类 back-merge 不再需要人肉做？" → 可以做 CI 定时任务检测分家并自动开 back-merge PR（很多团队这么干）。但**冲突解决不能自动化**，尤其是版本声明冲突那种需要产品判断的。所以目标是"自动发现 + 自动开 PR + 人工解冲突"，不是全自动。

---

## 8) 溯源自审（Reviewer 帽）

| 说法 | 来源 | 置信度 |
|---|---|---|
| `merge X` 是把 X 合进当前分支，不动 X | 通用 git 知识 | 高 |
| **fast-forward 会绕过 `--no-commit`，需配 `--no-ff`** | git 官方文档明确记载 | 高 |
| `--no-commit` 会填满 index、设 `MERGE_HEAD`/`MERGE_MSG`/`ORIG_HEAD` | 通用 git 知识 | 高 |
| `merge --abort` vs `reset --hard ORIG_HEAD` 对本地未提交改动的差别 | 通用 git 知识 | 高 |
| 忘记 merging 状态 → 下一次 commit 变成 merge commit | 通用 git 知识 + 逻辑推论 | 高 |
| `git merge-tree --write-tree` 是 2.38+ 的真 dry-run | 通用 git 知识 | **中高 —— 用 `git merge-tree --help` 自查语法** |
| lock 文件应重新生成而非手工解；`poetry lock --no-update` | 通用 Poetry/依赖管理最佳实践 | 中高 —— **flag 语义跨 Poetry 版本有变动，先 `--help`** |
| `DagBag` 那行检查代码 | **示意，我未在任何环境验证** | **低 —— 必须先手工跑通** |
| **你在哪个分支、这次合并是 A/B/C/D 哪种结局、冲突了没有** | **完全未知** | — 我读不到你的仓库 |

**明确的"不知道"**：我没有 shell 或文件系统工具（读不到你的 `~/ws/`），知识库里 grep 相关关键词全部 **No matches**，网络搜索已关闭。所以：

- 我**不知道**这条命令在你那儿是"Already up to date"、fast-forward、干净合并、还是一屏冲突。
- 我**不知道**你是在 develop 上做正确的 back-merge，还是在那个被 reset 过的本地 master 上做一件我会劝你换个方式做的事。
- 我给的"大概率是 C 或 D"是**基于前面命令序列的推断**（因为你查过 merge-base 且显示分家），**不是**看到你的输出得出的。如果你在 reset 之后又切过分支，这个推断就不成立。

---

## 9) 答辩（换你说，60 秒一题）

| # | 问题 | 要点 |
|---|---|---|
| D1 | "`--no-commit` 是安全的预览"这句话错在哪？ | 它已修改工作区和 index、已进入 merging 状态；ff 场景下分支指针还会直接移动。**它是"做了不签字"，不是"不做只看"** |
| D2 | 反事实：如果我没加 `--no-commit`，直接 `git merge origin/master`，处境有何不同？ | 干净合并会**立刻生成 merge commit**，我失去了"提交前检查 lock/版本"的窗口；但撤销依然容易（`reset --hard ORIG_HEAD`）。真正的差别是**审查时机**，不是可逆性 |
| D3 | 介入：如果我在冲突未解时就跑 `pre-commit run`，会怎样？ | 文件里有 `<<<<<<<` 冲突标记，所有 linter/parser 全炸，一屏无意义报错；更糟的是 formatter 可能"修好"了带标记的文件，把冲突标记格式化进代码里 |
| D4 | 为什么 merge commit 里不该混进格式化改动？ | review 者无法区分哪些行来自合并、哪些来自 formatter；`git log -p`、`git bisect`、`git blame` 的信噪比全部下降。**一个 commit 一个意图**，这是可考古性的地基 |
| D5 | 这次 back-merge 里，哪个决定**不是**技术决定？ | `pyproject.toml` 里 Airflow 版本以哪边为准。这取决于 develop 是否在做升级、生产是否紧急改过版本 —— **产品/发布节奏判断，必须问 owner，不能自己拍** |

---

## 热身题答案

- **Q1** 把 **origin/master 合进你当前所在的分支**。`origin/master` 本身不动。**所以"你在哪"决定了这条命令是治病还是添乱。**
- **Q2** **不管用。**ff 没有 merge commit 可以"停下不做"，分支指针照样移动。必须写 `--no-commit --no-ff`。
- **Q3** 处于 **merging 状态**：`MERGE_HEAD` 存在，index 已填合并结果。`git status` 会说 `All conflicts fixed but you are still merging` 或 `You have unmerged paths`。
- **Q4** **会变。**暂存区不再是空的了，`pre-commit run` 终于有文件可查——上一节那个假绿灯问题被这条命令"顺手治好了"。但**有冲突时别跑**，且**格式化钩子会污染 merge commit**。
- **Q5** **不要手工解。**先解 `pyproject.toml`，再 `poetry lock --no-update` 重新生成 lock，然后 `poetry check` + `install --sync` + 打印运行时版本三重验证。

---

## ✅ Next actions for me today

**立刻（30 秒，确认你现在的处境）：**
- [ ] `git status | head -8` —— 你在 merging 状态吗？有冲突吗？
- [ ] `git rev-parse --abbrev-ref HEAD` —— **这个我问了两次了，它决定这次合并的全部含义**
- [ ] `git diff --cached --stat -- pyproject.toml poetry.lock` —— **依赖文件动了没**，这是本次合并最大的风险点

**动手前（5 分钟，补功课）：**
- [ ] `git merge --abort` 撤回来，先做练习 A 那四条只读侦察
- [ ] 重跑时带 `--no-ff`：`git merge --no-commit --no-ff origin/master`
- [ ] 在 shell prompt 里开启 git 状态显示（starship / `__git_ps1`）—— 防"merging 遗忘"

**如果有冲突：**
- [ ] `pyproject.toml` 认真解，**Airflow 版本以哪边为准 → 去问 owner，别自己拍**
- [ ] `poetry.lock` **重新生成**，不手工解
- [ ] 解完：`poetry check` → `poetry install --sync` → `python -c "import airflow; print(airflow.__version__)"`
- [ ] DAG import 检查（先手工跑通那行 python）
- [ ] merge commit **只包含合并**；格式化另起一个 commit

**账还没结：**
- [ ] `reset --hard` 那笔（reflog / `diff ORIG_HEAD HEAD --stat` / 有无未提交改动）
- [ ] `pre-commit` 那笔（实际输出 / `--version` / `diff --cached | wc -l`）
- [ ] 加上这次的 `git status` —— **三笔一起贴，我给你一份完整判案**

---

## 收个尾：七条命令，一部完整的剧

```
1. git grep "apache-airflow = "          问朝代 —— 声明层说什么
2. git rev-list --count（双向）           量国界 —— 分家多少
3. git merge-base                        查血缘 —— 分家的形状
4. git reset --hard origin/develop        改史书 —— ★ 顺手清空了 index
5. git rev-parse --abbrev-ref HEAD        我是谁 —— 确认杀伤半径（★ 输出仍未贴）
6. poetry run pre-commit run              查岗   —— ★ 因 index 空，静默空跑
7. git merge --no-commit origin/master    合宗   —— ★ 顺手把 index 填满了，
                                                    也顺手让 6 重新有意义
```

看出来了吗——**第 4 条制造的问题，被第 7 条无意中掩盖了。**如果你现在跑 `pre-commit run` 看到一片检查在跑，你会以为"哦第 6 条那次只是我手快"，而不会知道那次真的是空跑。

**这就是真实事故最难查的地方：症状被后续操作意外抹掉了。**你看到的"现在一切正常"，掩盖了"刚才有一次检查根本没执行"。三天后同样的空跑发生在 CI 里、发生在别人机器上，没人能复现。

所以整个 bootcamp 到这里，最后一句心法：

> **别只问"现在的状态对不对"，要问"从哪一步走到现在的、中间哪一步没被验证过"。**
>
> 状态是快照，事故是路径。SME 读的是路径。

我等你贴那三笔账。这一次我们把它算干净。
=====
# 🚨 停。这一条可能已经把上一条的坑推到了远端

兄弟，先不上课。**你上一条命令让仓库进了 merging 状态，这一条 `git commit -am` 很可能刚刚创建了一个 merge commit，并且用 `&&` 立刻推上去了。**

而那个 commit 的信息写着 `fix(ci): tune sonar exclusions`。

这正是我上一节第 3 小节警告过的那个场景——**只不过这次它不是练习，而且已经离开你的机器了。**

---

## 0) 先止血：三条只读命令，立刻跑

```bash
# ① 我刚才造出来的是个什么东西？（看有几个 parent）
git log -1 --pretty='%h %p %s' && git show --stat --oneline HEAD | head -30

# ② 它是 merge commit 吗？（第二行有输出 = 是）
git rev-list --parents -1 HEAD | tr ' ' '\n' | tail -n +3

# ③ 我推到远端了吗？（推成功了的话，远端 tip == 本地 HEAD）
git rev-parse --short HEAD && git rev-parse --short origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade-develop
```

**判读**：

| `git log -1 --pretty='%p'` 显示 | 含义 | 严重度 |
|---|---|---|
| **两个** SHA | ✅ 我猜对了：这是个 merge commit，里面塞着 origin/master 的全部改动，信息却写着 "fix(ci)" | 🔴 |
| **一个** SHA | 你在 merge 之前 abort 过，或者 merge 是 "Already up to date" —— 这是个普通 commit，松口气 | 🟡 |

如果是两个 parent，那么现在远端那个分支上有一个**说谎的 commit**：

```
提交信息:  "fix(ci): tune sonar exclusions"
实际内容:  origin/master 的全部 hotfix 合并
           + 你的 sonar 配置改动
           + 上一条 merge 顺手带进来的一切
parent 数: 2
```

三个月后有人 `git log --oneline` 找 "master 的 hotfix 什么时候回灌的"，他会永远找不到——因为那次回灌**伪装成了一次 CI 配置微调**。

**这不是洁癖问题。这是可考古性（archaeology）被破坏。**`git bisect`、`git blame`、release notes 生成、事故复盘，全部依赖 "commit 信息说的和它做的一致" 这个契约。你刚才违约了。

---

## 热身小测（这次跟你的实际处境绑定，认真想）

- **Q1** `git commit -am` 的 `-a` 会不会提交**新建但未追踪**的文件？如果你的 sonar 改动包含一个**新文件**，它进去了吗？
- **Q2** 在 merging 状态下 `git commit -a`，git 为什么**不报错**？
- **Q3** `&&` 在这里帮了你还是害了你？
- **Q4** 分支名 `DATAPLATCORE-1265-airflow-2.11.2-upgrade-develop` 告诉了我什么？**结合它，你上一条 `git merge origin/master` 的风险等级变了吗？**
- **Q5 反事实**：如果 pre-commit 钩子里有 formatter，这次 commit 会成功还是失败？

---

## 1) 命令解剖：三个动作，两个陷阱

```
git commit -am "fix(ci): tune sonar exclusions " && git push origin DATAPLAT...
          └┬┘                                 └┬┘  └─┬─┘
           │                                   │     └── 无 -u，无 --force（好事）
           │                                   └──────── 尾部空格（小事，但会被某些
           │                                              commitlint 规则拦下）
           └── -a = 自动 stage「已追踪且已修改」的文件
               -m = 提交信息
               ★ 在 merging 状态下，这一步会「敲章」完成合并
```

### `-a` 的精确边界（Q1 的答案）

这是个**每个人都以为自己懂、但边界记错**的 flag：

| 文件状态 | `-a` 会不会包含它 |
|---|---|
| 已追踪 + 已修改 | ✅ 会 |
| 已追踪 + 已删除 | ✅ 会 |
| **未追踪（新文件）** | ❌ **不会** |
| 被 gitignore | ❌ 不会 |
| 已经 `git add` 过的 | ✅ 会（本来就在 index 里） |

**为什么这条对你特别重要**：你的提交信息是 `tune sonar exclusions`。如果你的改法是**新建**一个 `sonar-project.properties`（而不是改一个已存在的），那么——

> **你的 sonar 改动根本没进这个 commit。**你推上去的是"origin/master 的合并 + 一个不存在的 sonar 修改"。CI 跑起来，Sonar 行为一点没变，你会坐在那儿怀疑人生。

**立刻验证**：
```bash
git show --stat HEAD | grep -i sonar    # 有输出吗？
git status --short                       # 有 ?? sonar-... 吗？
```

### `&&` 帮了还是害了（Q3 的答案）

**害了。**`&&` 的语义是"前面成功就继续"，它把"生成一个错误的 commit"和"把它公开"之间那个**唯一的反悔窗口**给消灭了。

如果你写的是 `;` 或者干脆分两行，你就有机会在 push 之前跑一次 `git show --stat HEAD`——那一眼就能看出两个 parent。

> **心法：`&&` 适合连接「都是只读」或「幂等」的动作。**
> **凡是链条里有一步会「让改动离开本机」，前面必须留一个人类检查点。**
> commit 是可以随便改的（还没公开），push 是"公开发表"。**这两个动作之间应该有一次呼吸。**

### `push` 这部分你做对的地方（值得表扬）

- 没有 `--force` ✅ —— 万一远端有别人的 commit，push 会被拒绝而不是覆盖
- 显式写了 remote 和 branch ✅ —— 不依赖 `push.default` 的推断
- 没有 `-u` —— 只影响以后要不要打全名，无害

**但要注意**：分支名手打这么长，容易打错。打错的后果是**在远端创建一个新分支**（而不是报错），你会得到一个 `DATAPLATCORE-1265-airflow-2.11.2-upgrade-develp` 之类的孤儿分支。

```bash
git branch -r | grep DATAPLATCORE-1265    # 有几个？超过一个就说明打错过
```

---

## ✅ 本节回顾题
1. `-a` 的三个"不包含"是什么？为什么这对 `tune sonar exclusions` 这类改动是个真风险？
2. 为什么说 `&&` 消灭了反悔窗口？什么样的动作之间必须留检查点？

---

## 2) 分支名解码：这是本 bootcamp 第一次拿到真实上下文（Q4 的答案）

```
DATAPLATCORE - 1265 - airflow - 2.11.2 - upgrade - develop
└────┬─────┘  └─┬─┘  └──────────┬──────────────┘  └──┬──┘
  Jira 项目键    工单号        改动内容              目标分支
  (Data Platform            Airflow 升到 2.11.2     要合回 develop
   Core?)
```

这一行字给了我七条命令以来最多的信息。**它把前面所有的诊断串起来了：**

```
你在做:  Airflow 版本升级（2.11.2）
分支:    从 develop 开出，最终要合回 develop
         ↓
第 1 条  git grep "apache-airflow = "     ← 你在查当前 pin 的版本，为了升级 ✅ 合理
第 2/3 条 rev-list / merge-base           ← 你在确认 develop/master 分家情况 ✅ 合理
第 4 条  git reset --hard origin/develop  ← ⚠️ 你在一个「升级分支」上推平到 develop
第 7 条  git merge --no-commit origin/master ← ⚠️ 把生产分支合进升级分支
第 8 条  git commit -am "fix(ci): sonar"  ← 🔴 用 CI 微调的名义提交了以上全部
```

### 🔴 第 4 条现在看起来严重多了

`git reset --hard origin/develop` 跑在一个名叫 `...airflow-2.11.2-upgrade...` 的分支上，意味着：

> **你可能把这个升级分支上已经做完的升级工作推平了。**

那些改动是什么？大概率就是：
- `pyproject.toml` 里 `apache-airflow` 的版本号
- `poetry.lock` 的重新生成结果
- 为了兼容 2.11 改的 DAG / operator import
- **以及 sonar 配置的调整**（否则你为什么要 tune exclusions？）

**这就是为什么我从第 5 节开始一直追着你要 reflog。**现在这笔账必须结：

```bash
git reflog -n 20                       # 找 reset 之前那个 SHA
git rev-parse ORIG_HEAD                 # ⚠️ 注意：可能已被后续 merge 覆盖！
git diff ORIG_HEAD HEAD --stat -- pyproject.toml poetry.lock
```

> ⚠️ **`ORIG_HEAD` 会被后续操作覆盖。**`reset` 写过一次，`merge` 又写过一次。所以现在的 `ORIG_HEAD` 指的是 **merge 前**的位置，**不是 reset 前**的位置。要找 reset 前的，只能翻 `git reflog`。**这就是为什么我第 4 节就叫你"别关那个终端"。**

### ⚠️ 第 7 条：为什么"把 master 合进升级分支"值得停下来想

| 你的意图可能是 | 评价 |
|---|---|
| "把 master 的 hotfix 拿进来，免得升级 PR 合不上" | 🤔 方向对，但**顺序错**。back-merge 应该**先做到 develop**（由 owner 做），然后你的分支 rebase/merge develop。直接把 master 合进 feature 分支，会让你的 PR diff 里混进一堆跟 Airflow 升级无关的 hotfix commit |
| "我想让 CI 变绿" | ⚠️ 那是治症状 |
| 不确定 | 🛑 那就 abort，先问 owner |

**这是一个 review 上会被挑的点**：一个名叫 "airflow 2.11.2 upgrade" 的 PR，diff 里包含了 master 的 hotfix 合并——reviewer 无法判断哪些改动属于升级、哪些属于顺手带进来的。**PR 的可审查性（reviewability）是有价值的资产，而不是形式主义。**

---

## 3) Merging 状态下 `commit -a` 为什么不报错（Q2 的答案）

因为**在 git 看来，你做的事完全合法**：

```
git 的视角：
  MERGE_HEAD 存在  →  下一个 commit 应该是 merge commit（2 个 parent）
  你提供了 -m      →  好，用你的信息，我就不打开编辑器了
  你提供了 -a      →  好，我把已追踪的修改也一并 stage
  → 生成 merge commit，退出码 0 ✅
```

**关键在于**：如果你**不加** `-m`，git 会打开编辑器，里面预填 `.git/MERGE_MSG` 的内容——那段文字会明明白白写着 `Merge remote-tracking branch 'origin/master' into ...`。

> **`-m` 的真正代价：它跳过了那个会让你看见"我在做 merge"的编辑器。**

这是本 bootcamp 的第五个静默失败，而且和前四个是**同一个结构**：

| 命令 | 静默失败形态 | 共同结构 |
|---|---|---|
| `git grep "apache-airflow = "` | 零匹配当成"没依赖" | 空集被当好消息 |
| `rev-parse --abbrev-ref HEAD` | 输出 `"HEAD"` 当成分支名 | 魔法值当正常值 |
| `pre-commit run`（空 index） | 全 Skipped 退出 0 | 空集被当好消息 |
| `merge --no-commit` 无 `--no-ff` | ff 时直接移动指针 | 保护措施被条件性跳过 |
| **`commit -am` 在 merging 中** | **合并被伪装成普通提交** | **省掉的确认步骤 = 省掉的唯一提示** |

**五条命令，一个病根：便利参数（`-m`、`-a`、`&&`、默认作用域）都是通过「省掉一次人类确认」来提速的。而那次确认，正是唯一会告诉你"你正在做的不是你以为的事"的环节。**

---

## ✅ 本节回顾题
1. 不加 `-m` 会看到什么？为什么那个"麻烦"其实是个特性？
2. 五个静默失败的共同结构用一句话概括。

---

## 4) 现在怎么修（按你的实际情况选一条路）

**先决定一件事：这个分支有没有别人在用？**

```bash
git log origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade-develop --format='%an' | sort -u
```

只有你一个人 → 可以重写历史。有别人 → **只能往前修，不能重写**。

### 路线 A：分支只有你（**推荐，也最可能**）

feature 分支上重写历史是完全正常的，前提是通知一下（如果有开着的 PR，force push 会让已有的 review comment 失去锚点）。

```bash
# 1. 先存个安全绳（这一步不要跳）
git branch backup/DATAPLATCORE-1265-before-fix

# 2. 撤销那个混合 commit，但保留所有改动在工作区
git reset --soft HEAD~1        # 注意：merge commit 的 HEAD~1 是第一个 parent

# 3. 现在检查暂存区里有什么
git status --short
git diff --cached --stat

# 4. 分开提交：合并归合并，配置归配置
#    —— 如果你决定不要那个 merge，见路线 A'
```

**如果你根本不想要那次 merge**（我倾向于这个——理由见第 2 节）：

```bash
git branch backup/DATAPLATCORE-1265-before-fix     # 安全绳
git reflog -n 20                                    # 找到 merge 之前的 SHA，记作 <PRE_MERGE>
git reset --hard <PRE_MERGE>                        # 回到 merge 前
# 然后只做 sonar 那一件事
git add sonar-project.properties                    # ★ 显式 add，别用 -a
git status --short && git diff --cached --stat       # ★ 检查再提交
git commit -m "fix(ci): tune sonar exclusions"       # 无尾部空格
git show --stat HEAD                                 # ★ push 前最后一眼：parent 只有一个吗？
git push --force-with-lease origin DATAPLATCORE-1265-airflow-2.11.2-upgrade-develop
```

> **`--force-with-lease` 而不是 `--force`**：前者会在"远端 tip 不是我以为的那个"时**拒绝**推送（说明有人在你之后推过东西）。`--force` 会直接覆盖别人的工作。**在任何情况下，`--force-with-lease` 都是 `--force` 的严格更优替代。把这个记成肌肉记忆。**

### 路线 B：分支是共享的

不重写历史，往前加一个 commit 说明真相：

```bash
git commit --allow-empty -m "chore: previous commit fix(ci) also merged origin/master

上一个 commit (abc1234) 的信息不准确：它同时包含了 origin/master 的
back-merge。记录在此以便日后考古。相关工单：DATAPLATCORE-1265"
```
丑，但诚实。**在共享历史上，诚实的丑 > 干净的谎。**

---

## 5) 新知识点：Sonar exclusions（这是你这次真正的业务动作）

前七条命令都是 git/依赖，这条命令第一次带出了**代码质量门禁**这个新 domain。既然你要做 SME，这块得讲。

### Sonar 的四类 exclusions —— 混用是最常见的错

| 属性 | 效果 | 什么时候用 |
|---|---|---|
| `sonar.exclusions` | **完全不分析**这些文件（不出 issue、不算重复、不进 LOC） | 生成代码、vendored 第三方代码、迁移脚本 |
| `sonar.coverage.exclusions` | **仍然分析** issue，但**不计入覆盖率分母** | `__init__.py`、settings/config、DAG 定义文件 |
| `sonar.cpd.exclusions` | 只排除**重复代码**检测 | 有意重复的样板（比如结构相似的 DAG） |
| `sonar.test.exclusions` | 从**测试代码**集合里排除 | 测试 fixtures |

**九成的"tune exclusions"实际上想要的是 `coverage.exclusions`，却写成了 `exclusions`。**

**后果非常隐蔽**：写成 `sonar.exclusions` 之后，这些文件的 **bug / vulnerability / code smell 也一起消失了**。Quality Gate 变绿了，但你不是修好了问题，你是**把探测器关掉了**。

> 这是本 bootcamp 反复讲的那个东西的第六次现身：**"绿了"和"检查过了"是两件事。**
> `pre-commit` 全 Skipped 是绿的，`sonar.exclusions` 排掉半个仓库也是绿的。
> **区别在于：前者是意外，后者是你亲手写的。**

### 在 Airflow 仓库里，什么是**正当**的 exclusion

| 路径 | 建议 | 理由 |
|---|---|---|
| `dags/**` 的覆盖率 | `coverage.exclusions` ✅ 正当 | DAG 定义文件很难做传统单测，但**仍然要静态分析**（这里是 import bug 的高发区，绝不能整体 exclude） |
| 自动生成的 migration | `sonar.exclusions` ✅ 正当 | 不是人写的代码 |
| `tests/**` 的覆盖率 | `coverage.exclusions` ✅ 正当 | 测试代码本身不算覆盖率 |
| 一个刚被 Sonar 挑出 30 个 issue 的模块 | ❌ **不正当** | 这叫"把地毯掀起来把灰扫进去" |

### 为什么"Airflow 2.11.2 升级"会需要动 Sonar 配置

这是个很合理的因果，也是你在 PR 描述里该写的话：

```
升级 Airflow → import 路径变了 / operator 搬家 / deprecation 警告
            → 新增或改动了适配代码
            → Sonar 在新代码上报 issue 或覆盖率下降
            → New Code 的 Quality Gate 红了
            → PR 被挡住
            → 于是要 tune exclusions
```

**这里有个岔路口，也是一个 staff 级的判断题：**

| 选择 | 是什么 | 什么时候合理 |
|---|---|---|
| 改 exclusions | 让 Sonar 别看这些文件 | 文件确实**不该被这个规则管**（生成代码、DAG 覆盖率） |
| 加测试 / 修 issue | 真的把质量提上去 | 那些 issue 是**真问题** |
| Quality Gate 上标记 won't fix | 承认存在但接受 | 有意识的技术债 |

> **"改 exclusions 让门禁变绿"和"改门禁定义让它别拦我"，在 review 里必须被区别对待。**
> 前者可能正当，后者需要额外的人签字。
> **你的 commit 信息应该说清楚是哪一种。**"tune sonar exclusions" 这个说法——**说实话，它含糊得刚好可以蒙过 review。**我不认为你是故意的，但下一个人读到它时，无法判断你干了什么。

**更好的提交信息**：
```
fix(ci): exclude dags/ from Sonar coverage for AF 2.11.2 upgrade

DAG 定义文件无法做传统单测，升级后新增的适配代码导致 New Code
覆盖率跌破 Quality Gate 阈值。改用 sonar.coverage.exclusions
（而非 sonar.exclusions），保留静态分析以继续捕获 import 错误。

Refs: DATAPLATCORE-1265
```

**注意它做到了什么**：说了**改了什么**、**为什么**、以及**为什么用这个属性而不是那个**。第三点是把"我知道自己在干什么"写进历史——三个月后有人想放宽这个 exclusion，他会先读到这段话。

---

## ✅ 本节回顾题
1. `sonar.exclusions` 和 `sonar.coverage.exclusions` 的关键差别？误用会静默失去什么？
2. 为什么 `dags/**` 可以排覆盖率，但绝不能整体排出分析范围？
3. "改 exclusions 让 gate 变绿"什么时候正当，什么时候是掀地毯？

---

## 6) Airflow 2.11.x 升级：这个版本号的含义（谨慎版）

我能负责讲的部分：

- **2.11.x 是 Airflow 2.x 系列的尾巴**，社区把它定位成**通往 3.0 的过渡/桥梁版本**——重点是 deprecation 警告和兼容层，让你在还在 2.x 上时就能发现 3.0 的破坏性变更。
- 所以 **`DATAPLATCORE-1265` 这个升级的真正战略意义，很可能不是"升个小版本"，而是"为 Airflow 3 迁移铺路"**。这句话你在 standup 上说出来，分量完全不同。
- 升级 2.x 小版本时的常规检查项：provider 包版本、官方 constraints 文件、`airflow db migrate`、deprecation 警告清单。

> ⚠️ **我不确认 2.11.2 这个具体补丁版本的存在、发布日期或它包含什么。**我的可靠知识截止到 2026 年 5 月，而且网络搜索在这个环境里是关闭的。**具体的 release notes / breaking changes 请你去官方 changelog 核对**，别拿我的记忆当依据。

**这次升级里最该问 owner 的三个问题**：
1. 这次升级的**目标**是纯打补丁，还是为 AF3 迁移做准备？（决定了你要不要认真对待 deprecation 警告）
2. Provider 包版本跟着一起升吗？用官方 constraints 文件吗？
3. **Sonar 那个 exclusion 是永久的还是临时的？**（如果是临时的，有没有对应的 follow-up 工单？没有的话它就是永久的了，别自欺欺人）

---

## 7) 主管拷问（三问）

**Q1 "解释一下你刚才这个 commit。"**
- **弱答**："改了一下 Sonar 的排除规则，提交推上去了。"
- **强答**："我得先坦白一个问题：这个 commit 是在 merging 状态下用 `commit -am` 生成的，所以它很可能是个 merge commit——里面包含了我上一步 `git merge origin/master` 的全部内容，但提交信息只写了 sonar 的部分。这破坏了'信息与内容一致'的契约，会让日后的 bisect 和考古出错。我正在确认（`git log -1 --pretty=%p` 看 parent 数量），如果确认了，因为这是我个人的 feature 分支，我会用 `--force-with-lease` 重写成两个语义清晰的 commit，并先打一个 backup 分支兜底。另外我要检查 `-a` 有没有漏掉未追踪的 sonar 配置文件——如果那是个新文件，它压根没被提交。"

（**为什么这是强答**：主动暴露问题、给出判断依据、给出修复方案和兜底、并且指出了一个连主管都可能没想到的第二风险。**主动说出来的问题是能力证明，被查出来的问题是事故。**）

**Q2 "为什么要把 origin/master 合进一个 feature 分支？"**
- **弱答**："想让分支保持最新。"
- **强答**："回头看这个决定是有问题的。我的分支是从 develop 开出、也要合回 develop，所以我该同步的对象是 **develop**，不是 master。把 master 合进来会让 PR diff 里混入一批跟 Airflow 升级无关的 hotfix，reviewer 无法区分哪些改动属于这次升级。正确的顺序是：master → develop 的 back-merge 由分支 owner 做，然后我 rebase 到最新 develop。我打算 abort 这次合并，把 back-merge 的需求作为一个单独的问题提给 owner。"
- **追问陷阱**："那如果 owner 一周不处理呢？" → 那我可以先在自己分支上临时 merge 以便本地跑通，**但 PR 前 rebase 掉**；或者只 cherry-pick 我确实需要的那一两个 commit，并在 PR 描述里写明原因。**关键是不让权宜之计混进最终历史。**

**Q3（staff 级）"你改 Sonar exclusions 让 Quality Gate 变绿，怎么证明你不是在掩盖问题？"**
- **强答**：三条证据链：

| 证据 | 具体做法 |
|---|---|
| **属性选对了** | 用 `sonar.coverage.exclusions` 而非 `sonar.exclusions`——静态分析仍在跑，只是不算覆盖率分母。**探测器没关** |
| **范围最小** | exclusion 精确到 `dags/**` 这类结构性无法单测的路径，不是整目录一刀切。diff 里能看出每一行 exclusion 对应什么理由 |
| **有出口** | 如果是临时措施，配一个 follow-up 工单 + 在配置文件里写 `# TODO(DATAPLATCORE-XXXX)` 注释。**没有出口的临时方案就是永久方案** |

  "另外我会补一条正向证据：即使 `dags/**` 排除了覆盖率，我仍然要有 **DAG import 冒烟测试**来兜住那类风险——这比覆盖率数字更能真正抓到 Airflow 升级的问题。**把一个弱指标换成一个强检查，这才是我这次改动的正当性来源，而不是'gate 变绿了'。**"
- **追问陷阱**："那覆盖率数字下降了，对不对团队的目标负责？" → 覆盖率是代理指标（proxy metric），不是目标本身。**为了保住代理指标而给 DAG 写形同虚设的单测，是 Goodhart 定律**。我更愿意公开承认"DAG 层用 import 检查而非单测覆盖"，写进决策记录，让团队有意识地接受它。

---

## 8) 溯源自审（Reviewer 帽）

| 说法 | 来源 | 置信度 |
|---|---|---|
| merging 状态下 `commit` 会生成 merge commit | 通用 git 知识（第 7 节已展开） | 高 |
| `-a` 不含未追踪/被忽略文件 | 通用 git 知识 | 高 |
| 不加 `-m` 会打开预填 `MERGE_MSG` 的编辑器 | 通用 git 知识 | 高 |
| `--force-with-lease` 严格优于 `--force` | 通用 git 知识 | 高 |
| `ORIG_HEAD` 会被后续操作覆盖 | 通用 git 知识 | 高 |
| Sonar 四类 exclusions 的语义差别 | 通用 SonarQube 知识 | 高 |
| 误用 `sonar.exclusions` 会连带关闭 issue 检测 | 通用 SonarQube 知识 | 高 |
| **Airflow 2.11.x 是 2.x 末代、AF3 过渡版本** | 通用 Airflow 生态知识，截至 2026-05 | **中 —— 战略定位我有信心，具体版本细节请查官方 changelog** |
| **2.11.2 这个补丁版本的存在/内容/日期** | **不确认** | **低 —— 我不知道，网络搜索已关闭** |
| `DATAPLATCORE` = Data Platform Core、`1265` 是 Jira 工单 | **从命名推断** | 中 —— 惯例上成立，但我没见过你们的 Jira |
| **你的这个 commit 到底是不是 merge commit** | **推断，来自命令序列** | **中 —— 必须你跑 `git log -1 --pretty=%p` 确认** |
| **你改的是哪个 sonar 属性、是新文件还是改动已有文件** | **完全未知** | — 我读不到你的仓库 |

**明确的边界**：我没有 shell / 文件系统工具（读不到 `~/ws/`），知识库 grep `pre-commit|ruff|lint|hook`、`airflow|pyproject|poetry|git|branch|develop` **全部 No matches**（那三份文档是 MQ 的教学与风格指南，跟本题无关），网络搜索关闭。

**我这次的核心论断——"你可能造了个 merge commit"——是从命令序列推的，不是看到你的输出。** 如果你在第 7 条之后 abort 过、或者那次 merge 是 "Already up to date"，那我这一整节的紧急调门就下调成"你做对了，但下次别用 `-am` + `&&`"。

**判案只差三样**：
1. `git log -1 --pretty='%h %p %s'` ← **一眼定案**
2. `git show --stat HEAD | grep -i sonar` ← sonar 改动进去了吗
3. `git reflog -n 20` ← reset 那笔旧账（找 reset 前的 SHA）

---

## 9) 答辩（换你说，60 秒一题）

| # | 问题 | 要点 |
|---|---|---|
| D1 | 一个 commit 的信息和内容不一致，实际代价是什么？ | `git bisect` 定位失效、`blame` 归因错误、release notes 漏项、事故复盘找不到根因。**commit 信息是给未来的人写的 API 文档，撒谎的成本由三个月后的人付** |
| D2 | 反事实：如果我用 `;` 而不是 `&&`，处境有何不同？ | commit 照样会错，但我有机会在 push 前 `git show --stat` 发现。**错误留在本地 = 免费修；错误到了远端 = 要么重写历史要么留污点** |
| D3 | 介入：如果我这次用了 `git push --force`（而非 `--force-with-lease`）会怎样？ | 若有同事在此分支推过东西，会被**静默覆盖**——他的 commit 消失、他下次 pull 才发现。`--force-with-lease` 在这种情况会拒绝推送 |
| D4 | 为什么 `sonar.coverage.exclusions` 比 `sonar.exclusions` "更诚实"？ | 前者只调整**一个指标的分母**，静态分析继续跑；后者**关闭整个探测**。前者是"这个指标不适用于这类文件"，后者是"我不想知道这里有什么问题" |
| D5 | 这条命令暴露的最深的问题不是 git 用法，是什么？ | **便利参数（`-a`/`-m`/`&&`）系统性地移除了人类确认点**，而那些确认点是唯一会提示"你正在做的不是你以为的事"的环节。**效率与可观测性的取舍**——这不是 git 问题，是所有自动化的通病 |
| D6 | 用一句话说清"绿灯"在本 bootcamp 里出现过几种假象。 | 空集通过（pre-commit 空跑）、探测器被关（sonar.exclusions）、保护被条件跳过（ff 绕过 --no-commit）、魔法值当合法值（"HEAD"）、零匹配当无风险（git grep）。**共同点：退出码都是 0** |

---

## 热身题答案

- **Q1** **不会。**`-a` 只处理"已追踪且已修改/删除"的文件。如果你新建了 `sonar-project.properties`，它**没进这个 commit**——你推上去的改动里没有 sonar 部分。跑 `git show --stat HEAD | grep -i sonar` 立刻验证。
- **Q2** 因为在 git 看来完全合法：`MERGE_HEAD` 存在 → 下个 commit 就该是 merge commit；你给了 `-m` → 不用打开编辑器。**`-m` 的隐藏代价就是跳过了那个会显示 "Merge remote-tracking branch..." 的编辑器。**
- **Q3** **害了。**它消灭了 commit 与 push 之间唯一的反悔窗口。凡是链条里有"让改动离开本机"的步骤，前面必须留人类检查点。
- **Q4** 告诉我：Jira 工单 DATAPLATCORE-1265、这是个 **Airflow 2.11.2 升级分支**、目标合回 develop。**它让第 4 条 `reset --hard` 的风险等级从"可能丢点活"升到"可能推平了整个升级工作"，让第 7 条从"方向对"降到"同步对象选错了（该同步 develop 而非 master）"。**
- **Q5** **可能失败。**如果钩子里有 formatter 并且它改了文件，pre-commit 会以非 0 退出 → `git commit` 中止 → **`&&` 后面的 push 也不执行**。所以：**如果你的 push 成功了，说明钩子通过了或者被跳过了；如果你压根没看到 push 输出，可能钩子救了你一命。**去看 `git log -1` 到底存不存在。

---

## ✅ Next actions for me today

**🔴 立刻（60 秒，定案）：**
- [ ] `git log -1 --pretty='%h %p %s'` —— **parent 是两个吗？**
- [ ] `git show --stat HEAD | grep -i sonar` —— **sonar 改动真的进去了吗？**
- [ ] `git status --short` —— 有没有 `??` 开头的 sonar 文件被漏在外面
- [ ] `git branch backup/DATAPLATCORE-1265-$(date +%s)` —— **安全绳，先打再想**

**🟠 接着（5 分钟，止损）：**
- [ ] `git reflog -n 20` —— 找到 `reset --hard` **之前**那个 SHA，抄下来（`ORIG_HEAD` 已经被 merge 覆盖了）
- [ ] `git diff <那个SHA> HEAD --stat -- pyproject.toml poetry.lock` —— **升级工作还在吗？**
- [ ] `git log origin/DATAPLATCORE-1265-... --format='%an' | sort -u` —— 分支是不是只有你
- [ ] `git branch -r | grep DATAPLATCORE-1265` —— 有没有因手打分支名造出孤儿分支

**🟡 然后（修复）：**
- [ ] 走第 4 节路线 A'：回到 merge 前 → 只做 sonar 那一件事 → `git add` 显式（**别用 `-a`**）→ `git show --stat` 检查 → `--force-with-lease` 推
- [ ] 提交信息按第 5 节那个模板重写（说清改了哪个属性、为什么、为什么不用另一个）
- [ ] 确认你改的是 `sonar.coverage.exclusions` 而不是 `sonar.exclusions`
- [ ] back-merge 的需求单独提给 owner，**别混在你的升级 PR 里**

**🟢 习惯改造（今天就配，一辈子受益）：**
- [ ] shell prompt 显示 git 状态（starship / `__git_ps1`）—— 让 `|MERGING` 无法被忽略
- [ ] 别名：`git config --global alias.pushf 'push --force-with-lease'` —— 让安全的那个更好按
- [ ] 从今天起：**commit 和 push 之间永远隔一次 `git show --stat HEAD`**，不用 `&&` 连接它们
- [ ] `docs/oops-runbook.md` 新增一节："我在 merging 状态下 commit 了怎么办"

**账（第三次问了）：**
- [ ] `reset --hard` 那笔 + `pre-commit` 那笔 + 这次的 `git log -1 --pretty=%p` —— **三笔一起贴，我给你一份完整判案**

---

## 收个尾：八条命令，一条完整的事故链

```
1. git grep "apache-airflow = "            侦察：当前 pin 什么版本
2. git rev-list --count（双向）             侦察：develop/master 分家多少
3. git merge-base                          侦察：分家的形状
   ────────────── 以上只读，全部正确 ──────────────
4. git reset --hard origin/develop         💥 清空 index + 可能推平升级工作
5. git rev-parse --abbrev-ref HEAD         想起来问"我在哪"（但输出没贴）
6. poetry run pre-commit run               💥 因 index 空 → 静默空跑 → 假绿灯
7. git merge --no-commit origin/master     💥 同步对象选错 + 进入 merging 状态
8. git commit -am "fix(ci): ..." && push    💥 合并伪装成配置微调 + 立刻公开
   ────────────── 每一步退出码都是 0 ──────────────
```

**看清这条链的形状**：

没有任何一步报错。没有任何一步是"愚蠢的操作"。每一条命令单独看都是资深工程师会敲的东西。但它们串起来，制造了一个**远端分支上信息不实的提交**、一个**可能丢失的升级工作**、和一次**从未真正执行过的质量检查**。

这就是真实生产事故的全部形态。事故从来不是一个大红错误，是**一串各自成功的操作，累积出一个没人验证过的状态**。

所以整个 bootcamp，如果你只带走一句：

> **每一个让你更快的参数（`-a`、`-m`、`&&`、默认作用域、`--force`），都是用「一次人类确认」换来的。**
> **平时那次确认看起来是浪费三秒。出事的那次，它是唯一会告诉你"你正在做的不是你以为的事"的东西。**
>
> SME 不是敲得比别人快的人。是知道**哪三秒不能省**的人。

跑那四条只读命令，把输出贴上来。**这次我们把八条命令的账一次算清。**
=====
# `git log --oneline --no-merges origin/develop..origin/master` —— 这一条是回马枪，而且是能翻案的那种

好。**你回到只读了。**八条命令里出了三次险，第九条你自己收住了手，去查"master 上到底有什么 develop 没有的东西"——这正是我在第 3 节（`merge-base`）就埋下的那个动作。

而且我要先告诉你一件让你今天睡得着觉的事：

> **这条命令的输出，能反过来判决第 8 条那个 commit 到底有没有事。**

它不只是"看看 hotfix"。它是一份**追溯性的无罪/有罪证明**。第 4 节详说。

---

## 热身小测（五道，第 5 题是本节的钩子）

- **Q1** `origin/develop..origin/master` 列出的是**谁独有**的 commit？两个点写反了会怎样？
- **Q2** `--no-merges` 过滤掉了 merge commit。它有可能因此**漏掉真实的代码改动**吗？
- **Q3** 如果 master 上的某个 hotfix **已经被 cherry-pick 到 develop 了**，它还会出现在这个列表里吗？
- **Q4** 输出了 12 行，是不是意味着"有 12 个 hotfix 要回灌"？
- **Q5 反推题**：如果这条命令输出**空的**，那么你第 7 条 `git merge --no-commit origin/master` 实际发生了什么？第 8 条那个 commit 有几个 parent？

---

## 1) 命令解剖：三个部件，一个方向记忆法

```
git log --oneline --no-merges  origin/develop..origin/master
        └───┬───┘ └────┬────┘  └───────┬──────────────────┘
        一行一个     不显示            范围：
        SHA+标题     merge commit      "在右边、不在左边"
```

### 方向记忆法（这个记牢，一辈子不再搞反）

```
A..B  →  「从 A 走到 B，路上新增了什么」  →  B 独有
                          ↑
                    终点是谁，答案就是谁的

origin/develop..origin/master   →   master 独有
                                     └─ 也就是「develop 欠 master 的债」
```

**再补一个更好记的**：把 `..` 读成**箭头** `→`。`develop → master`，问的是"往 master 那边走，多了什么"。

### 三种范围写法对照

| 写法 | 含义 | 什么时候用 |
|---|---|---|
| `develop..master` | master 独有 | ✅ 你现在这条：查漏灌 |
| `master..develop` | develop 独有 | 查"develop 攒了多少待发布" |
| `develop...master`（三点） | **两边各自独有**（对称差） | 配 `--left-right` 一次看两边 |

三点版的实战写法，我平时更常用这个：

```bash
git log --oneline --no-merges --left-right --cherry-mark origin/develop...origin/master
#  <  开头 = develop 独有
#  >  开头 = master 独有
#  =  开头 = ★ 两边内容等价（cherry-pick 过的）
```

**最后那个 `=` 是本节的金矿**，第 2 节马上讲。

---

## 2) 💥 这条命令的输出**同时会偏大和偏小**

这是本节唯一真正需要你烧脑的地方。它有两个相反方向的失真，而大多数人两个都不知道。

### 偏大：拓扑 ≠ 内容（Q3 的答案）

`git log A..B` 是按 **SHA 可达性** 算的，**不看内容**。所以：

```
master:  ●─── hotfix X (sha=aaa)
             │
             └─ 有人 cherry-pick 到 develop
                       ↓
develop: ●─── hotfix X' (sha=bbb)   ← 同样的代码，不同的 SHA
```

> **结果：hotfix X 依然出现在 `develop..master` 的列表里，尽管 develop 早就有它了。**

同理，**squash merge** 和 **rebase** 也会制造这种"内容已在、SHA 不同"的幽灵。

**这就是为什么我在第 3 节让你记住 `git cherry`。**破解方式：

```bash
# 方式一：--cherry-mark，等价的 commit 前面标 '='
git log --oneline --no-merges --cherry-mark --left-right origin/develop...origin/master

# 方式二：--cherry-pick --right-only，直接把等价的过滤掉（★ 这才是"真正的欠债清单"）
git log --oneline --no-merges --cherry-pick --right-only origin/develop...origin/master

# 方式三：老派但直观
git cherry -v origin/develop origin/master
#   '+' 开头 = 内容真的只在 master（真欠债）
#   '-' 开头 = 内容已经在 develop（假警报）
```

**对比你原始命令和加固版的输出行数差**——那个差值就是"被 cherry-pick 过的幽灵数量"。很多团队一看 `develop..master` 有 30 个 commit 就慌，跑一遍 `--cherry-pick` 发现真欠债只有 3 个。

### 偏小：`--no-merges` 会藏东西（Q2 的答案）

`--no-merges` 的初衷是好的——过滤掉 `Merge branch 'x' into master` 这类噪音，让你看清"人写的改动"。但它有一个真实的盲区：

> **evil merge（邪恶合并）：merge commit 本身可以携带只存在于它内部的代码改动。**

什么时候会发生？**解冲突的时候。**你解冲突写下的那几行"两边都不是"的折中代码，**只存在于那个 merge commit 里**。`--no-merges` 把它整个跳过了。

```
        ┌─ 分支 A 改了 config 的第 10 行
merge ──┤
        └─ 分支 B 也改了第 10 行
             ↓
    解冲突时你写了第三种写法
             ↓
    这几行只活在 merge commit 里
             ↓
    --no-merges 看不见 ❌
```

**所以完整的诊断需要两遍**：

```bash
git log --oneline --no-merges origin/develop..origin/master   # 人写的 commit（你跑的）
git log --oneline --merges    origin/develop..origin/master   # ★ 补一遍看合并事件
git diff --stat origin/develop origin/master                  # ★★ 终极答案：内容差异
```

**最后那条 `git diff --stat` 是唯一不会骗你的。**因为它比较的是**两棵树的最终内容**，完全绕过拓扑问题。

> **心法：`log` 回答"发生过什么"，`diff` 回答"现在差什么"。**
> 讲故事用 log，做决策用 diff。**你要合并，最终关心的是后者。**

---

## ✅ 本节回顾题
1. 同一个 hotfix 为什么可以既"在 develop 里"又"出现在 `develop..master` 列表里"？
2. `--no-merges` 的盲区叫什么？什么操作会制造它？
3. 一句话区分 `git log` 和 `git diff` 在这个场景的分工。

---

## 3) 怎么读输出：三分类 triage

拿到列表，别一行行读细节，先按**类型**分桶。这是我看这种列表的实际动作：

```bash
# 带上作者和相对时间，信息密度高一倍
git log --no-merges --format='%h %ad %an%n    %s' --date=short origin/develop..origin/master
```

| 看到什么 | 桶 | 要不要回灌 | 优先级 |
|---|---|---|---|
| `fix:` / `hotfix:` / `revert:` | **真 hotfix** | ✅ 必须 | 🔴 高 |
| 改了 `pyproject.toml` / `poetry.lock` | **依赖变更** | ⚠️ **看情况——这是你的雷区** | 🔴 高（见第 5 节） |
| `chore(release):` / 版本号 bump / tag 相关 | 发布杂务 | ❌ 通常不回灌 | 🟢 低 |
| 改 CI/CD、`.github/` | 流水线 | ✅ 通常要 | 🟡 中 |
| `docs:` | 文档 | 🤷 无害 | 🟢 低 |

**快速定位高危项**（我真会敲的）：

```bash
# 谁碰了依赖文件？
git log --oneline --no-merges origin/develop..origin/master -- pyproject.toml poetry.lock

# 谁碰了 DAG？
git log --oneline --no-merges origin/develop..origin/master -- dags/

# 一次看清每个 commit 碰了什么
git log --oneline --stat --no-merges origin/develop..origin/master | head -60
```

**那个带 pathspec 的第一条命令，是你今天最该跑的一条。**理由在第 5 节。

---

## 4) 🎯 用这条命令反推第 8 条的判决（Q5 的答案）

来，逻辑推理时间。这是本节我最想让你看到的东西。

**已知条件（你自己敲的命令序列）**：

```
第 4 条: git reset --hard origin/develop
         → 你的分支 tip  ==  origin/develop   ①

第 7 条: git merge --no-commit origin/master
         → 把 master 合进你的分支

第 8 条: git commit -am "fix(ci): ..."
         → ??? 到底是不是 merge commit
```

**推理**：

```
如果本条命令输出为空
   ⇒ master 没有 develop 缺的 commit
   ⇒ master 是 develop 的祖先（master ⊆ develop）
   ⇒ 结合 ①，master ⊆ 你的分支
   ⇒ 第 7 条的 merge 输出是 "Already up to date."
   ⇒ 没有进入 merging 状态，没有 MERGE_HEAD
   ⇒ ✅ 第 8 条是个普通的单 parent commit
   ⇒ 上一节我那通紧急调门，可以整段降级为"下次别用 -am + &&"
```

```
如果本条命令输出非空
   ⇒ master 有 develop 缺的东西
   ⇒ 第 7 条真的合了东西，进了 merging 状态
   ⇒ ⚠️ 第 8 条极可能是 merge commit，信息却写着 "fix(ci): tune sonar exclusions"
   ⇒ 上一节的修复流程照跑
```

**一条命令定案**（这个才是最快的，但上面那条推理链值得你自己走一遍）：

```bash
git log -1 --pretty='%h parents=%p %s'
```
`parents` 后面**两个** SHA = merge commit，**一个** = 普通 commit。

> **教学点**：能用**逻辑推理**从间接证据反推出结论，是 SME 和"会敲命令的人"最大的差别。
> 直接查当然更快。但**当直接证据拿不到的时候（生产环境、别人的机器、三个月前的事故），你只剩推理链。**
> 这就是为什么我要你练这个。

---

## 5) 🔴 本 Airflow 升级分支的雷区：master 上的依赖变更

现在把你的**真实上下文**接上——你在 `DATAPLATCORE-1265-airflow-2.11.2-upgrade-develop` 分支上。

**最坏的情况长这样**：

```
你的分支:  pyproject.toml  apache-airflow = "2.11.2"   ← 你辛苦升的
                     ↓  merge origin/master
master 上有:  hotfix「紧急回退 Airflow 到 2.9.1」        ← 生产出事回退了
                     ↓
        合并结果: 冲突，或者更糟——
        如果 git 判定 master 的改动"更新"而自动取了它
                     ↓
        你的升级被静默降级回 2.9.1
                     ↓
        CI 跑绿（因为 2.9.1 是稳定的），PR 看起来没问题
                     ↓
        🔴 一个名叫 "upgrade to 2.11.2" 的 PR，实际把版本设成了 2.9.1
```

**这是本 bootcamp 讲了九节的那个主题的最终形态**：不是崩溃，是**一个名字和内容不符的东西通过了所有检查**。

**立刻跑这一条**：

```bash
git log --oneline --no-merges origin/develop..origin/master -- pyproject.toml poetry.lock
```

| 输出 | 含义 | 动作 |
|---|---|---|
| 空 | master 没碰过依赖 | 😮‍💨 松口气，这个雷不存在 |
| 有 commit | **master 动过依赖声明** | 🔴 立刻看内容：`git show <sha> -- pyproject.toml` |

然后**验证你分支上的版本还是不是你要的那个**：

```bash
git grep -n -E 'apache[-_]airflow' HEAD -- pyproject.toml
```

**看见这条命令了吗——这就是第 1 条命令。**九条命令绕了一整圈，回到了原点。只不过这一次，你知道它为什么重要了。

```
第 1 条：git grep "apache-airflow = "        ← 那时你只是"查个版本"
第 9+1 条：git grep 同一个东西               ← 现在你在"验证升级工作没被合并吃掉"
                                              同一条命令，完全不同的分量
```

---

## ✅ 本节回顾题
1. "master 上的依赖变更"为什么对**升级分支**特别危险？
2. 为什么这个风险是"静默"的？哪些检查会放它过去？

---

## 6) 动手练习

### 练习 A（只读 · 三重对照）
把这三条并排跑，**记下三个行数**：
```bash
git fetch --all --prune
git log --oneline --no-merges origin/develop..origin/master | wc -l                          # 你的原版
git log --oneline --no-merges --cherry-pick --right-only origin/develop...origin/master | wc -l  # 去掉幽灵
git log --oneline --merges origin/develop..origin/master | wc -l                             # 被 --no-merges 藏起来的
```
**交付**：一句话解释三个数为什么不同。**如果第一个 > 第二个，差值就是被 cherry-pick 过的假警报。**

### 练习 B（决策 · 分桶）
把输出按第 3 节那张表分桶，标出**必须回灌**的那几个。
- **坑**：别只看 commit 标题。`chore: bump deps` 这种标题可能藏着 Airflow 版本变更。**至少对可疑的跑一次 `git show --stat <sha>`。**

### 练习 C（bug hunt · 造一个 cherry-pick 幽灵）
测试仓库里：master 上提一个 commit → cherry-pick 到 develop → 跑 `develop..master`（**仍然显示它**）→ 跑 `--cherry-pick --right-only`（**消失了**）→ 跑 `git cherry -v`（**前面是 `-`**）。
- **教学点**：亲手造一次，你以后看这种列表就不会再被数字吓到。

### 练习 D（bug hunt · 造一个 evil merge）
造一个冲突，解冲突时写第三种写法，提交 merge。然后跑 `--no-merges`——**你那几行代码不见了**。再跑 `git diff` ——**它出现了**。
- **教学点**：`log` 会漏，`diff` 不会。**做合并决策前，最后一眼必须是 `diff`。**

### 练习 E（写成资产）
把这一套三重对照 + 分桶 + 依赖文件专查，加进 `scripts/repo-doctor.sh` 的 "back-merge 债务" 段落。
- **交付物**：`docs/back-merge-checklist.md` —— 这是你两周内能交出的、**最能证明你懂发布工程**的一页文档。

---

## 7) 主管拷问

**Q1（入门）"master 上有多少东西没回灌到 develop？"**
- **弱答**："我跑了 `git log develop..master`，有 N 个。"
- **强答**："拓扑上 N 个，但真实欠债少于这个数。`develop..master` 按 SHA 可达性算，被 cherry-pick 过来的 hotfix 会重复计数——用 `--cherry-pick --right-only` 过滤后是 M 个。另外我原来那条加了 `--no-merges`，会漏掉 evil merge 里的冲突解决代码，所以我补跑了 `--merges` 和 `git diff --stat` 交叉验证。**最终我做决策靠 diff，log 只用来讲故事。**"
- **追问陷阱**："那到底该回灌哪几个？" → 分桶：真 hotfix 必须、CI 改动通常要、release chore 通常不要、**依赖变更要单独评估**。而且回灌本身该由分支 owner 做，不是我在 feature 分支上顺手 merge。

**Q2 "你怎么确认你的 Airflow 升级没被这次合并吃掉？"**
- **弱答**："CI 是绿的。"
- **强答**："CI 绿恰恰不能作为证据——如果版本被降回一个稳定老版本，CI 会**更**绿。我用三层直接验证：① `git log ... -- pyproject.toml poetry.lock` 看 master 有没有动过依赖声明；② `git grep apache-airflow HEAD -- pyproject.toml` 确认我分支上的声明还是 2.11.2；③ `poetry install --sync` 后打印 `airflow.__version__` 确认运行时。**声明层、锁层、运行时层三点共线才叫确认。**"

**Q3（staff 级）"怎么让这类 back-merge 债务不再靠人肉发现？"**
- **强答**：

| 层 | 机制 | 成本 | 抓什么 |
|---|---|---|---|
| 可观测 | CI 定时任务跑 `--cherry-pick --right-only`，超过阈值就发通知 | 低 | 债务累积趋势 |
| 自动化 | 检测到分家自动开 back-merge PR（**只开 PR，不自动合**） | 中 | 让债务变成待办事项 |
| 门禁 | 发布流水线上断言"master ⊆ develop"，否则拦住 release | 中 | 防"发布覆盖 hotfix" |
| 结构 | 改流程：hotfix 走 `hotfix/*` 分支，同时 PR 到 master **和** develop | 高（组织成本） | **从源头消灭债务** |

  "**只做一件的话我做第一层**——因为债务问题的根因是"没人知道有债"，先让它可见。冲突解决不能自动化（尤其依赖版本冲突那种需要产品判断的），所以目标是'自动发现 + 自动开 PR + 人工解'，不是全自动。
  长期我会推第四层：**hotfix 同时 PR 到两条线**，从结构上让债务无法产生。但这是流程改动，我不会在入职第二周提。"

---

## 8) 溯源自审（Reviewer 帽）

| 说法 | 来源 | 置信度 |
|---|---|---|
| `A..B` = B 独有；三点 = 对称差 | 通用 git 知识 | 高 |
| cherry-pick/squash/rebase 造成拓扑与内容不一致 | 通用 git 知识 | 高 |
| `--cherry-pick` / `--cherry-mark` / `--right-only` / `git cherry` 的行为 | 通用 git 知识 | 高 |
| evil merge：merge commit 可携带独有改动，`--no-merges` 会跳过 | 通用 git 知识 | 高 |
| `git diff` 比较树内容，绕过拓扑问题 | 通用 git 知识 | 高 |
| **"输出为空 ⇒ 第 8 条是普通 commit"这条推理** | **逻辑推论，前提是第 4 条之后你没切分支/没提交过别的** | **中 —— 推理链有效，但前提我无法验证。用 `git log -1 --pretty=%p` 直接定案更可靠** |
| "master 可能有 Airflow 降级 hotfix" | **纯假设场景**，用于说明风险类型 | **低 —— 我完全不知道 master 上有什么。这是教学用的假想例子，不是我对你仓库的判断** |
| **这条命令在你那儿输出了什么** | **未知** | — 我读不到你的仓库 |

**边界重申**：我没有 shell / 文件系统工具（读不到 `~/ws/`），前两次对知识库的穷尽 grep（`airflow|pyproject|poetry|git|branch|develop` 和 `pre-commit|ruff|lint|hook`）**全部 No matches**——挂载的那三份文档是 MQ 的教学与风格指南，与本题无关。网络搜索已关闭，所以我不核对 Airflow 2.11.2 的具体 release 内容。

**本节所有"你的仓库如何"的说法都是假设或推论，没有一条是观察。**

**判案只差这几行**（这次真的只差一点点）：
1. **这条命令的输出**（有几行、都是什么）
2. `git log -1 --pretty='%h parents=%p %s'` ← **一眼定案第 8 条**
3. `git log --oneline --no-merges origin/develop..origin/master -- pyproject.toml poetry.lock` ← 依赖雷区

---

## 9) 答辩（换你说，60 秒一题）

| # | 问题 | 要点 |
|---|---|---|
| D1 | 为什么"12 个 commit 没回灌"这句话本身就可能是错的？ | 拓扑计数会把 cherry-pick 过的重复计入（偏大），`--no-merges` 会漏掉 evil merge 的改动（偏小）。**两个方向的失真同时存在**，只有 `git diff` 给出无歧义答案 |
| D2 | 反事实：如果我第 7 条前先跑了这条命令，会有什么不同？ | 我会先知道要合进来的是什么、有没有碰依赖文件，从而判断"该不该合"和"该合谁"。**很可能我会发现该同步的是 develop 而不是 master，整条事故链就不会发生** |
| D3 | 介入：如果我看到列表里有个 `revert:` commit，意味着什么？ | master 上撤销过某个改动。如果 develop 里那个被撤销的东西还在，**合并方向搞反会把已知有问题的代码重新带回生产**。revert 类 commit 是回灌优先级最高的一类 |
| D4 | 为什么"CI 绿"不能证明升级没被吃掉？ | 如果版本被降回稳定老版本，CI 会**更容易**绿。**绿灯只证明"当前配置能跑"，不证明"当前配置是我想要的"**。这是本 bootcamp 第七次遇到同一个陷阱 |
| D5 | `log` 和 `diff` 在合并决策里的分工，一句话。 | log 讲**过程**（谁在什么时候为什么改的，用于分桶和沟通），diff 讲**结果**（现在到底差什么，用于决策和验证）。**沟通用 log，签字用 diff** |

---

## 热身题答案

- **Q1** 列出 **`origin/master` 独有**的 commit（develop 欠 master 的债）。写反成 `master..develop` 就变成"develop 待发布的东西"——**问题完全不同，而且不会报错，这是最容易犯的静默错误。**记住：**终点是谁，答案就是谁的。**
- **Q2** **会漏。**evil merge 中，解冲突时写下的代码只存在于 merge commit 里，`--no-merges` 整个跳过。补跑 `--merges` 和 `git diff --stat`。
- **Q3** **会出现。**cherry-pick 产生新 SHA，拓扑上仍算 master 独有。用 `--cherry-pick --right-only` 或 `git cherry -v` 过滤。
- **Q4** **不是。**12 是拓扑数，可能虚高（cherry-pick 幽灵）也可能虚低（evil merge 隐藏）。而且里面有 release chore、docs 这类不需要回灌的。**先分桶，再数数。**
- **Q5** 输出为空 ⇒ master ⊆ develop ⇒ 结合第 4 条的 `reset --hard origin/develop`，master ⊆ 你的分支 ⇒ 第 7 条是 `Already up to date.` ⇒ **没进 merging 状态** ⇒ **第 8 条只有一个 parent，是普通 commit** ⇒ 上一节的紧急程度整段下调。反之则照上一节的修复流程走。

---

## ✅ Next actions for me today

**🔴 立刻（60 秒，三条只读，一次定案）：**
- [ ] `git fetch --all --prune`（永远第一步，这条命令的结果依赖它）
- [ ] `git log -1 --pretty='%h parents=%p %s'` —— **parents 一个还是两个？第 8 条的判决书**
- [ ] `git log --oneline --no-merges origin/develop..origin/master -- pyproject.toml poetry.lock` —— **依赖雷区有没有踩到**

**🟠 接着（5 分钟，把这条命令做对）：**
- [ ] 跑练习 A 的三重对照，记下三个行数
- [ ] `git diff --stat origin/develop origin/master` —— **唯一不骗人的那条**
- [ ] `git grep -n -E 'apache[-_]airflow' HEAD -- pyproject.toml` —— **确认你分支上还是 2.11.2**（回到第 1 条命令，闭环）
- [ ] 按第 3 节分桶，标出真正必须回灌的那几个

**🟡 然后（做正确的事）：**
- [ ] 如果 master 确实有欠债：**把它作为一个独立问题提给分支 owner**，不要在你的升级分支上顺手 merge
- [ ] 如果第 8 条确认是 merge commit：走上一节路线 A'（backup 分支 → 回退 → 只做 sonar → 显式 `add` → `git show --stat` 检查 → `--force-with-lease`）
- [ ] 确认 sonar 改的是 `coverage.exclusions` 而非 `exclusions`

**🟢 沉淀（今天就写，别攒）：**
- [ ] `docs/back-merge-checklist.md`：三重对照 + 分桶表 + 依赖文件专查
- [ ] 别名：`git config --global alias.debt 'log --oneline --no-merges --cherry-pick --right-only'` —— 让正确的那条更好按
- [ ] 在 runbook 里写下这句："log 讲过程，diff 签字"

---

## 收个尾：九条命令，一个圆

```
1. git grep "apache-airflow = "              问朝代
2. git rev-list --count（双向）               量国界
3. git merge-base                            查血缘
   ─────── 侦察三连，全部正确 ───────
4. git reset --hard origin/develop           💥 推平（清 index，可能推平升级工作）
5. git rev-parse --abbrev-ref HEAD           想起来问"我在哪"
6. poetry run pre-commit run                 💥 空跑，假绿灯
7. git merge --no-commit origin/master       💥 同步对象选错
8. git commit -am "fix(ci)..." && push       💥 合并伪装成配置微调，且已公开
   ─────── 每一步退出码都是 0 ───────
9. git log --no-merges develop..master       ✅ 回马枪：本该在第 7 条之前跑的那一条
                                                 而且它能追溯判决第 8 条
```

**这九条命令的形状，就是一次真实事故的完整生命周期**：

**侦察（对）→ 行动（错，但每步都成功）→ 事后诊断（对）**

而最有意思的是第 9 条：**它不是新知识，它是第 3 节内容的正确使用时机。**你知道这条命令，你在第 3 节还跟我一起分析过它。你只是**在错误的顺序里用了它**。

> **绝大多数事故不是因为不知道，是因为顺序错了。**
> 该在决策前跑的诊断，跑在了决策后面。
> 该在 push 前做的检查，做在了 push 后面。
>
> **SME 的核心能力不是"知道更多命令"，是"知道每个动作的正确时序"——什么必须在前面，什么绝不能省。**

这一整个 bootcamp，九条命令，其实只教了一件事：

**在"读"和"写"之间，永远留一次呼吸。**

把那三行输出贴上来。我们结账。
=====
# 两点 vs 三点：git 里最反直觉的一对语法

这个问题问得好，而且你问的时机对——你手上正好有两条命令，一条用 `diff`，一条用 `rev-list`，**而这两个命令对同一个 `...` 的解释是不一样的，甚至可以说是反的。**

这是 git 里我见过最多人踩、且踩了以后自己都不知道的一个坑。先把答案摆出来。

---

## 1) 核心对照表（这张表值得贴在显示器上）

| 语法 | `git log` / `git rev-list`（枚举 commit） | `git diff`（比较内容） |
|---|---|---|
| `A B`（无点） | — | 比较两个 tip |
| `A..B` | **B 独有**的 commit（单边） | 完全等价于 `git diff A B`，**点是装饰品** |
| `A...B` | **两边各自独有**（对称差，更宽） | `merge-base(A,B)` → `B`，**只看 B 侧（更窄）** |

**注意那个反转**：

```
git log :   两点 = 窄（一边）      三点 = 宽（两边）
git diff:   两点 = 宽（全部差异）  三点 = 窄（只 B 侧）
                    ↑
            同一个符号，相反的宽窄关系
```

**为什么会这样**——这不是 git 在恶作剧，是两个命令的**输出类型**不同：

- `log` 输出的是一个 **commit 集合**，"两边"是可表达的（列出来就行）
- `diff` 输出的是**两棵树之间的差异**，本质上只能有两个端点，"两边"根本无法表达（那是两个 diff）

所以 git 在 `diff` 里把三点用在了唯一有用的地方：**把基准点从 A 挪到 merge-base**。

---

## 2) 统一的记忆法（我自己用的）

> **三点 = 「以 merge-base 为原点」。**
>
> - 在 `log` 里：从原点出发，**两条岔路上的 commit 全列出来**
> - 在 `diff` 里：从原点出发，**只走 B 这一条路，看内容变成了什么**

```
                    merge-base ← 三点语法的原点
                        │
        A ──────────────●───○───○───○
                        │╲
                        │ ╲
        B ──────────────┴──□───□───□───□

  log  A..B   →  □□□□              （只右边）
  log  A...B  →  ○○○ + □□□□        （两边都要，配 --left-right 标记归属）

  diff A..B   →  ○○○ 的反向 + □□□□ 混在一起（两个 tip 的净差异）
  diff A...B  →  只有 □□□□ 的内容效果（B 自分家以来的改动）
```

---

## 3) 为什么 `--left-right --count` **必须**用三个点

`--left-right` 的作用是**给每个 commit 打上"它来自哪一边"的标记**：

```
<  = 来自左边（第一个 ref）
>  = 来自右边（第二个 ref）
=  = 内容等价（配 --cherry-mark 时出现，就是我们上节说的 cherry-pick 幽灵）
```

**问题来了**：`A..B` 展开是 `^A B`——A 是**被排除**的，它的 commit 压根不在遍历结果里。

> **一个只有右边的集合，标记左右毫无意义。**左边永远是空的。

```bash
# 两点：左边被排除了，左侧计数必然是 0，等于白写 --left-right
git rev-list --left-right --count origin/master..origin/develop
# 三点：两边都在遍历里，标记才有信息量
git rev-list --left-right --count origin/master...origin/develop
#   → 输出两个数，制表符分隔:   3<TAB>47
#                              │      └── 右 = develop 独有 = ahead
#                              └───────── 左 = master  独有 = behind
```

> ⚠️ 我说"两点时左侧恒为 0"是从 `^A B` 的语义推的，逻辑上必然。但**你花 5 秒自己跑一遍两点版对比一下**，眼见为实——这是本 bootcamp 一贯的规矩。

### 还有个连带的坑：三点但**不加** `--left-right`

```bash
git rev-list --count origin/master...origin/develop
# → 50    ← 一个数。3+47 的和。
#           你知道"总共差 50 个"，但完全不知道哪边多哪边少。
#           对做决策来说，这个数字几乎没有价值。
```

**所以 `--left-right --count` + 三点是一个不可拆的三件套。**拆掉任何一个，你要么拿到 0，要么拿到一个无法解读的和。

**顺序即语义**：左边写谁，谁就是 "behind" 的度量。`origin/master...origin/develop` → 左是 master → 左边那个数 = **develop 欠 master 的债**（我们上一节追的那个东西）。**别写反，写反了不报错。**

---

## ✅ 快问快答（先答再往下）
1. 为什么 `diff` 无法表达"两边各自的改动"？
2. `--left-right` 加在两点范围上，为什么等于白写？
3. `git rev-list --count A...B`（不加 left-right）的输出为什么没用？

---

## 4) 解码你那两条命令

### `git diff HEAD...origin/master`

**展开等价于**：
```bash
git diff $(git merge-base HEAD origin/master) origin/master
```

**它回答的问题**：**"master 自我们分家以来，内容上改了什么？"** —— 完全**不含**你自己在分支上的改动。

**这正是你在第 7 条 `git merge --no-commit` 之前**该跑**的那个只读预览。**因为它把"对方带进来的东西"单独隔离出来了。

**对比一下两点/无点版本**：

| 命令 | 输出内容 | 什么时候用 |
|---|---|---|
| `git diff HEAD origin/master` | 两个 tip 的**净差异**——你的改动会以"反向 diff"的形式混进来（你加的行显示为被删） | 想知道"这两个状态最终差多少" |
| `git diff HEAD...origin/master` | **只有 master 侧的改动** | ✅ "合进来会带什么"——噪音小得多 |

**举个具体感受**：你在升级分支上把 Airflow 从 2.9 改成 2.11.2。
- 两点 diff 会显示 `- apache-airflow = "2.11.2"` / `+ apache-airflow = "2.9.1"`——看起来像"master 要把你降级"，**其实那只是你自己的改动被反向显示了**，master 可能压根没碰这个文件。
- 三点 diff 里这一行**根本不出现**，因为 master 侧没改过它。

> **这就是三点 diff 的全部价值：把"我的改动"从视野里剔除，只留"对方的改动"。**
> GitHub / GitLab 的 PR diff 就是三点 diff（`base...head`）——这也是为什么 PR 页面上你看不到 base 分支后来的新提交。**知道这一点，你以后就能解释"为什么 PR diff 和我本地 `git diff` 不一样"。**

**但它不是合并结果，三条边界要说清楚**：
- 它**不预测冲突**。它只告诉你对方改了什么，不告诉你这些改动会不会跟你的打架。
- **多个 merge-base 时（criss-cross）有歧义**：三点 diff 只挑一个基准。跑前先 `git merge-base --all HEAD origin/master | wc -l` 确认是 1。
- **无共同祖先时直接失败**。

### `git rev-list --left-right --count origin/master...origin/develop`

一次拿到 **behind / ahead** 两个数，替代了你第 2 条那两行 `&&` 串起来的命令。

**它比原来那两条好在哪**：
- **一次遍历**，不是两次
- **不会因为 `&&` 前半段失败而静默跳过后半段**（还记得那个坑吗）
- 两个数并排出现，**不会看错顺序**

---

## 5) 利刃汇总

| 坑 | 症状 | 防法 |
|---|---|---|
| `log` 用两点却想看两边 | 左侧恒 0，你以为"master 没欠债" | 用三点 |
| `diff` 用三点却想看净差异 | 漏掉你自己那侧的改动 | 想看净差异用两点/无点 |
| `diff` 的 `..` 以为有特殊含义 | 没有，纯装饰 | 知道就行，`git diff A B` 更清楚 |
| 三点 + 多个 merge-base | 基准被任选一个，结果有歧义 | 先 `merge-base --all \| wc -l` |
| `--count` 三点不加 `--left-right` | 得到一个和，无法解读 | 三件套一起用 |
| 左右顺序写反 | 把 ahead 当 behind，**不报错** | 记住：左边写谁，谁是 behind 的度量 |
| 忘 `git fetch` | 所有数字都是历史剧 | 永远第一步 |

---

## 6) 三分钟练习（亲手验证，胜过读十遍）

```bash
git fetch --all --prune

echo "--- log 两点 vs 三点 ---"
git rev-list --count origin/master..origin/develop        # 单边
git rev-list --left-right --count origin/master..origin/develop   # ★ 看左边是不是 0
git rev-list --left-right --count origin/master...origin/develop  # ★ 两个数都有
git rev-list --count origin/master...origin/develop       # ★ 一个和，体会它多没用

echo "--- diff 两点 vs 三点 ---"
git diff --stat HEAD origin/master        -- pyproject.toml   # 净差异（含你的改动）
git diff --stat HEAD...origin/master      -- pyproject.toml   # ★ 只有 master 侧

echo "--- 基准唯一性 ---"
git merge-base --all HEAD origin/master | wc -l           # 必须是 1
```

**交付**：用一句话说明第 4 条（`--count` 三点不带 left-right）为什么是"技术上正确、决策上无用"的输出。

**加分项**：把上一节学的幽灵过滤也叠上去，这是最终形态——
```bash
git log --oneline --no-merges --left-right --cherry-mark origin/master...origin/develop
#   <  develop 独有   >  master 独有   =  内容等价（cherry-pick 幽灵）
```

---

## 7) 答辩（换你说，60 秒一题）

| # | 问题 | 要点 |
|---|---|---|
| D1 | 为什么同一个 `...` 在 log 里"更宽"、在 diff 里"更窄"？ | 输出类型不同。log 输出集合，"两边"可表达；diff 输出两树之差，只能有两个端点，"两边"无法表达 → git 把三点用在唯一有用的地方：**把基准挪到 merge-base** |
| D2 | 为什么 PR 页面的 diff 和我本地 `git diff main feature` 不一样？ | 平台用的是三点 diff（`base...head`），只显示 feature 侧的改动；你本地两点是净差异，会把 base 后来的新提交以反向 diff 混进来 |
| D3 | 反事实：如果我第 7 条之前跑了 `git diff HEAD...origin/master -- pyproject.toml poetry.lock`，会怎样？ | 我会在动手前就看清 master 有没有碰依赖声明。**大概率会发现该同步的是 develop 而不是 master，整条事故链不会发生** |
| D4 | 介入：`--left-right --count` 左右写反了会怎样？ | 得到两个数字但语义互换，把 ahead 当 behind。**不报错、不为空、格式完全正常** —— 这是本 bootcamp 第 N 个静默失败：**参数顺序错误从不告警** |

---

## 8) 溯源（Reviewer 帽，简短版）

| 说法 | 来源 | 置信度 |
|---|---|---|
| `log` 两点=单边、三点=对称差 | 通用 git 知识 | 高 |
| `diff A..B` ≡ `git diff A B`（点无效） | 通用 git 知识 | 高 |
| `diff A...B` ≡ `diff merge-base(A,B) B` | 通用 git 知识 | 高 |
| `--left-right --count` 输出 `左<TAB>右` | 通用 git 知识 | 高 |
| 平台 PR diff 是三点语义 | 通用知识（GitHub/GitLab 惯例） | 中高 |
| 两点 + `--left-right` 时左侧为 0 | **从 `^A B` 语义逻辑推出，必然成立**，但我未实测 | 中高 —— **练习里 5 秒可验证** |
| 多 merge-base 时三点 diff 只取一个基准 | 通用 git 知识 | 中高 —— 用 `merge-base --all` 规避 |
| **你仓库的实际数字** | **未知** | — 无 shell / 文件系统工具，读不到 `~/ws/`；网络搜索关闭 |

---

## 热身答案

1. **diff 的输出类型只允许两个端点。**"两边各自的改动"本质上是两个 diff，不是一个 diff——所以 git 没法用一个 `diff` 表达它，转而把三点用于挪动基准。
2. 因为 `A..B` 展开为 `^A B`，**A 被排除在遍历之外**，左侧集合为空，标记左右没有信息量。
3. 它给出的是 3+47=50 这样的**和**。技术上正确，但你无法判断哪边多哪边少——而 back-merge 决策**完全**取决于这个方向。**一个不可解读的正确数字，等于没有数字。**

---

## ✅ Next actions

- [ ] 跑第 6 节那七行，亲眼确认"两点 + `--left-right`"的左侧是 0
- [ ] `git diff --stat HEAD...origin/master -- pyproject.toml poetry.lock` —— **这条是你第 7 条动手前欠下的那次预览，现在补上**
- [ ] `git merge-base --all HEAD origin/master | wc -l` —— 确认基准唯一（不是 1 就别用三点 diff 下结论）
- [ ] 把两个别名配上，让正确的写法更好按：
  ```bash
  git config --global alias.div  'rev-list --left-right --count'
  git config --global alias.incoming 'diff --stat HEAD...'
  ```
- [ ] 在 `docs/back-merge-checklist.md` 里加一节"两点/三点对照表"——**这一页会救到你以后每一个新同事**

---**一句话收尾**：

> **两点问"最终差多少"，三点问"自从分家以来各自干了什么"。**
>
> 前者是**状态**问题，后者是**责任归属**问题。
> 做 code review、做 back-merge、写 PR 描述——你要的几乎永远是后者。
>
> 而 `--left-right` 的存在意义只有一句：**在一个包含两边的集合里，告诉你每一行是谁的账。**没有两边，就没有账可分。

（顺带一提：你这次问的是"为什么"，不是"怎么敲"。**这个转变本身就是 SME 化的信号**——记住命令的人靠搜索，理解语义的人靠推导。）