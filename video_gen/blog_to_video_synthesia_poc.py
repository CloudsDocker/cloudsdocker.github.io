#!/usr/bin/env python3
"""
选项 B POC: 用专业工具生成高质量视频

方案:
1. 解析博客 → 提取关键内容
2. 用 ElevenLabs 生成高质量 AI 语音
3. 生成视觉场景（改进版，带动画）
4. 用 FFmpeg 合成最终视频

或者直接用 Synthesia/Descript API 生成完整视频

前置条件:
- pip install requests python-dotenv
- 获取 ElevenLabs API key: https://elevenlabs.io
  (免费账户: 10k 字符/月)
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# 加载 .env 中的 API key
load_dotenv()

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
OUTPUT_DIR = Path("./video_poc_output")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


# ============================================================================
# 1. 解析博客（同前面的脚本）
# ============================================================================

def parse_markdown(file_path: str) -> Dict:
    """解析 Markdown 博客"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid markdown format")

    yaml_dict = {}
    for line in parts[1].strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            yaml_dict[key.strip()] = val.strip().strip("'\"")

    title = yaml_dict.get('title', 'Untitled')
    md_content = parts[2].strip()
    sections = _extract_sections(md_content)

    return {
        'title': title,
        'description': yaml_dict.get('description', ''),
        'sections': sections[:8]  # 限制
    }


