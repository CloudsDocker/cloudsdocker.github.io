# MiniMax-H3 Shot Prompts — "Schema Reasoning in Production AI"

Source post: `_posts/2026/09/08/2026-09-08-schema-reasoning-production-ai-en.md`

## 0. Hard constraints (verified, do not fight these)

Checked against `diffusers/modular_pipelines/minimax_h3/` in `video_gen/.venv` and the ComfyUI native docs:

| Constraint | Value | Consequence for you |
|---|---|---|
| Clip duration | **5–15s per generation** | There is no "one prompt = whole video". You generate a **shot list**. |
| Frame rate | fixed **24 fps** | — |
| Frame count | must be `17n + 5` | Use **192 frames = 8.000s**, **243 frames = 10.125s**, **345 frames = 14.375s** |
| Canvas | short edge 768, max 1,032,192 px, both axes ×32 | **1344×768** for 16:9. Upscale to 1080p/4K after. |
| Negative prompt | **does not exist** (checkpoint is guidance-distilled) | Put exclusions *inside* the prompt as director's notes. |
| Prompt handling | single string, **verbatim**, no chat template | What you type is what it reads. Max ~7,000 chars. |
| Audio | **native 32 kHz stereo**, generated jointly | You must direct sound, or you get mush. Audio VAE is **required** or the clip is silent. |
| References (ref2va) | ≤9 images, ≤3 video, ≤3 audio, ≤12 total; audio can't be alone | Order is semantic — it sets `<Picture i>` labels *and* the rotary clock. |

## 1. Strategy — what H3 should and should not render

H3 is not a code-screencast tool. It mangles small on-screen text. So:

- **H3 generates the cinematic spine**: the humans, the room, the tension, the metaphor, the outro. ~62s across 7 shots.
- **Code, schemas, the mermaid diagram, the tables** stay as crisp overlays/screen recordings composited in your editor on top of or between H3 shots.
- Every prompt below therefore explicitly pushes monitors **out of focus** and forbids legible text. This is deliberate — it is the single biggest source of cheap-looking AI video.

**Identity continuity**: Shot 1 is `t2va`. Freeze a clean frame of each character, then run Shots 2–7 as `ref2va` with those stills as image references. Without this, Maya changes face every shot and the video reads as AI slop.

## 2. Identity lock blocks (paste verbatim, never paraphrase)

```
MAYA: late-30s South Asian woman, shoulder-length black hair tied back loosely, thin gold-rimmed glasses, charcoal knit sweater over a white collar, small silver stud earrings, minimal makeup, tired eyes with faint dark circles.
```

```
DAVID: early-30s East Asian man, short messy black hair, three-day stubble, black zip hoodie over a grey t-shirt, black-framed glasses pushed up onto his head.
```

---

## 3. THE SHOTS

### SHOT 1 — Cold open / the hook
**Mode:** `t2va` · **1344×768** · **192 frames (8.0s)** · turbo LoRA 8 steps

```
A rain-streaked floor-to-ceiling window of a financial analytics office, late afternoon, storm light. MAYA: late-30s South Asian woman, shoulder-length black hair tied back loosely, thin gold-rimmed glasses, charcoal knit sweater over a white collar, small silver stud earrings, minimal makeup, tired eyes with faint dark circles. She sits at a desk with two monitors, the screens deliberately thrown out of focus into soft blue-white bokeh so no text is readable.

[0 to 3 seconds] Slow push in from behind her shoulder. She is still, reading. Rain runs down the glass beyond her. Her hand rests motionless on the mouse.
[3 to 5.5 seconds] She stops, leans a few centimetres closer to the screen, and her eyebrows draw together. Small, contained, real — not theatrical.
[5.5 to 8 seconds] She turns her head toward camera-left and speaks, exhausted rather than angry.

Camera: 35mm lens, shallow depth of field, slow dolly push, slight handheld float. Lighting: cool overcast key from the window, warm practical desk lamp rimming her cheek. Look: modern cinematic drama, Kodak Vision3 palette, fine grain, gentle halation on the desk lamp, deep soft shadows.

Audio: heavy rain against glass and a low HVAC hum fill the room, distant muffled keyboard clatter from across the floor, one soft notification chime at 3 seconds. Under it, a sparse minor-key piano note sustains and decays, no drums, no swell. MAYA says, quietly and flatly: "R and D spending didn't drop forty-two percent. It grew."

Do not render any legible text, numbers, user interface, charts or logos on any screen — all displays stay defocused abstract glow. No captions or subtitles burned into the image. No zoom punch-ins, no lens flares, no slow-motion, no stock-footage gloss.
```

