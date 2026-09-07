#!/usr/bin/env python3
"""
FDE Series Video Generator Runner
Converts the AI-FDE video scripts into video assets or imports them into video generators.
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "video_output" / "fde_series"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def list_episodes():
    print("\n=== AI-FDE Playbook Video Scripts Available ===")
    scripts = sorted(list(SCRIPTS_DIR.glob("ep*.md")))
    for idx, s in enumerate(scripts, 1):
        print(f"[{idx}] {s.name}")
    return scripts

def main():
    scripts = list_episodes()
    print(f"\nTotal scripts found: {len(scripts)}")
    print(f"Location: {SCRIPTS_DIR}")
    print("\nUsage options:")
    print("1. Copy script content directly into Descript / ElevenLabs / Teleprompter.")
    print("2. Feed into ShortGPT pipeline (e.g. runShortGPT.py).")
    print("3. Synthesize via local TTS and FFmpeg.")

if __name__ == "__main__":
    main()
