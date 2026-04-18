# PPTX Editing Agent

An LLM-based PowerPoint editing agent optimized for low latency.

## What it does

Takes a slide (JSON) and runs 3 steps through Claude:
1. **Analyze** — identify layout, find text issues
2. **Transform** — rewrite text to be professional
3. **Validate** — check nothing was broken

## Optimizations Applied

| Optimization | Before | After |
|---|---|---|
| Call pattern | Sequential (one after another) | Analyze + Transform in parallel |
| Prompt caching | None (full prompt sent every call) | `cache_control: ephemeral` on system prompt |
| Fallback model | None (fails if Sonnet is down) | Sonnet → Haiku fallback |
| Latency | ~6-8s | ~2-3s |

```
Before: Analyze (2s) → Transform (2s) → Validate (2s) = ~6s
After:  Analyze (2s) ─┐
                       ├→ Validate (1s) = ~3s
        Transform (2s) ┘
```

## Run

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key

# Run the agent
python src/agent.py

# Run benchmark (compares before vs after)
python src/benchmark.py
```
