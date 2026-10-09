---
title: "三条命令,吃透 zsh/bash 的查询与调试"
date: 2026-09-24
categories: [engineering, shell]
tags: [zsh, bash, shellcheck, debugging, dotfiles, cli]
---

平时敲 shell,很多"日常动作"其实藏着不少反直觉的坑:一个 `-i` 决定你的别名读不读得到,一个 `2>&1` 放错位置报错就漏了,一个 `bash -n` 能救你也能骗你。这篇把三条常见命令拆开,从"查命令定义"到"查环境变量"再到"查脚本语法",顺带把 zsh/bash 里那些 99% 的人没注意的细节一次讲透。

---

## Part 1:查命令到底是个啥 —— `which` / `whence` / `alias`

```sh
zsh -i -c 'which savee; whence -f savee; alias savee' 2>&1
```

**一句话:** 这条命令是在问 zsh "`savee` 到底是个啥?"—— 用三种不同的问法一次问完,还顺手把报错也一起收进来。它**不会执行 `savee`**,只是"查户口",纯只读。

拆开看每个零件:

- **`zsh -i -c '...'`** —— 开一个**交互式**(`-i`)的子 shell,执行引号里那串(`-c`)。关键是 `-i` 会加载 `.zshrc`;不加 `-i`,别名和自定义函数根本不会被读进来,结果就是"明明有 `savee` 却告诉你 not found"。
- **`which savee`** —— 定位 `savee`,是命令给路径,是别名/函数也会告诉你。
- **`whence -f savee`** —— `whence` 是 zsh 亲儿子。`-f` 的意思是:**如果它是个函数,把整个函数体打印出来**,不是只报个名。
- **`alias savee`** —— 如果它是别名,把别名内容吐出来。
- **`2>&1`** —— 把「标准错误」并进「标准输出」,万一 `savee` 不存在报了 not found,这句错误也能被一起看到。

一句话总结:**"是命令给路径、是函数给源码、是别名给内容,出错也别藏着。"**

### 三个小技巧

1. **其实一个 `whence` 全搞定,不用叠三层。** 试试 `whence -va savee`——`-v` 人话解释,`-a` 把「所有」匹配(别名、函数、可执行文件重名的情况)全列出来。
2. **想直接看函数源码 + 定义在哪个文件?** 神器是:`echo $functions_source[savee]`——直接告诉你这个函数从哪个文件加载来的,一秒定位。
3. `type -a savee` 也能干类似的活,而且 bash/zsh 通用,换机器不翻车。

### 深挖:`which` / `whence` / `type` 到底怎么选

一句话:**平时用 `type -a`,钻研 zsh 用 `whence`,`which` 能不用就不用。**

- **`which`** —— 历史包袱最重。在别的 shell 里它可能是**外部程序**,只会去 `$PATH` 里找可执行文件,**看不见你的 alias 和函数**。
- **`whence`** —— zsh 亲儿子,功能最全。三个开关:`-v` 说人话、`-a` 列出所有匹配、`-f` 打印函数体。组合技 `whence -vas savee`。
- **`type`** —— bash/zsh 通用,`type -a` 效果约等于 `whence -va`。换环境不想踩坑用它最稳。

> 记忆口诀:**日常 `type -a`,深挖 `whence`,`which` 留给老古董。**

### 深挖:秒定位一个函数在哪定义

```sh
echo $functions_source[savee]
```

zsh 会告诉你这个函数从哪个文件加载进来。进阶两招:

- `functions savee` —— 直接把函数体打出来(等价 `whence -f`)。
- 想跳进去改:`${EDITOR:-nvim} ${functions_source[savee]}` —— 一键用编辑器打开它所在的文件。

### 深挖:临时覆盖或绕过

- **它是 alias** → `.zshrc` 里重定义,或临时 `unalias savee` 干掉它。
- **它是函数** → 定位源文件去改;或临时重新 `savee() { ... }` 定义一遍,当前会话立即生效。
- **强制跑同名的真·命令**:`command savee` 跳过函数和别名;`\savee` 反斜杠开头**临时禁用别名**(函数还在)。