def _extract_sections(md_text: str) -> List[Dict]:
    """提取 Markdown 各部分"""
    sections = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('# ').strip()
            if title:
                sections.append({'type': 'heading', 'level': level, 'content': title})
            i += 1

        elif line.strip().startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code = '\n'.join(code_lines).strip()
            if code:
                sections.append({'type': 'code', 'content': code})
            i += 1

        elif line.strip() and not line.startswith('>'):
            para_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') and not lines[i].startswith('```'):
                para_lines.append(lines[i].strip())
                i += 1
            if para_lines:
                text = ' '.join(para_lines)
                if len(text) > 30:
                    sections.append({'type': 'text', 'content': text})

        else:
            i += 1

    return sections


# ============================================================================
# 2. ElevenLabs 高质量语音生成
# ============================================================================

def generate_speech_elevenlabs(text: str, output_file: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> float:
    """
    用 ElevenLabs 生成高质量 AI 语音

    voice_id 选项:
      - "21m00Tcm4TlvDq8ikWAM" (Rachel, 女性，清晰)
      - "jsCqWAovK2LkRecE7ZLT" (Sam, 男性，专业)
      - "EXAVITQu4vr4xnSDxMaL" (Bella, 女性，温暖)

    Free tier: 10,000 字符/月
    """
    if not ELEVENLABS_API_KEY:
        print("⚠️  未配置 ELEVENLABS_API_KEY，改用本地 TTS")
        return generate_speech_local(text, output_file)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    print(f"🎤 用 ElevenLabs 生成语音: {text[:50]}...")

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        with open(output_file, 'wb') as f:
            f.write(response.content)

        # 估算时长
        words = len(text.split())
        duration = words / 150 * 60  # 平均每分钟 150 词
        return max(duration, 2.0)

    except requests.exceptions.RequestException as e:
        print(f"❌ ElevenLabs API 错误: {e}")
        print("  使用本地 TTS 作为备选...")
        return generate_speech_local(text, output_file)


def generate_speech_local(text: str, output_file: str) -> float:
    """本地 TTS 备选"""
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.save_to_file(text, output_file)
    engine.runAndWait()

    words = len(text.split())
    return max(words / 150 * 60, 2.0)


# ============================================================================
# 3. 脚本生成（Descript 格式）
# ============================================================================

def generate_descript_script(blog: Dict) -> str:
    """
    生成 Descript 格式的脚本
    (可以导入到 Descript 中自动生成视频)

    Descript 支持:
    - 自动转录
    - AI 生成背景音乐
    - AI 虚拟主播（通过 Synthesia 集成）
    """
    script = f"""# {blog['title']}

## Scene 1: Title Card (3 seconds)

[INTRO MUSIC - upbeat tech theme]

Welcome to this tech deep dive: **{blog['title']}**

{blog.get('description', '')}

---

## Scene 2-N: Content Breakdown

"""

    for i, section in enumerate(blog['sections'], 1):
        if section['type'] == 'heading':
            script += f"\n## Scene {i+1}: {section['content']}\n\n"
            script += f"[TRANSITION - slide]\n\n"
            script += f"**{section['content']}**\n\n"

        elif section['type'] == 'text':
            script += f"\n{section['content']}\n\n"
            script += f"[PAUSE - 1 second]\n\n"

        elif section['type'] == 'code':
            script += f"\n```\n{section['content']}\n```\n\n"
            script += f"[CODE HIGHLIGHT ANIMATION]\n\n"

    script += f"""

---

## Scene Final: Outro (3 seconds)

[OUTRO MUSIC - fade out]

Thanks for watching! Subscribe for more tech deep dives.

[END]
"""

    return script


# ============================================================================
# 4. Synthesia / Descript API 集成（示意）
# ============================================================================

def create_synthesia_video_poc(blog: Dict) -> Dict:
    """
    POC: 如何用 Synthesia API 生成 AI 虚拟主播视频

    实际流程:
    1. 获取 Synthesia API key
    2. 创建 avatar (虚拟主播)
    3. 上传脚本
    4. 生成视频
    5. 下载 MP4

    定价: $30-100/月 (取决于视频数量)
    """

    config = {
        "api_provider": "Synthesia",
        "workflow": [
            "1. 登录 synthesia.io",
            "2. 获取 API key",
            "3. 选择虚拟主播角色（Rachel, Marcus 等）",
            "4. 上传脚本或使用 AI 自动生成",
            "5. 选择背景、音乐、字幕样式",
            "6. 点击生成 → 5-10 分钟后得到 MP4",
        ],
        "advantages": [
            "✅ 专业虚拟主播讲解",
            "✅ 多语言支持",
            "✅ 自动字幕生成",
            "✅ 一键发布到 YouTube",
        ],
        "estimated_time_per_video": "5-15 分钟（AI 生成）",
        "cost": "$30-100/月 + 按需付费",
    }

    return config


def create_descript_video_poc(blog: Dict) -> Dict:
    """
    POC: 如何用 Descript 生成视频

    Descript 特点:
    - 自动转录音频
    - 可视化编辑（像剪辑视频一样编辑文本）
    - AI 虚拟主播（通过 Synthesia 集成）
    - 自动字幕

    定价: 免费版有限制，付费版 $12-20/月
    """

    config = {
        "api_provider": "Descript",
        "workflow": [
            "1. 复制下面生成的脚本",
            "2. 登录 descript.com",
            "3. 创建新 Project",
            "4. 粘贴脚本",
            "5. 点击 'Generate Video' → Descript 生成音频 + 视频",
            "6. 编辑（调整段落、添加图片/视频）",
            "7. 导出 MP4",
        ],
        "advantages": [
            "✅ 非常直观（编辑文本 = 编辑视频）",
            "✅ 自动生成字幕",
            "✅ 支持多说话人",
            "✅ 集成 Clip Studios 库",
        ],
        "estimated_time_per_video": "10-20 分钟（含编辑）",
        "cost": "$12-20/月（付费版）",
    }

    return config


# ============================================================================
# 5. 完整工作流 POC
# ============================================================================

def main_poc(blog_path: str):
    """生成 POC 配置和脚本"""

    print(f"📖 读取博客: {blog_path}")
    blog = parse_markdown(blog_path)

    print(f"✅ 标题: {blog['title']}")
    print(f"✅ 章节数: {len(blog['sections'])}")

    # ---- 方案 1: ElevenLabs + FFmpeg ----
    print(f"\n{'='*60}")
    print(f"方案 1: ElevenLabs 高质量语音 + 自定义视频")
    print(f"{'='*60}")

    print(f"\n📋 脚本内容:")
    script_content = "\n".join([
        f"【{s['type'].upper()}】 {s['content'][:60]}..."
        for s in blog['sections']
    ])
    print(script_content)

    print(f"\n🎤 生成高质量语音...")
    title_text = f"Welcome to {blog['title']}"
    audio_file = OUTPUT_DIR / "narration_elevenlabs.mp3"
    duration = generate_speech_elevenlabs(title_text, str(audio_file))
    print(f"✅ 音频已生成: {audio_file} ({duration:.1f}s)")

    # ---- 方案 2: Descript ----
    print(f"\n{'='*60}")
    print(f"方案 2: Descript 自动生成视频")
    print(f"{'='*60}")

    descript_config = create_descript_video_poc(blog)
    print(f"\n📋 Descript 工作流:")
    for step in descript_config['workflow']:
        print(f"  {step}")

    print(f"\n💡 优势:")
    for adv in descript_config['advantages']:
        print(f"  {adv}")

    print(f"\n⏱️  预计时间: {descript_config['estimated_time_per_video']}")
    print(f"💰 价格: {descript_config['cost']}")

    # ---- 生成 Descript 脚本文件 ----
    script_text = generate_descript_script(blog)
    script_file = OUTPUT_DIR / "descript_script.md"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_text)
    print(f"\n✅ Descript 脚本已生成: {script_file}")

    # ---- 方案 3: Synthesia ----
    print(f"\n{'='*60}")
    print(f"方案 3: Synthesia AI 虚拟主播")
    print(f"{'='*60}")

    synthesia_config = create_synthesia_video_poc(blog)
    print(f"\n📋 Synthesia 工作流:")
    for step in synthesia_config['workflow']:
        print(f"  {step}")

    print(f"\n💡 优势:")
    for adv in synthesia_config['advantages']:
        print(f"  {adv}")

    print(f"\n⏱️  预计时间: {synthesia_config['estimated_time_per_video']}")
    print(f"💰 价格: {synthesia_config['cost']}")

    # ---- 总结 ----
    print(f"\n{'='*60}")
    print(f"📊 三种方案对比")
    print(f"{'='*60}\n")

    comparison = """
    ┌──────────────┬─────────────────┬─────────────────┬──────────────┐
    │ 方案         │ 质量            │ 速度            │ 成本         │
    ├──────────────┼─────────────────┼─────────────────┼──────────────┤
    │ ElevenLabs   │ ⭐⭐⭐⭐⭐      │ 🔥 快           │ 💰 便宜      │
    │ + 自定义     │ (语音很好)      │ (几分钟)        │ (免费试用)   │
    │              │                 │                 │              │
    │ Descript     │ ⭐⭐⭐⭐       │ 🔥 中等         │ 💰 中等      │
    │              │ (直观编辑)      │ (10-20分钟)     │ ($12-20/月)  │
    │              │                 │                 │              │
    │ Synthesia    │ ⭐⭐⭐⭐⭐      │ 🔥 快           │ 💰 贵        │
    │ (AI主播)     │ (专业级)        │ (5-10分钟)      │ ($30-100/月) │
    └──────────────┴─────────────────┴─────────────────┴──────────────┘

    推荐流程:

    ✅ 短期（这周）: 用 Descript 免费版测试
       - 导入上面生成的脚本
       - 看看效果

    ✅ 如果满意: 升级 Descript 付费版 ($12/月)
       - 解锁无限导出
       - 获得更多功能

    ✅ 长期（可选）: 考虑 Synthesia
       - 如果想要虚拟主播讲解
       - 完全自动化（每周自动生成）
    """

    print(comparison)

    # ---- 保存配置文件 ----
    config_file = OUTPUT_DIR / "poc_config.json"
    poc_config = {
        "blog_title": blog['title'],
        "descript_script_file": str(script_file),
        "elevenlabs_audio_file": str(audio_file),
        "recommended_platform": "Descript (free trial first)",
        "next_steps": [
            "1. 检查上面生成的 descript_script.md",
            "2. 去 descript.com 注册免费账户",
            "3. 复制脚本到 Descript",
            "4. 点击 'Generate Video'",
            "5. 等待 5-10 分钟",
            "6. 下载 MP4 并上传到 YouTube"
        ]
    }

    with open(config_file, 'w') as f:
        json.dump(poc_config, f, indent=2)

    print(f"\n✅ POC 配置已保存: {config_file}")
    print(f"\n📁 输出文件:")
    print(f"   - {script_file}")
    print(f"   - {audio_file}")
    print(f"   - {config_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python blog_to_video_synthesia_poc.py <blog_path>")
        sys.exit(1)

    blog_path = sys.argv[1]
    main_poc(blog_path)
