#!/usr/bin/env python3
"""
Tech Blog → YouTube Video Generator
自动将 Markdown 博客转成 MP4 视频

用法:
    python blog_to_video.py <blog_path>
    python blog_to_video.py _posts/2025/02/02/2025-02-02-deep-dive-NR-FNR-in-awk-command.md
"""

import os
import sys
import re
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

import pyttsx3
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    TextClip, concatenate_videoclips, ColorClip
)
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import markdown
from bs4 import BeautifulSoup


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class Config:
    """视频生成配置"""
    # 输出
    output_dir = Path("./video_output")

    # 视频参数
    video_width = 1920
    video_height = 1080
    fps = 30

    # 颜色主题（极简专业风格）
    bg_color = (20, 20, 20)  # 深灰
    text_color = (255, 255, 255)  # 白色
    accent_color = (0, 200, 255)  # 浅蓝

    # 字体
    font_size_title = 80
    font_size_heading = 60
    font_size_body = 40
    font_size_code = 32
    font_file = "C:/Windows/Fonts/arial.ttf"  # Windows

    # 时长（秒）
    scene_duration_title = 3
    scene_duration_heading = 2
    scene_duration_text = 4
    scene_duration_code = 5

    # TTS
    tts_rate = 150  # 语速（词/分钟）


config = Config()


# ============================================================================
# 1. 博客解析
# ============================================================================

@dataclass
class BlogContent:
    """解析后的博客内容"""
    title: str
    description: str
    tags: List[str]
    sections: List[Dict]  # [{'type': 'text|code|heading', 'content': ...}, ...]


