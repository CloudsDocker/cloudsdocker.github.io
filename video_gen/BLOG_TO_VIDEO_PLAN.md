# Tech Blog → YouTube Video Automation Plan

## 📋 整体工作流

```
Markdown Blog
    ↓
[1] Parse Content (标题、段落、代码块、图片)
    ↓
[2] Generate Narration (语音旁白 + 时间戳)
    ↓
[3] Render Visuals (代码截图、文字卡、图片)
    ↓
[4] Compose Video (拼接 + 音频 + 字幕)
    ↓
[5] Upload to YouTube (自动发布 + SEO)
```

---

## 🛠️ 技术栈选择

### Phase 1: MVP（核心功能）

| 功能 | 工具 | 原因 |
|------|------|------|
| **Markdown 解析** | `markdown` + `BeautifulSoup` | 提取结构化内容 |
| **文本转语音（TTS）** | `pyttsx3`（本地）或 `gTTS`（Google） | 本地离线运行，不依赖 API key |
| **图像生成** | `Pillow`（PIL） | 渲染代码块、文字卡、表格截图 |
| **视频合成** | `MoviePy`（基于 FFmpeg） | 纯 Python，易于集成 |
| **字幕生成** | 从 TTS 时间戳自动生成 | 同步音频和文字 |
| **背景音乐** | `librosa` + 开源音乐库（YouTube Audio Library） | 版权安全 |

### Phase 2: 增强（后续迭代）

| 功能 | 工具 | 目的 |
|------|------|------|
| **代码语法高亮** | `pygments` + `PIL` | 美观的代码截图 |
| **表格动画** | `matplotlib` + `MoviePy` | 动态数据展示 |
| **屏幕录制** | `pyautogui` + `mss` | 实时演示效果 |
| **YouTube 自动上传** | `google-auth-oauthlib` | 自动发布 |
| **字幕文件** | 生成 `.srt` 格式 | YouTube 自动识别 |

---

## 📹 视频生成具体方案

### 方案对比

```
┌─────────────────┬──────────────────┬────────────────┬────────────┐
│ 工具            │ 优点              │ 缺点            │ 选择       │
├─────────────────┼──────────────────┼────────────────┼────────────┤
│ MoviePy         │ 纯Python,易集成   │ 较慢（CPU渲染） │ ✅ 用这个   │
│ FFmpeg          │ 快速,功能完整     │ 命令行复杂      │ MoviePy下层│
│ OpenCV          │ 高效              │ 学习曲线陡      │ 备选       │
│ Shotcut/Resolve │ 功能强大          │ 不可编程,GUI    │ ❌ 不用    │
│ Stable Video    │ 生成动画视频      │ 需要 GPU 优化   │ 未来版本   │
└─────────────────┴──────────────────┴────────────────┴────────────┘
```

### 为什么选 MoviePy？

1. **纯 Python** — 可完全自动化，无需外部 GUI
2. **易集成** — 直接在脚本中控制每一帧
3. **足够快** — 单个视频（5 分钟）∼ 5-10 分钟合成
4. **灵活** — 支持文字、图像、音频、过渡效果

---

## 🎬 具体视频结构

每个视频分为 N 个 **场景（Scene）**，每个场景包括：

```python
Scene:
  - 背景图像（代码截图 / 文字卡 / 博客图片）
  - 音频片段（对应的语音旁白）
  - 字幕文字
  - 持续时间（从音频长度计算）
  - 过渡效果（淡入/淡出）
```

### 示例：5 分钟的视频结构

```
[Scene 1] 标题卡（3秒）
  背景: 大标题 + 博客封面
  音频: "Welcome to our tech blog..."
  字幕: "Missing a Rust compiler? Don't rustup"

[Scene 2-5] 内容部分（270秒，4.5分钟）
  背景: 代码块截图 / 文字说明 / 表格
  音频: 分段语音旁白
  字幕: 自动同步

[Scene 6] 结尾卡（3秒）
  背景: 频道信息 + 订阅按钮
  音频: 背景音乐
  字幕: "Thanks for watching..."

总长: ~5 分钟
```

