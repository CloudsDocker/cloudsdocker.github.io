1. 主标题
每个工程师都在运行你工具链的一个私有分支
一条无聊的 Git 命令，暴露了配置溯源缺失，以及为什么客户端配置是平台工程里最后一块无人审计的表面

2. 备选标题（5 个）
git config --get-regexp '^alias\.'：你组织里成本最低的一次审计
没有溯源的配置，本质上就是未经测试的状态
你的 Git alias 是一份团队意图的分布式缓存，而没人做失效
别在客户端做策略强制：一次 Git 配置事故复盘
级联问题：CSS、Kubernetes 与 Git 是同一种失败
3. 执行摘要
多数工程师把 Git alias 当作个人手感优化——无害，够不上架构关注的门槛。这是一次范畴错误。

Alias 是版本控制系统 API 表面的用户态扩展，而且它从不单独出现：它捆绑着一个更大的负载——那套分层、按优先级解析、没有溯源信息的配置级联，它决定了每台机器如何解释团队共享的命令。同一个 shell 动词，在不同同事机器上产出不同的历史形状、不同的行尾、不同的冲突解析结果、不同的强推语义。静默发生，且没有任何遥测。

git config --get-regexp '^alias\.' 只是打开这扇门的把手。门后的东西才有意思：一个与 CSS 级联、Kustomize overlay、Spring profile 结构同型的解析算法，共享同一个核心失败模式——后写胜出，且来源不可见。

战略结论:客户端配置是「人机工效平面」,永远不是「强制平面」。 把策略写进 .gitconfig 的团队,等于在浏览器里做校验,然后管它叫安全。

4. 正文
这条命令，以及为什么它不是重点
bash

Collapse
Save
Copy
1
git config --get-regexp '^alias\.'
输出：


Collapse
Save
Copy
1
2
3
4
alias.st status -sb
alias.up pull --rebase --autostash
alias.pf push --force-with-lease
alias.nah !git reset --hard && git clean -df
四行，十五秒。现在跑真正重要的那个版本：

bash

Collapse
Save
Copy
1
git config --show-scope --show-origin --get-regexp '^alias\.'

Collapse
Save
Copy
1
2
global  file:/home/dev/.gitconfig    alias.up pull --rebase --autostash
local   file:.git/config             alias.up pull
同一个动词，两个定义。后者胜出。没人知道它存在。

这六行终端输出就是整篇文章。下面只是解释它为什么比你以为的更贵。

第 1 层 — 表层：工程师看到的东西
Alias 是字符串替换。git st → git status -sb。便宜、私人、随手就忘。

三个必须精确掌握的表层事实——因为它们在中文技术博客里几乎总是被写错：

事实： --get-regexp 匹配的是键名，不是值。模式是 POSIX 扩展正则（ERE），不支持 \d、\w、前向断言。而且是非锚定的，所以 alias 会同时命中 alias.st 和 my.aliases.legacy。加锚点：'^alias\.'。

事实： 无匹配时，无输出，退出码 1。在 set -e 下这会直接终止你的 bootstrap 脚本。这个坑在新人环境自动化里反复出现。

事实： alias 无法覆盖内置命令。alias.push = push --force-with-lease 完全无效。你以为装上的那层安全护栏根本不存在。（这一条事实，直接推翻了网上大量「Git 加固」建议。）

第 2 层 — 机制层：它是级联，不是文件
多数人脑中的模型是「Git 读我的 .gitconfig」。真实模型是对最多五个来源做有序合并：

优先级
作用域
位置
1（最低）
--system
/etc/gitconfig
2
--global
~/.gitconfig、~/.config/git/config
3
--local
$GIT_DIR/config
4
--worktree
每 worktree 独立，需 extensions.worktreeConfig
5（最高）
命令行
git -c key=value …


再加上 [include] 与 [includeIf]：被包含的文件在包含点处插入——也就是说，include 的顺序（而非文件身份）决定谁胜出。

几个让人意外的解析语义：

