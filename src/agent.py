"""
PPTX Editing Agent — Baseline version (slow, sequential).

Takes a slide JSON, runs 3 steps through Claude:
1. Analyze — identify layout, find text issues
2. Transform — rewrite text to be professional
3. Validate — check nothing was broken

Problems:
- All 3 calls run sequentially (~6-8s total)
- No prompt caching (system prompt sent fresh every call)
- No fallback model (if Sonnet fails, everything fails)
"""

import json
import time
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"

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
            "x": 50, "y": 30, "width": 800, "height": 60,
            "font_size": 28, "font_color": "#000000", "bg_color": None,
        },
        {
            "id": "subtitle_1",
            "text": "we made alot of $$ this quarter, heres the numbers",
            "x": 50, "y": 100, "width": 800, "height": 40,
            "font_size": 18, "font_color": "#666666", "bg_color": None,
        },
        {
            "id": "body_1",
            "text": "Revenue: $4.2M (up 23%)\nNew customers: 340\nChurn: down to 2.1%\nTop region: North America",
            "x": 50, "y": 160, "width": 400, "height": 300,
            "font_size": 14, "font_color": "#333333", "bg_color": "#F5F5F5",
        },
        {
            "id": "footer_1",
            "text": "confidential - do not share",
            "x": 50, "y": 500, "width": 800, "height": 30,
            "font_size": 10, "font_color": "#999999", "bg_color": None,
        },
    ],
}


def call_claude(user_prompt):
    """Make a single Claude call. No caching, no fallback."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
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
    """Run the full pipeline SEQUENTIALLY."""
    if slide is None:
        slide = SAMPLE_SLIDE

    start = time.time()

    # Step 1: Analyze (blocks until done)
    print("Step 1: Analyzing slide...")
    t1 = time.time()
    analysis = analyze_slide(slide)
    print(f"  Done in {time.time() - t1:.1f}s")

    # Step 2: Transform (waits for Step 1, even though it doesn't need its output)
    print("Step 2: Transforming slide...")
    t2 = time.time()
    transformed = transform_slide(slide)
    print(f"  Done in {time.time() - t2:.1f}s")

    # Step 3: Validate (needs Step 2's output)
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
