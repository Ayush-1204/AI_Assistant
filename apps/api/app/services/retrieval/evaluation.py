from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Awaitable
from typing import Callable

from app.services.retrieval.ranking import RetrievedChunk
from app.services.retrieval.ranking import document_title
from app.services.retrieval.ranking import find_expected_rank


RankedChunks = list[RetrievedChunk]


@dataclass(slots=True)
class RetrievalEvaluationExample:
    query: str
    expected_document: str
    expected_chunk: int | None = None


@dataclass(slots=True)
class RetrievalEvaluationRow:
    rank: int
    document_id: int
    document_title: str
    chunk_index: int
    token_count: int
    distance: float
    content: str


@dataclass(slots=True)
class RetrievalEvaluationCase:
    query: str
    expected_document: str
    expected_chunk: int | None
    top1_correct: bool
    top3_correct: bool
    top5_correct: bool
    first_hit_distance: float | None
    expected_hit_distance: float | None
    returned_document: str | None
    returned_chunk: int | None
    ranking_position: int | None
    latency_ms: float
    rows: list[RetrievalEvaluationRow]


@dataclass(slots=True)
class RetrievalEvaluationSummary:
    queries_evaluated: int
    average_top1_accuracy: float
    average_top3_accuracy: float
    average_top5_accuracy: float
    average_retrieval_distance: float
    average_expected_distance: float | None
    average_retrieval_latency_ms: float


@dataclass(slots=True)
class RetrievalEvaluationConfig:
    top_k: int
    threshold: float
    chunk_size: int | None = None
    overlap: int | None = None


@dataclass(slots=True)
class RetrievalEvaluationReport:
    config: RetrievalEvaluationConfig
    summary: RetrievalEvaluationSummary
    cases: list[RetrievalEvaluationCase]


@dataclass(slots=True)
class RetrievalEvaluationRun:
    config: RetrievalEvaluationConfig
    report: RetrievalEvaluationReport


FetchRankedChunks = Callable[
    [str, int], Awaitable[RankedChunks]
]


