"""A/B testing framework for personalised ranking (v0.4.8).

Compare effectiveness of personalised vs non-personalised ranking.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict
import json
import statistics

from ragged.retrieval.retriever import RetrievedChunk
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ABTestResult:
    """Results from A/B test comparing ranking strategies.

    Attributes:
        test_id: Unique test identifier
        test_name: Human-readable test name
        variant_a_name: Name of first variant (e.g., "standard")
        variant_b_name: Name of second variant (e.g., "personalised")
        queries_tested: Number of queries tested
        variant_a_metrics: Metrics for variant A
        variant_b_metrics: Metrics for variant B
        improvement_pct: Percentage improvement (B vs A)
        p_value: Statistical significance (if calculated)
        winner: Which variant performed better
        created_at: Test creation timestamp
    """
    test_id: str
    test_name: str
    variant_a_name: str
    variant_b_name: str
    queries_tested: int
    variant_a_metrics: Dict[str, float]
    variant_b_metrics: Dict[str, float]
    improvement_pct: float
    p_value: Optional[float]
    winner: str
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'ABTestResult':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class ABTester:
    """A/B testing framework for ranking comparison.

    Compares two ranking strategies by evaluating them on the same queries
    and measuring relative performance.

    Example:
        >>> tester = ABTester()
        >>> result = tester.run_test(
        ...     test_name="Personalisation Test",
        ...     queries=["machine learning", "RAG systems"],
        ...     variant_a_results=[...],  # Standard results
        ...     variant_b_results=[...],  # Personalised results
        ... )
        >>> print(f"Winner: {result.winner}, Improvement: {result.improvement_pct:.1f}%")
    """

    def __init__(self):
        """Initialise A/B tester."""
        self._test_results: Dict[str, ABTestResult] = {}
        logger.info("ABTester initialised")

    def run_test(
        self,
        test_name: str,
        queries: List[str],
        variant_a_results: List[List[RetrievedChunk]],
        variant_b_results: List[List[RetrievedChunk]],
        variant_a_name: str = "standard",
        variant_b_name: str = "personalised",
    ) -> ABTestResult:
        """Run A/B test comparing two ranking variants.

        Args:
            test_name: Human-readable test name
            queries: List of test queries
            variant_a_results: Results for each query from variant A
            variant_b_results: Results for each query from variant B
            variant_a_name: Name for variant A
            variant_b_name: Name for variant B

        Returns:
            ABTestResult with comparison metrics

        Raises:
            ValueError: If queries and results lengths don't match
        """
        if len(queries) != len(variant_a_results) or len(queries) != len(variant_b_results):
            raise ValueError("Queries and results lists must have same length")

        # Calculate metrics for each variant
        logger.info(f"Running A/B test '{test_name}' on {len(queries)} queries")

        a_metrics = self._calculate_variant_metrics(variant_a_results)
        b_metrics = self._calculate_variant_metrics(variant_b_results)

        # Calculate improvement
        # Primary metric: average relevance score (approximated by position)
        a_avg_score = a_metrics["avg_score"]
        b_avg_score = b_metrics["avg_score"]

        if a_avg_score > 0:
            improvement_pct = ((b_avg_score - a_avg_score) / a_avg_score) * 100
        else:
            improvement_pct = 0.0

        # Determine winner
        if improvement_pct > 5.0:  # Threshold: 5% improvement
            winner = variant_b_name
        elif improvement_pct < -5.0:
            winner = variant_a_name
        else:
            winner = "tie"

        # Calculate p-value (simplified t-test)
        p_value = self._calculate_p_value(variant_a_results, variant_b_results)

        # Create result
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = ABTestResult(
            test_id=test_id,
            test_name=test_name,
            variant_a_name=variant_a_name,
            variant_b_name=variant_b_name,
            queries_tested=len(queries),
            variant_a_metrics=a_metrics,
            variant_b_metrics=b_metrics,
            improvement_pct=improvement_pct,
            p_value=p_value,
            winner=winner,
            created_at=datetime.now(),
        )

        # Store result
        self._test_results[test_id] = result

        logger.info(
            f"Test complete: {winner} wins with {improvement_pct:+.1f}% improvement "
            f"(p={p_value:.3f})"
        )

        return result

    def _calculate_variant_metrics(
        self,
        variant_results: List[List[RetrievedChunk]],
    ) -> Dict[str, float]:
        """Calculate metrics for a variant.

        Metrics calculated:
        - avg_score: Average relevance score (based on similarity scores)
        - avg_results: Average number of results returned
        - avg_top_score: Average score of top result

        Args:
            variant_results: Results for each query

        Returns:
            Dictionary of metrics
        """
        if not variant_results:
            return {
                "avg_score": 0.0,
                "avg_results": 0.0,
                "avg_top_score": 0.0,
            }

        # Calculate metrics
        scores = []
        result_counts = []
        top_scores = []

        for results in variant_results:
            result_counts.append(len(results))

            if results:
                # Average score for this query
                query_scores = [self._normalize_score(chunk.score) for chunk in results]
                scores.append(statistics.mean(query_scores))

                # Top result score
                top_scores.append(self._normalize_score(results[0].score))
            else:
                scores.append(0.0)
                top_scores.append(0.0)

        return {
            "avg_score": statistics.mean(scores) if scores else 0.0,
            "avg_results": statistics.mean(result_counts) if result_counts else 0.0,
            "avg_top_score": statistics.mean(top_scores) if top_scores else 0.0,
        }

    def _normalize_score(self, score: float) -> float:
        """Normalise distance score to similarity (0.0-1.0, higher is better).

        Args:
            score: Distance score from retrieval

        Returns:
            Normalized similarity score
        """
        # Assume score is distance (lower is better)
        # Convert to similarity: 1 / (1 + distance)
        return 1.0 / (1.0 + score)

    def _calculate_p_value(
        self,
        variant_a_results: List[List[RetrievedChunk]],
        variant_b_results: List[List[RetrievedChunk]],
    ) -> Optional[float]:
        """Calculate statistical significance (p-value).

        Uses simplified t-test on average scores.

        Args:
            variant_a_results: Results from variant A
            variant_b_results: Results from variant B

        Returns:
            P-value (0.0-1.0) or None if cannot calculate
        """
        # Extract average scores for each query
        a_scores = []
        b_scores = []

        for results in variant_a_results:
            if results:
                scores = [self._normalize_score(chunk.score) for chunk in results]
                a_scores.append(statistics.mean(scores))
            else:
                a_scores.append(0.0)

        for results in variant_b_results:
            if results:
                scores = [self._normalize_score(chunk.score) for chunk in results]
                b_scores.append(statistics.mean(scores))
            else:
                b_scores.append(0.0)

        if len(a_scores) < 2 or len(b_scores) < 2:
            return None

        # Simplified t-test (would need scipy for proper implementation)
        try:
            a_mean = statistics.mean(a_scores)
            b_mean = statistics.mean(b_scores)
            a_std = statistics.stdev(a_scores)
            b_std = statistics.stdev(b_scores)

            # Pooled standard deviation
            n_a = len(a_scores)
            n_b = len(b_scores)
            pooled_std = ((a_std ** 2 / n_a) + (b_std ** 2 / n_b)) ** 0.5

            if pooled_std > 0:
                # t-statistic
                t_stat = abs(b_mean - a_mean) / pooled_std

                # Approximate p-value (very simplified)
                # Proper implementation would use scipy.stats.t.sf()
                # This is rough approximation: p ≈ e^(-t²/2)
                import math
                p_value = math.exp(-t_stat ** 2 / 2)
                return min(p_value, 1.0)
            else:
                return 1.0  # No difference

        except statistics.StatisticsError:
            return None

    def get_test_result(self, test_id: str) -> Optional[ABTestResult]:
        """Retrieve stored test result.

        Args:
            test_id: Test identifier

        Returns:
            ABTestResult if found, None otherwise
        """
        return self._test_results.get(test_id)

    def list_tests(self) -> List[ABTestResult]:
        """List all stored test results.

        Returns:
            List of ABTestResult objects
        """
        return list(self._test_results.values())

    def export_results(self, test_id: str, filepath: str):
        """Export test results to JSON file.

        Args:
            test_id: Test identifier
            filepath: Output file path

        Raises:
            ValueError: If test not found
        """
        result = self.get_test_result(test_id)
        if result is None:
            raise ValueError(f"Test not found: {test_id}")

        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Test results exported to {filepath}")

    def generate_report(self, test_id: str) -> str:
        """Generate human-readable test report.

        Args:
            test_id: Test identifier

        Returns:
            Formatted report string

        Raises:
            ValueError: If test not found
        """
        result = self.get_test_result(test_id)
        if result is None:
            raise ValueError(f"Test not found: {test_id}")

        report = f"""
