---
title: saml2aws 在 WSL 上每次都要重新登录：一个被 INFO 日志吞掉的 storageState bug
header:
    image: /assets/images/hd_aws_certificat.png
date: 2026-10-07
tags:
 - aws
 - wsl
 - saml2aws
 - debugging
 - sso
permalink: /blogs/tech/zh/saml2aws-wsl-storagestate-silent-failure
layout: single
category: tech
---

> 天下难事，必作于易；天下大事，必作于细。——《道德经》

# 被 INFO 日志吞掉的真相：一个从没被创建的目录，让每次 SSO 都前功尽弃

*从「是不是没保存密码」到「错误的代价不看级别，看可观测性 × 频率」——一次 WSL 排错的完整心路*

## 事故

我在 Mac 上用 `saml2aws login` 换 AWS 临时凭据，用了很久：第一次在弹出的浏览器里登一下 Google SSO，之后每次都直接跳过，几秒拿到 credentials。丝滑。

把同一套配置搬到 WSL2 之后，变成了另一副样子：**每一次** `saml2aws login`，弹出的 Chromium 都要我从头输一遍 Google 邮箱、密码、再过一遍 MFA。配置文件一模一样，工具版本一样（`saml2aws 2.36.19`），凭什么 Mac 记得住、WSL 记不住？

我的第一直觉——也是大多数人的第一直觉——是错的：

> 「WSL 上肯定是没把登录信息存进 keyring 吧？Linux 没有 macOS Keychain，密码没地方存，所以每次问我。」

这个直觉听起来非常合理。它也把我带偏了至少十分钟。

如果你也遇到过「同一个工具，在这台机器上记得住登录、在另一台上死活记不住」，下面这条排查链就是为你准备的。

你会拿走三个东西：

- 一个判断「持久化到底落在哪」的方法——**别猜，顺着数据应该写到哪去倒查**；
- 一条「成功的命令 + 静默失败」这类最难缠 bug 的定位思路；
- 一个比这个 bug 本身更贵的工程教训：**错误的代价不取决于它的严重级别**。

下面按「最有用」的顺序讲，不完全是我当时踩坑的时间顺序——真实排查里我在 keyring 那条死路上多绕了十分钟，这里替你省掉。

## 一、错误的第一直觉：这不是 keyring 的问题

我先去验证「keyring 没存密码」这个假设。查下来 WSL 确实没有一个能用的 secret-service：`secret-tool` 没装，`GNOME_KEYRING_CONTROL` 是空的，gnome-keyring 守护进程根本没在跑。证据齐全，假设看起来成立。

但有一个细节把整条推理推翻了——我的配置里写着：

```ini
# ~/.saml2aws
provider = Browser
```

`provider = Browser` 意味着**真正把我登进 Google 的，是浏览器里那套 SSO 流程**，不是终端里敲的密码。终端那个 Username/Password 提示（以及它旁边那句 "To use saved password just hit enter"）在 Browser 模式下基本是摆设。换句话说：**keyring 存不存密码，根本不影响浏览器里要不要重新登录。**

| 普通人的看法 | 资深工程师的洞察 |
|---|---|
| 每次问我密码 = 密码没存住 = keyring 坏了 | 先看 `provider`。Browser 模式下认证发生在浏览器，终端密码是摆设 |
| macOS 有 Keychain，Linux 没有，所以行为不同 | 两边工具同一份代码。差异一定在「这段代码在两个 OS 上读写的那个东西」上 |

**对称性破缺**：当两台机器跑的是同一份二进制、同一份配置，行为却不同，差异一定不在代码里，而在「代码所依赖的外部状态」上。我要找的不是「哪段逻辑不一样」，而是「哪个外部文件/目录，一台有、一台没有」。

> 同样的代码，不同的行为，差异一定藏在它读写的那块地里。

## 二、第二次转向：持久化不在浏览器 profile 里