def load_dataset(dataset_path: str | Path) -> list[RetrievalEvaluationExample]:
    path = Path(dataset_path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    examples: list[RetrievalEvaluationExample] = []

    for item in raw:
        examples.append(
            RetrievalEvaluationExample(
                query=item["query"],
                expected_document=item["expected_document"],
                expected_chunk=item.get("expected_chunk"),
            )
        )

    return examples


def _rows_for_display(
    results: RankedChunks,
    *,
    limit: int,
) -> list[RetrievalEvaluationRow]:
    rows: list[RetrievalEvaluationRow] = []

    for rank, result in enumerate(results[:limit], start=1):
        rows.append(
            RetrievalEvaluationRow(
                rank=rank,
                document_id=result.document_id,
                document_title=result.document_title,
                chunk_index=result.chunk_index,
                token_count=result.token_count,
                distance=float(result.distance),
                content=result.content,
            )
        )

    return rows


def evaluate_case(
    example: RetrievalEvaluationExample,
    results: RankedChunks,
    *,
    top_k: int,
    threshold: float,
    latency_ms: float,
) -> RetrievalEvaluationCase:
    filtered_results = [
        result
        for result in results[:top_k]
        if result.distance <= threshold
    ]

    ranking_position = find_expected_rank(
        filtered_results,
        example.expected_document,
        example.expected_chunk,
    )

    first_hit_distance = (
        filtered_results[0].distance
        if filtered_results
        else None
    )

    expected_hit_distance = (
        filtered_results[ranking_position - 1].distance
        if ranking_position is not None
        else None
    )

    returned_document = (
        filtered_results[0].document_title
        if filtered_results
        else None
    )

    returned_chunk = (
        filtered_results[0].chunk_index
        if filtered_results
        else None
    )

    return RetrievalEvaluationCase(
        query=example.query,
        expected_document=example.expected_document,
        expected_chunk=example.expected_chunk,
        top1_correct=ranking_position == 1,
        top3_correct=ranking_position is not None and ranking_position <= 3,
        top5_correct=ranking_position is not None and ranking_position <= 5,
        first_hit_distance=first_hit_distance,
        expected_hit_distance=expected_hit_distance,
        returned_document=returned_document,
        returned_chunk=returned_chunk,
        ranking_position=ranking_position,
        latency_ms=latency_ms,
        rows=_rows_for_display(
            results,
            limit=top_k,
        ),
    )


def summarize_cases(
    cases: list[RetrievalEvaluationCase],
) -> RetrievalEvaluationSummary:
    if not cases:
        return RetrievalEvaluationSummary(
            queries_evaluated=0,
            average_top1_accuracy=0.0,
            average_top3_accuracy=0.0,
            average_top5_accuracy=0.0,
            average_retrieval_distance=0.0,
            average_expected_distance=None,
            average_retrieval_latency_ms=0.0,
        )

    average_expected_distance_values = [
        case.expected_hit_distance
        for case in cases
        if case.expected_hit_distance is not None
    ]

    return RetrievalEvaluationSummary(
        queries_evaluated=len(cases),
        average_top1_accuracy=sum(
            1.0 if case.top1_correct else 0.0 for case in cases
        ) / len(cases),
        average_top3_accuracy=sum(
            1.0 if case.top3_correct else 0.0 for case in cases
        ) / len(cases),
        average_top5_accuracy=sum(
            1.0 if case.top5_correct else 0.0 for case in cases
        ) / len(cases),
        average_retrieval_distance=sum(
            case.first_hit_distance or 0.0 for case in cases
        ) / len(cases),
        average_expected_distance=(
            sum(average_expected_distance_values) / len(average_expected_distance_values)
            if average_expected_distance_values
            else None
        ),
        average_retrieval_latency_ms=sum(
            case.latency_ms for case in cases
        ) / len(cases),
    )


async def evaluate_dataset(
    dataset: list[RetrievalEvaluationExample],
    fetch_ranked_chunks: FetchRankedChunks,
    *,
    top_k: int,
    threshold: float,
) -> RetrievalEvaluationReport:
    cases: list[RetrievalEvaluationCase] = []

    for example in dataset:
        started_at = perf_counter()
        results = await fetch_ranked_chunks(
            example.query,
            top_k,
        )
        latency_ms = (perf_counter() - started_at) * 1000.0

        cases.append(
            evaluate_case(
                example,
                results,
                top_k=top_k,
                threshold=threshold,
                latency_ms=latency_ms,
            )
        )

    return RetrievalEvaluationReport(
        config=RetrievalEvaluationConfig(
            top_k=top_k,
            threshold=threshold,
        ),
        summary=summarize_cases(cases),
        cases=cases,
    )


async def evaluate_grid(
    dataset: list[RetrievalEvaluationExample],
    fetch_ranked_chunks: FetchRankedChunks,
    configs: list[RetrievalEvaluationConfig],
) -> list[RetrievalEvaluationRun]:
    if not configs:
        return []

    max_top_k = max(config.top_k for config in configs)
    raw_results_cache: dict[str, RankedChunks] = {}
    latency_cache: dict[str, float] = {}

    for example in dataset:
        started_at = perf_counter()
        raw_results_cache[example.query] = await fetch_ranked_chunks(
            example.query,
            max_top_k,
        )
        latency_cache[example.query] = (
            perf_counter() - started_at
        ) * 1000.0

    runs: list[RetrievalEvaluationRun] = []

    for config in configs:
        cases: list[RetrievalEvaluationCase] = []

        for example in dataset:
            cases.append(
                evaluate_case(
                    example,
                    raw_results_cache[example.query],
                    top_k=config.top_k,
                    threshold=config.threshold,
                    latency_ms=latency_cache[example.query],
                )
            )

        report = RetrievalEvaluationReport(
            config=config,
            summary=summarize_cases(cases),
            cases=cases,
        )
        runs.append(
            RetrievalEvaluationRun(
                config=config,
                report=report,
            )
        )

    return runs


def format_case_report(case: RetrievalEvaluationCase) -> str:
    lines = [
        f'Query: "{case.query}"',
        f'Expected: {case.expected_document}'
        + (
            f" Chunk {case.expected_chunk}"
            if case.expected_chunk is not None
            else ""
        ),
        "Returned:",
    ]

    for row in case.rows:
        lines.append(
            f"{row.rank}. {row.document_title} Chunk {row.chunk_index} distance {row.distance:.3f}"
        )

    lines.append("PASS" if case.top1_correct else "CHECK")
    return "\n".join(lines)


def format_detailed_case_report(case: RetrievalEvaluationCase) -> str:
    lines = [
        f'Query: "{case.query}"',
        f'Expected document: {case.expected_document}',
        (
            f"Expected chunk: {case.expected_chunk}"
            if case.expected_chunk is not None
            else "Expected chunk: any chunk in the expected document"
        ),
        "Retrieved results:",
    ]

    for row in case.rows:
        lines.append(
            (
                f"{row.rank}. document={row.document_title} "
                f"document_id={row.document_id} "
                f"chunk_index={row.chunk_index} "
                f"distance={row.distance:.6f}"
            )
        )

    lines.append(
        (
            "Scoring compares case-insensitive document title first; "
            "if expected_chunk is provided, chunk_index must match exactly. "
            "Top-1/Top-3/Top-5 are derived from the rank of the first filtered "
            "result that matches those expected fields."
        )
    )
    lines.append("PASS" if case.top1_correct else "CHECK")
    return "\n".join(lines)


def format_scoring_rules() -> str:
    return "\n".join(
        [
            "Scoring rules:",
            "- Expected document is matched against the retrieved document title using case-insensitive comparison.",
            "- The retrieval title fallback is title -> original_filename -> filename.",
            "- If expected_chunk is provided, chunk_index must match exactly.",
            "- Top-1 correct means the first filtered matching result has rank 1.",
            "- Top-3 correct means the first filtered matching result has rank <= 3.",
            "- Top-5 correct means the first filtered matching result has rank <= 5.",
        ]
    )


def format_summary_report(report: RetrievalEvaluationReport) -> str:
    summary = report.summary

    return "\n".join(
        [
            f"Queries evaluated {summary.queries_evaluated}",
            f"Average Top1 accuracy {summary.average_top1_accuracy:.0%}",
            f"Average Top3 accuracy {summary.average_top3_accuracy:.0%}",
            f"Average Top5 accuracy {summary.average_top5_accuracy:.0%}",
            f"Average retrieval distance {summary.average_retrieval_distance:.2f}",
            f"Average retrieval latency {summary.average_retrieval_latency_ms:.0f} ms",
        ]
    )