---

### SHOT 2 — The escalation
**Mode:** `ref2va` — `<Picture 1>` = Maya still from Shot 1, `<Picture 2>` = David keyframe · **243 frames (10.125s)** · turbo 4 steps

```
Use Picture 1 only as the identity lock for MAYA — her face, glasses, hair and sweater must match exactly. Use Picture 2 only as the identity lock for DAVID — his face, stubble, hoodie and pushed-up glasses must match exactly. Neither picture defines the framing or the background of this shot.

An open-plan engineering bay at dusk, glass partitions, whiteboards with faint unreadable marker scribbles well out of focus in the background. DAVID: early-30s East Asian man, short messy black hair, three-day stubble, black zip hoodie over a grey t-shirt, black-framed glasses pushed up onto his head. He stands at a standing desk; MAYA is seated to his left in the near foreground, slightly out of focus.

[0 to 3 seconds] Medium two-shot. David gestures at his defocused monitor with an open palm, confident, already sure of his answer.
[3 to 6.5 seconds] He speaks, then shrugs once — the shrug of an engineer who has already checked his own work twice.
[6.5 to 10 seconds] Rack focus off David and onto Maya in the foreground. She does not reply. She is looking past him, thinking, and slowly shakes her head a single degree.

Camera: 50mm lens, locked-off tripod, one deliberate rack focus at 6.5 seconds. Lighting: cold overhead fluorescent wash, magenta monitor spill on David's jaw, blue window light dying behind them. Look: naturalistic office cinematography, muted desaturated palette, fine grain, no glamour.

Audio: room tone of server fans and fluorescent ballast hum, a chair creak as David shifts weight, faint typing from off-screen. Music: a single low synth pad enters at 6.5 seconds on the rack focus and holds, unresolved. DAVID says, with easy certainty: "The retrieval is flawless. The model is hallucinating math." Then, half a beat later: "We need a fine-tune."

Do not render any legible text, code, numbers, dashboards or logos anywhere — all screens and whiteboards remain defocused. No burned-in subtitles. No dramatic music swell, no camera shake, no lens flare.
```

---

### SHOT 3 — The mental model (the accountant metaphor)
**Mode:** `t2va` · **243 frames (10.125s)** · turbo 8 steps

```
A stark examination hall, high windows, long rows of empty wooden desks receding into soft darkness. A single accountant in his sixties, grey cardigan, thin wire glasses, sits alone under one hard overhead lamp. In front of him lies one pristine white score sheet. In his hand is a thick black indelible marker with the cap already off. There is no scrap paper anywhere on the desk — the empty wood around the sheet is conspicuous.

[0 to 3.5 seconds] Slow overhead crane descent toward the desk. His hand hovers, marker tip trembling one centimetre above the blank sheet.
[3.5 to 7 seconds] Cut in to a tight macro of the marker tip and the paper fibres. The tip touches down, hesitates, and leaves a single spreading black dot that bleeds into the paper.
[7 to 10 seconds] Pull back wide and high. He is very small in the empty hall, alone under the one lamp, the marker still in the air.

Camera: overhead crane descent, then 100mm macro insert, then a wide pull-back on a crane. Lighting: single hard top light, deep falloff to near-black, dust motes visible in the beam. Look: high-contrast chiaroscuro, desaturated to near-monochrome with warm skin tones retained, heavy filmic grain, slight gate weave.

Audio: cavernous room reverb, one distant clock tick every two seconds, the dry squeak of marker felt on paper at 4 seconds, a single held breath. Music: one sustained cello note, slow, no vibrato, fading at 8 seconds. No dialogue in this shot.

Do not render any legible text, letters, numbers or handwriting on the score sheet — it stays blank except for the single ink dot. No subtitles. No fast cuts, no digital glitch effects, no floating holograms.
```

---

### SHOT 4 — The mechanism (abstract, no text)
**Mode:** `t2va` · **192 frames (8.0s)** · turbo 8 steps