> 一句话:**改要动源文件、临时用 `unalias`/重定义、绕过用 `command` 或 `\`。**

---

## Part 2:查环境变量 —— 以及那个致命的 `-i`

```sh
zsh -c 'echo "TODDY_SRC_HOME=$TODDY_SRC_HOME, OLLAMA_MODEL=$OLLAMA_MODEL"'
```

**一句话:** 这条命令是在问 `TODDY_SRC_HOME` 和 `OLLAMA_MODEL` 这俩环境变量现在是啥值。但重点藏在写法里。

### 隐藏的大坑:这次没有 `-i`

对比 Part 1 的 `zsh -i -c`,**这条是 `zsh -c`,没有 `-i`**:

- **非交互式 shell 不加载 `.zshrc`。**
- 所以如果你的 `TODDY_SRC_HOME` 只写在 `.zshrc` 里,这条命令跑出来就是**空的**。

那什么情况下能查到值?**只有当它是真·环境变量**(被 `export` 过、或写在 `.zshenv` 里、或从父进程继承)时才会出现。所以这条命令其实是个**体检**:判断"这个变量到底是全局环境变量,还是只是我 `.zshrc` 里的局部小玩具"。

### zsh 启动文件加载顺序

```
.zshenv   → 每次都加载(非交互也读)✅
.zprofile → 只在登录 shell
.zshrc    → 只在交互式 shell(-i 才有)
.zlogin   → 只在登录 shell
```

**心法:想让一个变量"到处都在"(脚本里、cron 里、非交互里都能读到),写进 `.zshenv` 并 `export`。**

### 几个小技巧

1. **给个默认值别露馅**:`${TODDY_SRC_HOME:-~/src}` —— 没设就用 `~/src`。
2. **没设就报错退出**(脚本防呆):`echo ${OLLAMA_MODEL:?"没设 OLLAMA_MODEL!"}`。
3. **单/双引号嵌套**:外层单引号(不让当前 shell 提前展开),里层双引号(让子 shell 里的 `$VAR` 展开)—— 嵌套得刚刚好。
4. **只想确认"存不存在"**:`typeset -p TODDY_SRC_HOME` 或 `[[ -v TODDY_SRC_HOME ]]` 能区分"设为空字符串"和"压根没设"。

### 深挖:`.zshenv` vs `.zshrc` 怎么分工

一句话:**`.zshenv` 是"环境变量的家",`.zshrc` 是"交互体验的家"。**

- **`.zshenv`** —— 每次开 zsh 都读,包括非交互、脚本、cron。放 `export PATH/EDITOR/变量`。**别放**一堆 `source`、插件、耗时初始化——每个子 shell 都会跑一遍。
- **`.zshrc`** —— 只在交互式 shell 读。放别名、提示符、补全、插件、键位绑定。放这儿的变量,脚本和后台读不到。

> 记忆法:**"变量进 env,好看进 rc。"** 分不清时问自己"后台脚本需要它吗?"——需要就 `.zshenv`。

### 深挖:为什么 export 了子进程还是读不到

1. **export 的时机太晚**:子进程在启动那一刻拍下父进程环境,你后来才 export,已跑起来的子进程看不到,得重启。
2. **在子 shell / 括号里 export**:`( export FOO=1 )` 出了括号就没了,不回传给父 shell。
3. **只赋值没 export**:`FOO=bar` 只是当前 shell 的局部变量,必须 `export FOO=bar`。
4. **GUI 程序读不到**:很多 GUI app 不从终端启动,环境来自 launchd/systemd/桌面会话,没读你的 `.zshenv`。
5. **值里有空格没引号**:`export MSG=hello world` → `world` 被当成命令。

> 快速自检:`env | grep OLLAMA` 看它在不在环境;`typeset -p OLLAMA_MODEL` 看它是不是带 `-x`。

### 深挖:单/双引号嵌套展开规则

- **双引号 `"..."`** —— "半透明"。`$变量`、`$(命令)` 会展开。
- **单引号 `'...'`** —— "全封闭"。里面啥都不展开,连 `$` 都是死的。
- **`$(...)`** —— 命令替换,先跑里面再把输出塞回来。

`zsh -c 'echo "$FOO"'` 的逻辑:外层单引号挡住当前 shell 提前展开,内层双引号交给子 zsh 后才展开 `$FOO`。**精髓:用单引号"运输"一段代码给子 shell,让展开延迟到子 shell 里发生。** 这是 `ssh remote '...'`、`sudo zsh -c '...'` 的标准姿势。

### 深挖:区分"没设"和"设为空"

`echo $FOO` 的致命缺陷:变量没设、和设成空字符串,打出来一模一样。正确工具:

- **`[[ -v FOO ]]`** —— 判断变量存不存在(不管值空不空)。
- **`typeset -p FOO`** —— 存在就打印完整声明(含是否 export、是否数组),不存在直接报错。
- **参数展开辨别**:`${FOO-未设}` 只有**没设**才触发;`${FOO:-...}` 空**或**没设都触发。

> 记住:**冒号 = 连空也管。**

---

## Part 3:跑之前先体检 —— `bash -n` 与 shellcheck

```sh
bash -n /path/to/git_checkin_e.sh
```

**一句话:** `-n` = 只检查语法,不执行(noexec)。这条命令把脚本从头到尾读一遍、检查有没有语法错误,但一行都不真跑。纯静态检查、零副作用——自动 git 脚本先扫一遍再放心跑,姿势非常正确。

### 怎么看结果

**没有任何输出 = 语法过关。** shell 界的哲学:沉默就是最大的褒奖。有毛病它会告诉你第几行炸了:

```
git_checkin_e.sh: line 42: syntax error: unexpected end of file
```

通常是 `if` 没配 `fi`、`do` 没配 `done`、引号没闭合。

### 但 `-n` 有个天花板

`-n` **只抓语法错,抓不到逻辑错和运行时错**:

- ✅ 管得着:引号没闭合、`if/fi`、`for/done` 不配对、括号错位。
- ❌ 管不着:变量没定义、路径不存在、`rm` 删错东西、git 用错参数、逻辑写反。

换句话说:**`-n` 保证脚本"读得通",不保证它"跑得对"。**

### 真正的神器:shellcheck

```sh
shellcheck git_checkin_e.sh
```

它能揪出没加引号的变量、用了未定义变量、`cd` 失败还硬往下跑等等,每条都给编号 + 解释 + 修复建议。nvim 里挂个 shellcheck 的 LSP,边写边红。

### 配套最佳实践

1. **脚本开头三件套**:`set -euo pipefail`。
2. **想边执行边看每行怎么跑**(排查逻辑):`bash -x 脚本`——注意 `-x` 是**真执行**。
3. **组合体检**:`bash -n xxx.sh && shellcheck xxx.sh`。

### 深挖:shellcheck 常抓的错 Top 榜

1. **变量不加引号(SC2086)** —— 头号杀手。`rm $file` 遇到带空格的路径就删错。永远写 `"$file"`。
2. **`cd` 失败还硬往下跑(SC2164)** —— 写成 `cd /dir || exit`。
3. **拼错变量名(SC2154)** —— 配合 `set -u` 当场现形。
4. **`[ ]` 里变量没引号(SC2070/SC2086)** —— 用 `[[ ]]` 更稳。
5. **`for f in $(ls)`(SC2045)** —— 直接 `for f in *`。
6. **管道 while 里改的变量丢了(SC2031)** —— 子 shell 坑。

> 一句话:**shellcheck 抓的 80% 都是"引号"和"没检查失败"两件事。**

### 深挖:`set -euo pipefail` 每个到底干嘛

- **`set -e`(errexit)** —— 任何命令返回非 0 就立刻退出。例外:命令在 `if`、`||`、`&&` 里时不触发。
- **`set -u`(nounset)** —— 用了未定义变量直接报错。确实可能为空的用 `${VAR:-}` 绕过。
- **`set -o pipefail`** —— 管道里任何一环失败整条都算失败。

> 焊死记忆:**`-e` 出错即停,`-u` 空变量即抓,`pipefail` 管道不漏。**
> 进阶:`set -E` + `trap 'echo 出错在第 $LINENO 行' ERR` 做出错定位。

### 深挖:`-n` / `-x` / `-v` 调试三剑客

| 旗标 | 干嘛 | 执行吗 | 什么时候用 |
|---|---|---|---|
| **`-n`** | 只查语法 | ❌ 不执行 | 跑之前预检,最安全 |
| **`-v`** | 打印读到的每行**原样** | ✅ 执行 | 想看"读进去的是什么" |
| **`-x`** | 打印每行**展开变量后**的实际命令 | ✅ 执行 | 排查"变量到底变成啥了" |

关键区别:**`-v` 打你写的原文,`-x` 打变量替换后的真实样子**。debug 逻辑基本靠 `-x`——它能让你看到 `rm "$dir"` 实际变成了 `rm ""`(空变量!)这种要命的展开。只想追踪一段就 `set -x` / `set +x` 局部包起来,别刷屏。

> 口诀:**跑前 `-n`,看原文 `-v`,抓变量 `-x`。**

### 深挖:自动 git 脚本怎么写才不炸

1. **先确认在 git 仓库里**:`git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 1`。
2. **没东西改就别提交**:`git diff --cached --quiet && { echo "无变更,跳过"; exit 0; }`。
3. **慎用 `git add .` / `git add -A`** —— 容易把 `.env`、密钥、临时大文件一起提交。精确指定路径,`.gitignore` 配严。
4. **push 前确认分支**:`git symbolic-ref --short HEAD`,别自动 push 到 `main`。
5. **commit message 带时间/来源**:`git commit -m "auto: $(date +%F_%T)"`。
6. **配合前面**:开头 `set -euo pipefail`,`cd "$repo" || exit`,所有变量加引号。

> 铁律:**自动化脚本的风险不在"跑不起来",而在"跑起来了但干错了"。** 每个写操作前先加一道判断。

---

## 收尾

三条命令,一条主线:**shell 的很多"日常动作"背后都有你没注意的语义**。查命令定义时,`-i` 决定别名读不读得到;查环境变量时,`.zshenv` 和 `.zshrc` 的分工决定变量在不在;查脚本时,`bash -n` 保证读得通、shellcheck 和 `set -euo pipefail` 才保证跑得对。把这几条心法焊进肌肉记忆,以后 debug 能省下大把时间。
