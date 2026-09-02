---
title: 你的命令行工具，藏不住你的手艺
header:
    image: /assets/images/Python-expert-write-code-like-this.jpg
date: 2026-09-01
tags:
 - python
 - cli
 - developer-tools
 - terminal-ui
permalink: /blogs/tech/zh/cli-is-a-product-not-a-script
layout: single
category: tech
---

> 彼节者有间，而刀刃者无厚；以无厚入有间，恢恢乎其于游刃必有余地矣。
> —— 庄子《庖丁解牛》

# 你的命令行工具，藏不住你的手艺

*从一个 `Panel(dict)` 崩溃说起：为什么克制，才是命令行工具最高级的礼貌*

你大概率见过这样一段崩溃日志：

```
Errors found Unable to render {'topic': ..., 'titles': [...]};
A str, Segment or object with __rich_console__ method is required
```

背后的代码通常长这样，改起来只要三十秒：

```python
# 崩溃版本
console.print(Panel(data, title=f"Title for {selected_file}"))
# data 是一个 dict：{'topic': ..., 'titles': [...]}
```

大多数人会这样收尾：套一层 `try/except`，把异常吞掉，或者干脆 `str(data)` 糊一下，工具能跑就行——毕竟这只是"内部脚本"，又不是要卖钱的产品。

但这恰恰是这篇文章想戳破的假设：**一个内部工具的界面质量，是你专业水准唯一不需要客户开口就能验证的证据**。你可以在合同里写"资深工程师""十年经验"，但当对方看到你随手写的一个 CLI 工具时——是裸露的 dict 报错，还是一个清楚知道"什么时候该问、什么时候不该问"的交互——判断已经悄悄发生了。

这篇文章按"从崩溃到克制"的教学顺序展开，不是我踩坑的时间顺序。读完你会带走三样东西：

- `rich` 的渲染契约到底是什么，为什么"打印"和"渲染"是两件事；
- `InquirerPy` 里一个几乎没人提到的样式技巧：`style_override=False`；
- 一个判断"这里到底要不要加一次确认"的具体标准，而不是"多加总没错"的直觉。

## 一、渲染契约：`Panel` 不是不会打印 dict，是它压根没打算猜

`rich.Panel`（以及大多数 `rich` 的容器组件）只接受三种输入：字符串、`Segment`，或者实现了 `__rich_console__` 的对象。一个原始 `dict` 三样都不是，所以它拒绝渲染，而不是"尽力猜一下你想要什么"。

| 普通人的看法 | 资深工程师的洞察 |
|---|---|
| "`console.print` 应该什么都能打印，这是库设计得不够宽容" | "渲染层只对『渲染契约』负责，不对『你传了什么』负责——宽容地猜测，才是真正危险的设计" |
| "加个 `try/except` 把崩溃兜住就行" | "`except` 只解决『程序不崩』，解决不了『用户看懂发生了什么』；崩溃往往是工具唯一一次主动告诉你『这份数据我还没有真的看过』的机会" |

修复本身很小——从 dict 里把真正要展示的字段（这里是 `titles` 这个 list）取出来，转成字符串：

```python
titles = data.get("titles", []) if isinstance(data, dict) else data
titles_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
console.print(Panel(titles_text, title=f"Title for {selected_file}"))
```

> 崩溃不是工具的失败，是工具在提醒你：你从来没有真的"渲染"过这份数据，只是在"打印"它。

## 二、从"打印"升级成"界面"：一张会说话的 Table

修完崩溃之后，真正的问题才浮现：五个候选标题挤在一段纯文本里，用户要靠肉眼数编号才能选。升级成一张分色的表格，成本不到十行：

```python
TITLE_PALETTE = ["cyan", "magenta", "green", "yellow", "bright_blue"]

table = Table(
    title="✨ Generated Title Options ✨",
    box=box.ROUNDED,
    show_lines=True,
    title_style="bold white on dark_magenta",
)
table.add_column("#", style="bold white", justify="center", width=3)
table.add_column("Title", style="bold")
for i, t in enumerate(titles):
    color = TITLE_PALETTE[i % len(TITLE_PALETTE)]
    table.add_row(f"[{color}]{i + 1}[/{color}]", f"[{color}]{t}[/{color}]")
console.print(table)
```

颜色在这里不是装饰，是分组信号——每一行一个颜色，眼睛不需要再靠数字对齐就能锁定一整行。这是 `rich` 真正的卖点：它把"终端只能输出字符"这件事,从约束变成了一个可以设计的画布。

## 三、`get_style(..., style_override=False)`：借默认值的光，别把灯全拆了

`InquirerPy` 的样式系统里有个几乎没人在文档示例里强调的参数，踩错了会让你以为自己需要重新发明整套配色：

```python
TITLE_PICKER_STYLE = get_style(
    {
        "questionmark": "#f5a742 bold",
        "pointer": "#f542a7 bold",
        "answer": "#42c5f5 bold",
    },
    style_override=False,
)
```

