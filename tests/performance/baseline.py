"""Baseline management for performance regression tests.

v0.2.9: Load, compare, and validate performance baselines.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Single benchmark result."""
    
    mean: float
    median: float
    std_dev: float
    min: float
    max: float
    iterations: int


class BaselineManager:
    """Manage performance baselines for regression detection."""
    
    def __init__(self, baseline_path: Optional[Path] = None):
        """Initialize baseline manager.
        
        Args:
            baseline_path: Path to baseline JSON file
        """
        if baseline_path is None:
            baseline_path = Path(__file__).parent / "baseline.json"
        
        self.baseline_path = Path(baseline_path)
        self._baseline: Optional[Dict[str, Any]] = None
    
    def load_baseline(self) -> Dict[str, Any]:
        """Load baseline from JSON file.
        
        Returns:
            Baseline dictionary
            
        Raises:
            FileNotFoundError: If baseline file doesn't exist
        """
        if not self.baseline_path.exists():
            logger.warning(f"Baseline not found: {self.baseline_path}")
            raise FileNotFoundError(f"Baseline not found: {self.baseline_path}")
        
        with open(self.baseline_path, "r") as f:
            self._baseline = json.load(f)
        
        logger.info(f"Loaded baseline: {self._baseline.get('version', 'unknown')}")
        return self._baseline
    
    def get_benchmark(self, name: str) -> Optional[BenchmarkResult]:
        """Get baseline result for a specific benchmark.
        
        Args:
            name: Benchmark name
            
        Returns:
            Baseline result or None if not found
        """
        if self._baseline is None:
            try:
                self.load_baseline()
            except FileNotFoundError:
                return None
        
        if self._baseline is None:
            return None
        
        benchmarks = self._baseline.get("benchmarks", {})
        result_data = benchmarks.get(name)
        
        if result_data is None:
            logger.warning(f"No baseline for benchmark: {name}")
            return None
        
        return BenchmarkResult(**result_data)
    
    def save_baseline(
        self,
        version: str,
        benchmarks: Dict[str, BenchmarkResult]
    ) -> None:
        """Save new baseline to JSON file.
        
        Args:
            version: Version identifier
            benchmarks: Dictionary of benchmark results
        """
        from datetime import datetime
        
        baseline_data = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {
                name: asdict(result)
                for name, result in benchmarks.items()
            }
        }
        
        with open(self.baseline_path, "w") as f:
            json.dump(baseline_data, f, indent=2)
        
        logger.info(f"Saved baseline: {version} ({len(benchmarks)} benchmarks)")
    
    def compare(
        self,
        name: str,
        current: BenchmarkResult,
        threshold: float = 0.05
    ) -> bool:
        """Compare current result against baseline.
        
        Args:
            name: Benchmark name
            current: Current benchmark result
            threshold: Regression threshold (default 5%)
            
        Returns:
            True if within threshold, False if regression detected
        """
        baseline = self.get_benchmark(name)
        
        if baseline is None:
            logger.warning(f"No baseline for {name}, accepting current")
            return True
        
        # Compare mean times
        ratio = current.mean / baseline.mean
        
        if ratio > (1.0 + threshold):
            logger.error(
                f"REGRESSION in {name}: "
                f"current={current.mean:.3f}s vs baseline={baseline.mean:.3f}s "
                f"({(ratio-1)*100:.1f}% slower)"
            )
            return False
        
        if ratio < (1.0 - threshold):
            logger.info(
                f"IMPROVEMENT in {name}: "
                f"current={current.mean:.3f}s vs baseline={baseline.mean:.3f}s "
                f"({(1-ratio)*100:.1f}% faster)"
            )
        
        return True
