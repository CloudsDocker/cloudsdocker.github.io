#!/usr/bin/env python3
"""
简化版：Tech Blog → MP4 视频生成器
用 FFmpeg 命令行合成，避免 MoviePy 的依赖问题

用法:
    python blog_to_video_simple.py <blog_path>
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict

from PIL import Image, ImageDraw, ImageFont
import pyttsx3


# ============================================================================
# CONFIG
# ============================================================================

OUTPUT_DIR = Path(__file__).parent / "video_output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

BG_COLOR = (20, 20, 20)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (0, 200, 255)

FONT_FILE = "C:/Windows/Fonts/arial.ttf"

TTS_RATE = 150


# ============================================================================
# 1. 博客解析
# ============================================================================

def parse_markdown(file_path: str) -> Dict:
    """解析 Markdown 博客"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid markdown format")

    yaml_str = parts[1]
    yaml_dict = {}
    for line in yaml_str.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            yaml_dict[key.strip()] = val.strip().strip("'\"")

    title = yaml_dict.get('title', 'Untitled')
    md_content = parts[2].strip()
    sections = _extract_sections(md_content)

    return {
        'title': title,
        'sections': sections[:12]  # 限制章节数
    }


def _extract_sections(md_text: str) -> List[Dict]:
    """提取 Markdown 各部分"""
    sections = []
    lines = md_text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # 标题
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('# ').strip()
            if title:
                sections.append({'type': 'heading', 'level': level, 'content': title})
            i += 1

        # 代码块
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

        # 段落
        elif line.strip() and not line.startswith('>'):
            para_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') and not lines[i].startswith('```'):
                para_lines.append(lines[i].strip())
                i += 1
            if para_lines:
                text = ' '.join(para_lines)
                if len(text) > 20:  # 过滤太短的
                    sections.append({'type': 'text', 'content': text})

        else:
            i += 1

    return sections


# ============================================================================
# 2. 文本转语音
# ============================================================================

def generate_narration(text: str, output_file: str) -> float:
    """生成语音，返回时长（秒）"""
    print(f"🎤 生成语音: {text[:50]}...")

    engine = pyttsx3.init()
    engine.setProperty('rate', TTS_RATE)
    engine.save_to_file(text, output_file)
    engine.runAndWait()

    # 估算时长（每分钟 ~150 词）
    word_count = len(text.split())
    duration = word_count / (TTS_RATE / 60)
    return max(duration, 2.0)


# ============================================================================
# 3. 图像渲染
# ============================================================================

def render_image(text: str, code: str = None, title_mode: bool = False) -> str:
    """生成单个场景图像"""
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(FONT_FILE, 80)
        font_large = ImageFont.truetype(FONT_FILE, 50)
        font_body = ImageFont.truetype(FONT_FILE, 38)
        font_code = ImageFont.truetype(FONT_FILE, 30)
    except:
        font_title = font_large = font_body = font_code = ImageFont.load_default()

    if title_mode:
        # 标题卡
        y = 300
        for line in _wrap_text(text, 40):
            bbox = draw.textbbox((0, 0), line, font=font_title)
            x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, fill=ACCENT_COLOR, font=font_title)
            y += 120

    elif code:
        # 代码卡
        draw.rectangle(
            [(80, 100), (VIDEO_WIDTH - 80, VIDEO_HEIGHT - 100)],
            fill=(30, 30, 40),
            outline=ACCENT_COLOR,
            width=2
        )

        y = 150
        for line in code.split('\n')[:15]:
            if line.strip().startswith('#'):
                color = (100, 200, 100)
            elif any(k in line for k in ['awk', 'bash', 'if', 'for']):
                color = (200, 150, 100)
            else:
                color = (150, 200, 200)

            draw.text((120, y), line[:100], fill=color, font=font_code)
            y += 50

    else:
        # 文本卡
        y = 150
        for line in _wrap_text(text, 100):
            draw.text((100, y), line, fill=TEXT_COLOR, font=font_body)
            y += 80
            if y > VIDEO_HEIGHT - 150:
                break

    hash_val = abs(hash(text + str(code)))
    img_path = OUTPUT_DIR / f"scene_{hash_val}.png"
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
# 4. 用 FFmpeg 合成视频
# ============================================================================

def compose_video_ffmpeg(scenes: List[Dict], output_file: str):
    """
    用 FFmpeg 命令行合成视频
    scenes: [
        {
            'image': image_path,
            'audio': audio_path,
            'duration': seconds
        }
    ]
    """
    print(f"🎬 用 FFmpeg 合成视频 ({len(scenes)} 个场景)...")

    # 创建临时文件列表
    concat_file = OUTPUT_DIR / "concat.txt"
    concat_list = []

    for i, scene in enumerate(scenes):
        # 创建图像视频片段（图像持续指定秒数）
        img_video = OUTPUT_DIR / f"video_{i}.mp4"

        # 用 FFmpeg 从静态图像生成视频
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', str(scene['image']),
            '-c:v', 'libx264',
            '-t', str(scene['duration']),
            '-pix_fmt', 'yuv420p',
            str(img_video)
        ]
        print(f"  [创建片段 {i+1}/{len(scenes)}]")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 添加音频
        if 'audio' in scene and scene['audio'] and Path(scene['audio']).exists():
            img_video_with_audio = OUTPUT_DIR / f"video_with_audio_{i}.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', str(img_video),
                '-i', str(scene['audio']),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                str(img_video_with_audio)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            concat_list.append(str(img_video_with_audio))
        else:
            concat_list.append(str(img_video))

    # 写入 concat 文件
    with open(concat_file, 'w') as f:
        for video_path in concat_list:
            f.write(f"file '{video_path}'\n")

    # 合并所有片段
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-c', 'copy',
        output_file
    ]

    print(f"  [合并片段...]")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ 视频已保存: {output_file}")
    else:
        print(f"❌ FFmpeg 错误: {result.stderr}")


# ============================================================================
# 5. 主函数
# ============================================================================

def main(blog_path: str):
    """主函数"""
    print(f"📖 读取博客: {blog_path}")

    # 解析博客
    blog = parse_markdown(blog_path)
    print(f"✅ 标题: {blog['title']}")
    print(f"✅ 章节数: {len(blog['sections'])}")

    scenes = []

    # 场景 1: 标题
    print(f"\n🎨 生成场景...")
    title_img = render_image(blog['title'], title_mode=True)
    title_audio = OUTPUT_DIR / "narration_title.mp3"
    title_text = f"Welcome to: {blog['title']}"
    duration = generate_narration(title_text, str(title_audio))

    scenes.append({
        'image': title_img,
        'audio': str(title_audio),
        'duration': max(duration, 3)
    })

    # 场景 2-N: 内容
    for i, section in enumerate(blog['sections']):
        print(f"  [场景 {i+2}] {section['type']}: {section['content'][:40]}...")

        if section['type'] == 'heading':
            img = render_image(section['content'], title_mode=False)
            duration = 2.0

        elif section['type'] == 'code':
            img = render_image("Code Example", code=section['content'])
            narration_file = OUTPUT_DIR / f"narration_code_{i}.mp3"
            code_desc = f"Here's a code example: {section['content'][:100]}"
            duration = generate_narration(code_desc, str(narration_file))
            scenes.append({
                'image': img,
                'audio': str(narration_file),
                'duration': max(duration, 4)
            })
            continue

        elif section['type'] == 'text':
            img = render_image(section['content'])
            narration_file = OUTPUT_DIR / f"narration_text_{i}.mp3"
            duration = generate_narration(section['content'], str(narration_file))
            scenes.append({
                'image': img,
                'audio': str(narration_file),
                'duration': max(duration, 3)
            })
            continue

        else:
            continue

        scenes.append({
            'image': img,
            'duration': duration
        })

    # 合成视频
    output_file = str(OUTPUT_DIR / "output_video.mp4")
    print(f"\n🎬 合成视频...")
    compose_video_ffmpeg(scenes, output_file)

    print(f"\n✨ 完成！视频: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python blog_to_video_simple.py <blog_path>")
        sys.exit(1)

    blog_path = sys.argv[1]
    main(blog_path)
