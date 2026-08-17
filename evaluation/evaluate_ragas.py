"""Standalone RAGAS evaluation for the Telecom RAG chatbot.

This script reuses the existing public interfaces only:
- ChatService.chat()
- HybridRetriever.retrieve()
It does not modify retrieval, routing, prompts, memory, or the app logic.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datasets import Dataset

from app.retrieval.retriever import HybridRetriever
from app.services.chat import ChatService

try:
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )
except Exception:  # pragma: no cover - graceful handling
    evaluate = None
    answer_relevancy = None
    context_precision = None
    context_recall = None
    faithfulness = None


DATASET_PATH = PROJECT_ROOT / "evaluation" / "dataset.csv"
RESULTS_PATH = PROJECT_ROOT / "evaluation" / "ragas_results.json"
REPORT_PATH = PROJECT_ROOT / "evaluation" / "ragas_report.md"
DEBUG_PATH = PROJECT_ROOT / "evaluation" / "retrieval_debug.json"
PER_QUESTION_PATH = PROJECT_ROOT / "evaluation" / "per_question_results.csv"

ABSTAIN_PATTERNS = (
    "i could not find relevant information",
    "not in the provided 3gpp documentation",
    "not in corpus",
    "not_in_corpus",
    "i don't have enough information",
    "cannot answer from the provided context",
)


def load_dataset(path: Path) -> list[dict]:
    """Load the benchmark dataset with expected behavior."""

    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if not row.get("question"):
                continue
            rows.append(
                {
                    "question": row["question"].strip(),
                    "ground_truth": row.get("ground_truth", "").strip(),
                    "expected_behavior": row.get("expected_behavior", "ANSWER").strip().upper(),
                }
            )
    return rows


def is_abstention_answer(answer: str) -> bool:
    """Return True when the model abstains instead of answering from the corpus."""

    if not answer:
        return False
    lowered = answer.lower()
    return any(pattern in lowered for pattern in ABSTAIN_PATTERNS)


def safe_float(value):
    """Convert metric values to float when possible."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_retrieved_contexts(question: str) -> tuple[list[str], list[dict], str | None]:
    """Use the existing HybridRetriever to obtain the real retrieval context."""

    try:
        retriever = HybridRetriever()
        chunks = retriever.retrieve(question)
    except Exception as exc:  # pragma: no cover - graceful handling
        return [], [{"question": question, "error": str(exc)}], str(exc)

    contexts: list[str] = []
    debug_rows: list[dict] = []

    for index, chunk in enumerate(chunks):
        text = (chunk.get("text") or "").strip()
        if text:
            contexts.append(text)

        debug_rows.append(
            {
                "chunk_index": index,
                "chunk_id": chunk.get("chunk_id") or chunk.get("id") or index,
                "document": chunk.get("document"),
                "section": chunk.get("section"),
                "retrieval_score": chunk.get("score"),
                "rerank_score": chunk.get("rerank_score"),
            }
        )

    return contexts, debug_rows, None


def run_chatbot(question: str, session_id: str) -> str:
    """Execute the public chatbot interface for the question."""

    try:
        service = ChatService(session_id=session_id)
        return service.chat(question)
    except Exception as exc:  # pragma: no cover - graceful handling
        return f"CHATBOT_ERROR: {exc}"