既然认证在浏览器，那「记住登录」就等于「浏览器记住了 Google 的 session cookie」。我顺着这个思路去翻磁盘，想找 saml2aws 启动 Chromium 用的那个用户目录。结果找到的是这个：

```text
/tmp/playwright_chromiumdev_profile-DGdPIX/Default/Cookies
```

注意那个随机后缀 `-DGdPIX`。这是 Playwright 为**一次性临时 profile** 起的名字——用完即弃，每次启动都是全新的一个。也就是说，saml2aws 的 Browser provider（底层是 playwright-go）每次都开一个干净的临时浏览器。

那问题来了：如果浏览器 profile 是一次性的，Mac 又是怎么「记住」的？

答案是：**真正的持久化根本不在浏览器 profile 里。** 这是我这次排查的转折点。与其继续猜，不如直接读源码，看它到底把会话存去了哪。

## 三、第一性原理：读源码，别猜

我去读了 `saml2aws` v2.36.19 的 `pkg/provider/browser/browser.go`。机制一下子清楚了——它用的是 Playwright 的 **storage state** 机制：浏览器 profile 是临时的，但登录产生的 cookie + localStorage 会被导出成一个外挂的 JSON 文件，下次再注回一个全新的 context：

```go
storageStatePath := fmt.Sprintf("%s/.aws/saml2aws/storageState.json", userHomeDir)
```

关键在于它怎么用这个路径。三段代码，拼出了完整的 bug：

```go
// 1）加载是有条件的：文件存在才读
if _, err := os.Stat(storageStatePath); err == nil {
    contextOptions.StorageStatePath = playwright.String(storageStatePath)
}

// 2）保存前，没有任何 os.MkdirAll —— 它从不创建这个目录

// 3）保存失败只记一条 INFO 日志，然后咽下去
_, err := context.StorageState(storageStatePath)
if err != nil {
    logger.Info("Error saving storage state", err)
}
```

**代码考古学**：三个月后没人记得「为什么 Mac 行、WSL 不行」，因为答案从不在报错里，只在一条没人会去看的 INFO 日志里。读源码花了五分钟，比我在 keyring 那条路上瞎猜的十分钟更快、更确定。

> 当「成功的命令」配上「悄悄失败的副作用」，日志级别就是你唯一的线索——而它偏偏被调到了最低。

## 四、根因与一行修复

把三段代码和我这台 WSL 的现状对上，死循环就完整了：

```text
~/.aws/saml2aws/            ← 整个目录不存在
~/.aws/saml2aws/storageState.json   ← 因此从没被创建
```

于是每次登录都是：**目录不存在 → 没文件可加载(os.Stat 失败) → 完整登录 + MFA → 想保存却因目录不存在而失败 → 失败被降级成 INFO 日志咽掉 → 文件永远建不出来 → 下次又从零开始。**

Mac「丝滑」的唯一原因，是那个目录在某个时间点被创建过——一旦 `storageState.json` 存在，循环就自我维持了。差异不在 OS 的能力，在一个目录的有无。

修复就是一行：

```bash
mkdir -p ~/.aws/saml2aws
# 然后再登录一次（这次会完整登录并成功写出 storageState.json）
saml2aws login --profile <your-profile>
# 验证文件真的生成了
ls -la ~/.aws/saml2aws/storageState.json
```

之后每次登录都会像 Mac 一样自动跳过，直到 Google 的 session cookie 过期（通常几天到几周）。

**WSL 的二级坑（面试拿分点）**：如果你在 WSL 里把 `~/.aws` 软链到了 Windows 盘——

```text
~/.aws  ->  /mnt/c/Users/<you>/.aws     （drvfs 挂载）
```

那么就算建了目录，`storageState.json` 的写入也可能因为 drvfs 的文件锁/原子写兼容性问题而不稳定。真遇到，就把 `~/.aws`（或单独给 saml2aws 一个路径）落到 WSL 原生文件系统上，绕开 drvfs。这个坑，两个现有的上游修复 PR 都没覆盖。

## 五、比 bug 更贵的教训：错误的代价 = 可观测性 × 发生频率