单值键：最后读到的值胜出。之前的值不是合并，是被遮蔽。
多值键（remote.origin.fetch、include.path、safe.directory）：所有值累积。一个键属于哪一类，是消费它的代码的属性，不是配置文件的属性——没有 schema 可查。
section 与 key 不区分大小写，输出时归一化为小写；subsection（如 remote."Origin"）区分大小写。这种不对称会产出「看起来一样、行为不一样」的配置。
这是一个有优先级、无 schema 的级联。对照组很有教育意义：CSS 级联、Kustomize overlay 合并、Spring profile 分层、Terraform 变量优先级、/etc 与用户 dotfiles。它们产生同一类 bug，而每个成熟的系统最终都长出同一个解药：溯源工具。浏览器 devtools 告诉你哪条 CSS 规则赢了；kubectl kustomize 渲染合并结果；Git 的答案是 --show-origin（约 2.8）与 --show-scope（约 2.26）。

观点： git config --list 默认不带 --show-origin，是 Git 配置系统最大的可用性缺陷。

第 3 层 — 系统层：alias 层比 alias 宽得多
危险的配置不是那些 alias，而是与它同行的东西。

Alias 只是客户端配置平面露出水面的部分，这个平面还包括：

pull.rebase、rebase.autoStash、merge.ff → 历史形状
core.autocrlf、core.eol 及与 .gitattributes 的交互 → 内容字节
merge.conflictStyle（merge / diff3 / zdiff3）→ 冲突解析结果
core.hooksPath、init.templateDir → 提交时运行哪些代码
filter.*.clean / filter.*.smudge、diff.external、core.pager、core.editor、sequence.editor → 普通 Git 操作期间的任意进程执行
credential.helper → 你的 token 存在哪里
还有一个关键点：IDE 内置的 Git 客户端通常不展开你的 alias——它们调 plumbing，或者用自己的 libgit2 / JGit 实现。于是同一个工程师，在同一个仓库、同一分钟内，从终端和从 IDE 的「Update Project」按钮得到不同行为。绝大多数团队从未察觉，因为没人对客户端做度量。

开发者机器配置没有遥测平面。 你对服务有可观测性，对生产这些服务的工具则完全没有。

第 4 层 — 规模层：方差是乘性的
方差表面大致是 工程师 × 机器 × 仓库 × 作用域。8 个人时，这是靠结对开发就能吸收的噪声。800 人时，它变成可度量的可靠性输入，因为三件事变了：

新人入职把未版本化的状态扇出。 某个人的 dotfiles 仓库因为被复制粘贴而成为事实标准。它是副本，所以永远收不到更新。于是你有了配置的代际地层：zdiff3 改动之前入职的人，和之后入职的人。
CI 与本地在构造上就分叉。 CI 容器的 global config 几乎是空的；本地机器塞得满满的。每一个「本地通过、CI 失败且 diff 看不出差别」的 bug，都是配置级联的候选根因。
部落式工作流变得无法传授。 当资深工程师演示的是 git up && git nah && git pf，被传递的知识是 alias，而不是操作。新人学到一套在别人机器上不存在的词汇，出问题时无法自行调试。这是组织成本，也是唯一会复利累积的那一项。
第 5 层 — 失效层：一个叙事
背景。 某公司（称之为 project-alpha）的平台团队把 40 个服务仓库合并为 monorepo。既定分支策略是线性历史：合并前 rebase，main 上不允许 merge commit。写进了贡献指南，入职时反复强调。

触发。 迁移三周后，main 上以每天约一个的速度长出 merge commit。不是所有人——是一个稳定的、约十来人的子集。团队为旧仓库自建的 bisect 工具假设线性历史，在一次延迟回归排查中开始给出错误答案。

升级。 先用了最显然的办法：重申策略、加进 PR 模板、加一个 lint 步骤 grep 提交信息里的 "Merge branch"。merge commit 继续出现。两位工程师坚称自己确实 rebase 了——就动机而言他们没说错。

