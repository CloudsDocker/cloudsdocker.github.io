import torch
from diffusers import StableDiffusion3Pipeline

# 检查 CUDA 可用性
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# 加载模型
print("\n[1/3] 正在加载模型...")
pipe = StableDiffusion3Pipeline.from_pretrained(
    "G:/dev/ai/video-gen/models/sd3-medium",
    torch_dtype=torch.float16  # 省 VRAM：16-bit 精度
)
pipe = pipe.to("cuda")

# 设置生成参数
print("[2/3] 正在生成图像...")
prompt = "one young fashionable modern girl wearing black stockings, high heels, short skirt, sexy, topless, taking a selfie in front of a mirror indoors"
negative_prompt = "realistic, and like a photograph"

with torch.no_grad():
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        height=768,
        width=1024,
        num_inference_steps=28,
        guidance_scale=7.5
    ).images[0]

print("[3/3] 保存图像...")
image.save("G:/dev/ai/video-gen/test_output.png")
print(f"✓ 完成！图像保存到 test_output.png")

# 检查 VRAM 使用
print(f"\n峰值 VRAM: {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")