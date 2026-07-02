from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import asyncpg

from app.config import settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run retrieval evaluation against the current corpus.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).with_name("retrieval_dataset.json"),
        help="Path to the retrieval evaluation dataset.",
    )
    parser.add_argument(
        "--user-id",
        type=int,
        required=True,
        help="User ID whose documents should be evaluated.",
    )
    parser.add_argument(
        "--top-k-values",
        type=str,
        default="5",
        help="Comma-separated top_k values to evaluate.",
    )
    parser.add_argument(
        "--threshold-values",
        type=str,
        default="0.35",
        help="Comma-separated distance thresholds to evaluate.",
    )
    return parser


async def _fetch_ranked_chunks(
    query: str,
    user_id: int,
    top_k: int,
) -> list[tuple]:
    from app.services.ai.embeddings.embedding_service import EmbeddingService
    from app.services.ai.embeddings.providers.ollama import (
        OllamaEmbeddingProvider,
    )
    from app.services.retrieval.ranking import RetrievedChunk

    embedding_service = EmbeddingService(
        OllamaEmbeddingProvider(),
    )

    embedding = await embedding_service.embed(query)

    embedding_literal = "[" + ",".join(
        f"{value:.10f}" for value in embedding
    ) + "]"

    database_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://",
        "postgresql://",
    )

    sql = """
        SELECT
            dc.id AS chunk_id,
            d.id AS document_id,
            COALESCE(d.title, d.original_filename, d.stored_filename) AS document_title,
            dc.chunk_index,
            dc.token_count,
            dc.content,
            dc.embedding <=> CAST($1 AS vector) AS distance
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.user_id = $2
          AND d.status = 'READY'
        ORDER BY distance ASC
        LIMIT $3
    """

    connection = await asyncpg.connect(database_url)
    try:
        records = await connection.fetch(
            sql,
            embedding_literal,
            user_id,
            top_k,
        )
    finally:
        await connection.close()

    return [
        RetrievedChunk(
            document_id=record["document_id"],
            document_title=record["document_title"],
            chunk_id=record["chunk_id"],
            chunk_index=record["chunk_index"],
            token_count=record["token_count"],
            distance=float(record["distance"]),
            content=record["content"],
        )
        for record in records
    ]


async def _run(args: argparse.Namespace) -> int:
    from app.services.retrieval.evaluation import (
        RetrievalEvaluationConfig,
        evaluate_dataset,
        evaluate_grid,
        format_detailed_case_report,
        format_case_report,
        format_summary_report,
        format_scoring_rules,
        load_dataset,
    )

    dataset = load_dataset(args.dataset)

    top_k_values = [int(value) for value in args.top_k_values.split(",") if value]
    threshold_values = [
        float(value)
        for value in args.threshold_values.split(",")
        if value
    ]

    async def fetch_ranked_chunks(
        query: str,
        top_k: int,
    ) -> list[tuple]:
        return await _fetch_ranked_chunks(
            query,
            args.user_id,
            top_k,
        )

    if len(top_k_values) == 1 and len(threshold_values) == 1:
        report = await evaluate_dataset(
            dataset,
            fetch_ranked_chunks,
            top_k=top_k_values[0],
            threshold=threshold_values[0],
        )

        print(format_scoring_rules())
        print()

        for case in report.cases[:5]:
            print(format_detailed_case_report(case))
            print()

        print(format_summary_report(report))
        print()

        for case in report.cases:
            print(format_case_report(case))
            print()
        return 0

    configs = [
        RetrievalEvaluationConfig(
            top_k=top_k,
            threshold=threshold,
        )
        for top_k in top_k_values
        for threshold in threshold_values
    ]

    runs = await evaluate_grid(
        dataset,
        fetch_ranked_chunks,
        configs,
    )

    print(format_scoring_rules())
    print()

    for run in runs:
        print(
            f"Config top_k={run.config.top_k} threshold={run.config.threshold:.2f}"
        )
        for case in run.report.cases[:5]:
            print(format_detailed_case_report(case))
            print()
        print(format_summary_report(run.report))
        print()

    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