调查。 那个为「保留各仓库设置」而写的迁移脚本，在 monorepo 的 clone 指引里写入了一份 .git/config。这份 local 配置在 30 行无害内容中，夹着一行 pull.rebase = false。local 打败 global。 那些在自己 global 配置里设了 pull.rebase = true 的人——也就是把自己配置正确的那批人——被静默覆盖。而没有任何 global 设置的人反倒毫无感知，因为他们本来就出于习惯手动 rebase。

诊断只需一条命令：

bash

Collapse
Save
Copy
1
git config --show-scope --show-origin --get-regexp 'pull\.|rebase\.|merge\.'
三周内没人跑过它。因为配置不是工程师寻找行为 bug 的地方——他们去看代码。

解决。 三项改动，价值递增：

删掉那个键。（修好了事故，结构上什么都没修。）
用被包含的配置替代被复制的配置：仓库内一份经评审的 tools/git/team.gitconfig，通过 [include] path = ../tools/git/team.gitconfig 接入。指针会收到更新，副本不会。
在服务端强制线性历史。 一条拒绝非线性合并的分支保护规则。至此，不论 800 台笔记本怎么想，该不变量都成立。
教训。 客户端配置从来不是控制手段，它只是一种「客户端会守规矩」的期望表达。当这个不变量真正重要的那一刻，它必须搬到唯一有单一真相来源的地方。

一般化表述：任何仅以客户端配置表达的策略都只是建议性的。如果你需要它为真，它属于服务端。

第 6 层 — 战略层：把边界画对一次
这是 Principal 级别的重构，而它其实不是关于 Git 的。

平面
拥有什么
性质
正确工具
客户端配置
手感、速度、默认值、安全提示
按人漂移、不可审计、不可强制
[include]、[includeIf]、文档、合理的团队默认值
仓库内容
内容的可复现性
版本化、经评审、人人一致
.gitattributes、.editorconfig、入库 hooks + core.hooksPath 引导
服务端 / 代码托管
不变量
单一真相来源、可强制、可审计
分支保护、必需检查、push 规则、签名提交


在成熟组织里我最常见的失效模式，不是不知道这张表，而是把东西放在了它应属列的左边一格——因为左边更容易改。客户端配置是阻力最小的路径，也是保证最弱的路径。

.gitattributes 值得单独点名：它是行尾混乱的正确答案，恰恰因为它是内容而非配置——版本化、经评审、对所有 clone 的人完全一致。core.autocrlf 是同一问题的错误答案，因为它是按机器的。同一个问题、两个平面、可靠性差一个量级。优先选择有溯源的那个平面。

安全：! 前缀
以 ! 开头的 alias 通过 shell 执行：


Collapse
Save
Copy
1
alias.deploy !sh -c 'git push origin HEAD && ./scripts/deploy.sh'
这是任意代码执行，携带你的开发者凭据、云 token、SSH agent 与包仓库权限。

事实： git clone 不会复制远端的 .git/config，所以那个天真的攻击路径（「clone 这个仓库就被 alias 打穿」）不成立。Git 也加固了仓库归属校验——safe.directory 正是针对 CVE-2022-24765 引入的，该漏洞下位于他人所属目录中的仓库配置可能被信任。

依我的经验，真实暴露面在哪： 不是 clone，而是工程师未经评审就运行的东西——

curl … | bash 式的 bootstrap 与 dotfiles 安装脚本
几十人贡献、没有 CODEOWNERS 的共享 dotfiles 仓库
devcontainer / Codespaces 的 setup 步骤
事故期间在群里粘贴的「跑一下这个就能修好环境」
继承了基础镜像 /etc/gitconfig 的 CI 镜像
以上任何一条都能把 alias.*、core.pager、core.hooksPath 或 filter.*.clean 写进 global 配置。core.pager 是其中最优雅的一个：它在 git log、git diff、git show 时触发——工程师条件反射式敲的命令，绝不会当成信任边界。

便宜可落地的控制：先让客户端配置变得可审计。

bash