def parse_markdown(file_path: str) -> BlogContent:
    """解析 Markdown 博客文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分离 YAML frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid markdown format: missing frontmatter")

    # 解析 YAML（简单版）
    yaml_str = parts[1]
    yaml_dict = {}
    for line in yaml_str.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            yaml_dict[key.strip()] = val.strip()

    title = yaml_dict.get('title', 'Untitled')
    tags = yaml_dict.get('tags', '').split() if 'tags' in yaml_dict else []

    # 解析 Markdown 内容
    md_content = parts[2].strip()
    sections = _extract_sections(md_content)

    # 提取描述（第一段）
    description = ""
    for section in sections:
        if section['type'] == 'text':
            description = section['content'][:150]
            break

    return BlogContent(
        title=title,
        description=description,
        tags=tags,
        sections=sections
    )


def _extract_sections(md_text: str) -> List[Dict]:
    """提取 Markdown 中的各个部分（标题、段落、代码块等）"""
    sections = []
    lines = md_text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # 标题
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('# ').strip()
            sections.append({'type': 'heading', 'level': level, 'content': title})
            i += 1

        # 代码块
        elif line.strip().startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            sections.append({'type': 'code', 'content': '\n'.join(code_lines).strip()})
            i += 1

        # 段落（多行文本）
        elif line.strip():
            para_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') and not lines[i].startswith('```'):
                para_lines.append(lines[i].strip())
                i += 1
            if para_lines:
                sections.append({'type': 'text', 'content': ' '.join(para_lines)})

        else:
            i += 1

    return sections


# ============================================================================
# 2. 文本转语音 (TTS)
# ============================================================================

def generate_narration(text: str, output_file: str) -> float:
    """
    生成语音，返回音频时长（秒）
    """
    engine = pyttsx3.init()
    engine.setProperty('rate', config.tts_rate)
    engine.setProperty('volume', 1.0)

    print(f"🎤 生成语音：{text[:50]}...")
    engine.save_to_file(text, output_file)
    engine.runAndWait()

    # 读取音频文件获取时长
    try:
        audio = AudioFileClip(output_file)
        duration = audio.duration
        audio.close()
        return duration
    except:
        # 如果无法读取，估算时长（平均每60个单词5秒）
        return len(text.split()) / 12


# ============================================================================
# 3. 场景渲染（生成图像）
# ============================================================================

def render_title_scene(blog: BlogContent) -> str:
    """生成标题卡"""
    img = Image.new('RGB', (config.video_width, config.video_height), config.bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(config.font_file, config.font_size_title)
        font_small = ImageFont.truetype(config.font_file, 40)
    except:
        font_title = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 标题
    title_lines = _wrap_text(blog.title, 40)
    y_pos = 300
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        line_width = bbox[2] - bbox[0]
        x_pos = (config.video_width - line_width) // 2
        draw.text((x_pos, y_pos), line, fill=config.accent_color, font=font_title)
        y_pos += 100

    # 描述
    desc_lines = _wrap_text(blog.description, 80)
    y_pos += 50
    for line in desc_lines:
        bbox = draw.textbbox((0, 0), line, font=font_small)
        line_width = bbox[2] - bbox[0]
        x_pos = (config.video_width - line_width) // 2
        draw.text((x_pos, y_pos), line, fill=config.text_color, font=font_small)
        y_pos += 50

    # 保存
    img_path = f"{config.output_dir}/scene_title.png"
    img.save(img_path)
    return img_path


def render_heading_scene(heading: str) -> str:
    """生成章节标题卡"""
    img = Image.new('RGB', (config.video_width, config.video_height), config.bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(config.font_file, config.font_size_heading)
    except:
        font = ImageFont.load_default()

    # 居中显示标题
    lines = _wrap_text(heading, 50)
    y_pos = 400
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x_pos = (config.video_width - line_width) // 2
        draw.text((x_pos, y_pos), line, fill=config.accent_color, font=font)
        y_pos += 80

    # 下方装饰线
    draw.rectangle(
        [(400, y_pos + 50), (config.video_width - 400, y_pos + 55)],
        fill=config.accent_color
    )

    img_path = f"{config.output_dir}/scene_heading_{abs(hash(heading))}.png"
    img.save(img_path)
    return img_path


def render_text_scene(text: str) -> str:
    """生成文本卡"""
    img = Image.new('RGB', (config.video_width, config.video_height), config.bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(config.font_file, config.font_size_body)
    except:
        font = ImageFont.load_default()

    # 文本换行显示
    lines = _wrap_text(text, 100)
    y_pos = 150
    for line in lines:
        draw.text((100, y_pos), line, fill=config.text_color, font=font)
        y_pos += 80
        if y_pos > config.video_height - 150:
            break

    img_path = f"{config.output_dir}/scene_text_{abs(hash(text))}.png"
    img.save(img_path)
    return img_path


def render_code_scene(code: str) -> str:
    """生成代码块卡"""
    img = Image.new('RGB', (config.video_width, config.video_height), config.bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(config.font_file, config.font_size_code)
        font_small = ImageFont.truetype(config.font_file, 28)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 代码块背景
    code_bg_color = (30, 30, 40)
    draw.rectangle(
        [(80, 100), (config.video_width - 80, config.video_height - 100)],
        fill=code_bg_color,
        outline=config.accent_color,
        width=2
    )

    # 显示代码
    lines = code.split('\n')[:15]  # 最多15行
    y_pos = 150
    for line in lines:
        # 简单语法高亮
        if line.strip().startswith('#'):
            color = (100, 150, 100)  # 绿色注释
        elif any(kw in line for kw in ['awk', 'bash', 'if', 'for', 'while']):
            color = (200, 150, 100)  # 橙色关键字
        else:
            color = (150, 200, 200)  # 青色文本

        draw.text((120, y_pos), line[:100], fill=color, font=font_small)
        y_pos += 50

    img_path = f"{config.output_dir}/scene_code_{abs(hash(code))}.png"
    img.save(img_path)
    return img_path


def _wrap_text(text: str, width: int) -> List[str]:
    """按宽度换行文本"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > width:
            lines.append(' '.join(current_line[:-1]))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


# ============================================================================
# 4. 视频合成
# ============================================================================