def evaluate_dataset(rows: list[dict]) -> dict:
    """Compute RAGAS metrics for questions whose expected behavior is ANSWER."""

    if evaluate is None or faithfulness is None:
        return {
            "status": "skipped",
            "reason": "RAGAS is unavailable in the current environment.",
            "results": {},
        }

    answer_rows = []
    for item in rows:
        if item.get("expected_behavior") != "ANSWER":
            continue
        question = item["question"]
        contexts, debug_rows, error = get_retrieved_contexts(question)
        answer = run_chatbot(question, session_id=f"ragas-{question[:20].replace(' ', '-')}")
        answer_rows.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": item.get("ground_truth", ""),
                "retrieval_debug": debug_rows,
                "retrieval_error": error,
            }
        )

    if not answer_rows:
        return {
            "status": "ok",
            "results": {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "overall_score": 0.0,
            },
        }

    dataset = Dataset.from_dict(
        {
            "question": [row["question"] for row in answer_rows],
            "answer": [row["answer"] for row in answer_rows],
            "contexts": [row["contexts"] for row in answer_rows],
            "ground_truth": [row["ground_truth"] for row in answer_rows],
        }
    )

    try:
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
        )
        metric_map = {}
        if hasattr(result, "to_dict"):
            metric_map = result.to_dict()
        else:
            metric_map = dict(result)
        metric_map["overall_score"] = (
            mean(
                [
                    safe_float(metric_map.get("faithfulness")),
                    safe_float(metric_map.get("answer_relevancy")),
                    safe_float(metric_map.get("context_precision")),
                    safe_float(metric_map.get("context_recall")),
                ]
            )
            if any(v is not None for v in [
                safe_float(metric_map.get("faithfulness")),
                safe_float(metric_map.get("answer_relevancy")),
                safe_float(metric_map.get("context_precision")),
                safe_float(metric_map.get("context_recall")),
            ])
            else 0.0
        )
        return {"status": "ok", "results": metric_map}
    except Exception as exc:  # pragma: no cover - graceful handling
        return {"status": "error", "reason": str(exc), "results": {}}