Collapse
Save
Copy
1
2
3
4
5
6
7
8
9
# 级联里任何位置有 shell 逃逸型 alias 吗？
git config --show-scope --show-origin --get-regexp '^alias\.' | grep -- '!'

# 具备执行能力的键
git config --show-scope --show-origin --get-regexp \
  '^(core\.(pager|editor|hooksPath|fsmonitor)|sequence\.editor|diff\..*\.(command|textconv)|filter\..*\.(clean|smudge)|init\.templateDir)$'

# 带溯源的完整清单，作为快照存进你的 dotfiles
git config --show-scope --show-origin --list | sort
观点： 任何 50 人以上的工程组织，都该有一条「打印我的 Git 配置及其来源」的命令，以及一份文档化的期望基线。几乎没人有。成本是一个下午。

几乎没人用的那个原语：includeIf
如果这篇文章你只带走一个操作技巧，请带走这个。条件包含让你不必再维护一份「对一半仓库都是错的」的全局配置。

ini

Collapse
Save
Copy
1
2
3
4
5
6
7
8
9
10
11
12
13
# ~/.gitconfig
[user]
    name = Alex Engineer
    email = alex@example.com

[include]
    path = ~/.config/git/aliases.common     # 版本化、共享、经评审

[includeIf "gitdir:~/work/"]
    path = ~/.config/git/work.gitconfig     # 工作身份、签名密钥、rebase 策略

[includeIf "gitdir:~/oss/"]
    path = ~/.config/git/oss.gitconfig      # 公开身份、不带公司签名密钥
版本支持情况，请对照你自己的 Git 核实（先 git --version，再查对应版本的 release notes）：

指令
大致引入版本
includeIf "gitdir:…"
2.13
includeIf "onbranch:…"
2.23
includeIf "hasconfig:remote.*.url:…"
2.36
--show-origin
2.8
--show-scope
2.26
--fixed-value、--value=<pattern>
2.30
git config get/set/list/unset 子命令
2.46


hasconfig:remote.*.url: 是被严重低估的那个：它以远端而非文件系统路径为条件，而这才是你说「在公司仓库里用公司身份」时真正的意思。目录约定只是一个代理变量，远端才是事实。

如实陈述权衡： 条件包含用「多个文件 + 一条解析规则」换掉「一个令人困惑的文件」。若你不同时养成 --show-origin 的习惯，可调试性会下降。如果团队不肯采纳这个诊断动作，就不要采纳这份复杂度——你会造出一个读不懂的级联，而那比一个读得懂的巨石文件更糟。

5. 反共识洞见
流行的信念
Git alias 是个人效率工具。在团队里统一它属于刷自行车棚（bikeshedding）、略带专制，而且是平台团队注意力的浪费。

为什么它看起来正确
它所声称的大部分内容确实正确。本地工具链上的开发者自主权是真有价值的。Alias 没有运行时开销、不交付给客户、不出现在任何依赖图里。强制用 st 而不是 s 确实是刷棚，工程师有权反感。这个信念背后还有不错的社会学：殖民个人环境的平台团队会失去信任，而信任正是他们赖以运转的资源。

它在哪里崩塌
三个隐藏假设：

假设一：alias 是私有的。 不是——它是词汇。当资深工程师在结对时、在事故频道里、在 runbook 里说「你跑一下 git up」，这个 alias 已经进入共享语言，而它仍然是按机器存在的产物。共享词汇 + 按机器语义 = 协调型 bug 的定义。

假设二：影响半径是一个开发者。 alias.pf = push --force 与 alias.pf = push --force-with-lease 差一个 flag，也差「并发工作是否存活」。包裹破坏性操作的 alias，把一条需要刻意敲出、边敲边想的命令，压缩成三个字符的肌肉记忆。这不是效率提升，这是移除了一份正在承重的摩擦力。

假设三：alias 本身是关注对象。 它从来不是。Alias 只是级联中最可读的那一条。审计它的价值主要在于：它是让你顺手也去审计 core.hooksPath 和 pull.rebase 的那个习惯。

