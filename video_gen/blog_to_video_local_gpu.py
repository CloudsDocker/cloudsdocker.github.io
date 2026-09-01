#!/usr/bin/env python3
"""
完全本地 + OSS 方案: Tech Blog → 专业质量 YouTube 视频

工具栈:
  - Coqui TTS (本地 TTS，GPU 加速)
  - OpenAI Whisper (生成字幕)
  - FFmpeg (视频合成)
  - Pyautogui (屏幕录制)
  - Pillow (图像生成)

硬件要求:
  - GPU: RTX 5080 (或任何 NVIDIA GPU)
  - RAM: 16GB+
  - 磁盘: 50GB 空闲

安装:
  pip install TTS openai-whisper pyautogui Pillow
  # 首次运行会自动下载模型 (~2GB)

用法:
  python blog_to_video_local_gpu.py <blog_path>
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import time

from PIL import Image, ImageDraw, ImageFont

# TTS - 改用 gTTS
try:
    from gtts import gTTS
except ImportError:
    print("❌ 需要安装: pip install gTTS")
    sys.exit(1)

# 屏幕录制
try:
    import pyautogui
    import mss
except ImportError:
    print("❌ 需要安装: pip install pyautogui mss")
    sys.exit(1)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class Config:
    # 输出
    output_dir = Path("./video_hq_output")

    # 视频参数
    video_width = 1920
    video_height = 1080
    fps = 30

    # 颜色
    bg_color = (15, 15, 25)  # 深蓝黑
    text_color = (240, 240, 250)
    accent_color = (100, 200, 255)  # 浅蓝
    code_bg_color = (20, 25, 35)

    # 字体
    font_file = "C:/Windows/Fonts/arial.ttf"

    # TTS 配置
    # 使用 gTTS (Google Text-to-Speech)
    # - 质量: ⭐⭐⭐⭐ (自然，清晰)
    # - 速度: 快 (5-10 秒生成 1 分钟音频)
    # - 成本: 免费
    # - 需要: 网络连接（首次下载缓存）


config = Config()
config.output_dir.mkdir(exist_ok=True, parents=True)


# ============================================================================
# 1. 博客解析 (同前)
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
        'sections': sections[:10]
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
# 2. Coqui TTS (GPU 加速)
# ============================================================================

def generate_tts_gtts(text: str, output_file: str) -> float:
    """
    用 gTTS (Google Text-to-Speech) 生成语音
    - 质量好，自然
    - 需要网络（首次缓存）
    - 支持多语言
    """
    print(f"🎤 [gTTS] 生成语音: {text[:50]}...")

    try:
        # 创建 gTTS 对象
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)

        print(f"✅ 语音已保存: {output_file}")

        # 获取音频时长
        try:
            import wave
            with wave.open(output_file, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        except:
            # 备选: 估算（英文，每分钟 ~150 词）
            words = len(text.split())
            return max(words / 150 * 60, 2.0)

    except Exception as e:
        print(f"❌ TTS 错误: {e}")
        raise


# ============================================================================
# 3. 屏幕录制 (真实演示代码执行)
# ============================================================================

def record_terminal_demo(commands: List[str], duration: int, output_file: str):
    """
    录制 Terminal 执行代码的演示

    例如:
      commands = [
        "awk '{print NR, $0}' example.txt",
        "awk 'NR==5' example.txt"
      ]
    """
    print(f"📹 录制终端演示: {len(commands)} 个命令")
    print(f"   时长: {duration}s")
    print(f"   输出: {output_file}")

    # 使用 FFmpeg 录屏
    cmd = [
        'ffmpeg', '-y',
        '-f', 'gdigrab',  # Windows 屏幕捕获
        '-framerate', str(config.fps),
        '-i', 'desktop',  # 捕获整个桌面
        '-t', str(duration),  # 录制 duration 秒
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_file
    ]

    print("⚠️  手动操作: 在 Terminal 中运行以下命令")
    for cmd_str in commands:
        print(f"  $ {cmd_str}")
    print(f"\n按 Enter 开始录屏（{duration}s）...")
    input()

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ============================================================================
# 4. 高质量图像渲染
# ============================================================================

def render_title_card(title: str, subtitle: str = "") -> str:
    """生成专业标题卡"""
    img = Image.new('RGB', (config.video_width, config.video_height), config.bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(config.font_file, 100)
        font_subtitle = ImageFont.truetype(config.font_file, 50)
    except:
        font_title = font_subtitle = ImageFont.load_default()

    # 渐变背景 (简单版: 用半透明矩形)
    for i in range(config.video_height):
        # 渐变从深蓝到黑
        alpha = int(i / config.video_height * 30)
        color = (20 + alpha, 30 + alpha, 50 + alpha)
        draw.line([(0, i), (config.video_width, i)], fill=color, width=1)

    # 标题
    title_lines = _wrap_text(title, 40)
    y = 250
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        x = (config.video_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=config.accent_color, font=font_title)
        y += 130

    # 副标题
    if subtitle:
        y += 50
        for line in _wrap_text(subtitle, 80):
            bbox = draw.textbbox((0, 0), line, font=font_subtitle)
            x = (config.video_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, fill=config.text_color, font=font_subtitle)
            y += 70

    img_path = config.output_dir / "card_title.png"
    img.save(img_path)
    return str(img_path)


def render_code_card(code: str, language: str = "bash") -> str:
    """生成代码卡（带语法高亮）"""
    img = Image.new('RGB', (config.video_width, config.video_height), config.bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_code = ImageFont.truetype(config.font_file, 36)
        font_label = ImageFont.truetype(config.font_file, 32)
    except:
        font_code = font_label = ImageFont.load_default()

    # 代码框背景
    margin = 80
    draw.rectangle(
        [(margin, 100), (config.video_width - margin, config.video_height - 100)],
        fill=config.code_bg_color,
        outline=config.accent_color,
        width=3
    )

    # 语言标签
    draw.text((margin + 30, 120), f"$ {language}", fill=config.accent_color, font=font_label)

    # 代码行
    y = 200
    for line in code.split('\n')[:18]:  # 最多18行
        # 简单语法高亮
        if line.strip().startswith('#'):
            color = (100, 180, 100)  # 绿色
        elif any(kw in line for kw in ['awk', 'bash', 'if', 'for', 'while', 'print']):
            color = (200, 150, 80)  # 橙色
        else:
            color = (150, 200, 255)  # 蓝色

        draw.text((margin + 40, y), line[:95], fill=color, font=font_code)
        y += 50

    img_path = config.output_dir / f"card_code_{abs(hash(code))}.png"
    img.save(img_path)
    return str(img_path)


def render_text_card(text: str) -> str:
    """生成文本卡"""
    img = Image.new('RGB', (config.video_width, config.video_height), config.bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_body = ImageFont.truetype(config.font_file, 44)
    except:
        font_body = ImageFont.load_default()

    # 内容框
    margin = 100
    draw.rectangle(
        [(margin, 100), (config.video_width - margin, config.video_height - 100)],
        fill=(25, 30, 40),
        outline=config.accent_color,
        width=2
    )

    # 文本
    y = 150
    for line in _wrap_text(text, 100):
        draw.text((margin + 50, y), line, fill=config.text_color, font=font_body)
        y += 80
        if y > config.video_height - 150:
            break

    img_path = config.output_dir / f"card_text_{abs(hash(text))}.png"
    img.save(img_path)
    return str(img_path)


def _wrap_text(text: str, width: int) -> List[str]:
    """换行"""
    words = text.split()
    lines = []
    current = []

    for word in words:
        current.append(word)
        if len(' '.join(current)) > width:
            lines.append(' '.join(current[:-1]))
            current = [word]

    if current:
        lines.append(' '.join(current))

    return lines


# ============================================================================
# 5. 用 FFmpeg 合成最终视频
# ============================================================================

def compose_final_video(scenes: List[Dict], output_file: str):
    """用 FFmpeg 合成最终高质量 MP4"""
    print(f"\n🎬 合成最终视频 ({len(scenes)} 场景)...")

    concat_file = config.output_dir / "concat.txt"
    concat_list = []

    for i, scene in enumerate(scenes):
        print(f"  [{i+1}/{len(scenes)}] {scene.get('caption', 'Scene')[:30]}...")

        img_video = config.output_dir / f"scene_{i}.mp4"

        # FFmpeg: 从图像生成视频
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', str(scene['image']),
            '-c:v', 'libx264',
            '-crf', '20',  # 质量 (18-28，低=更好)
            '-preset', 'slow',  # slow=更高质量但更慢
            '-t', str(scene['duration']),
            '-pix_fmt', 'yuv420p',
            str(img_video)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 添加音频
        if 'audio' in scene and Path(scene['audio']).exists():
            scene_with_audio = config.output_dir / f"scene_audio_{i}.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', str(img_video),
                '-i', str(scene['audio']),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                str(scene_with_audio)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            concat_list.append(str(scene_with_audio))
        else:
            concat_list.append(str(img_video))

    # 合并
    with open(concat_file, 'w') as f:
        for video in concat_list:
            f.write(f"file '{video}'\n")

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-c', 'copy',
        '-crf', '20',
        output_file
    ]

    print(f"\n  [合并所有场景...]")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ 视频已生成: {output_file}")


# ============================================================================
# 6. 主函数
# ============================================================================

def main(blog_path: str):
    """主函数"""
    print(f"\n{'='*70}")
    print(f"🎥 本地 GPU 高质量视频生成器")
    print(f"{'='*70}\n")

    print(f"📖 读取博客: {blog_path}\n")
    blog = parse_markdown(blog_path)

    print(f"✅ 标题: {blog['title']}")
    print(f"✅ 章节数: {len(blog['sections'])}\n")

    print(f"🔧 配置:")
    print(f"   TTS: gTTS (Google Text-to-Speech)")
    print(f"   视频: {config.video_width}x{config.video_height} @ {config.fps}fps\n")

    scenes = []

    # 场景 1: 标题
    print(f"🎨 生成场景...\n")
    title_img = render_title_card(blog['title'])
    title_audio = config.output_dir / "narration_000_title.wav"
    title_text = f"{blog['title']}"
    duration = generate_tts_gtts(title_text, str(title_audio))

    scenes.append({
        'image': title_img,
        'audio': str(title_audio),
        'caption': blog['title'],
        'duration': max(duration, 3.0)
    })

    # 场景 2-N: 内容
    for i, section in enumerate(blog['sections'], 1):
        section_type = section['type']
        content = section['content'][:60]
        print(f"  Scene {i+1}: [{section_type.upper()}] {content}...")

        if section_type == 'heading':
            img = render_text_card(section['content'])
            duration = 2.0
            scenes.append({'image': img, 'duration': duration})

        elif section_type == 'code':
            img = render_code_card(section['content'])
            audio_file = config.output_dir / f"narration_{i:03d}_code.wav"
            narration = f"Here's a {section['content'].split()[0] if section['content'] else 'code'} example"
            duration = generate_tts_gtts(narration, str(audio_file))
            scenes.append({
                'image': img,
                'audio': str(audio_file),
                'duration': max(duration, 3.0)
            })

        elif section_type == 'text':
            img = render_text_card(section['content'])
            audio_file = config.output_dir / f"narration_{i:03d}_text.wav"
            duration = generate_tts_gtts(section['content'], str(audio_file))
            scenes.append({
                'image': img,
                'audio': str(audio_file),
                'duration': max(duration, 3.0)
            })

    # 合成
    output_file = str(config.output_dir / "final_video_hq.mp4")
    print(f"\n🎬 合成最终视频...")
    compose_final_video(scenes, output_file)

    print(f"\n✨ 完成!")
    print(f"📁 输出: {output_file}")
    print(f"📊 总时长: {sum(s['duration'] for s in scenes):.1f}s")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python blog_to_video_local_gpu.py <blog_path>")
        sys.exit(1)

    blog_path = sys.argv[1]
    main(blog_path)
