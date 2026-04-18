"""
PPTX Editing Agent — FIXED version (fast, parallel, cached, with fallback).

Fixes:
1. Analyze + Transform run in PARALLEL (they don't depend on each other)
2. System prompt uses prompt caching (sent once, reused across calls)
3. Fallback model: if Sonnet fails/times out, retry with Haiku
4. Target latency: <3 seconds per slide
"""

import json
import time
import concurrent.futures
import anthropic

client = anthropic.Anthropic()

PRIMARY_MODEL = "claude-sonnet-4-20250514"
FALLBACK_MODEL = "claude-haiku-4-5-20251001"

# Same system prompt, but will be sent with cache_control for prompt caching
SYSTEM_PROMPT = """You are a PowerPoint slide editing assistant.
You work with slide data in JSON format. Each slide has shapes with properties like:
- text: the text content
- x, y: position on the slide
- width, height: size of the shape
- font_size: text size
- bg_color: background color (hex)
- font_color: text color (hex)

Always respond in valid JSON."""

SAMPLE_SLIDE = {
    "slide_number": 1,
    "shapes": [
        {
            "id": "title_1",
            "text": "Q4 sales r up big time!!!",
            "x": 50,
            "y": 30,
            "width": 800,
            "height": 60,
            "font_size": 28,
            "font_color": "#000000",
            "bg_color": None,
        },
        {
            "id": "subtitle_1",
            "text": "we made alot of $$ this quarter, heres the numbers",
            "x": 50,
            "y": 100,
            "width": 800,
            "height": 40,
            "font_size": 18,
            "font_color": "#666666",
            "bg_color": None,
        },
        {
            "id": "body_1",
            "text": "Revenue: $4.2M (up 23%)\nNew customers: 340\nChurn: down to 2.1%\nTop region: North America",
            "x": 50,
            "y": 160,
            "width": 400,
            "height": 300,
            "font_size": 14,
            "font_color": "#333333",
            "bg_color": "#F5F5F5",
        },
        {
            "id": "footer_1",
            "text": "confidential - do not share",
            "x": 50,
            "y": 500,
            "width": 800,
            "height": 30,
            "font_size": 10,
            "font_color": "#999999",
            "bg_color": None,
        },
    ],
}


def call_claude(user_prompt, use_fallback=True):
    """
    Make a Claude call with:
    - Prompt caching (system prompt cached via cache_control)
    - Fallback model (if primary fails, try fallback)
    """
    # FIX: Prompt caching — tell Claude to cache the system prompt
    # First call pays full cost, subsequent calls reuse the cached prompt
    system_with_cache = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    try:
        # Try primary model first
        response = client.messages.create(
            model=PRIMARY_MODEL,
            max_tokens=1024,
            system=system_with_cache,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    except Exception as e:
        if not use_fallback:
            raise

        # FIX: Fallback model — if Sonnet fails, try Haiku
        print(f"  Primary model failed ({e}), falling back to Haiku...")
        response = client.messages.create(
            model=FALLBACK_MODEL,
            max_tokens=1024,
            system=system_with_cache,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text


def analyze_slide(slide_json):
    """Step 1: Analyze the slide layout and content."""
    prompt = f"""Analyze this slide and return a JSON summary with:
- "shape_count": number of shapes
- "has_title": true/false
- "has_body": true/false
- "text_issues": list of issues (typos, informal language, etc.)
- "layout_type": "title-body", "title-only", "blank", etc.

Slide:
{json.dumps(slide_json, indent=2)}"""

    return call_claude(prompt)


def transform_slide(slide_json):
    """Step 2: Transform the slide text to be professional."""
    prompt = f"""Rewrite all text in this slide to be professional and polished.
Fix typos, grammar, and informal language.
Return the full slide JSON with updated text fields only.
Keep all other properties (x, y, width, height, colors) exactly the same.

Slide:
{json.dumps(slide_json, indent=2)}"""

    return call_claude(prompt)


def validate_output(original_json, transformed_json):
    """Step 3: Validate the transformation."""
    prompt = f"""Compare the original and transformed slide.
Check that:
1. All shape IDs are preserved
2. No text was deleted (only rewritten)
3. Layout properties (x, y, width, height) are unchanged

Return JSON with:
- "valid": true/false
- "issues": list of any problems found

Original:
{json.dumps(original_json, indent=2)}

Transformed:
{transformed_json}"""

    return call_claude(prompt)


def run(slide=None):
    """Run the full pipeline with PARALLEL calls where possible."""
    if slide is None:
        slide = SAMPLE_SLIDE

    start = time.time()

    # FIX: Steps 1 and 2 run in PARALLEL (they don't depend on each other)
    # Before: Analyze(2s) → Transform(2s) → Validate(2s) = 6s
    # After:  Analyze(2s) + Transform(2s) in parallel → Validate(1s) = 3s
    print("Steps 1+2: Analyzing and transforming in parallel...")
    t1 = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        analyze_future = executor.submit(analyze_slide, slide)
        transform_future = executor.submit(transform_slide, slide)

        analysis = analyze_future.result()
        transformed = transform_future.result()

    print(f"  Done in {time.time() - t1:.1f}s")

    # Step 3: Validate (needs transform output, so must run after)
    print("Step 3: Validating output...")
    t3 = time.time()
    validation = validate_output(slide, transformed)
    print(f"  Done in {time.time() - t3:.1f}s")

    total = time.time() - start
    print(f"\nTotal latency: {total:.1f}s")

    return {
        "analysis": analysis,
        "transformed": transformed,
        "validation": validation,
        "latency_ms": int(total * 1000),
    }


if __name__ == "__main__":
    result = run()
    print(f"\nLatency: {result['latency_ms']}ms")
