# Stable Diffusion 3 Setup & Troubleshooting Guide

## Environment Setup

### Initial Setup Issues & Fixes

#### Issue 1: Wrong Python Environment (Miniconda Conflict)
**Problem**: Miniconda was conflicting with the system Python, causing PATH issues.

**Fix**:
```bash
# Remove miniconda to clean up environment
rm -r C:\Users\aidraworker\miniconda3

# Verify system Python is used
python --version  # Should show Windows Python, not conda
```

#### Issue 2: HuggingFace Index Configuration
**Problem**: PyTorch packages were cached to wrong locations due to improper HF_HOME configuration.

**Fix**:
1. Set HF_HOME environment variable in `.env`:
   ```bash
   HF_HOME=G:\dev\ai\video-gen\.cache
   HF_DATASETS_CACHE=G:\dev\ai\video-gen\.cache\datasets
   MODEL_PATH=G:\dev\ai\video-gen\models\sd3-medium
   ```

2. Configure `uv.toml` to use multiple indices:
   ```toml
   # PyTorch CUDA 13.2 index (for torch, torchvision, torchaudio)
   [[index]]
   url = "https://download.pytorch.org/whl/cu132"
   
   # Standard PyPI (for all other packages)
   [[index]]
   url = "https://pypi.org/simple"
   default = true
   ```

#### Issue 3: RTX 5080 CUDA Compatibility
**Problem**: RTX 5080 uses CUDA Compute Capability 12.0 (sm_120), but PyTorch 2.13.0+cu126 only supports up to sm_90.

**Error Message**:
```
torch.AcceleratorError: CUDA error: no kernel image is available for execution on the device
```

**Fix**:
```bash
# Upgrade PyTorch to CUDA 13.2 (supports RTX 5080)
uv pip uninstall torch torchvision torchaudio -y
uv cache clean

# Clean and resync
rm -rf .venv
rm uv.lock
uv sync

# Verify correct version
python -c "import torch; print(torch.__version__)"
# Should show: 2.13.0+cu132 or newer
```

#### Issue 4: Model Index Configuration
**Problem**: Downloaded original weights from `stabilityai/stable-diffusion-3-medium` but diffusers expects `model_index.json`.

**Root Cause**: The original weights repo is not diffusers-compatible. Need to download from the diffusers version.

**Fix**:
```bash
# Download diffusers-compatible weights
rm -rf G:\dev\ai\video-gen\models\sd3-medium
hf download stabilityai/stable-diffusion-3-medium-diffusers \
  --local-dir "G:\dev\ai\video-gen\models\sd3-medium"
```

**Reference**: Original README at line 71 points to:
- **Diffusers support**: https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers

---

## Generation Parameters Guide

### `num_inference_steps`
**What it is**: Number of diffusion denoising steps

**Impact**:
- **Higher** = Better image quality, slower generation
- **Lower** = Faster generation, lower quality

**Recommended values**:
| Steps | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| 20 | ~3-5 min | Good | Quick testing |
| 28 | ~9 min | Excellent | Balanced (default) |
| 50 | ~15-20 min | Best | Production quality |

**SD3 Official Recommendation**: 28-50 steps

---

### `guidance_scale`
**What it is**: How strongly the model follows your text prompt (Classifier-Free Guidance)

**Range**: 0-20 (most effective: 7-15)

**Effect by value**:
- **0** = Ignores prompt completely, pure random creativity
- **5-7** = Creative freedom, may diverge from prompt
- **7.5** = Balanced (recommended, your setting)
- **10-12** = Strong adherence to prompt
- **15+** = Very strict, less diversity, may oversaturate

**Prompt adherence vs. Creativity**:
```
Low Guidance  ←────────────────→  High Guidance
(5)                              (15)
  ↓                                ↓
Creative, free            Strict, prompt-focused
Unpredictable             Predictable
```

---

## Performance Metrics

### Your System Specs
- **GPU**: NVIDIA GeForce RTX 5080 (17.1 GB VRAM)
- **PyTorch**: 2.13.0+cu132
- **CUDA**: 13.2

### Benchmark Results
**Configuration**: 
- `num_inference_steps=28`
- `guidance_scale=7.5`
- `height=768, width=1024`
- `dtype=float16`

**Results**:
- Generation time: ~9 min 5 sec
- Peak VRAM: 19.5 GB
- Throughput: ~3.08 it/s (28 steps / 9.05 sec)

---

## Recommended Configurations

### Quick Prototyping (3-5 minutes)
```python
pipe(
    prompt="your prompt here",
    num_inference_steps=20,
    guidance_scale=7.5,
    height=768,
    width=1024
)
```

### Balanced (9 minutes) - **Recommended**
```python
pipe(
    prompt="your prompt here",
    num_inference_steps=28,
    guidance_scale=7.5,
    height=768,
    width=1024
)
```

### High Quality (15-20 minutes)
```python
pipe(
    prompt="your prompt here",
    num_inference_steps=50,
    guidance_scale=7.5,
    height=768,
    width=1024
)
```

### Creative Mode (Lower guidance)
```python
pipe(
    prompt="your prompt here",
    num_inference_steps=28,
    guidance_scale=5.0,  # More creative freedom
    height=768,
    width=1024
)
```

---

## Useful Environment Variables

Add to `.env`:
```bash
# HuggingFace Configuration
HF_HOME=G:\dev\ai\video-gen\.cache
HF_DATASETS_CACHE=G:\dev\ai\video-gen\.cache\datasets
HF_TOKEN=your_hf_token_here

# Model paths
MODEL_PATH=G:\dev\ai\video-gen\models\sd3-medium
OUTPUT_PATH=G:\dev\ai\video-gen\outputs

# PyTorch (optional)
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb=512
```

Load in Python:
```python
from dotenv import load_dotenv
import os

load_dotenv()
model_path = os.getenv('MODEL_PATH')
```

---

## Troubleshooting Checklist

- [x] PyTorch version is cu132 (`torch.__version__` shows `+cu132`)
- [x] CUDA is available (`torch.cuda.is_available()` = True)
- [x] Model weights are in diffusers format (has `model_index.json`)
- [x] Virtual environment is activated
- [x] HuggingFace token is set (if needed)
- [x] No conflicting conda/miniconda installation

---

## References

- [Diffusers Documentation](https://huggingface.co/docs/diffusers)
- [Stable Diffusion 3 Model Card](https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers)
- [PyTorch CUDA Setup](https://pytorch.org/get-started/locally/)
- [RTX 5080 Specs](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/)