```
A pure abstract visualisation in a black void. A single horizontal chain of small glowing amber glass beads is strung left to right, each bead lighting in strict sequence as if igniting one after another, left neighbour feeding the next. Fine luminous filaments trail backwards from each newly lit bead to every bead behind it, building a dense fan of connections.

[0 to 2.5 seconds] Macro side-on. Two beads light in sequence, then the chain abruptly stops — the next bead flares once, cold blue and wrong, with no filaments behind it, and dims.
[2.5 to 5.5 seconds] Reset. The same chain lights again, but now a long run of beads ignites steadily in amber, each throwing filaments back through the whole chain until the strand is woven with light.
[5.5 to 8 seconds] The final bead at the right end ignites brilliant white, fed visibly by every filament behind it, and holds steady.

Camera: locked macro, extremely shallow depth of field, a slow lateral truck left to right that matches the ignition sequence. Lighting: the beads are the only light source, amber and white against absolute black, soft bloom and subtle anamorphic streak.

Audio: fine crystalline ticks, one per bead ignition, dry and close. A rising filtered synth drone builds from 2.5 seconds. At 5.5 seconds the drone resolves into a clean sustained major chord as the final bead ignites. No dialogue, no narration.

Do not render any text, numbers, code, brackets, user interface or symbols of any kind — this shot is purely physical light and glass. No subtitles. No neon cyberpunk grid, no circuit-board imagery, no rotating brain or robot.
```

---

### SHOT 5 — The fix
**Mode:** `ref2va` — `<Picture 1>` = David still · **192 frames (8.0s)** · turbo 4 steps

```
Use Picture 1 only as the identity lock for DAVID — face, stubble, hoodie and pushed-up glasses must match exactly. It does not define framing or background.

Night. The engineering bay is now dark and nearly empty, lit only by one desk lamp and defocused monitor glow. DAVID sits alone, sleeves pushed up, a cold half-finished coffee beside the keyboard. His monitor is thrown fully out of focus into soft blue bokeh.

[0 to 3 seconds] Tight over-the-shoulder from behind and slightly above. His hands move on the keyboard in short deliberate bursts, then stop.
[3 to 6 seconds] Cut to a close profile. He reads back what he has written, and something settles in his face — not triumph, just recognition. He exhales through his nose.
[6 to 8 seconds] He reaches out and presses a single key, unhurried. The defocused screen glow shifts subtly warmer across his face.

Camera: 85mm lens, very shallow depth of field, minimal handheld float, one cut from over-shoulder to profile at 3 seconds. Lighting: single warm tungsten desk lamp as key, cool blue monitor bounce as fill, everything else falling to black. Look: quiet late-night cinematography, warm-cool colour contrast, fine grain, soft halation on the lamp.

Audio: a nearly silent office, distant ventilation, mechanical keyboard keys in short irregular bursts, one long pause, then a single decisive keypress at 6.5 seconds. A ceramic mug touches the desk at 2 seconds. Music: a soft ascending piano figure, three notes, entering at 6 seconds. No dialogue.

Do not render any legible code, text, characters, brackets, editor windows or logos — the screen stays fully defocused glow. No burned-in subtitles. No matrix-style falling characters, no green terminal text, no typing montage with visible syntax.
```

---

### SHOT 6 — The resolution
**Mode:** `ref2va` — `<Picture 1>` = Maya still, `<Picture 2>` = David still · **192 frames (8.0s)** · turbo 4 steps