更好的心智模型
Alias 是一份分布式的、按机器的「团队意图缓存」——而没有人实现失效机制。

一切都从这个框架推导出来：

缓存需要溯源 → --show-scope --show-origin 就是你的缓存检视工具。
缓存需要失效 → [include] 一个版本化文件（指针），而不是复制配置（快照）。副本就是 TTL 为无穷的缓存。
缓存必须保语义 → 个人 alias 可以缩短命令，但不能改变命令的含义。co = checkout 永远没问题；在一个有 rebase 策略的团队里，up = pull 是一个起了短名字的谎。
缓存不是真相来源 → 不变量住在服务端。永远。
由此落地的实际策略，既不是「全部统一」也不是「完全不管」：

不要统一个人速记。 真的不关任何人的事。
要把编码了团队语义的 alias 版本化并分发——凡是碰 force-push、reset、clean、rebase 或历史形状的——通过一个经评审的 included 文件。
要让级联可检视，并在入职培训里把 --show-origin 和 git log 放在一起教。
要把每一个真正的不变量搬到代码托管平台，把客户端配置只当作人机工效。
这比「统一 alias」是小得多的干预，而且是能在 800 人规模下存活的那一个。

6. Principal Engineer 视角
初级工程师 — 实现
问：我怎么列出我的 alias？
git config --get-regexp '^alias\.'。学到 --get-regexp 匹配键名；无输出 + 退出码 1 意味着「没有」，不是「坏了」。

高级工程师 — 正确性与可维护性
问：到底哪个定义在生效，为什么？
默认就带 --show-scope --show-origin。知道单值键是遮蔽而非合并、subsection 区分大小写、alias 无法覆盖内置命令、! alias 是 shell 代码。会不假思索地选 .gitattributes 而非 core.autocrlf。

Staff 工程师 — 架构与团队影响
问：我们的工作流能容忍多少方差，剩下的在哪里吸收？
把级联识别为分布式配置问题，不再用「写文档」来解决它。交付一份版本化的 team.gitconfig，用 [include] 分发而非复制粘贴。把「带溯源的配置 dump」加进 CI 一致性检查清单和事故模板。注意到 IDE 的 Git 客户端会绕过 alias，并明确决定是否在意。

Principal 工程师 — 演进、组织成本、战略风险
问：这一类保证，长期应该由哪个平面拥有？

四个立场：

客户端配置是人机工效平面，永不是强制平面。 .gitconfig 里的策略等于浏览器里的校验。如果它必须为真，就由托管平台强制、由 CI 验证。
优先选有溯源的平面。 两个能力相当的机制之间，选那个「生效值可追溯到一份经评审产物」的。.gitattributes 优于 core.autocrlf；入库 hooks 优于按机器 hooks；服务端规则优于礼节。
复制是反模式，指向才是模式。 共享配置的每一份副本都是一个 TTL 无穷的未版本化分支。入职脚本里的 cp 一个 dotfile，就是在制造明天的代际漂移。
未被观测的平面在组织规模下单调累积风险。 你对开发者机器配置没有遥测，这意味着方差只增不减，且只能通过事故被发现。便宜的缓解是「文档化基线 + 自助溯源 dump」——而不是 MDM 式的强制管控，那会消耗信任，换来的合规你还是无法验证。
跳过这一切的战略风险：你组织里使用频率最高的工具，拥有一个按用户变化的行为表面，无人评审、无人监控，而所有人都假设它是统一的。这个假设，正在为你的每一份事故复盘承重。

7. 推荐图表
图 1 — Git 配置级联解析
目的： 用「有序合并」模型替换「Git 读我的 .gitconfig」，并指出溯源在哪里丢失。

是
否
执行 git <command>
system: /etc/gitconfig
global: ~/.gitconfig
local: .git/config
worktree 配置(需extensions.worktreeConfig)
命令行: git -c key=value
该键是多值键吗?
所有值累积
最后读到的值胜出先前值被静默遮蔽
生效配置
来源仅通过--show-scope --show-origin可见



