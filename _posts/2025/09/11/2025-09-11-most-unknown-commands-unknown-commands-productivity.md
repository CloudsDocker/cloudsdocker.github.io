---
header:
    image: /assets/images/hd_sdkman_omz.png
title:  5个被忽视的 Bash 命令行技巧：<()> 进程替换、tee、xargs -P、/dev/tcp、参数扩展（效率翻倍实战）
date: 2025-09-11
tags:
    - tech
    - bash
    - shell
    - 命令行
    - 进程替换
    - tee
    - xargs
    - dev-tcp
    - 参数扩展
    - linux
permalink: /blogs/tech/cn/bash-command-line-tips-process-substitution-tee-xargs-dev-tcp-parameter-expansion
layout: single
category: tech
lang: zh-CN
excerpt: 本文系统讲解 5 个被忽视但极其高效的 Bash/Shell 命令行技巧：进程替换 <()>、tee、xargs -P 并行、/dev/tcp、参数扩展，含实战用法、兼容性与性能边界。
description: 5个被忽视的 Bash 命令行技巧全解析：<()> 进程替换、tee、xargs -P 并行、/dev/tcp、Shell 参数扩展。附实战场景、脚本示例、兼容性与性能权衡，助你显著提升命令行效率。
---
> Life isn't about finding yourself. Life is about creating yourself. - George Bernard Shaw

# 隐藏于日常之下的神力：程序员未曾察觉的命令行宇宙

先说个不夸张的真实场景。某次周会前 10 分钟，Leader 突然抛来一句：
“能不能马上对比一下线上和本地同名目录有什么差异？就现在。”

我第一反应是：scp 两份列表、落盘、diff、清理临时文件……然后我停住了——这也太慢了。接着我做了三次尝试：
- 尝试1：直接 ssh 列表，复制到本地临时文件 -> 太多中间步骤，删文件麻烦。
- 尝试2：`rsync --dry-run` -> 输出复杂，不利于快速阅读。
- 尝试3：进程替换 `<()>` + `diff` -> 当场出结果，还优雅。

这篇文章不是“命令大全”，而是讲清5个被忽视却极其实用的“命令行武器”，并展示我如何一步步从问题出发，选择工具、验证思路、承认限制、给出替代方案。你会看到的不是“结论”，而是“思考的路径”。

---

## 神力一：进程替换 `<()>` —— 无影的临时文件

是什么？
- 把“命令的输出”伪装成“一个文件名”。Shell 在幕后用命名管道或文件描述符完成连接，省掉落盘与清理。

为什么用它？
- 减少中间文件、提升可读性；非常适合“比较两个命令输出”“把多个流喂给只接受文件参数的程序”。

真实用法：
1) 远程与本地目录对比（周会救命术）
```bash
# 两个命令的输出瞬间“文件化”，直接 diff
 diff <(ssh user@remote 'ls -l /path/to/dir') <(ls -l /local/path/to/dir)
```
2) 多流处理：排序后对比差异
```bash
comm -3 <(find ~ -name "*.txt" | sort) <(ps aux | awk '{print $11}' | sort)
```
3) while 循环里保持变量（避免子 Shell 丢失）
```bash
count=0
while read -r line; do
  ((count++))
  echo "Processing $line"
done < <(grep "error" my_app.log)  # 注意：重定向 < + 进程替换 <()

echo "Total errors: $count"
```

思考过程与边界：
- 兼容性：bash、zsh、ksh支持；/bin/sh（dash、busybox的 ash）通常不支持。Docker Alpine 里用 /bin/sh 时要小心。
- 可读性：适度使用；层层嵌套会变“难读”。
- 可替代方案：不支持时可退化为落盘临时文件或用 `mktemp` 管道串联。

---

## 神力二：`tee` —— 数据流的“三通阀”

是什么？
- 从标准输入读取，同时写到“屏幕”和“文件”。边看结果，边把证据存档。

为什么用它？
- CI/CD 和排障现场尤其有用；配合 `sudo` 能优雅解决“重定向没有权限”的老难题。

经典用法：
1) 一边看日志，一边保存
```bash
./deploy_to_production.sh | tee deployment.log
```
2) sudo 写保护文件（避免 `sudo echo ... > file` 的坑）
```bash
echo "server_ip=192.168.1.100" | sudo tee -a /etc/my_app/config.conf  # -a 追加
```
进阶与细节：
- 保留上游错误码：
```bash
set -o pipefail
some_cmd | tee out.log
echo $?    # 结合 pipefail，能拿到 some_cmd 的失败状态
```
- 信号与中断：`tee -i` 可忽略中断信号；超长流水建议分卷写文件。
- 多路写入：`tee file1 file2 file3` 同时保存多份。

承认复杂性：
- 大量写磁盘会拖慢流水；对性能敏感的场景，仅在必要阶段开启 tee。

---

## 神力三：`xargs -P` —— 并行的低门槛增压器

是什么？
- 把标准输入的一行行参数“打包”交给后面的命令，并用 `-P` 同时跑多个进程，吃满多核。

为什么用它？
- 在“批量任务”场景里，能以极低改造成本把串行任务“拧一拧”就并行化。