| `style_override=True`（大多数示例代码的写法） | `style_override=False`（这里用的写法） |
|---|---|
| 你没写的每一个字段（`instruction`、`checkbox`、`separator`……）全部变成空字符串，样式"清零" | 你没写的字段继续沿用 `InquirerPy` 精心调过的默认色板（`#61afef`、`#98c379`……） |
| 你必须把十几个字段全部手写一遍，否则界面会看起来"缺了一块" | 你只需要覆盖你真正在意的三五个字段，其余的交给库的默认审美 |

这和写 CSS 时"只覆盖你关心的属性，别整份重写"是同一个直觉——但这个参数的名字（`style_override`）恰好和它的行为反直觉：`False` 才是"不要粗暴覆盖"的那一档。

## 四、`console.status()` 包一次真实的 `await`：把"不确定"变成"看得见的不确定"

工具在等一次真实的网络调用（这里是等 Gemini 生成候选标题）时，最常见的两种写法都不好：要么界面直接冻住，用户不知道是卡死还是在跑；要么打一行"正在处理中..."就再也不刷新。

`Console.status()` 当上下文管理器用，能在 `await` 真正等待的这段时间里跑一个动画：

```python
with console.status("[bold cyan]Asking Gemini for title ideas...[/bold cyan]", spinner="dots"):
    result = await mcp_client.call_tool("suggest_N_titles", {...})
```

细节：`status()` 单独调用不会显示任何东西——它返回的是一个 `Status` 对象，只有作为 `with` 块使用（或手动 `.start()`）才会真正启动那个后台刷新的 spinner。这也是这份代码里原本的一个隐藏 bug：早期版本里 `console.status("fetching raw files....")` 只是孤零零调用了一次，从没进 `with`，所以那行状态提示其实从来没有真正显示过。

## 五、庖丁解牛：确认框只放在真正的"节"上

开头那句庄子的话，字面意思是刀刃很薄，关节之间有空隙，把没有厚度的刀刃送进有空隙的关节，自然游刃有余。这句话经常被简化成"熟能生巧"，但真正值得学的其实是前一句被省略的部分——庖丁的刀十九年不卷刃，不是因为他动作快,是因为他"依乎天理,批大郤,导大窾",只在骨节的天然缝隙里下刀，从不硬砍。

命令行工具的确认提示（confirm/prompt）就是那把刀。加得太多，用户会对着一堆"你确定吗？"练出肌肉记忆式的连续回车，真正危险的那一次也会被顺手按过去——这和"狼来了"是同一个机制。加得太少，一次误触就把用户的源文件移进了归档目录。诀窍不是"多加一层保险"，是找到真正的"节"：

```python
publish_languages = await inquirer.checkbox(
    message="🌐 Publish which language version(s)?",
    choices=[Choice("zh", ...), Choice("en", ...)],
).execute_async()

confirmed = await inquirer.confirm(
    message=f"Publish {selected_file} as {'/'.join(publish_languages)} with this title?",
    default=False,   # 关键：不确认的默认值不是"是"
).execute_async()
```

| 这里选择要确认的动作 | 特征 |
|---|---|
| 发布：真实调用两次 Gemini（花钱）、往另一个仓库写文件、把源笔记移进 archive/ | 不可逆或有真实成本，且用户此前的选择（标题、语言）不会自动暴露这个后果 |
| 语言 checkbox 本身、标题 fuzzy 搜索的每一次按键 | 可逆、零成本、随时能改主意——加确认框只是在制造摩擦 |

`default=False` 也是一个刻意的选择：这是一个会花钱、会移动文件的动作,默认值不该是"用户按回车就等于同意"。

## 收束：五个决定,对应五种"用户成本"

| 决定 | 保护的是哪种成本 |
|---|---|
| `Panel` 要传字符串,不是 dict | 可读性成本——用户能不能看懂输出 |
| 分色 Table | 扫描成本——用户要不要靠数数字才能选对 |
| `style_override=False` | 你自己的开发成本——不用重新发明整套配色 |
| `console.status()` | 等待中的确定性成本——用户知不知道工具还活着 |
| `checkbox` + `confirm(default=False)` | 决策成本 + 不可逆成本——只在真正的"节"上停一停 |

## 立刻可以做的事

1. 翻一下你自己最近写的一个"内部小工具",搜一下有没有 `print(some_dict)` 或者裸露的 `except Exception as e: print(e)`——这些地方就是"崩溃在替你说话"的地方。
2. 检查你所有的 `confirm()` / `input("确定吗?")`,数一下有几个。如果超过三个,大概率有一半是在制造摩擦而不是保护用户——试着删掉那些"可逆、零成本"的确认。
3. 找一个你重复运行超过十次的脚本,给它加一个 `console.status()` 或等价的进度提示——这十分钟的投入,会在你自己第十一次运行它的时候还清。

*一把好的刀十九年不卷刃,不是因为它锋利,是因为它只切开真正有空隙的地方。你的命令行工具也一样——克制,才是最高级的礼貌。*
