"""Evaluation commands for ragged CLI."""

import json
import sys
from pathlib import Path
from typing import Literal, Optional, cast

import click

from src.cli.common import console
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def evaluate() -> None:
    """Evaluate RAG pipeline quality using various frameworks.

    \b
    Available evaluation methods:
        ragas - RAGAS framework evaluation (context, faithfulness, relevancy)

    \b
    Examples:
        ragged evaluate ragas test_set.json
        ragged evaluate ragas test_set.json --format json
    """
    pass


@evaluate.command()
@click.argument("test_set", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format (table for human-readable, json for programmatic use)",
)
def ragas(test_set: str, output_format: str) -> None:
    """Evaluate RAG pipeline using RAGAS framework.

    Test set should be a JSON file with format:
    [
        {
            "question": "What is RAG?",
            "ground_truth": "RAG is retrieval-augmented generation" (optional)
        },
        ...
    ]

    \b
    Examples:
        ragged evaluate ragas data/test_sets/baseline_v0.3.json
        ragged evaluate ragas my_tests.json --format json > results.json
    """
    from src.config.settings import get_settings
    from src.evaluation.ragas_evaluator import RAGASEvaluator
    from src.generation.ollama_client import OllamaClient
    from src.retrieval.bm25 import BM25Retriever
    from src.retrieval.hybrid import HybridRetriever
    from src.retrieval.retriever import Retriever
    from src.generation.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt

    console.print(f"[bold blue]Loading test set:[/bold blue] {test_set}")

    try:
        # Load test set
        test_path = Path(test_set)
        with open(test_path) as f:
            tests = json.load(f)

        if not isinstance(tests, list) or not tests:
            console.print("[bold red]Error:[/bold red] Test set must be non-empty list")
            sys.exit(1)

        # Validate test set format
        for i, test in enumerate(tests):
            if "question" not in test:
                console.print(
                    f"[bold red]Error:[/bold red] Test {i+1} missing 'question' field"
                )
                sys.exit(1)

        console.print(f"[green]✓[/green] Loaded {len(tests)} test queries\n")

        # Initialize components
        console.print("[bold]Initialising evaluation components...[/bold]")
        settings = get_settings()
        vector_retriever = Retriever()
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(
            vector_retriever=vector_retriever, bm25_retriever=bm25_retriever
        )
        llm = OllamaClient()
        evaluator = RAGASEvaluator()
        console.print("[green]✓[/green] Components ready\n")

        # Run queries
        console.print("[bold]Running queries and generating answers...[/bold]")
        questions = [t["question"] for t in tests]
        ground_truths = [t.get("ground_truth") for t in tests]

        answers = []
        contexts = []

        for i, question in enumerate(questions, 1):
            console.print(f"  [{i}/{len(questions)}] {question[:60]}...")

            # Retrieve
            chunks = hybrid_retriever.retrieve(
                question,
                top_k=5,
                method=cast(
                    Optional[Literal["vector", "bm25", "hybrid"]],
                    settings.retrieval_method,
                ),
            )
            context = [c.text for c in chunks]
            contexts.append(context)

            # Generate
            prompt = build_rag_prompt(question, chunks)
            answer = llm.generate(prompt, system=RAG_SYSTEM_PROMPT)
            answers.append(answer)

        console.print("[green]✓[/green] Queries complete\n")

        # Evaluate
        console.print("[bold]Running RAGAS evaluation...[/bold]")
        result = evaluator.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths if any(ground_truths) else None,
        )
        console.print("[green]✓[/green] Evaluation complete\n")

        # Display results
        if output_format == "table":
            console.print("[bold]RAGAS Evaluation Results:[/bold]")
            console.print(f"  Context Precision: {result.context_precision:.3f}")
            console.print(f"  Context Recall:    {result.context_recall:.3f}")
            console.print(f"  Faithfulness:      {result.faithfulness:.3f}")
            console.print(f"  Answer Relevancy:  {result.answer_relevancy:.3f}")
            console.print(f"  [bold]Overall Score:     {result.overall_score:.3f}[/bold]")
        else:
            print(json.dumps(result.to_dict(), indent=2))

    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Test set not found: {test_set}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON in test set: {e}")
        sys.exit(1)
    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[bold red]Error:[/bold red] Evaluation failed: {e}")
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)
