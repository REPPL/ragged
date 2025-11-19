"""Tests for baseline management.

v0.2.9: Test baseline loading, comparison, and validation.
"""

import pytest
import json
import tempfile
from pathlib import Path

from tests.performance.baseline import BaselineManager, BenchmarkResult


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""
    
    def test_create_result(self):
        """Test creating benchmark result."""
        result = BenchmarkResult(
            mean=1.5,
            median=1.4,
            std_dev=0.2,
            min=1.2,
            max=1.9,
            iterations=10
        )
        
        assert result.mean == 1.5
        assert result.median == 1.4
        assert result.iterations == 10


class TestBaselineManager:
    """Tests for BaselineManager."""
    
    @pytest.fixture
    def temp_baseline(self):
        """Create temporary baseline file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            baseline_data = {
                "version": "test-0.1.0",
                "timestamp": "2025-01-01T00:00:00Z",
                "benchmarks": {
                    "test-benchmark": {
                        "mean": 1.0,
                        "median": 0.9,
                        "std_dev": 0.1,
                        "min": 0.8,
                        "max": 1.2,
                        "iterations": 10
                    }
                }
            }
            json.dump(baseline_data, f)
            path = Path(f.name)
        
        yield path
        
        # Cleanup
        if path.exists():
            path.unlink()
    
    def test_load_baseline(self, temp_baseline):
        """Test loading baseline from file."""
        manager = BaselineManager(baseline_path=temp_baseline)
        baseline = manager.load_baseline()
        
        assert baseline["version"] == "test-0.1.0"
        assert "test-benchmark" in baseline["benchmarks"]
    
    def test_load_nonexistent_baseline(self):
        """Test loading baseline that doesn't exist."""
        manager = BaselineManager(baseline_path=Path("/nonexistent/baseline.json"))
        
        with pytest.raises(FileNotFoundError):
            manager.load_baseline()
    
    def test_get_benchmark(self, temp_baseline):
        """Test retrieving specific benchmark."""
        manager = BaselineManager(baseline_path=temp_baseline)
        result = manager.get_benchmark("test-benchmark")
        
        assert result is not None
        assert result.mean == 1.0
        assert result.median == 0.9
        assert result.iterations == 10
    
    def test_get_nonexistent_benchmark(self, temp_baseline):
        """Test retrieving benchmark that doesn't exist."""
        manager = BaselineManager(baseline_path=temp_baseline)
        result = manager.get_benchmark("nonexistent-benchmark")
        
        assert result is None
    
    def test_save_baseline(self):
        """Test saving baseline to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = Path(f.name)
        
        try:
            manager = BaselineManager(baseline_path=path)
            
            benchmarks = {
                "test-1": BenchmarkResult(1.0, 0.9, 0.1, 0.8, 1.2, 10),
                "test-2": BenchmarkResult(2.0, 1.9, 0.2, 1.7, 2.3, 10)
            }
            
            manager.save_baseline("test-0.2.0", benchmarks)
            
            # Verify saved
            assert path.exists()
            
            # Load and verify
            with open(path, 'r') as f:
                data = json.load(f)
            
            assert data["version"] == "test-0.2.0"
            assert len(data["benchmarks"]) == 2
            assert "test-1" in data["benchmarks"]
            assert "test-2" in data["benchmarks"]
        
        finally:
            if path.exists():
                path.unlink()
    
    def test_compare_within_threshold(self, temp_baseline):
        """Test comparison when within threshold."""
        manager = BaselineManager(baseline_path=temp_baseline)
        
        # Current result is 1.04s (4% slower, within 5% threshold)
        current = BenchmarkResult(
            mean=1.04,
            median=1.03,
            std_dev=0.1,
            min=0.95,
            max=1.15,
            iterations=10
        )
        
        passed = manager.compare("test-benchmark", current, threshold=0.05)
        assert passed is True
    
    def test_compare_regression_detected(self, temp_baseline):
        """Test comparison when regression detected."""
        manager = BaselineManager(baseline_path=temp_baseline)
        
        # Current result is 1.10s (10% slower, exceeds 5% threshold)
        current = BenchmarkResult(
            mean=1.10,
            median=1.09,
            std_dev=0.1,
            min=1.0,
            max=1.2,
            iterations=10
        )
        
        passed = manager.compare("test-benchmark", current, threshold=0.05)
        assert passed is False
    
    def test_compare_improvement(self, temp_baseline):
        """Test comparison when performance improved."""
        manager = BaselineManager(baseline_path=temp_baseline)
        
        # Current result is 0.85s (15% faster)
        current = BenchmarkResult(
            mean=0.85,
            median=0.84,
            std_dev=0.08,
            min=0.75,
            max=0.95,
            iterations=10
        )
        
        passed = manager.compare("test-benchmark", current, threshold=0.05)
        assert passed is True  # Improvements always pass
    
    def test_compare_no_baseline(self):
        """Test comparison when no baseline exists."""
        manager = BaselineManager(baseline_path=Path("/nonexistent/baseline.json"))
        
        current = BenchmarkResult(1.5, 1.4, 0.2, 1.2, 1.8, 10)
        
        # Should pass (accept current as new baseline)
        passed = manager.compare("new-benchmark", current)
        assert passed is True
    
    def test_compare_exact_threshold(self, temp_baseline):
        """Test comparison at exact threshold boundary."""
        manager = BaselineManager(baseline_path=temp_baseline)
        
        # Current result is exactly 1.05s (exactly 5% slower)
        current = BenchmarkResult(
            mean=1.05,
            median=1.04,
            std_dev=0.1,
            min=0.95,
            max=1.15,
            iterations=10
        )
        
        # At exactly 5%, should pass (uses > not >=)
        passed = manager.compare("test-benchmark", current, threshold=0.05)
        assert passed is True
        
        # Just over 5% should fail
        current_over = BenchmarkResult(
            mean=1.051,
            median=1.05,
            std_dev=0.1,
            min=0.95,
            max=1.15,
            iterations=10
        )
        
        passed_over = manager.compare("test-benchmark", current_over, threshold=0.05)
        assert passed_over is False