A/B Test Report: {result.test_name}
{'=' * 60}
Test ID: {result.test_id}
Created: {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Configuration:
- Variant A: {result.variant_a_name}
- Variant B: {result.variant_b_name}
- Queries Tested: {result.queries_tested}

Results:

{result.variant_a_name.upper()} Metrics:
  Average Score:     {result.variant_a_metrics['avg_score']:.4f}
  Average Results:   {result.variant_a_metrics['avg_results']:.1f}
  Avg Top Score:     {result.variant_a_metrics['avg_top_score']:.4f}

{result.variant_b_name.upper()} Metrics:
  Average Score:     {result.variant_b_metrics['avg_score']:.4f}
  Average Results:   {result.variant_b_metrics['avg_results']:.1f}
  Avg Top Score:     {result.variant_b_metrics['avg_top_score']:.4f}

Analysis:
  Improvement:       {result.improvement_pct:+.2f}%
  Statistical Sig:   p={result.p_value:.3f if result.p_value else 'N/A'}
  Winner:            {result.winner.upper()}

Interpretation:
"""
        if result.p_value and result.p_value < 0.05:
            report += f"  ✓ Result is statistically significant (p<0.05)\n"
        else:
            report += f"  ⚠ Result may not be statistically significant\n"

        if abs(result.improvement_pct) > 10:
            report += f"  ✓ Large practical difference (>10%)\n"
        elif abs(result.improvement_pct) > 5:
            report += f"  ✓ Moderate practical difference (>5%)\n"
        else:
            report += f"  ~ Small practical difference (<5%)\n"

        return report