高效而安全的用法：
1) 瞬间克隆一堆仓库（安全处理空格/特殊字符）
```bash
# repos.txt 里每行是一个 URL；用 -0 搭配 find -print0 可完美处理空格
cat repos.txt | xargs -P 8 -n 1 -I {} git clone {}
```
2) 生产更稳妥的写法：
```bash
# 处理文件名建议：find -print0 | xargs -0 ...
find . -type f -name "*.log" -print0 | xargs -0 -n 10 -P 4 gzip
```
要点与取舍：
- `-P` 并发度不是越大越好：会打爆网络或 API 限流；可加 `sleep 0.2` 做“人为节流”。
- `-n` 每次传给子进程的参数个数，影响进程创建次数与吞吐。
- 出错处理：GNU `xargs` 有 `-r`（无输入不执行）、`-t`（回显命令），必要时结合 `set -e`、重试逻辑。
- 何时上更重的轮子：需求复杂（依赖/重试/收敛）时考虑 GNU parallel 或队列系统。

---

## 神力四：`/dev/tcp` —— 用“文件”打通网络

是什么？
- 在 bash（和部分 ksh）中，`/dev/tcp/host/port` 与 `/dev/udp/host/port` 是“特殊设备文件”，用重定向即可直接发起 TCP/UDP 连接。

为什么用它？
- 零依赖、随手可用；当你没有 `curl`、`nc` 或被最小化镜像“阉割”时尤为好用。

用法：最轻量的健康检查
```bash
exec 3<>/dev/tcp/api.internal.com/80
printf "GET /health HTTP/1.1\r\nHost: api.internal.com\r\nConnection: close\r\n\r\n" >&3
cat <&3
```
注意与不确定性：
- 可移植性一般：dash、busybox 的 ash 通常不支持；生产脚本尽量降级到 `nc`/`curl`。
- 网络策略：被防火墙/出口策略拦住时，要尊重合规；此技巧适合“临时排障”，不建议长期依赖。

---

## 神力五：`${VAR%pattern}` —— 参数扩展的内功心法

是什么？
- Shell 内置的“字符串手术刀”，在变量替换时直接做裁剪、替换，无需 `sed`/`awk`/`basename`，省一次进程创建。

为什么用它？
- 高频字符串处理走内建通道，性能与可读性更好；可与通配符（glob）组合表达丰富意图。

实践清单：
1) 快速剥壳：文件名与目录名
```bash
full_path="/home/user/archive.tar.gz"

# 从后往前删：%（最短） / %%（最长）
echo "${full_path%.*}"   # /home/user/archive.tar    去掉最后一个后缀
${full_path%%.*}         # /home/user/archive        去掉所有后缀链

# 从前往后删：#（最短） / ##（最长）
echo "${full_path##*/}"  # archive.tar.gz           去掉最后一个/
${full_path#*/}          # home/user/archive.tar.gz  去掉第一个/
```
2) 批量重命名
```bash
for file in *.jpeg; do
  mv "$file" "${file%.jpeg}.jpg"
done
```
3) 以“为什么”收尾的几招
```bash
# 默认值与必填校验（脚本健壮性）
echo "${ENV:-dev}"      # 若未设置 ENV，则取 dev
: "${TOKEN:?TOKEN 未设置}"  # 未设置就报错退出

# 替换而非正则（是 glob，不是 regex）
name="hello_world_world"
echo "${name/_/ }"       # 只替换第一个下划线 -> "hello world_world"
echo "${name//_/ }"      # 全部替换 -> "hello world world"
```
承认复杂性：
- 通配符语义是“glob”，不是“正则”；遇到复杂匹配/多字节场景，宁可回到 `sed`/`awk`，别硬抠。

---

## 什么时候不要用它们（同样重要）
- `<()>`：团队脚本需跑在 `/bin/sh` 时；或需要极简可移植性。
- `tee`：写磁盘成为瓶颈时；或泄露敏感信息到日志的风险存在时。
- `xargs -P`：外部服务有严格 QPS/顺序语义；或需要强事务保障。
- `/dev/tcp`：合规/审计要求严格；或需双向健壮协议处理。
- 参数扩展：团队成员不熟悉，读者成本高；此时用清晰的外部工具反而更好。

---

## 小练习（发到群里也有讨论价值）
- 把“线上/预发/本地”三份配置差异，用 `<()> + diff` 做一键对比，并输出到 `tee` 的同时高亮新增项。
- 用 `find -print0 | xargs -0 -P 4` 批量转码图片，统计失败清单并二次重试。
- 用 `/dev/tcp` 自己实现一个极简 `nc`，并写下你遇到的网络/权限问题。
- 只用参数扩展完成“文件名去前缀、去后缀、归档到按日期分目录”的脚本雏形。

---

## 结语：展示思考，而非只给答案

这5个“武器”并不神秘，它们厉害在于能把“工具链的缝隙”补齐。真正拉开差距的，是你如何选择它、验证它、在遇到限制时换挡：
- 策略一：展示思考过程，而非只抛结论（把你的尝试与取舍写出来）
- 策略二：用个人经历替代通用案例（具体的人、具体的场景）
- 策略三：承认不确定性和复杂性（写出兼容性、性能与合规边界）

愿你不再被“看似简单”的命令困住，而是把它们用到极致。