图 2 — 同一个共享动词导致的分叉结果
目的： 展示相同指令如何在两位工程师处产出不同历史。

远端 main
工程师 B (local pull.rebase=false 胜出)
工程师 A (global pull.rebase=true)
远端 main
工程师 B (local pull.rebase=false 胜出)
工程师 A (global pull.rebase=true)
Runbook 写着: push 前先跑 git up
bisect 工具假设线性历史
开始返回错误答案
alias up -> pull --rebase --autostash
1
push (线性历史)
2
alias up -> pull (local 覆盖 global)
3
push (产生 merge commit)
4
main 已非线性
5



图 3 — 失效流：策略被表达在了错误的平面
目的： 让「客户端=建议，服务端=不变量」这条边界无可辩驳。

策略: main 保持线性历史
写在贡献指南里
写在 .gitconfig / alias 里
写成分支保护规则
建议性被静默违反
建议性被级联优先级覆盖
不变量在真相来源处拒绝 push
main 非线性bisect 工具失效
不论 800 台笔记本如何配置策略恒成立



图 4 — 方差表面的增长
目的： 说明为什么 10 人时是噪声，800 人时是可靠性输入。

工程师数 N
方差表面N x 机器数 x 仓库数 x 5个作用域
人均机器数
人均仓库数
配置作用域(5) + includes
N 较小时可被结对开发吸收
复制粘贴式入职形成代际地层
客户端无遥测方差单调增长
只能通过事故被发现



图 5 — 平面归属模型
目的： 可以直接带去架构评审的那一张图。

漂移, 不可审计
版本化, 经评审
单一真相来源
托管平台平面 - 不变量
分支保护
必需检查
push 规则, 签名提交
仓库平面 - 内容
.gitattributes
.editorconfig
入库 hooks + 引导脚本
客户端配置平面 - 人机工效
aliases
core.autocrlf, core.pager
includeIf, 身份配置
仅建议性
可复现
可强制



8. 常见问题（FAQ）
Q1：git config --get-regexp alias 到底做什么？
它打印所有键名匹配 ERE 模式 alias 的配置项，格式为 键 值。因为所有 Git alias 都存放在 alias.* 下，它就成了「列出我的 alias」。该模式非锚定，所以建议写 git config --get-regexp '^alias\.'，避免误伤 my.aliases.legacy 这类无关键名。

Q2：为什么它没有输出还返回退出码 1？
因为没有键匹配。这是一次正常且成功的执行，只是结果集为空——Git 用退出码表达「未找到」。在脚本里请加保护（if git config --get-regexp '^alias\.' >/dev/null 2>&1; then … fi），而不是让 set -e 直接中断你的 bootstrap。

Q3：怎么知道某个配置来自哪个文件？
git config --show-scope --show-origin --get-regexp '^alias\.'。--show-origin（约 Git 2.8）打印文件；--show-scope（约 2.26）打印 system/global/local/worktree/command。这是 Git 配置系统里最有用的一条诊断，应该成为习惯而非最后手段。

Q4：同一个键被设置两次时，哪个作用域胜出？
单值键：system → global → local → worktree → 命令行，越靠后越高，先前的值被遮蔽而非合并。多值键（如 remote.origin.fetch、include.path、safe.directory）则累积。一个键是单值还是多值，由读取它的代码决定，没有可供查阅的 schema。

Q5：Git alias 能覆盖 git status 这类内置命令吗？
不能。内置命令永远优先，alias.status = log 无效。实务含义很重要：你无法通过 alias 让 git push 变安全。请用独立名字（alias.pf = push --force-with-lease），并把真正的约束放到服务端强制。

Q6：以 ! 开头的 alias 危险吗？
它们通过 shell 执行，携带你完整的开发者凭据，属于任意代码执行。git clone 不复制远端的 .git/config，所以「恶意仓库」这条天真路径已被堵住，Git 也加入了归属校验（safe.directory，源于 CVE-2022-24765）。现实中的暴露面是：未经评审的 bootstrap 脚本、共享 dotfiles 仓库、devcontainer setup、以及往 global 配置写东西的 CI 基础镜像。审计用 git config --show-scope --show-origin --get-regexp '^alias\.' | grep -- '!'，并把范围扩展到 core.pager、core.hooksPath、filter.*.clean/smudge、diff.*.command。