def compose_video(scenes: List[Dict], blog: BlogContent, output_file: str):
    """
    合成最终视频
    scenes: [
        {
            'image': image_path,
            'audio': audio_path,
            'caption': '字幕文本'
        },
        ...
    ]
    """
    clips = []

    print(f"🎬 开始合成视频...")

    for i, scene in enumerate(scenes):
        print(f"  [{i+1}/{len(scenes)}] 处理场景...")

        # 创建图像片段
        img_clip = ImageClip(scene['image']).set_duration(scene['duration'])

        # 添加音频（如果有）
        if 'audio' in scene and scene['audio']:
            try:
                audio = AudioFileClip(scene['audio'])
                img_clip = img_clip.set_audio(audio)
            except:
                pass

        # 添加字幕（如果有）
        if 'caption' in scene and scene['caption']:
            try:
                txt_clip = TextClip(
                    scene['caption'],
                    fontsize=40,
                    color='white',
                    font='Arial',
                    method='caption',
                    size=(config.video_width - 200, 150)
                ).set_duration(scene['duration']).set_position(('center', 'bottom'))
                img_clip = CompositeVideoClip([img_clip, txt_clip])
            except:
                pass

        clips.append(img_clip)

    # 合并所有片段
    if clips:
        final_video = concatenate_videoclips(clips, method='chain')
        final_video.write_videofile(
            output_file,
            fps=config.fps,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        print(f"✅ 视频已保存: {output_file}")
    else:
        print("❌ 没有可合成的片段")


# ============================================================================
# 5. 主流程
# ============================================================================

def main(blog_path: str):
    """主函数"""
    print(f"📖 读取博客: {blog_path}")

    # 创建输出目录
    config.output_dir.mkdir(exist_ok=True)

    # 1. 解析博客
    blog = parse_markdown(blog_path)
    print(f"✅ 标题: {blog.title}")
    print(f"✅ 章节数: {len(blog.sections)}")

    # 2. 生成场景
    scenes = []

    # 场景 1: 标题
    print(f"\n🎨 生成场景...")
    title_img = render_title_scene(blog)
    title_audio = f"{config.output_dir}/narration_title.mp3"
    title_text = f"Welcome to this tech deep dive: {blog.title}"
    duration = generate_narration(title_text, title_audio)
    scenes.append({
        'image': title_img,
        'audio': title_audio,
        'caption': blog.title,
        'duration': max(duration, config.scene_duration_title)
    })

    # 场景 2-N: 内容部分
    for section in blog.sections[:10]:  # 限制场景数量（时间限制）
        if section['type'] == 'heading':
            img = render_heading_scene(section['content'])
            duration = config.scene_duration_heading
            caption = section['content']

        elif section['type'] == 'code':
            img = render_code_scene(section['content'])
            narration_file = f"{config.output_dir}/narration_code_{abs(hash(section['content']))}.mp3"
            # 简化：直接设置代码块的时长
            duration = config.scene_duration_code
            caption = f"```\n{section['content'][:80]}\n```"

        elif section['type'] == 'text':
            img = render_text_scene(section['content'])
            narration_file = f"{config.output_dir}/narration_text_{abs(hash(section['content']))}.mp3"
            duration = generate_narration(section['content'], narration_file)
            duration = max(duration, config.scene_duration_text)
            caption = section['content'][:100]

        else:
            continue

        scenes.append({
            'image': img,
            'caption': caption,
            'duration': min(duration, 10)  # 最长 10 秒
        })

    # 3. 合成视频
    output_file = f"{config.output_dir}/output_video.mp4"
    print(f"\n🎬 合成视频（{len(scenes)} 个场景）...")
    compose_video(scenes, blog, output_file)

    print(f"\n✨ 完成！视频保存到: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python blog_to_video.py <blog_path>")
        sys.exit(1)

    blog_path = sys.argv[1]
    main(blog_path)