```
Use Picture 1 only as the identity lock for MAYA and Picture 2 only as the identity lock for DAVID. Faces, glasses, hair and clothing must match exactly. Neither picture defines the framing or background.

Next morning. The same office, now flooded with clean low-angle sunlight after the storm, the window still beaded with drying rain. MAYA stands at the desk; DAVID stands beside her. Her monitor is out of focus in soft warm bokeh.

[0 to 3 seconds] Medium shot, slight low angle. Maya scrolls, checking, still guarded. David watches her face rather than the screen.
[3 to 5.5 seconds] Her shoulders drop a centimetre. The smallest possible smile — closed mouth, mostly in the eyes. She glances sideways at David.
[5.5 to 8 seconds] David lets out a short quiet laugh and rubs the back of his neck. Camera drifts slowly past them toward the bright window and the wet glass.

Camera: 40mm lens, slow drift past the subjects toward the window, shallow depth of field. Lighting: warm low golden sun as key raking across both faces, cool bounce fill, visible dust in the sunbeam. Look: warm optimistic cinematography, gentle highlight roll-off, fine grain, light halation in the window.

Audio: morning office ambience, a distant lift chime, quiet conversation far off, birds faint beyond the glass. A short soft exhale from Maya at 3.5 seconds and a quiet two-note laugh from David at 6 seconds. Music: warm sustained strings resolving to a major chord, understated, entering at 3 seconds. MAYA says, under her breath and almost amused: "Eight point four."

Do not render any legible text, numbers, percentages, charts or logos on any screen — displays stay defocused. No subtitles. No high-five, no applause, no celebratory slow-motion, no corporate stock-footage energy.
```

---

### SHOT 7 — Outro / subscribe beat
**Mode:** `t2va` · **243 frames (10.125s)** · turbo 8 steps

```
Return to the abstract black void of the glowing bead chain, now seen from a wide graceful distance. Many parallel strands of amber beads stretch away into the dark in gentle arcs, each igniting in sequence at slightly different times, filling the frame with slow travelling waves of light.

[0 to 4 seconds] Slow orbital drift around the strands, the ignition waves moving away from camera into depth.
[4 to 7.5 seconds] The camera settles. One strand in the foreground completes its run and its final bead ignites brilliant white, holding.
[7.5 to 10 seconds] All strands fade down in a slow even dissolve toward black, leaving only the single white bead, then it too fades.

Camera: slow orbital drift, then a locked wide, long lens compression, very shallow depth of field. Lighting: self-illuminated beads only, amber to white, deep black background, soft bloom and subtle anamorphic streaks.

Audio: a soft bed of crystalline ticks at varying distances, spatially spread wide across stereo. A warm analogue synth pad rises from 4 seconds and resolves into a full sustained chord at 7.5 seconds, then decays into near silence with a long reverb tail. No dialogue, no narration.

Do not render any text, numbers, logos, watermarks, subscribe buttons, arrows or user interface of any kind — this shot is pure light and must stay clean for graphics to be composited over it. No fast strobing, no glitch effects, no neon grid.
```

---

## 4. ComfyUI execution notes

**Files** (from `Comfy-Org/MiniMax-H3` on Hugging Face):

| File | Folder |
|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `models/diffusion_models/` |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | `models/diffusion_models/` |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `models/text_encoders/` |
| `minimax_h3_video_vae_fp16.safetensors` | `models/vae/` |
| `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | `models/loras/` |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | `models/loras/` |

- **Load the audio VAE.** Skipping it is the most common mistake and silently produces a mute clip.
- Two checkpoint partitions: `fl2va` serves t2va and image/first-last-frame; `ref2va` serves reference mode. Load only the one the shot needs — each partition is large.
- Nodes: `UNETLoader` → LoRA → `BasicGuider`, with `MiniMaxH3ImageToVideo` / `MiniMaxH3ReferenceToVideo` and `MiniMaxH3AddGuide` for frame anchoring. Resolution Selector at **1344×768** (or megapixels `0.98`, multiple `32`).
- Steps: **20** base, **8** turbo for t2va/i2v, **4** turbo for ref2va.
- Generate each shot **3–4 seeds** and pick. Budget for that — first-take usable rate is low, and the difference between "AI slop" and "commercial grade" is almost entirely selection discipline.

## 5. Post pipeline

1. Generate Shots 1–7 → keep best seed each.
2. Upscale 1344×768 → 2160p (Topaz or an ESRGAN video pass), then master 1080p.
3. Composite code/schema/table overlays between and over shots — this is where the actual teaching happens.
4. Keep H3's native stereo audio as the bed; duck it under your VO.
5. Record VO yourself. Synthetic narration over synthetic video is what makes viewers bounce.

## 6. Packaging

- **Title:** `The JSON Key That Cost Us 42%`
- **Thumbnail:** Maya's Shot 1 frame, left third; right two-thirds black with `{"value"` in large mono type, a red strike, and `{"reasoning"` below in green.
- **First 8 seconds are the whole game.** Shot 1 opens cold on the dialogue line — no intro card, no channel animation, no "hey guys".
