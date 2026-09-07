# Why Your RAG Fails at Financial Reports: The Structured Outputs Secret

**Subtitle**: Building a production-grade Conversational Financial QA system from scratch, and eliminating LLM "math hallucinations" once and for all.

---

> 💡 **TL;DR**: Stop throwing generic LangChain wrappers at financial QA tasks. This article breaks down why rearranging field order in a JSON Schema (forcing `reasoning` first) leads to a massive leap in accuracy for complex tabular reasoning. An open-source, industrial-grade playbook is provided at the end.

The market is flooded with RAG tutorials: parse a PDF, chunk it, dump it into a vector DB, and use `RetrievalQA` to fetch context. 

This works fine for HR manuals. But feed it a real 10-K financial filing and ask, *"What was the percentage growth in R&D spending compared to the previous year?"* and 99% of RAG systems collapse.

Why? Because **financial reports contain dense tabular data, reverse-chronological columns, and require multi-hop numerical references**. LLMs face two fatal traps here: spatial misinterpretation and math hallucination.

As an AI Forward-Deployed Engineer (FDE), I want to share a deeply guarded architectural secret used by top AI labs (OpenAI, Anthropic): **Ordering is Mechanism**.

---

### ❌ The Fatal Flaw: The Missing Scratchpad

Let's return to the physics of the Transformer architecture: **LLMs are autoregressive next-token predictors.**

If you define a JSON Schema for your output like this:

```python
# The amateur approach: forcing the model to guess immediately
ANSWER_FORMAT = {
    "properties": {
        "value": {"type": "number", "description": "The final numeric answer"},
        "unit": {"type": "string"}
    },
    "required": ["value", "unit"]
}
```

During generation, once the model outputs `{"value": `, it **must predict the exact correct final number on the very next token!** The model has zero tokens to "think" in its head. It's like asking a student to solve advanced calculus without scratch paper, forcing them to write the final answer instantly.

---

### ✅ The FDE Architecture: Schema-Enforced Chain-of-Thought (CoT)

In production, we use `Structured Outputs` (`strict: True`) combined with a clever schema field ordering to physically force the model to think.

We don't just ask for `value`. We introduce `reasoning` and `evidence` fields, **and we place them BEFORE `value`**. Here is the industrial-grade pattern from my open-source `AI-FDE-Playbook`:

```python
# Extracted from src/prompts.py
_REASONING_FIELD = {
    "type": "string",
    "description": (
        "Your derivation: name the row label and column header of every "
        "figure you read, then show the arithmetic."
    ),
}

answer_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "final_answer",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                # CRITICAL: Reasoning must come first!
                "reasoning": _REASONING_FIELD, 
                "evidence": _EVIDENCE_FIELD,
                "value": {"type": ["number", "null"]},
                "unit": {"type": "string"}
            },
            "required": ["reasoning", "evidence", "value", "unit"],
            "additionalProperties": False
        }
    }
}
```

**Why is this magic?** Because JSON keys are generated in order. The model is forced to output `{"reasoning": "` first, giving it hundreds of tokens to "talk to itself" (e.g., *"The user wants 2021 vs 2020. Row 2 shows 2021=120M, 2020=100M. Formula is (120-100)/100..."*). 

By the time it finally encounters `"value": `, its **autoregressive self-attention mechanism is fully conditioned on those high-value derivation tokens**, driving the probability of predicting the correct final number through the roof.

---

### 📊 Scientific Verification

In AI engineering, "vibes" are dangerous. I built a full evaluation pipeline over the ConvFinQA dataset to prove this. 

Using **McNemar's exact test**, introducing strict numerical discipline and schema CoT raised strict accuracy by 5.2 points (p=0.035).

I've open-sourced this entire architecture: [GitHub Repo: AI-FDE-Playbook](https://github.com/CloudsDocker/AI-FDE-Playbook). Give it a Star! In Part 2, we will uncover how to use AST sandboxes to solve fundamental LLM arithmetic failures.
