---
title: The Goal of Troubleshooting Is to Make Troubleshooting Unnecessary
header:
    image: /assets/images/hd_cpu_system_info_aws.jpg
date: 2026-09-16
tags:
 - llm
 - ollama
 - gpu
 - performance-tuning
 - troubleshooting
permalink: /blogs/tech/en/llm-vram-budget-shift-left
layout: single
category: tech
---

> "The first principle is that you must not fool yourself — and you are the easiest person to fool."
> — Richard Feynman, *Cargo Cult Science*, Caltech commencement address, 1974

# I Wrote a Six-Step Debugging Runbook, Then Realized the Right Move Was to Delete It

*From "I can diagnose this" to "this never happens" — that's where senior stops and principal starts.*

I had the answer in about four seconds. It was wrong.

I run local LLMs on my workstation. A 24B model finished loading and `ollama` had put only 34 of its 41 layers on the GPU. I went to the logs and this line jumped out:

```
level=INFO source=sched.go:450 msg="gpu memory" available="11.9 GiB" free="12.4 GiB"
```

**11.9 GiB.** But this card has 15.9 GiB.

Obvious, right? The previous model hadn't fully unloaded — `OLLAMA_KEEP_ALIVE=30m` was still holding VRAM, so the scheduler made its layer-split decision against a **stale memory ledger**. Clear the VRAM and it's fixed.

I was already drafting the runbook entry in my head.

Then I did the thing I almost skipped: **I tried to falsify it.**

```bash
ollama stop huihui_ai/mistral-small:24b
sleep 8
nvidia-smi --query-gpu=memory.used --format=csv,noheader
# 3304 MiB — confirmed clean
ollama run huihui_ai/mistral-small:24b --verbose "..."
```

```
load_tensors: offloaded 34/41 layers to GPU
```

**34/41. Byte for byte identical.**

My hypothesis was dead. And it needed to be — if I'd skipped that step and written "just clear the VRAM" into the runbook, I'd have carried a broken causal model into the next three failures and explained exactly none of them.

Three things you should be able to take away:

- **That CPU percentage in `ollama ps` is lying to you** — it looks like a slope, it behaves like a step function
- **MoE is the *worst* architecture to run on a VRAM-constrained box**, which is the opposite of the common advice
- **The most valuable debugging is the kind that makes debugging unnecessary** — and that collapses into a single shell function

The order below is pedagogical, not chronological. I'll give you the judgment call that saves you the most time first, then the mechanism underneath it. I walked it the other way that night. Four times.

---

## 1. The Percentage That Fooled Me

It started with `btop` showing all 24 cores pinned red.

```
CPU      95%          Load avg: 26.41 22.26 12.64
C0  95%  C8  95%  C16 94%
C1  95%  C9  94%  C17 97%
C2  94%  C10 93%  C18 94%
...
```

Same second, `nvidia-smi`:

```
| 0%   30C   P3   36W / 360W |  14355MiB / 16303MiB |   0%   Default |
```

**VRAM 14.3GB full. GPU utilization 0%. Power draw 36W. Temperature 30°C.**

The first time you see this combination it makes no sense. The memory is full — why is the card ice cold?

`top` gave the first hard evidence:

```
PID       USER    %CPU   RES     COMMAND
1524594   ollama  2140   15.3g   ollama
```

**`%CPU 2140`** — 21.4 cores, all inside one `ollama` process.