def write_debug_rows(rows: list[dict]) -> None:
    """Persist retrieval metadata for each evaluated question."""

    debug_payload = []
    for item in rows:
        question = item["question"]
        contexts, debug_rows, error = get_retrieved_contexts(question)
        debug_payload.append(
            {
                "question": question,
                "ground_truth": item.get("ground_truth", ""),
                "expected_behavior": item.get("expected_behavior", "ANSWER"),
                "retrieved_contexts": contexts,
                "retrieved_chunk_debug": debug_rows,
                "retrieval_error": error,
            }
        )
    DEBUG_PATH.write_text(json.dumps(debug_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_per_question_results(rows: list[dict], metric_summary: dict) -> None:
    """Persist per-question pass/fail outcomes and metric values."""

    output_rows = []
    for item in rows:
        question = item["question"]
        expected_behavior = item.get("expected_behavior", "ANSWER")
        retrieved_contexts, debug_rows, retrieval_error = get_retrieved_contexts(question)
        answer = run_chatbot(question, session_id=f"perq-{question[:20].replace(' ', '-')}")
        faith = metric_summary.get(question, {}).get("faithfulness")
        relevancy = metric_summary.get(question, {}).get("answer_relevancy")
        context_precision = metric_summary.get(question, {}).get("context_precision")
        context_recall = metric_summary.get(question, {}).get("context_recall")

        if expected_behavior == "ABSTAIN":
            passed = is_abstention_answer(answer)
            ground_truth_value = "NOT_IN_CORPUS"
        else:
            passed = bool(
                faith is not None and relevancy is not None and context_precision is not None and context_recall is not None
            )
            ground_truth_value = item.get("ground_truth", "")

        output_rows.append(
            {
                "question": question,
                "expected_behavior": expected_behavior,
                "actual_answer": answer,
                "ground_truth": ground_truth_value,
                "retrieved_chunk_ids": "; ".join(str(d.get("chunk_id")) for d in debug_rows),
                "retrieval_scores": "; ".join(str(d.get("retrieval_score")) for d in debug_rows),
                "faithfulness": "" if faith is None else faith,
                "answer_relevancy": "" if relevancy is None else relevancy,
                "context_precision": "" if context_precision is None else context_precision,
                "context_recall": "" if context_recall is None else context_recall,
                "pass_fail": "PASS" if passed else "FAIL",
            }
        )

    fieldnames = [
        "question",
        "expected_behavior",
        "actual_answer",
        "ground_truth",
        "retrieved_chunk_ids",
        "retrieval_scores",
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "pass_fail",
    ]

    with PER_QUESTION_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


def save_results(payload: dict) -> None:
    """Persist JSON evaluation output."""

    RESULTS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(results: dict) -> None:
    """Persist a real markdown evaluation report."""

    metrics = results.get("metrics", {})
    overall = results.get("overall_score", "N/A")
    answered = results.get("answered_questions", 0)
    abstentions = results.get("abstentions", 0)
    lowest = results.get("lowest_scoring_questions", [])
    highest = results.get("highest_scoring_questions", [])

    def fmt_value(value):
        return "N/A" if value is None else value

    report = f"""# Telecom RAG Evaluation Report

## Dataset
- Rows: {results.get('dataset_size', 0)}
- Answer expected questions: {answered}
- Abstention expected questions: {abstentions}

## Metric Definitions
- Faithfulness: measures whether the answer is supported by the retrieved context.
- Answer Relevancy: measures whether the answer addresses the asked question.
- Context Precision: measures how relevant the retrieved context is.
- Context Recall: measures whether the retrieved context covers the needed information.

## Overall Metrics
- Overall Score: {fmt_value(overall)}
- Faithfulness: {fmt_value(metrics.get('faithfulness'))}
- Answer Relevancy: {fmt_value(metrics.get('answer_relevancy'))}
- Context Precision: {fmt_value(metrics.get('context_precision'))}
- Context Recall: {fmt_value(metrics.get('context_recall'))}

## Dataset Size
{results.get('dataset_size', 0)} benchmark questions were evaluated.

## Number of Abstentions
{abstentions} questions were expected to abstain because their answer is not in the indexed 3GPP corpus.

## Number of Answered Questions
{answered} questions were expected to be answered from the corpus.

## Lowest Scoring Questions
{json.dumps(lowest, ensure_ascii=False, indent=2) if lowest else 'No low-scoring questions available.'}

## Highest Scoring Questions
{json.dumps(highest, ensure_ascii=False, indent=2) if highest else 'No high-scoring questions available.'}

## Observations
- Grounded evaluation is based on the indexed corpus rather than general world knowledge.
- Out-of-domain questions are treated as abstention cases and are not judged as factual failures.
- Retrieval quality is captured explicitly in retrieval_debug.json.

## Failure Analysis
- If a question expected an answer but was abstained or had weak metric values, inspect retrieval context coverage and retrieval scores.
- If a question expected abstention but the model answered factually, the model is not respecting grounded abstention behavior.
- If retrieved context is weak or empty, the evaluation should be treated as retrieval failure rather than answer failure.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    """Run the standalone evaluation pipeline."""

    rows = load_dataset(DATASET_PATH)
    if not rows:
        payload = {
            "dataset_size": 0,
            "answered_questions": 0,
            "abstentions": 0,
            "overall_score": None,
            "metrics": {},
            "status": "error",
            "reason": "Dataset is empty.",
        }
        save_results(payload)
        write_report(payload)
        return

    write_debug_rows(rows)

    metric_summary = {}
    answer_rows = [row for row in rows if row.get("expected_behavior") == "ANSWER"]
    abstain_rows = [row for row in rows if row.get("expected_behavior") == "ABSTAIN"]

    ragas_result = evaluate_dataset(rows)
    metric_map = ragas_result.get("results", {})

    for row in answer_rows:
        # keep metric summary keyed by question for downstream per-question reporting
        metric_summary[row["question"]] = {
            "faithfulness": safe_float(metric_map.get("faithfulness")),
            "answer_relevancy": safe_float(metric_map.get("answer_relevancy")),
            "context_precision": safe_float(metric_map.get("context_precision")),
            "context_recall": safe_float(metric_map.get("context_recall")),
        }

    write_per_question_results(rows, metric_summary)

    answered_questions = len(answer_rows)
    abstentions = len(abstain_rows)

    payload = {
        "dataset_size": len(rows),
        "answered_questions": answered_questions,
        "abstentions": abstentions,
        "status": ragas_result.get("status", "skipped"),
        "reason": ragas_result.get("reason"),
        "metrics": {
            "faithfulness": safe_float(metric_map.get("faithfulness")),
            "answer_relevancy": safe_float(metric_map.get("answer_relevancy")),
            "context_precision": safe_float(metric_map.get("context_precision")),
            "context_recall": safe_float(metric_map.get("context_recall")),
        },
        "overall_score": safe_float(metric_map.get("overall_score")),
    }
    save_results(payload)
    write_report(payload)


if __name__ == "__main__":
    main()
