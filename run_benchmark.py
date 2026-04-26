"""
DEVAN End-to-End Benchmark
==========================

Indexes a folder of documents and evaluates Q&A quality against a JSONL
file of question / expected-answer pairs, then writes a structured results
JSON for analysis or paper reporting.

Usage
-----
    # Index docs/sample/ and run against benchmark_sample.jsonl
    python run_benchmark.py --folder docs/sample --questions benchmark_sample.jsonl

    # Custom output and DB path
    python run_benchmark.py \\
        --folder /path/to/corpus \\
        --questions my_questions.jsonl \\
        --out results/run1.json \\
        --db /tmp/bench.db

JSONL format (one JSON object per line)
----------------------------------------
    {"question": "What is the revenue for Q2?", "expected_answer": "12.4M"}
    {"question": "Who authored this report?",   "expected_answer": ""}

Metrics reported
----------------
    citation_present   – fraction of answers with ≥1 citation
    has_answer         – fraction of non-empty answers
    avg_latency_ms     – mean query latency in milliseconds
    avg_chunks_used    – mean chunks retrieved per query
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Allow running from the project root without installing as a package
sys.path.insert(0, str(Path(__file__).parent))

from systems.devan.adapter import DevanAdapter


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score(result, expected: str) -> dict:
    return {
        "citation_present": len(result.citations) > 0,
        "has_answer": bool(result.answer.strip()),
        "answer_length": len(result.answer),
        "chunks_used": result.chunks_used,
        "latency_ms": result.latency_ms,
    }


# ---------------------------------------------------------------------------
# Main benchmark coroutine
# ---------------------------------------------------------------------------

async def run(
    folder: str,
    questions_file: str,
    out_file: str,
    db_path: str,
    top_k: int,
    no_synthesis: bool,
) -> dict:
    print(f"\n{'='*60}")
    print(f"  DEVAN Benchmark")
    print(f"{'='*60}")
    print(f"  Corpus : {folder}")
    print(f"  Q file : {questions_file}")
    print(f"  DB     : {db_path}")
    print(f"  Top-K  : {top_k}")
    print(f"{'='*60}\n")

    adapter = DevanAdapter(db_path=db_path)

    # ── Indexing phase ──────────────────────────────────────────────────────
    print("Phase 1 — Indexing")
    files_seen: list[str] = []

    async def _progress(name: str, done: int, total: int):
        files_seen.append(name)
        bar_len = 30
        filled = int(bar_len * done / max(total, 1))
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\r  [{bar}] {done}/{total}  {name[:40]:<40}", end="", flush=True)

    t_index = time.perf_counter()
    index_result = await adapter.index_folder(folder, progress_cb=_progress)
    index_ms = (time.perf_counter() - t_index) * 1000
    print()  # newline after progress bar

    print(f"\n  ✓ {index_result.files_indexed} files | {index_result.total_chunks} chunks | {index_ms:.0f} ms")
    if index_result.errors:
        print(f"  ⚠ {len(index_result.errors)} file(s) failed:")
        for e in index_result.errors:
            print(f"      {e}")

    if index_result.total_chunks == 0:
        print("\n  ERROR: Nothing was indexed. Check the folder path and server setup.")
        sys.exit(1)

    # ── Query phase ─────────────────────────────────────────────────────────
    questions: list[dict] = []
    q_path = Path(questions_file)
    if not q_path.exists():
        print(f"\n  ERROR: Questions file not found: {questions_file}")
        sys.exit(1)

    with open(q_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    if not questions:
        print("\n  ERROR: No questions found in JSONL file.")
        sys.exit(1)

    print(f"\nPhase 2 — Querying ({len(questions)} questions, top_k={top_k})")
    results: list[dict] = []

    for i, q in enumerate(questions):
        question = q.get("question", "").strip()
        expected = q.get("expected_answer", "")
        if not question:
            continue

        qr = await adapter.query(
            question,
            index_result.session_id,
            top_k=top_k,
            synthesize=not no_synthesis,
        )
        scores = _score(qr, expected)

        entry = {
            "question_id": i + 1,
            "question": question,
            "expected": expected,
            "answer": qr.answer,
            "citations": [
                {"file": c.file_name, "ref": c.source_ref, "excerpt": c.excerpt[:200]}
                for c in qr.citations
            ],
            **scores,
        }
        results.append(entry)

        cite_flag = "✓" if scores["citation_present"] else "✗"
        ans_flag  = "✓" if scores["has_answer"]       else "✗"
        print(
            f"  [{i+1:>2}/{len(questions)}] "
            f"cited={cite_flag}  ans={ans_flag}  "
            f"chunks={scores['chunks_used']}  "
            f"lat={scores['latency_ms']:.0f}ms  "
            f"{question[:55]}"
        )

    # ── Aggregate metrics ───────────────────────────────────────────────────
    n = len(results)
    if n == 0:
        print("\n  No results to aggregate.")
        sys.exit(1)

    metrics = {
        "citation_present":  round(sum(r["citation_present"] for r in results) / n, 4),
        "has_answer":        round(sum(r["has_answer"]       for r in results) / n, 4),
        "avg_latency_ms":    round(sum(r["latency_ms"]       for r in results) / n, 1),
        "avg_chunks_used":   round(sum(r["chunks_used"]      for r in results) / n, 2),
        "avg_answer_length": round(sum(r["answer_length"]    for r in results) / n, 1),
    }

    summary = {
        "benchmark_config": {
            "folder":          folder,
            "questions_file":  questions_file,
            "questions_count": n,
            "top_k":           top_k,
            "synthesis":       not no_synthesis,
        },
        "index": {
            "session_id":   index_result.session_id,
            "files_indexed": index_result.files_indexed,
            "total_chunks":  index_result.total_chunks,
            "index_time_ms": round(index_ms),
            "errors":        index_result.errors,
        },
        "metrics": metrics,
        "results": results,
    }

    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  Results saved → {out_file}")
    print(f"{'='*60}")
    print(f"  citation_present : {metrics['citation_present']:.1%}")
    print(f"  has_answer       : {metrics['has_answer']:.1%}")
    print(f"  avg_latency_ms   : {metrics['avg_latency_ms']:.0f} ms")
    print(f"  avg_chunks_used  : {metrics['avg_chunks_used']:.1f}")
    print(f"{'='*60}\n")

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="DEVAN end-to-end RAG benchmark",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--folder",    required=True,  help="Folder of documents to index")
    parser.add_argument("--questions", default="benchmark_sample.jsonl",
                        help="JSONL file with {question, expected_answer} objects")
    parser.add_argument("--out",       default="benchmark_results.json",
                        help="Output JSON results file")
    parser.add_argument("--db",        default="benchmark_indexer.db",
                        help="SQLite database path for the benchmark run")
    parser.add_argument("--top-k",     type=int, default=8,
                        help="Chunks retrieved per query")
    parser.add_argument("--no-synthesis", action="store_true",
                        help="Skip Claude synthesis; return raw excerpts only")
    args = parser.parse_args()

    asyncio.run(run(
        folder=args.folder,
        questions_file=args.questions,
        out_file=args.out,
        db_path=args.db,
        top_k=args.top_k,
        no_synthesis=args.no_synthesis,
    ))


if __name__ == "__main__":
    main()