Q7：团队应该统一 Git alias 吗？
个人速记不必。但编码了团队语义的 alias 应当版本化并分发——凡是包裹 force-push、reset、clean、rebase 的——做成经评审的文件、用 [include] 引入，这样接收方拿到的是会更新的指针而不是冻结的副本。而任何必须成立的东西（例如线性历史）请搬到托管平台的分支保护。客户端配置在构造上就只是建议。

Q8：工作与开源身份怎么分开管理最好？
用条件包含。[includeIf "gitdir:~/work/"]（约 2.13）以路径为条件；[includeIf "hasconfig:remote.*.url:…"]（约 2.36）以远端 URL 为条件，而后者通常才是你真正的意思。用 git --version 确认支持情况。并接受权衡：文件更多 + 一条解析规则，所以务必同时养成 --show-origin 的习惯。

9. 关键要点
git config --get-regexp '^alias\.' 用非锚定 ERE 匹配键名；空输出 + 退出码 1 表示「无匹配」，不是失败。
Git 配置是五层、无 schema 的级联。单值键遮蔽、多值键累积；subsection 区分大小写，而 section 与 key 不区分。
真正该敲的是 --show-scope --show-origin。 你缺的不是值，是溯源。
Alias 无法覆盖内置命令——客户端给 push 加的「安全护栏」并不存在。
风险不在 alias 本身，而在与它同行的东西——pull.rebase、core.autocrlf、core.hooksPath、core.pager、filter.*.clean。
优先选有溯源的平面： .gitattributes 优于 core.autocrlf，入库 hooks 优于按机器 hooks，服务端规则优于礼节。
指向，别复制。 [include] 一份版本化团队配置；被复制的 dotfile 是 TTL 无穷的未版本化分支。
客户端配置是人机工效，托管平台才是强制。 只存在于 .gitconfig 的策略等于浏览器里的校验。
includeIf——尤其是 hasconfig:remote.*.url:——是 Git 配置中最被低估的原语。
规模之下，未被观测的平面单调累积风险。你对开发者配置没有遥测；「文档化基线 + 自助溯源 dump」的成本只是一个下午。
10. SEO 元数据
主标题： 每个工程师都在运行你工具链的一个私有分支：Git 配置溯源与客户端策略的边界

SEO 描述（约 155 字符）：
为什么 git config --get-regexp alias 重要：Git 配置级联、用 --show-scope 追溯来源、includeIf 实践，以及为什么客户端配置永远无法强制策略。

关键词：
git config --get-regexp alias、git config 优先级、git config show-origin、git config show-scope、git alias 列表、git includeIf、hasconfig remote url、pull.rebase local 覆盖 global、core.autocrlf 与 gitattributes、git 配置安全、git alias shell 执行、core.pager 代码执行、safe.directory CVE-2022-24765、开发环境漂移、配置溯源、客户端与服务端策略强制、分支保护 线性历史、平台工程 开发者体验、git 配置级联、dotfiles 规模化漂移

TL;DR：
git config --get-regexp '^alias\.' 通过匹配键名列出你的 alias。但真正该敲的是 git config --show-scope --show-origin --get-regexp '^alias\.'——因为 Git 配置是一个五层级联，后写者静默胜出。Alias 只是一个未经审计的客户端配置平面中最可读的部分，而这个平面还决定历史形状、行尾、冲突解析，以及提交时运行哪些代码。把客户端配置当作人机工效来对待：共享配置版本化后用 [include] 引入而非复制、用 includeIf 管理身份、优先 .gitattributes 而非按机器设置，并把每一个真正的不变量搬到服务端分支保护。写在 .gitconfig 里的策略，等于在浏览器里做校验。
