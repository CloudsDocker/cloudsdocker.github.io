# Humanity Checklist

The whole point of this pipeline is "输出倒逼输入" — writing forces real
learning, and the writing has to actually be *the author's*, not a generic
LLM essay wearing the author's frontmatter. This file is the gate a draft has
to pass before it's offered to the user as done.

## Why this file exists

Left alone, a model asked to "write a technical blog post about X" converges
on the same handful of moves regardless of who's asking: hedge everything,
summarize instead of arguing, praise every technology's tradeoffs equally,
reach for the same dozen transition phrases. None of that is *wrong*, but a
few hundred of these posts across the internet read identically. This
author's blog already has a real, distinctive voice (see `voice-profile.md`)
— the job here is to protect it, not sand it down toward the mean.

## Phrases and moves to never use

If any of these show up in a draft, rewrite the sentence — don't just
delete the phrase, since the underlying move (hedge, pad, summarize) is the
actual problem:

- "In today's fast-paced world / rapidly evolving landscape"
- "It's important to note that...", "It's worth mentioning..."
- "Dive into", "unlock the power of", "game-changer", "seamless(ly)"
- "In conclusion", "Overall", "To sum up" as a section opener
- A closing paragraph that restates the intro without adding anything
- On-one-hand/on-the-other-hand hedging that never actually lands on a
  position — this author *always* lands on a position (see "Principal's
  解法", "一句话哲学", "第一性原则" — these are all verdicts, not surveys)
- A list of adjectives standing in for a real claim ("robust, scalable,
  efficient solution") — replace with the specific mechanism that makes it
  true, or cut it
- Praising a tool/pattern without naming what it costs, or criticizing one
  without naming what it's for — this voice's tables always show both sides
- Uniform, evenly-spaced rhythm (same sentence length throughout, an em dash
  in every third sentence) — read the draft aloud; if it sounds like a
  metronome, vary it

## What every draft must have (verify explicitly before calling it done)

1. **A stance the reader could disagree with.** Not "there are tradeoffs" —
   an actual claim like "用户态 polling 永远是次优解" that someone could push
   back on in a comment. If the raw material doesn't contain one, that's a
   sign the piece isn't ready to publish yet — surface this to the user
   rather than manufacturing a fake-confident claim to fill the gap.
2. **At least one concrete, checkable artifact**: a real error message, a
   real log line, a real file path, a real command output — pulled from the
   raw notes or supplied by the user. Never invent a plausible-looking error
   message or benchmark number; mark it `[NEEDS REAL ARTIFACT: ...]` and ask
   instead.
3. **Exactly one clearly-stated counter-intuitive insight** (a "反直觉的洞察"),
   not a laundry list of five equally-weighted takeaways. Pick the strongest
   one from the raw notes.
4. **A biographical or narrative detail that only the author could supply**
   if the post uses a personal hook (a real mentee's situation, a real
   incident, a real year/company/scale number). If the raw notes don't have
   one, do not invent an "Alex" scenario from nothing — ask the user for the
   real anecdote, or fall back to a first-person framing that doesn't
   require a fabricated third party. See "Required interview" below.
5. **Variation from the last few posts.** Before finalizing, skim the 2-3
   most recent posts in `_posts/` (`ls -t _posts/*/*/*/*.md | head`) and
   check: same narrative device (Alex) three times running? Same closer
   label ("一句话哲学") every time? Same mental-model term reused back to
   back? If yes, change it — the goal is a recognizable voice, not a
   template.

## Required interview before drafting (don't skip this)

Never fabricate specifics attributed to the real author. Before writing the
narrative hook, ask the user directly (a short, specific question, not an
open-ended "tell me about yourself"):

- "Did this actually happen to you, or should I frame it in third person /
  hypothetically?"
- "Is there a real number, error message, or timestamp from when this
  happened that I should use instead of a generic one?"
- "Is there a strong opinion you hold here that I should make the spine of
  the post, even if it's a little combative?"

If the user is in a hurry and says "just use your judgment / make something
up that's plausible", that's their call to make — but say explicitly in
your reply which details are invented placeholders, so they can swap in real
ones before publishing. Never silently present a fabricated anecdote as if
it were the author's real experience.

## Bilingual check

The English version must not be a literal translation — re-derive the hook,
since a "凌晨两点" phone call reads differently translated than reframed for
an English-reading audience. Keep the same argument, tables, and code; the
narrative dressing can and should shift idiom. Cross-check both versions
land the same core stance.