(One easy misread: `btop` shows the same process at 82.6%, because it normalizes by core count. `top` uses the cumulative single-core convention. **Different units — don't use one to "verify" the other.**)

And here's `ollama`'s own account of itself:

```
NAME                      SIZE     PROCESSOR          CONTEXT
dolphin-mixtral:latest    27 GB    58%/42% CPU/GPU    4096
```

A 26GB model on a 16GB card. Whatever doesn't fit gets thrown back to the CPU. The logs are blunt about it:

```
load_tensors: offloaded 13/33 layers to GPU
NumThreads:24
```

13 of 33 layers on the GPU. The other 20 get ground out by 24 CPU threads. That's where the 24 red bars come from.

### Memorize this fingerprint

| Symptom combination | Meaning | Next step |
|---|---|---|
| **VRAM full + GPU 0% + CPU pinned** | Hybrid inference, model too large | Pick a smaller model |
| VRAM full + GPU 70%+ | Normal. This is what healthy looks like | Nothing to do |
| VRAM **not** full + CPU pinned | GPU never engaged at all | Check driver / CUDA / container passthrough |

> **Of those three metrics, `power.draw` is the honest one.**
> Utilization is an instantaneous sample — it misses peaks between polls. Power has thermal inertia; it can't lie to you.
> My card pulls 253W during real inference and 36W while offloading. **10% of TDP. No ambiguity in that signal.**

---

## 2. Killing My Own Hypothesis

Back to that experiment.

Once the hypothesis died, the real cause turned out to be far more boring: **the model simply does not fit on this card.** Nothing to do with scheduler timing, `KEEP_ALIVE`, or any config value.

14.3GB of weights against 15.9GB of VRAM, minus KV cache, CUDA context and fragmentation. **It isn't short by a stroke of bad luck. It's short structurally.**

I want to sit on this for a moment, because it's about method, not GPUs:

| | Looks like debugging | Actually debugging |
|---|---|---|
| On seeing something suspicious | Treat it as the cause | Form a **hypothesis** |
| Next move | Go fix it | Design an experiment that can **falsify it** |
| When the experiment disagrees | Explain it away | **Declare the hypothesis dead**, form a new one |
| Output | A superstitious fix | A reproducible causal chain |

That left-hand column is how you end up, three months later, with a comment that says "don't remove this line, things break" and nobody alive who remembers why.

> **A hypothesis that has never survived an attempt to kill it doesn't get to be called a conclusion.**

That `11.9 GiB` log line is still true, by the way. It *is* a bug — the scheduler read a stale ledger. **It just wasn't the cause of this failure.** Real systems routinely have several anomalies live at once. **The hard part of debugging was never finding an anomaly. It's proving which one is causal.**

---

## 3. A Step Function, Not a Slope

Now the numbers. All from my own machine, same evening, same RTX 5080 16GB, same prompt.

| Model | Architecture | Weights | CPU share | prompt eval | **eval rate** |
|---|---|---|---|---|---|
| qwen2.5-14b | Dense 14B | 9.0 GB | **0%** | **1705.85 tok/s** | **86.97 tok/s** |
| mistral-small | Dense 24B | 14.3 GB | 18% | 487.34 tok/s | **2.35 tok/s** |
| qwen3:30b | MoE 30.5B | 19 GB | 35% | 7.40 tok/s | **1.38 tok/s** |
| dolphin-mixtral | MoE 46.7B | 26 GB | 58% | — | single digits |

Sit with row two for three seconds:

**18% of layers on the CPU. 97% of throughput gone.**

### The naive read vs. the senior read

**Naive read:** `18%/82% CPU/GPU` — so roughly 20% slower, good enough.

**Senior read:** Transformer layers are **strictly sequential**. Layer 1's output is layer 2's input; there is no parallelism to exploit across them. Split those layers across CPU and GPU and you get:

```
token N:  GPU runs 34 layers (fast) ──→ wait ──→ CPU runs 7 layers (slow) ──→ emit
                                                  ↑
                                    the whole chain is gated here
```

**Hybrid inference doesn't compute a weighted average. It takes a minimum.** This is Amdahl's law showing up in the inference stack: the serial portion sets the ceiling, no matter how small its share.

GPU utilization 28%, power 47W — it spends 70% of its time waiting.

### The metric you should actually watch is prompt eval

Everyone stares at generation speed. The real killer is one column over:

| | prompt eval | Degradation |
|---|---|---|
| Fully on GPU | 1705.85 tok/s | baseline |
| 35% offloaded | **7.40 tok/s** | **230x worse** |

**Prefill degrades harder than generation does.**

Which is backwards from intuition — prefill is a **batched, parallel** matrix operation, supposedly the GPU's home turf, and it collapses the furthest. That tells you the CPU-resident layers eat the entire benefit of batching.

Translated into a workload you actually run:

```
2000 tokens of RAG context ÷ 7.40 tok/s = 270 seconds
```

**Four and a half minutes before the first character appears.** If you're wiring a local model into RAG or a long-document pipeline, `prompt eval rate` matters more than `eval rate`.

> **There is no middle ground in hybrid inference. If `ollama ps` shows a CPU percentage — any value at all, even 1% — the configuration is dead.**

Say this to your team as a **binary** rule. Leave any room for "well, it depends" and people will tolerate 10%, then 20%, to squeeze in a bigger model — and then file tickets about the machine being slow.

---

## 4. MoE: The Architecture You Least Want to Offload

This was the night's most counter-intuitive finding, because it contradicts most of what's written about MoE.

`qwen3:30b` has neither "moe" nor "mixtral" in its name. I only caught it from `ollama show`:

```
architecture        qwen3moe        ← here
parameters          30.5B
quantization        Q4_K_M
```

Qwen3-30B-A3B: 30.5B total parameters, roughly 3B activated per token.

By the popular reasoning — "MoE activates fewer params, so it's friendly to modest hardware" — it should beat the dense 24B.

Measured: **1.38 tok/s. Slower than the dense 24B's 2.35.**

### Why? Because CPU inference was never compute-bound

| | Dense layer on CPU | **MoE layer on CPU** |
|---|---|---|
| Which weights per token | The same block, always | **8 random experts out of 128** |
| Memory access pattern | Sequential, contiguous | **Random, scattered** |
| CPU prefetcher | Hits perfectly | **Effectively useless** |
| L3 cache reuse | High | **Near zero** |
| Effective bandwidth | Close to DDR5 peak | **Far below peak** |

MoE routing is decided **per token, per layer**. The previous token just pulled expert #8 into cache; the router for the next token says: fetch #73. **Cache invalidated, prefetcher defeated — every token is a cold start.**

GPUs don't care (GDDR7 has low random-access latency and bandwidth to spare). **CPUs care enormously.**

> **MoE saves compute. The CPU is short on bandwidth.**
> It economizes exactly where you weren't constrained, and bills you where you were.

There's an earlier trap in the same family: **MoE sizes your VRAM by *total* parameters and your throughput by *activated* parameters.** You pay 46.7B worth of VRAM to buy 12.9B worth of intelligence — because routing is per-token, all 8 experts must stay resident. You can't evict any of them.

**Corrected selection order:**

```
MoE that fits fully  >  dense that fits fully  >>  dense that overflows  >>  MoE that overflows
```

**"MoE is friendly to modest hardware" only holds while it fits entirely in VRAM.** The moment offloading starts, it's the worst option on the board.

---

## 5. The Floating Budget: An Invisible Windows VRAM Tax

One more trap, and this one is WSL2-specific.

With every model unloaded:

```bash
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```
```
3304 MiB          ← nothing loaded, 3.3GB still held
```

So who's holding it?

```bash
nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv
```
```
pid, used_gpu_memory [MiB], process_name
                              ← empty
```

**WSL2 reaches the GPU through GPU-PV (paravirtualization). Inside WSL, `nvidia-smi` can read total VRAM but cannot enumerate host-side processes.** That 3.3GB belongs to Windows — browser hardware acceleration, the editor, the desktop compositor.

Which rewrites the budget:

| | Nominal | Actual |
|---|---|---|
| Total VRAM | 16.3 GB | 16.3 GB |
| Windows resident | — | **−3.3 GB** |
| CUDA context + fragmentation | — | −0.5 GB |
| **Actually available to ollama** | ~15.9 GB | **≈ 12.5 GB** |

**And it gets worse.** Two hours later, same command:

```
0 MiB, 16303 MiB
```

**The 3.3GB was gone** — I'd closed the browser.

So the honest statement isn't "the budget is 12.5GB." It's: **the budget floats between 12.5 and 15.3GB depending on what Windows happens to be doing.**

### That's the genuinely dangerous part

Size for 15.3GB and pick a 14GB model:

- Tonight: 100% GPU, flying ✅
- Tomorrow morning with a browser and a video call open: Windows takes its 3.3GB → **the next load quietly degrades to CPU offload** → 60x slower ❌

And you'll have no idea why. You'll just think the machine "feels slow today."

> **Intermittent failures that depend on external state are the hardest class of bug there is.**
> They don't reproduce. By the time you investigate, the browser is closed and everything looks fine.

**Capacity planning goes by the worst case.** Take the 9GB model with real headroom over the 14GB one that needs Windows to be in a good mood.

On a shared GPU, **headroom is itself a performance metric**. A config that's 5% faster on average but intermittently 60x slower is net negative engineering.

---

## 6. Making the Troubleshooting Unnecessary

Here's what this post is actually about.

That night I ran the same diagnostic sequence **three times**:

| # | Model | Conclusion |
|---|---|---|
| 1 | dolphin-mixtral 26GB | Over budget → offload |
| 2 | mistral-small 14.3GB | Over budget → offload |
| 3 | qwen3:30b 19GB | Over budget → offload |

Three failures. **One root cause.**

Somewhere in the third pass it landed: **I was using an elegant methodology to repeatedly solve a problem that should never have occurred.**

| | Junior SME | Senior SME |
|---|---|---|
| Trigger point | After the failure | **Before the decision** |
| Action | Run six diagnostic steps → find root cause | One line of arithmetic → **reject the option** |
| Cost | 20 minutes, every time | 5 seconds, every time |
| Output | One correct diagnosis | **An entire failure class that stops occurring** |

All three of those failures die to a single size check run **before `ollama pull`**.

### Turning tribal knowledge into an engineering artifact

"Don't run models over 12.5GB on a 16GB card." If that sentence lives only in my head, it's **tribal knowledge** — it depends on me being in the room and someone remembering to ask.

The line between senior and principal is **turning it into an artifact**:

```bash
# Put this in your shell config — ask it before you pull
ollama-fit() {
  local budget=12.5   # your real budget: nominal − Windows tax − CUDA context
  python3 -c "
import urllib.request, json, sys
m = sys.argv[1]
ns, tag = m.rsplit(':', 1) if ':' in m else (m, 'latest')
p = ns if '/' in ns else 'library/' + ns
d = json.loads(urllib.request.urlopen(
    f'https://registry.ollama.ai/v2/{p}/manifests/{tag}', timeout=20).read())
s = sum(l['size'] for l in d['layers'] if 'model' in l['mediaType']) / 1e9
print(f'{m}: {s:.1f} GB  ->', 'PULL OK' if s < $budget else f'REJECT (budget ${budget}GB)')
" "$1"
}
```

```bash
$ ollama-fit qwen3:30b
qwen3:30b: 19.0 GB  -> REJECT (budget 12.5GB)

$ ollama-fit gemma4:12b
gemma4:12b: 7.4 GB  -> PULL OK
```

**Five seconds. No 19GB download, no 21 pinned cores, no postmortem.**

Plus one rule aimed squarely at the MoE trap:

```bash
# Check the architecture before pulling — the number in the name lies
ollama show <model> | grep -E 'architecture|parameters'
# See moe (qwen3moe / mixtral / deepseek2…) → size VRAM by TOTAL parameters
```

### What Bian Que told the king

King Wen of Wei asked the physician Bian Que: of you three brothers, who is the best doctor?

Bian Que answered: **my eldest brother is best, my second brother next, and I am the worst of the three.**

> "My eldest brother treats illness before it takes form, so his name never travels beyond our household.
> My second brother treats it when it is still a wisp, so his name never leaves our village.
> As for me — I puncture veins, administer harsh medicines, cut into flesh. And so my name is known among the lords."
> — *Heguanzi*, chapter "Shixian" (c. 3rd century BCE)

The famous one is famous because he handles crises that have already erupted. The genuinely great one is invisible, **because nobody can name a single thing he ever cured.**

**A system that never has incidents and a system whose incidents are handled beautifully look different from the outside. In engineering, the first one is the higher achievement.**

Which is why I mean it about deleting the runbook. Not because it's wrong — **because its measure of success is never needing to open it.**

---

## Three Tables, One Idea

| Level | Question | Answer |
|---|---|---|
| **Symptom** | Why is the CPU at 95%? | Model overflowed; 20 layers thrown back to CPU |
| **Mechanism** | Why does 18% offload cost 97%? | Transformer layers are strictly serial — minimum, not average |
| **Decision** | How does it stop happening? | One line of arithmetic before pull: `size < budget` |

Top to bottom is troubleshooting. **Bottom to top is not needing to.**

---

## Do These Today

1. **Measure your machine's real VRAM budget — and measure it while the machine is busy.**
   ```bash
   # Browser, IDE, video call all open. What you measure is the floor.
   nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader
   # real budget ≈ (total − used) − 500MB
   ```

2. **Copy `ollama-fit` into your shell config** with `budget` set to the number you just measured. Run it before every pull.

3. **Audit the models you already have** and delete anything over budget. They aren't "a bit slow," they're unusable:
   ```bash
   ollama list                                  # check each line against your budget
   ollama show <each> | grep architecture        # flag anything with moe in it
   ```

4. **Fix a trap I fell into:** `ollama stop --all` **is not a real flag** (verified on v0.13.2) — and when it fails it still returns **exit code 0**, so even `set -e` won't catch it. The working form:
   ```bash
   ollama ps | awk 'NR>1 && NF {print $1}' | xargs -r -n1 ollama stop
   ```

5. **Post item 2 in your team channel.** In your head it's tribal knowledge; in a config file it's an artifact — and only once you've shared it does it start doing the work for you.

---

*The best runbook is the one gathering dust in a drawer because nobody has needed to open it.*
