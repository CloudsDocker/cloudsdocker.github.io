---
title: "[AI FDE Playbook 03] From 30% to 85% Accuracy: Multi-turn Prompt Ablation & In-Context Calibration"
episode: 3
series: "AI-FDE-Playbook"
language: "en-US"
duration: "4m 45s"
target_platform: "YouTube / Descript"
tags: ["Prompt Engineering", "Ablation Study", "Evaluation", "ConvFinQA", "FDE"]
---

# Video Script: From 30% to 85% Accuracy: Multi-turn Prompt Ablation & In-Context Calibration

## Scene 1: The Hook (0:00 - 0:45)
**[Visual Cue]**
- Realistic agent failure demo: Turn 1: "What was the gross margin in 2020?" -> Answer: "42.5%".
- Turn 2: "What about the previous year?" -> Agent hallucination: pulls data from 2021 instead of 2019!
- Red alert highlighting "previous year": relative temporal references breaking multi-turn context.
- Ablation progression chart: 31% Zero-Shot to 84.7% Calibrated Few-Shot.

**[Audio / Voiceover Narration]**
"In conversational AI agents, the most insidious bugs are not calculation errors—they are coreference resolution and temporal drift.
Turn 1 discusses 2020. Turn 2 asks 'What about the previous year?'. Suddenly the model shifts forward to 2021. In high-stakes finance or enterprise workflows, a single temporal slip invalidates the entire downstream analysis.
Today, we skip intuitive prompt guessing and use formal ablation studies to demonstrate how we systematically elevated multi-turn reasoning accuracy from 31% to over 84%."

---

## Scene 2: The Three Conversational Traps (0:45 - 1:45)
**[Visual Cue]**
- Three failure taxonomy cards:
  1. Temporal Shifting: relative chronological anchors lost across turns.
  2. Entity Conflation: confusing operating income with gross profit in dense financial tables.
  3. Unit Mismatch: implicit 'in thousands' table footnotes dropped between dialogue steps.

**[Audio / Voiceover Narration]**
"Auditing hundreds of error traces across the ConvFinQA benchmark revealed three dominant failure patterns:
First, Temporal Shifting: without an explicit temporal anchor, models default to the newest year present in the text.
Second, Entity Conflation: as conversations alternate across tables and text, attention drifts to adjacent rows.
Third, Unit Mismatch: scaling factors like 'in millions' noted in table headers get lost as turns accumulate."

---

## Scene 3: The Ablation Study Matrix (1:45 - 3:00)
**[Visual Cue]**
- Step-by-step ablation bar chart:
  - A0: Zero-Shot Baseline -> 31.2%
  - A1: + Chain of Thought (Scratchpad) -> 58.4% (+27.2%)
  - A2: + Calibrated Few-Shot In-Context Examples -> 76.1% (+17.7%)
  - A3: + Explicit Temporal Anchor Guidance -> 84.7% (+8.6%)
- Code inspection: `src/prompts/` few-shot selection strategy.

**[Audio / Voiceover Narration]**
"To conquer these failure modes, we executed a disciplined ablation matrix, measuring the marginal ROI of each component:
Our uncalibrated zero-shot baseline achieved only 31.2%.
Adding the schema scratchpad we introduced in episode one drove a 27-point leap to 58.4%.
Next, in step A2, instead of random examples, we curated Few-Shot exemplars specifically demonstrating chronological backward stepping and cross-turn reference. Accuracy climbed to 76.1%.
Finally, adding strict temporal anchoring rules in the system prompt pushed benchmark accuracy to 84.7%."

---

## Scene 4: FDE Methodology: Evaluation-Driven Engineering (3:00 - 4:00)
**[Visual Cue]**
- Running evaluation pipeline: `src/evaluate.py` tracking per-turn and conversation-level pass rates.
- Displaying version comparison tables in `REPORT.md`.

**[Audio / Voiceover Narration]**
"This rigorous feedback loop separates senior practitioners from hobbyists: never tweak prompts on intuition. Anchor every iteration to regression testing.
In our repository, every prompt modification is recorded in `REPORT.md` alongside automated test runs, guaranteeing that gains on one slice do not trigger silent regressions elsewhere."

---

## Scene 5: Outro & Next Episode Teaser (4:00 - 4:45)
**[Visual Cue]**
- Screen showing `AI-FDE-Playbook` GitHub repo and `REPORT.md`.
- Next episode teaser: 'Error Cascades & Circuit Breakers: Preventing Cost Explosions in Multi-turn Agents'.

**[Audio / Voiceover Narration]**
"When you replace prompt intuition with formal ablation, you unlock reliable enterprise performance.
All ablation configurations, prompt exemplars, and test suites are live in the `AI-FDE-Playbook` repo.
In our final episode, we tackle the hardest operational challenge: multi-turn error cascading and runaway API costs.
Like, subscribe, and star the repo. See you in the finale!"