这才是我想让你带走的那一个反直觉的洞察。

缺的那行 `os.MkdirAll` 不是什么高深 bug，它是个一眼能看懂的疏漏。但它的**代价**被严重低估了，因为我们习惯用「严重级别」给 bug 排序——崩溃是 P0，INFO 日志是「还好吧」。这个排序是错的。

真正决定代价的是两件事的乘积：

- **可观测性**：这个失败有多难被发现？（崩溃：立刻可见；INFO 日志里的一行：几乎不可见）
- **发生频率**：它多久发生一次？（这个 bug：每个新装用户、每次登录）

一个崩溃会被立刻修，因为它吵。而这个被降级成 INFO 的保存失败，安安静静地让**每一个**新装 Browser provider 的用户、在**每一次**登录时都白做一遍 MFA——而且没人知道会话持久化其实是坏的。

这不是我的臆测。去上游看一眼就知道它有多贵：

| 信号 | 实情 |
|---|---|
| 这个 bug 被报告了吗 | 是，issue **#1526**，标题几乎和我的结论一字不差 |
| 有修复吗 | 有**两个** PR（**#1522**、**#1527**），都是加一行 `os.MkdirAll` |
| 修复合并了吗 | 没有。分别躺了 4–7 个月，零 review |
| 这是个冷门项目吗 | ⭐ 2246，**295 个 open issue**，最近一次发版是 **18 个月前** |

一行正确的修复，在一个两千多 star 的工具里躺了大半年没人合。不是因为难，是因为它从不吵——**没人被它吵醒过。**

**部落知识 → 工程产物**：这正是 Senior 和 Principal 的分水岭。Senior 知道「mkdir 一下就好了」，把自己这台修好，继续干活——这个知识活在他脑子里，是部落知识。Principal 会问：为什么每个新用户都要重新发现一遍？于是那行修复会变成代码里的 `os.MkdirAll`、会变成一个保存失败时的显式报错（而不是 INFO）、会变成 README 里的一句话。**把只在口口相传里的东西，固化成代码/文档/检查——这是 Principal 的活。**

> 最危险的浪费，是你根本没意识到的浪费。日志级别调得越低，这种浪费活得越久。

## 三张地图

把这次排查收束成一句话：我追的不是 bug，是「持久化到底落在哪」这条数据流。

| 我以为持久化在哪 | 实际在哪 | 为什么我会猜错 |
|---|---|---|
| keyring（密码保险箱） | 跟它无关 | 被「Linux 没 Keychain」的常识带偏 |
| 浏览器 profile（cookie 在浏览器里） | 临时目录，用完即弃 | 以为「记住登录」= 浏览器记住 cookie |
| —— | 外挂的 `storageState.json`（但目录没被创建） | 真相只在源码里，不在报错里 |

## 立刻可以做的事

1. 如果你在用 `saml2aws` 的 Browser provider、又每次都要重登：`mkdir -p ~/.aws/saml2aws`，再登一次，确认 `storageState.json` 生成。
2. 顺手去 issue **#1526** 留一条「WSL2 + v2.36.19 已复现」，给 **#1522 / #1527** 点个 LGTM——帮一个失维但有用的工具把正确修复推过线，比你自己再开一个重复 PR 更有价值。
3. 回头审一下你自己代码里的 `logger.Info("...failed...", err)`：有没有哪个「失败」被你降级成了 INFO？用「可观测性 × 发生频率」给它重新定级，而不是用「感觉严不严重」。

## 预告

这个 bug 让我动了另一个念头：既然 Browser provider 这条路径（真实浏览器做 SSO）是未来趋势、原版又明显没人精修，**如果让我来重写这条路径，会话持久化该怎么做对？** 自动续期、过期感知、多账号会话管理、WSL-first 的工程化——下一篇聊聊这个设计。

---

*工具不会因为「能跑」就等于「做对了」。它只是把失败调低了音量，等你某天换台机器，才被迫听见。*
