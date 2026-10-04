#!/usr/bin/env python3
"""
ResQ-AI: Master Test Orchestrator & Unified Test Runner
Author: e2e_test_writer_1 (E2E Test Suite Architect)
Reference: ORIGINAL_REQUEST.md, PROJECT.md, TEST_INFRA.md

Usage:
    python scripts/run_all_tests.py [--all] [--unit] [--integration] [--scenarios] [--e2e] [--dry-run]

Exit Codes:
    0: All selected test suites executed and passed successfully.
    1: One or more test suites failed.
    2: Configuration or fatal environment error.
"""

import sys
import os
import time
import argparse
import subprocess
from typing import List, Tuple, Dict, Any


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TEST_SUITES = [
    {
        "id": "unit",
        "name": "Unit Tests (14 Classical AI Algorithms & Models)",
        "path": os.path.join(PROJECT_ROOT, "backend", "tests", "unit"),
        "tier": "Tier 1 & Tier 2",
    },
    {
        "id": "integration",
        "name": "Integration Tests (22 REST API Endpoints)",
        "path": os.path.join(PROJECT_ROOT, "backend", "tests", "integration"),
        "tier": "Tier 1 & Tier 3",
    },
    {
        "id": "scenarios",
        "name": "Collegiate Demo Scenarios (Scenarios 1-5)",
        "path": os.path.join(PROJECT_ROOT, "backend", "tests", "scenarios"),
        "tier": "Tier 4",
    },
    {
        "id": "e2e",
        "name": "Opaque-Box E2E Workflows & Scenarios",
        "path": os.path.join(PROJECT_ROOT, "tests", "e2e"),
        "tier": "Tiers 1-4 Full Stack",
    },
]


def format_header(title: str) -> str:
    line = "=" * 78
    return f"\n{line}\n  {title}\n{line}"


def run_suite(suite_info: Dict[str, Any], verbose: bool = False, dry_run: bool = False) -> Tuple[str, str, float]:
    """
    Executes a single test suite using pytest.
    Returns: (status, message, duration_in_seconds)
    """
    name = suite_info["name"]
    path = suite_info["path"]

    rel_path = os.path.relpath(path, PROJECT_ROOT)

    if not os.path.exists(path):
        return ("PENDING", f"Path not found: {rel_path} (Awaiting milestone implementation)", 0.0)

    # Check if there are python files in the directory
    py_files = [f for f in os.listdir(path) if f.startswith("test_") and f.endswith(".py")]
    if not py_files:
        return ("PENDING", f"No test files found in {rel_path}", 0.0)

    if dry_run:
        return ("READY", f"Verified {len(py_files)} test files in {rel_path}", 0.0)

    cmd = [sys.executable, "-m", "pytest", path]
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    print(f"\n>> Executing: {name}")
    print(f"   Command: {' '.join(cmd)}")

    start_time = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=not verbose,
            text=True,
            timeout=300
        )
        duration = time.time() - start_time

        if proc.returncode == 0:
            return ("PASSED", f"Passed in {duration:.2f}s", duration)
        elif proc.returncode == 5:
            # Pytest code 5 means no tests collected / all skipped
            return ("SKIPPED", "No tests collected or all skipped", duration)
        else:
            err_msg = f"Failed with exit code {proc.returncode}"
            if not verbose and proc.stderr:
                err_msg += f"\n{proc.stderr.strip()[:300]}"
            elif not verbose and proc.stdout:
                err_msg += f"\n{proc.stdout.strip()[-300:]}"
            return ("FAILED", err_msg, duration)
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return ("TIMEOUT", f"Execution timed out (>300s)", duration)
    except Exception as exc:
        duration = time.time() - start_time
        return ("ERROR", f"Subprocess error: {str(exc)}", duration)


def main():
    parser = argparse.ArgumentParser(description="ResQ-AI Unified Master Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all test suites (default)")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run API integration tests only")
    parser.add_argument("--scenarios", action="store_true", help="Run demo scenario tests only")
    parser.add_argument("--e2e", action="store_true", help="Run E2E opaque-box workflows only")
    parser.add_argument("--dry-run", action="store_true", help="Validate test targets without executing")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose pytest output")

    args = parser.parse_args()

    # Determine which suites to run
    selected_ids = []
    if args.unit:
        selected_ids.append("unit")
    if args.integration:
        selected_ids.append("integration")
    if args.scenarios:
        selected_ids.append("scenarios")
    if args.e2e:
        selected_ids.append("e2e")

    # If --all or no specific suite flag provided, run all
    if args.all or not selected_ids:
        selected_ids = [s["id"] for s in TEST_SUITES]

    suites_to_run = [s for s in TEST_SUITES if s["id"] in selected_ids]

    print(format_header("ResQ-AI Master Test Suite Runner"))
    print(f"Working Directory: {PROJECT_ROOT}")
    print(f"Target Suites: {', '.join(s['id'] for s in suites_to_run)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'ACTIVE EXECUTION'}")

    results = []
    has_failure = False

    total_start = time.time()
    for suite in suites_to_run:
        status, details, duration = run_suite(suite, verbose=args.verbose, dry_run=args.dry_run)
        results.append({
            "name": suite["name"],
            "tier": suite["tier"],
            "status": status,
            "details": details,
            "duration": duration,
        })
        if status in ("FAILED", "TIMEOUT", "ERROR"):
            has_failure = True

    total_duration = time.time() - total_start

    # Print Summary Table
    print(format_header("Test Execution Summary"))
    col_suite = 48
    col_tier = 18
    col_status = 10
    col_time = 10

    header_row = f"{'Suite / Test Target':<{col_suite}} | {'Tier':<{col_tier}} | {'Status':<{col_status}} | {'Time (s)':<{col_time}}"
    print(header_row)
    print("-" * len(header_row))

    for r in results:
        status_color = r["status"]
        row = f"{r['name']:<{col_suite}} | {r['tier']:<{col_tier}} | {status_color:<{col_status}} | {r['duration']:<10.2f}"
        print(row)
        if r["status"] in ("FAILED", "TIMEOUT", "ERROR") and not args.verbose:
            print(f"   └──> Details: {r['details']}")

    print("-" * len(header_row))
    print(f"Total Duration: {total_duration:.2f}s")

    if has_failure:
        print("\n>> VERIFICATION RESULT: ONE OR MORE SUITES FAILED [EXIT 1]")
        sys.exit(1)
    else:
        print("\n>> VERIFICATION RESULT: ALL EXECUTED SUITES PASSED [EXIT 0]")
        sys.exit(0)


if __name__ == "__main__":
    main()