---

## 💻 技术实现细节

### 第 1 步：解析博客

```python
from markdown import markdown
from bs4 import BeautifulSoup

def parse_blog(file_path):
    """
    返回:
      - title: 标题
      - sections: [{
          'heading': '章节标题',
          'text': '段落文本',
          'code': '代码块',
          'image': '图片路径'
        }, ...]
    """
```

### 第 2 步：生成语音 + 时间戳

```python
import pyttsx3

def generate_narration(text_segments):
    """
    返回:
      - audio_file: 合并后的音频 MP3
      - timestamps: [
          {'text': '段落文本', 'start': 0.5, 'end': 5.2},
          ...
        ]
    """
    # pyttsx3 本地生成，快速，无需 API key
```

### 第 3 步：渲染视觉内容

```python
from PIL import Image, ImageDraw, ImageFont

def render_scene(text, code=None, image=None):
    """
    生成一帧图像（1920x1080，YouTube 标准）
    
    内容优先级:
      1. 图片（如果有）
      2. 代码块（带语法高亮）
      3. 纯文字卡
    """
```

### 第 4 步：合成视频

```python
from moviepy.editor import *

def compose_video(scenes, audio_file, background_music=None):
    """
    scenes: [
      {'image': path, 'duration': 5.0, 'caption': '...'},
      ...
    ]
    
    输出: video.mp4
    """
    # 每个 scene 显示对应的图像
    # 同时播放 audio + background_music
    # 底部添加字幕轨道
```

### 第 5 步：上传 YouTube（后期）

```python
from googleapiclient.discovery import build

def upload_to_youtube(video_file, title, description, tags):
    """
    自动上传到 YouTube
    需要: OAuth2 token
    """
```

---

## 📦 依赖安装

```bash
# 核心依赖
pip install moviepy pyttsx3 markdown pillow beautifulsoup4 python-dotenv

# 可选（图像美化）
pip install pygments matplotlib

# 可选（YouTube 上传）
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

## 🚀 开发计划

### Week 1: MVP 完成

- [ ] Day 1-2: 博客解析 + TTS 语音生成
- [ ] Day 3-4: 场景渲染（代码截图 + 文字卡）
- [ ] Day 5: MoviePy 视频合成 + 字幕
- [ ] Day 6-7: 测试 + 调优

**产出**：可生成 1 个完整 5 分钟 MP4 视频

### Week 2-3: 扩展

- [ ] 批量处理多篇博客
- [ ] 代码语法高亮（pygments）
- [ ] 背景音乐集成
- [ ] YouTube 上传自动化

### Week 4+: 高级功能

- [ ] 屏幕录制演示（pyautogui）
- [ ] 多语言字幕（Google Translate API）
- [ ] 动画效果（过渡、缩放）
- [ ] SEO 优化

---

## 📊 性能预期

| 操作 | 耗时 | GPU 需求 |
|------|------|---------|
| TTS 生成（5 分钟） | ~30 秒 | ❌ 不需要 |
| 图像渲染（60 帧） | ~2 分钟 | ❌ 不需要 |
| 视频合成（5 分钟） | ~5-10 分钟 | ✅ 用 CPU，可选 GPU 加速 |
| **总耗时** | **~15-20 分钟** | **可 CPU 完成** |

---

## 🎯 成功标准

✅ MVP 成功：
- 能从 Markdown 自动生成 MP4
- 音频 + 字幕 + 背景同步
- 支持代码块展示
- 视频质量 ≥ YouTube 标准（1080p）

✅ 可发布：
- 频率：每周 1-2 篇博客 → 1-2 个视频
- 自动上传 YouTube
- 配置字幕 + SEO 标签
- 赚钱：启用 YouTube Partner Program

---

## 📝 下一步

1. **确认选择**：你同意用 **MoviePy** 吗？
2. **选择 TTS**：
   - `pyttsx3`（完全离线，速度快）
   - `gTTS`（Google 合成，质量好）
3. **选择第一篇博客**：用哪篇作为测试？

准备好开始编码吗？

