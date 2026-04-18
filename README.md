# PPTX Editing Agent

An LLM-based PowerPoint editing agent that takes slide JSON and processes it through Claude.

## What it does

Takes a slide (JSON) and runs 3 steps:
1. **Analyze** — identify layout, find text issues
2. **Transform** — rewrite text to be professional
3. **Validate** — check nothing was broken

## Run

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key
python src/agent.py
```

## Known Issues

- All 3 Claude calls run sequentially (~6-8s total latency)
- No prompt caching — system prompt sent fresh every call
- No fallback model — if Sonnet fails, everything fails
- No parallelization — Step 1 and 2 are independent but run one after another
