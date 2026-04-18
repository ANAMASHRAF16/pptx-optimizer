"""
Benchmark: Compare broken vs fixed agent latency.

Usage:
    python src/benchmark.py
"""

import time
from agent_broken import run as run_broken
from agent_fixed import run as run_fixed


def benchmark():
    print("=" * 50)
    print("BENCHMARK: Broken vs Fixed Agent")
    print("=" * 50)

    # Run broken version
    print("\n--- BROKEN (sequential, no cache, no fallback) ---\n")
    broken_result = run_broken()
    broken_ms = broken_result["latency_ms"]

    print("\n--- FIXED (parallel, cached, fallback) ---\n")
    fixed_result = run_fixed()
    fixed_ms = fixed_result["latency_ms"]

    # Summary
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Broken:  {broken_ms}ms")
    print(f"Fixed:   {fixed_ms}ms")
    print(f"Speedup: {broken_ms / fixed_ms:.1f}x faster")
    print(f"Target:  {'PASS' if fixed_ms < 3000 else 'FAIL'} (< 3000ms)")


if __name__ == "__main__":
    benchmark()
